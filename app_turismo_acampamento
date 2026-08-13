import os
import folium
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import streamlit as st
from streamlit_folium import st_folium

# ---------------------------------------------------------
# 1. CONFIGURAÇÃO DE PÁGINA & TEMA VISUAL
# ---------------------------------------------------------
st.set_page_config(
    page_title="Inteligência de Mercado | Acampamentos Turísticos",
    page_icon="🪿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilização CSS personalizada
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
    "<div class='main-header'>🪿 Mundo Ganso | Inteligência de Mercado</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<div class='sub-header'>Análise competitiva e presença regional de estabelecimentos 'Acampamento Turístico', extraído do Ministério do Turismo.</div>",
    unsafe_allow_html=True,
)

# Bloco Conceitual do MTur
with st.expander(
    "📖 **Conceito Legal de Acampamento Turístico (Diretrizes MTur/Cadastur)**",
    expanded=False,
):
    st.markdown("""
    **Definição Oficial (Lei Geral do Turismo - Lei nº 11.771/2008):**  
    Consideram-se **Acampamentos Turísticos** as áreas ao ar livre dotadas de infraestrutura e instalações destinadas ao alojamento temporário de praticantes de campismo, com prestação de serviços de apoio às atividades recreativas e de lazer.
    """)


# ---------------------------------------------------------
# 2. CONEXÃO COM O BANCO DE DADOS (HOSTGATOR / SECRETS)
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def carregar_dados():
    # Detecta se está rodando no Streamlit Cloud (via Secrets) ou localmente
    if "mysql" in st.secrets:
        db = st.secrets["mysql"]
        host = db["host"]
        user = db["user"]
        password = db["password"]
        database = db["database"]
        port = db["port"]
    else:
        # Fallback de conexão direta com a HostGator
        host = "162.241.2.244"
        user = "tucfur51_pasquacosta"
        password = "alttycc1298!!"  # Substitua pela sua senha da HostGator se rodar localmente
        database = "tucfur51_vidaz_dev"
        port = 3306

    engine = create_engine(
        f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    )

    query = """
    SELECT 
        t.*,
        g.latitude,
        g.longitude
    FROM tb_acampamento_turistico t
    LEFT JOIN tb_geolocalizacao_municipios g 
        ON LOWER(t.municipio) = LOWER(g.municipio) 
       AND t.uf = g.uf;
    """
    return pd.read_sql(query, con=engine)


try:
    df_raw = carregar_dados()
except Exception as e:
    st.error(
        f"⚠️ Não foi possível conectar ao banco de dados na HostGator. Detalhes: {e}"
    )
    st.stop()


# ---------------------------------------------------------
# 3. FILTROS NA BARRA LATERAL (SIDEBAR)
# ---------------------------------------------------------
st.sidebar.image(
    "https://img.icons8.com/color/96/goose.png", width=70
)  # Ícone decorativo
st.sidebar.title("Filtros do Estudo")

# Filtro de Estado (UF)
ufs_disponiveis = sorted(df_raw["uf"].dropna().unique())
default_ufs = [uf for uf in ["SP", "MG", "RJ"] if uf in ufs_disponiveis]
selected_ufs = st.sidebar.multiselect(
    "Estados (UF):", options=ufs_disponiveis, default=default_ufs
)

# Filtro do Trimestre
periodos_disponiveis = sorted(df_raw["periodo_trimestre"].dropna().unique())
selected_periodo = st.sidebar.selectbox(
    "Trimestre de Análise:",
    options=periodos_disponiveis,
    index=len(periodos_disponiveis) - 1 if len(periodos_disponiveis) > 0 else 0,
)

# Filtro de Exclusividade (Capacidade Limite)
cap_max_bd = int(df_raw["capacidade"].max()) if "capacidade" in df_raw else 2000
cap_limite = st.sidebar.slider(
    "Capacidade Máxima (Exclusividade/Glamping):",
    min_value=10,
    max_value=cap_max_bd,
    value=300,
    help="Filtra locais com menor adensamento de público.",
)

# Aplicação dos Filtros no DataFrame
df_filtrado = df_raw[
    (df_raw["uf"].isin(selected_ufs))
    & (df_raw["capacidade"] <= cap_limite)
    & (df_raw["periodo_trimestre"] == selected_periodo)
]


# ---------------------------------------------------------
# 4. PAINEL DE INDICADORES (KPIS)
# ---------------------------------------------------------
col_k1, col_k2, col_k3, col_k4 = st.columns(4)

with col_k1:
    st.metric(
        "Estabelecimentos Mapeados",
        len(df_filtrado),
        help="Total de CNPJs cadastrados no recorte",
    )

with col_k2:
    cap_tot = int(df_filtrado["capacidade"].sum())
    st.metric(
        "Capacidade Total (Hóspedes)",
        f"{cap_tot:,}",
        help="Soma da capacidade declarada",
    )

with col_k3:
    multilingue_cnt = len(
        df_filtrado[~df_filtrado["idiomas"].isin(["-", "Não informado", ""])]
    )
    st.metric(
        "Oferta Multilíngue (Atendimento)",
        multilingue_cnt,
        help="Indicador de sofisticação de atendimento",
    )

with col_k4:
    media_cap = (
        round(df_filtrado["capacidade"].mean(), 1)
        if len(df_filtrado) > 0
        else 0
    )
    st.metric("Capacidade Média / Local", media_cap)

st.markdown("---")


# ---------------------------------------------------------
# 5. ABAS PRINCIPAIS DE NAVEGAÇÃO
# ---------------------------------------------------------
tab_mapa, tab_regiao, tab_historico, tab_dados = st.tabs(
    [
        "🗺️ Mapa Leaflet de Concorrentes",
        "📍 Análise de Proximidade (Query 3)",
        "📈 Série Histórica 24 Meses",
        "📋 Tabela Completa de Concorrentes",
    ]
)


# --- ABA 1: MAPA LEAFLET INTERATIVO ---
with tab_mapa:
    st.subheader("Mapeamento Geográfico da Concorrência (Coordenadas Reais)")
    st.write(
        "Localização espacial dos estabelecimentos baseada no centro geográfico dos municípios."
    )

    # Centro geográfico inicial do mapa (Serra da Mantiqueira / Sul de MG)
    lat_centro, lon_centro = -22.4500, -45.9000

    m = folium.Map(
        location=[lat_centro, lon_centro], zoom_start=8, tiles="OpenStreetMap"
    )

    # Ponto de Referência do MUNDO GANSO
    folium.Marker(
        [-22.3833, -46.0833],
        popup="<b>Mundo Ganso (Complexo)</b>",
        tooltip="📍 SEU EMPREENDIMENTO (Mundo Ganso)",
        icon=folium.Icon(color="green", icon="star", prefix="fa"),
    ).add_to(m)

    # Filtra apenas registros que contêm coordenadas
    df_mapa = df_filtrado.dropna(subset=["latitude", "longitude"])

    for idx, row in df_mapa.iterrows():
        nome = row.get("nome_fantasia", "Sem Nome")
        muni = row.get("municipio", "Não informado")
        cap = row.get("capacidade", 0)
        idioma = row.get("idiomas", "-")
        lat = row.get("latitude")
        lon = row.get("longitude")

        popup_html = f"""
            <div style="font-family: Arial; width: 220px;">
                <h4 style="margin:0; color:#1E3A8A;">{nome}</h4>
                <p style="margin:5px 0;"><b>Município:</b> {muni} ({row.get('uf')})</p>
                <p style="margin:5px 0;"><b>Capacidade:</b> {cap} hóspedes</p>
                <p style="margin:5px 0;"><b>Idiomas:</b> {idioma}</p>
            </div>
        """

        cor_pino = (
            "orange" if idioma not in ["-", "Não informado", ""] else "blue"
        )

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{nome} ({muni})",
            icon=folium.Icon(color=cor_pino, icon="campground", prefix="fa"),
        ).add_to(m)

    st_folium(m, width=1100, height=500)
    st.info(
        "💡 **Legenda:** Pinos **Laranjas** indicam locais com atendimento multilíngue. Pinos **Azuis** indicam atendimento padrão."
    )


# --- ABA 2: ANÁLISE DE PROXIMIDADE (QUERY 3) ---
with tab_regiao:
    st.subheader("Análise de Adensamento e Oferta por Município (Proximidade)")
    st.write(
        "Concentração de leitos e número de estabelecimentos nos principais municípios do recorte selecionado."
    )

    col_m1, col_m2 = st.columns([1, 2])

    with col_m1:
        st.markdown("#### Top Municípios em Destaque")
        df_q3 = (
            df_filtrado.groupby("municipio")
            .agg(
                qtd_estabelecimentos=("numero_de_inscricao_do_cnpj", "count"),
                capacidade_total=("capacidade", "sum"),
                media_capacidade=("capacidade", "mean"),
            )
            .reset_index()
            .sort_values(by="capacidade_total", ascending=False)
        )

        st.dataframe(
            df_q3.head(12),
            use_container_width=True,
            hide_index=True,
        )

    with col_m2:
        fig_bar_q3 = px.bar(
            df_q3.head(10),
            x="capacidade_total",
            y="municipio",
            orientation="h",
            color="qtd_estabelecimentos",
            title="Capacidade Total Instalada nos Principais Municípios",
            labels={
                "capacidade_total": "Capacidade em Leitos",
                "municipio": "Município",
                "qtd_estabelecimentos": "Qtd Locais",
            },
            color_continuous_scale="Forest",
        )
        fig_bar_q3.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_bar_q3, use_container_width=True)


# --- ABA 3: SÉRIE HISTÓRICA DO MERCADO ---
with tab_historico:
    st.subheader("Evolução Histórica do Mercado (24 Meses / 8 Trimestres)")

    df_hist_full = df_raw[
        (df_raw["uf"].isin(selected_ufs)) & (df_raw["capacidade"] <= cap_limite)
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
        title="Volume de Estabelecimentos Ativos ao Longo do Tempo",
        labels={
            "periodo_trimestre": "Trimestre",
            "numero_de_inscricao_do_cnpj": "Quantidade de Estabelecimentos",
            "uf": "Estado",
        },
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    st.plotly_chart(fig_evol, use_container_width=True)


# --- ABA 4: TABELA COMPLETA ---
with tab_dados:
    st.subheader("Base Mapeada de Concorrentes")
    st.write(
        "Utilize a tabela abaixo para realizar pesquisas pontuais e exportar listas de contatos."
    )

    cols_exibir = [
        col
        for col in [
            "uf",
            "municipio",
            "nome_fantasia",
            "porte",
            "capacidade",
            "idiomas",
            "estrutura_basica",
            "telefone_comercial",
            "e_mail_comercial",
        ]
        if col in df_filtrado.columns
    ]

    st.dataframe(df_filtrado[cols_exibir], use_container_width=True)
