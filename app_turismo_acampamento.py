import os
import folium
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import streamlit as st
from streamlit_folium import st_folium

# ---------------------------------------------------------
# 1. CONFIGURAÇÃO DE PÁGINA & TEMA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Inteligência de Mercado | Acampamentos Turísticos",
    page_icon="🏕️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E3A8A; }
    .sub-header { font-size: 1.1rem; color: #475569; margin-bottom: 15px; }
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    "<div class='main-header'>🏕️ Inteligência de Mercado | Acampamentos Turísticos</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<div class='sub-header'>Análise competitiva e presença regional de estabelecimentos 'Acampamento Turístico', extraído do Ministério do Turismo.</div>",
    unsafe_allow_html=True,
)

with st.expander(
    "📖 **Conceito Legal de Acampamento Turístico (Diretrizes MTur/Cadastur)**",
    expanded=False,
):
    st.markdown("""
    **Definição Oficial (Lei Geral do Turismo - Lei nº 11.771/2008):**  
    Consideram-se **Acampamentos Turísticos** as áreas ao ar livre dotadas de infraestrutura e instalações destinadas ao alojamento temporário de praticantes de campismo, com prestação de serviços de apoio às atividades recreativas e de lazer.
    """)


# ---------------------------------------------------------
# 2. CONEXÃO E CARGA DE DADOS
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def carregar_dados():
    if "mysql" in st.secrets:
        db = st.secrets["mysql"]
        host, user, password, database, port = (
            db["host"],
            db["user"],
            db["password"],
            db["database"],
            db["port"],
        )
    else:
        host = "162.241.2.244"
        user = "tucfur51_pasquacosta"
        password = "alttycc1298!!"
        database = "tucfur51_vidaz_dev"
        port = 3306

    engine = create_engine(
        f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    )

    query = """
    SELECT 
        t.*,
        g.latitude,
        g.longitude,
        COALESCE(g.faixa_distancia, 'Não mapeado') AS faixa_distancia,
        COALESCE(g.distancia_km, 9999) AS distancia_km
    FROM tb_acampamento_turistico t
    LEFT JOIN tb_geolocalizacao_municipios g 
        ON LOWER(t.municipio) = LOWER(g.municipio) 
       AND t.uf = g.uf;
    """
    df = pd.read_sql(query, con=engine)

    # Tratamento de contagem de idiomas
    def contar_idiomas(val):
        if pd.isna(val) or val in ["-", "Não informado", ""]:
            return 0
        return len([i.strip() for i in str(val).split(",") if i.strip()])

    df["qtd_idiomas"] = df["idiomas"].apply(contar_idiomas)
    df["tem_multilingue_2plus"] = df["qtd_idiomas"] >= 2
    return df


try:
    df_raw = carregar_dados()
except Exception as e:
    st.error(f"⚠️ Erro ao conectar ao banco de dados: {e}")
    st.stop()


# ---------------------------------------------------------
# 3. FILTROS LATERAIS REFORMULADOS
# ---------------------------------------------------------
st.sidebar.title("Filtros de Pesquisa")

ufs_disponiveis = sorted(df_raw["uf"].dropna().unique())
default_ufs = [uf for uf in ["SP", "MG", "RJ"] if uf in ufs_disponiveis]
selected_ufs = st.sidebar.multiselect(
    "Estados (UF):", options=ufs_disponiveis, default=default_ufs
)

periodos_disponiveis = sorted(df_raw["periodo_trimestre"].dropna().unique())
selected_periodo = st.sidebar.selectbox(
    "Trimestre de Análise:",
    options=periodos_disponiveis,
    index=len(periodos_disponiveis) - 1 if len(periodos_disponiveis) > 0 else 0,
)

# Abordagem Negocial/Estratégica para Faixas de Capacidade
opcoes_capacidade = {
    "Exclusivo / Boutique (Até 150 hóspedes)": (0, 150),
    "Médio Porte (151 a 500 hóspedes)": (151, 500),
    "Grande Porte (501 a 1.500 hóspedes)": (501, 1500),
    "Mega Empreendimentos (Mais de 1.500 hóspedes)": (1501, 999999),
    "Todos os Portes": (0, 999999),
}

perfil_cap = st.sidebar.selectbox(
    "Perfil de Porte / Capacidade:",
    options=list(opcoes_capacidade.keys()),
    index=0,  # Default na faixa exclusiva até 150
    help="Filtra estabelecimentos de acordo com o porte de operação.",
)

min_cap, max_cap = opcoes_capacidade[perfil_cap]

df_filtrado = df_raw[
    (df_raw["uf"].isin(selected_ufs))
    & (df_raw["capacidade"] >= min_cap)
    & (df_raw["capacidade"] <= max_cap)
    & (df_raw["periodo_trimestre"] == selected_periodo)
]


# ---------------------------------------------------------
# 4. KPIS
# ---------------------------------------------------------
col_k1, col_k2, col_k3, col_k4 = st.columns(4)
with col_k1:
    st.metric("Estabelecimentos Mapeados", len(df_filtrado))
with col_k2:
    st.metric("Capacidade Total", f"{int(df_filtrado['capacidade'].sum()):,}")
with col_k3:
    st.metric(
        "Atendimento Multilíngue (2+ Idiomas)",
        len(df_filtrado[df_filtrado["tem_multilingue_2plus"]]),
    )
with col_k4:
    media_c = (
        round(df_filtrado["capacidade"].mean(), 1)
        if len(df_filtrado) > 0
        else 0
    )
    st.metric("Capacidade Média / Local", media_c)

st.markdown("---")


# ---------------------------------------------------------
# 5. ABAS NAVEGÁVEIS
# ---------------------------------------------------------
tab_mapa, tab_distancia, tab_historico, tab_insights, tab_dados = st.tabs(
    [
        "🗺️ Mapa de Acampamentos turísticos",
        "📍 Análise de presença no Sul de Minas",
        "📈 Série Histórica (24 Meses)",
        "📊 Perfil de Atendimento e Porte",
        "📋 Base Mapeada de Concorrentes",
    ]
)


# --- ABA 1: MAPA ---
with tab_mapa:
    st.subheader("Mapeamento Geográfico da Concorrência")
    m = folium.Map(
        location=[-22.4500, -45.9000], zoom_start=7, tiles="OpenStreetMap"
    )

    df_mapa = df_filtrado.dropna(subset=["latitude", "longitude"])
    for idx, row in df_mapa.iterrows():
        nome = row.get("nome_fantasia", "Sem Nome")
        muni = row.get("municipio", "Não informado")
        cap = row.get("capacidade", 0)
        faixa = row.get("faixa_distancia", "N/A")

        popup_html = f"""
            <div style="font-family: Arial; width: 220px;">
                <h4 style="margin:0; color:#1E3A8A;">{nome}</h4>
                <p style="margin:3px 0;"><b>Município:</b> {muni} ({row.get('uf')})</p>
                <p style="margin:3px 0;"><b>Capacidade:</b> {cap} hóspedes</p>
                <p style="margin:3px 0;"><b>Faixa Raio:</b> {faixa}</p>
            </div>
        """
        cor = "orange" if row.get("tem_multilingue_2plus") else "blue"
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{nome} ({muni})",
            icon=folium.Icon(color=cor, icon="campground", prefix="fa"),
        ).add_to(m)

    st_folium(m, width=1100, height=500)


# --- ABA 2: PRESENÇA NO SUL DE MINAS (RAIOS DE DISTÂNCIA) ---
with tab_distancia:
    st.subheader("Análise de Adensamento por Faixa de Distância (Sul de Minas)")
    st.write(
        "Distribuição de estabelecimentos e capacidade instalada a partir do polo focal."
    )

    ordem_faixas = [
        "Até 20 km",
        "21 a 100 km",
        "101 a 200 km",
        "201 a 300 km",
        "301 a 400 km",
        "401 a 500 km",
        "Mais de 500 km",
        "Não mapeado",
    ]

    df_faixas = (
        df_filtrado.groupby("faixa_distancia")
        .agg(
            qtd_locais=("numero_de_inscricao_do_cnpj", "count"),
            capacidade_total=("capacidade", "sum"),
            locais_multilingues_2plus=("tem_multilingue_2plus", "sum"),
        )
        .reindex(ordem_faixas)
        .dropna(subset=["qtd_locais"])
        .reset_index()
    )

    col_d1, col_d2 = st.columns([1, 1])

    with col_d1:
        st.markdown("#### Matriz por Raio de Distância")
        st.dataframe(
            df_faixas,
            use_container_width=True,
            hide_index=True,
            column_config={
                "faixa_distancia": "Faixa de Distância",
                "qtd_locais": "Qtd Locais",
                "capacidade_total": "Capacidade (Leitos)",
                "locais_multilingues_2plus": "Locais (2+ Idiomas)",
            },
        )

    with col_d2:
        fig_faixa = px.bar(
            df_faixas,
            x="faixa_distancia",
            y="capacidade_total",
            color="locais_multilingues_2plus",
            title="Capacidade em Leitos por Raio e Oferta Multilíngue",
            labels={
                "faixa_distancia": "Raio de Distância",
                "capacidade_total": "Capacidade Total",
                "locais_multilingues_2plus": "Locais com 2+ Idiomas",
            },
            color_continuous_scale="Blues",
        )
        st.plotly_chart(fig_faixa, use_container_width=True)


# --- ABA 3: SÉRIE HISTÓRICA ---
with tab_historico:
    st.subheader("Evolução Histórica da Oferta (24 Meses)")
    df_hist_full = df_raw[
        (df_raw["uf"].isin(selected_ufs))
        & (df_raw["capacidade"] >= min_cap)
        & (df_raw["capacidade"] <= max_cap)
    ]
    hist_line = (
        df_hist_full.groupby(["periodo_trimestre", "uf"])[
            "numero_de_inscricao_do_cnpj"
        ]
        .count()
        .reset_index()
    )

    fig_evol = px.line(
        hist_line,
        x="periodo_trimestre",
        y="numero_de_inscricao_do_cnpj",
        color="uf",
        markers=True,
        title="Evolução do Número de Estabelecimentos por Estado",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    st.plotly_chart(fig_evol, use_container_width=True)


# --- ABA 4: NOVAS SUGESTÕES DE ANÁLISE ---
with tab_insights:
    st.subheader("Indicadores Complementares de Mercado")
    col_i1, col_i2 = st.columns(2)

    with col_i1:
        st.markdown("#### Distribuição por Porte Empresarial")
        fig_porte = px.pie(
            df_filtrado,
            names="porte",
            title="Proporção de Estabelecimentos por Porte Declarado",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Darkmint,
        )
        st.plotly_chart(fig_porte, use_container_width=True)

    with col_i2:
        st.markdown("#### Sofisticação de Atendimento (Idiomas)")
        df_idiomas = (
            df_filtrado["qtd_idiomas"].value_counts().reset_index()
        )
        df_idiomas.columns = ["qtd_idiomas", "total"]
        fig_id = px.bar(
            df_idiomas,
            x="qtd_idiomas",
            y="total",
            title="Quantidade de Idiomas Oferecidos na Recepção",
            labels={
                "qtd_idiomas": "Nº de Idiomas Atendidos",
                "total": "Qtd Estabelecimentos",
            },
            color="total",
            color_continuous_scale="Greens",
        )
        st.plotly_chart(fig_id, use_container_width=True)


# --- ABA 5: TABELA DADOS ---
with tab_dados:
    st.subheader("Base Mapeada de Concorrentes")
    cols_exibir = [
        col
        for col in [
            "uf",
            "municipio",
            "faixa_distancia",
            "nome_fantasia",
            "porte",
            "capacidade",
            "idiomas",
            "telefone_comercial",
            "e_mail_comercial",
        ]
        if col in df_filtrado.columns
    ]
    st.dataframe(df_filtrado[cols_exibir], use_container_width=True)
