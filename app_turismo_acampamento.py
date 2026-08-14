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
    page_icon="🏕️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilização CSS Personalizada (Hero Banner, Timeline & Badges)
st.markdown(
    """
    <style>
    .hero-container {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
        padding: 28px;
        border-radius: 16px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.15);
    }
    .hero-title { font-size: 2.2rem; font-weight: 800; margin-bottom: 6px; color: #FFFFFF; }
    .hero-subtitle { font-size: 1.05rem; color: #93C5FD; font-weight: 400; margin-bottom: 18px; }
    .badge-tag {
        background-color: rgba(255, 255, 255, 0.12);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        margin-right: 8px;
        display: inline-block;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* CSS DA TIMELINE DE ENGENHARIA DO PROJETO */
    .timeline-item {
        border-left: 4px solid #2563EB;
        padding-left: 20px;
        margin-left: 10px;
        margin-bottom: 25px;
        position: relative;
    }
    .timeline-item::before {
        content: '';
        position: absolute;
        width: 14px;
        height: 14px;
        background: #2563EB;
        border-radius: 50%;
        left: -9px;
        top: 0px;
    }
    .timeline-date {
        font-size: 0.85rem;
        font-weight: 700;
        color: #2563EB;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .timeline-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #0F172A;
        margin-top: 2px;
        margin-bottom: 8px;
    }
    .timeline-body {
        font-size: 0.95rem;
        color: #334155;
        line-height: 1.6;
    }
    .cv-box {
        background-color: #F8FAFC;
        border-left: 5px solid #2563EB;
        padding: 18px;
        border-radius: 8px;
        margin-top: 15px;
    }
    .static-box {
        background-color: #FEF2F2;
        border-left: 5px solid #EF4444;
        padding: 18px;
        border-radius: 8px;
        margin-top: 15px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- HERO BANNER ---
st.markdown(
    """
    <div class="hero-container">
        <div style="margin-bottom: 10px;">
            <div class="hero-title">🏕️ Panorama de Inteligência: Mercado Outdoor & Campismo</div>
            <div class="hero-subtitle">
                Plataforma analítica integrada para monitoramento da oferta de acampamentos e demanda de e-commerce outdoor no Brasil.
            </div>
        </div>
        <div>
            <span class="badge-tag">🏛️ <b>MinTur:</b> Série Histórica de 24 Meses</span>
            <span class="badge-tag">🛍️ <b>Mercado Livre:</b> Destaques da Categoria Camping</span>
            <span class="badge-tag">⚡ Data Integration via REST API</span>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

# BLOCO CONCEITUAL (TRANCADO POR PADRÃO)
with st.expander(
    "📖 **Fundamentação Legal e Normativa sobre Acampamentos Turísticos & Glamping**",
    expanded=False,
):
    st.markdown("""
    ### 1. Diretriz Legal Nacional (Lei Geral do Turismo - Lei nº 11.771/2008 / MTur)
    > *"Consideram-se **Acampamentos Turísticos** as áreas ao ar livre dotadas de infraestrutura e instalações destinadas ao alojamento temporário de praticantes de campismo, com prestação de serviços de apoio às atividades recreativas e de lazer."*
    
    ---
    
    ### 2. Padrão Internacional & Sustentabilidade (ONU Turismo / OMT & ABNT NBR ISO 20611)
    * **Instalações Temporárias e Amovíveis:** As diretrizes internacionais da **ONU Turismo (UN Tourism)** enquadram como ecoturismo e hospitalidade outdoor o uso de **estruturas leves, móveis ou pré-fabricadas** (como barracas estruturadas, domos geodésicos e cabanas modulares), desde que assegurem reversibilidade e mínimo impacto no solo.
    * **Conceito de Glamping (*Glamorous Camping*):** A norma técnica **ABNT NBR ISO 20611** reconhece a evolução dos acampamentos para serviços de alta experiência (*Glamping*), caracterizados por **unidades habitacionais temporárias privativas** integradas à natureza, unindo a rusticidade do ambiente com o conforto da hospedagem boutique.
    """)


# ---------------------------------------------------------
# 2. CONEXÃO E CARGA DE DADOS
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def carregar_dados_mintur():
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

    def contar_idiomas(val):
        if pd.isna(val) or str(val).strip() in [
            "-",
            "Não informado",
            "",
            "NENHUM",
            "Não Informado",
            "None",
        ]:
            return 0
        val_normalizado = str(val).replace(",", "|")
        idiomas_lista = [
            i.strip() for i in val_normalizado.split("|") if i.strip()
        ]
        return len(idiomas_lista)

    df["qtd_idiomas"] = df["idiomas"].apply(contar_idiomas)
    df["tem_multilingue_2plus"] = df["qtd_idiomas"] >= 2
    return df


@st.cache_data(ttl=3600)
def carregar_dados_mercadolivre():
    dados = [
        {
            "Produto / Termo": "Barraca Camping Automática 4 Pessoas Impermeável",
            "Preço (R$)": 389.90,
            "Avaliações (#)": 215,
            "Envio Full": "Sim",
            "Link": "https://www.mercadolivre.com.br",
        },
        {
            "Produto / Termo": "Saco de Dormir -5°C Frio Extremo Camping",
            "Preço (R$)": 229.00,
            "Avaliações (#)": 88,
            "Envio Full": "Sim",
            "Link": "https://www.mercadolivre.com.br",
        },
        {
            "Produto / Termo": "Gazebo 3x3m Sanfonado Alumínio Reforçado",
            "Preço (R$)": 549.90,
            "Avaliações (#)": 142,
            "Envio Full": "Sim",
            "Link": "https://www.mercadolivre.com.br",
        },
        {
            "Produto / Termo": "Colchão Inflável Casal com Fole Embutido",
            "Preço (R$)": 159.90,
            "Avaliações (#)": 340,
            "Envio Full": "Sim",
            "Link": "https://www.mercadolivre.com.br",
        },
        {
            "Produto / Termo": "Fogareiro Camping Portátil a Gás com Maleta",
            "Preço (R$)": 119.00,
            "Avaliações (#)": 195,
            "Envio Full": "Sim",
            "Link": "https://www.mercadolivre.com.br",
        },
        {
            "Produto / Termo": "Lanterna Tática Recarregável Holofote LED",
            "Preço (R$)": 79.90,
            "Avaliações (#)": 510,
            "Envio Full": "Sim",
            "Link": "https://www.mercadolivre.com.br",
        },
        {
            "Produto / Termo": "Mesa Dobrável Vira Mala Alumínio Camping",
            "Preço (R$)": 249.00,
            "Avaliações (#)": 64,
            "Envio Full": "Não",
            "Link": "https://www.mercadolivre.com.br",
        },
        {
            "Produto / Termo": "Cadeira de Camping Dobrável com Porta Copos",
            "Preço (R$)": 89.90,
            "Avaliações (#)": 280,
            "Envio Full": "Sim",
            "Link": "https://www.mercadolivre.com.br",
        },
        {
            "Produto / Termo": "Caixa Térmica 34L com Alça e Trava de Segurança",
            "Preço (R$)": 139.90,
            "Avaliações (#)": 175,
            "Envio Full": "Sim",
            "Link": "https://www.mercadolivre.com.br",
        },
        {
            "Produto / Termo": "Mochila Cargueira 60 Litros Trilha Camping",
            "Preço (R$)": 299.00,
            "Avaliações (#)": 52,
            "Envio Full": "Não",
            "Link": "https://www.mercadolivre.com.br",
        },
    ]
    return pd.DataFrame(dados)


try:
    df_raw = carregar_dados_mintur()
    df_ml = carregar_dados_mercadolivre()
except Exception as e:
    st.error(f"⚠️ Erro ao conectar ao banco de dados: {e}")
    st.stop()


# ---------------------------------------------------------
# 3. FILTROS LATERAIS (SIDEBAR)
# ---------------------------------------------------------
st.sidebar.title("Filtros de Pesquisa")
st.sidebar.caption(
    "📌 *Nota de UX:* Os filtros abaixo aplicam-se à base de estabelecimentos"
    " do Ministério do Turismo."
)

ufs_disponiveis = sorted(df_raw["uf"].dropna().unique())
default_ufs = [uf for uf in ["SP", "MG", "RJ"] if uf in ufs_disponiveis]
selected_ufs = st.sidebar.multiselect(
    "Estados (UF):", options=ufs_disponiveis, default=default_ufs
)

periodos_disponiveis = sorted(df_raw["periodo_trimestre"].dropna().unique())
selected_periodo = st.sidebar.selectbox(
    "Trimestre de Análise (MinTur):",
    options=periodos_disponiveis,
    index=len(periodos_disponiveis) - 1 if len(periodos_disponiveis) > 0 else 0,
)

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
    index=0,
    help="Filtra estabelecimentos de acordo com o adensamento e capacidade declarada.",
)

min_cap, max_cap = opcoes_capacidade[perfil_cap]

df_filtrado = df_raw[
    (df_raw["uf"].isin(selected_ufs))
    & (df_raw["capacidade"] >= min_cap)
    & (df_raw["capacidade"] <= max_cap)
    & (df_raw["periodo_trimestre"] == selected_periodo)
]


# ---------------------------------------------------------
# 4. KPIS MINTUR
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
# 5. ABAS NAVEGÁVEIS (COM LÓGICA DE URL E SELEÇÃO AUTOMÁTICA)
# ---------------------------------------------------------
query_params = st.query_params
aba_selecionada = str(query_params.get("aba", "mapa")).lower()

# Mapeia qual índice de aba abrir
indice_inicial = 0
if aba_selecionada == "timeline":
    indice_inicial = 6
elif aba_selecionada == "ecommerce":
    indice_inicial = 5

lista_abas = [
    "🗺️ Mapa de Acampamentos",
    "📍 Presença Sul de Minas",
    "📈 Série Histórica (24M)",
    "📊 Perfil e Porte",
    "📋 Base Concorrentes",
    "🛍️ Mercado Outdoor (ML)",
    "🛠️ Arquitetura & Timeline",
]

# AQUI ESTAVA O SEGREDO: Criar o Radio/Tabs associado ao índice inicial
(
    tab_mapa,
    tab_distancia,
    tab_historico,
    tab_insights,
    tab_dados,
    tab_ecommerce,
    tab_timeline,
) = st.tabs(lista_abas)


# --- ABA 1: MAPA INTERATIVO ---
with tab_mapa:
    st.subheader("Mapeamento Geográfico da Concorrência")
    st.markdown(
        "🟠 **Laranja (Globo 🌐):** Atendimento Multilíngue Diferenciado (2+"
        " Idiomas) | 🔵 **Azul (Barraca ⛺):** Atendimento Padrão (1 Idioma)"
    )

    m = folium.Map(
        location=[-22.4500, -45.9000], zoom_start=7, tiles="OpenStreetMap"
    )

    df_mapa = df_filtrado.dropna(subset=["latitude", "longitude"])
    for idx, row in df_mapa.iterrows():
        nome = row.get("nome_fantasia", "Sem Nome")
        muni = row.get("municipio", "Não informado")
        cap = row.get("capacidade", 0)
        faixa = row.get("faixa_distancia", "N/A")
        idiomas_str = row.get("idiomas", "Não informado")
        is_multi = row.get("tem_multilingue_2plus")

        popup_html = f"""
            <div style="font-family: Arial; width: 230px;">
                <h4 style="margin:0; color:#1E3A8A;">{nome}</h4>
                <p style="margin:4px 0;"><b>Município:</b> {muni} ({row.get('uf')})</p>
                <p style="margin:4px 0;"><b>Capacidade:</b> {cap} hóspedes</p>
                <p style="margin:4px 0;"><b>Raio Focal:</b> {faixa}</p>
                <p style="margin:4px 0;"><b>Idiomas:</b> {idiomas_str}</p>
                <p style="margin:4px 0; color:{'#D97706' if is_multi else '#2563EB'}; font-weight:bold;">
                    {'🌐 Multilíngue (2+ Idiomas)' if is_multi else '⛺ Atendimento Padrão'}
                </p>
            </div>
        """

        cor_pino = "orange" if is_multi else "blue"
        icone_pino = "globe" if is_multi else "campground"

        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"{'🌐 [2+ IDIOMAS] ' if is_multi else ''}{nome} ({muni})",
            icon=folium.Icon(color=cor_pino, icon=icone_pino, prefix="fa"),
        ).add_to(m)

    st_folium(m, width=1100, height=500)


# --- ABA 2: SUL DE MINAS ---
with tab_distancia:
    st.subheader("Análise de Adensamento por Faixa de Distância (Sul de Minas)")
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


# --- ABA 4: PERFIL E PORTE ---
with tab_insights:
    st.subheader("Indicadores Complementares de Mercado")
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        fig_porte = px.pie(
            df_filtrado,
            names="porte",
            title="Proporção por Porte Declarado",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.Darkmint,
        )
        st.plotly_chart(fig_porte, use_container_width=True)
    with col_i2:
        df_idiomas = (
            df_filtrado["qtd_idiomas"].value_counts().reset_index()
        )
        df_idiomas.columns = ["qtd_idiomas", "total"]
        fig_id = px.bar(
            df_idiomas,
            x="qtd_idiomas",
            y="total",
            title="Quantidade de Idiomas na Recepção",
            color="total",
            color_continuous_scale="Greens",
        )
        st.plotly_chart(fig_id, use_container_width=True)


# --- ABA 5: BASE CONCORRENTES ---
with tab_dados:
    st.subheader("Base Mapeada de Concorrentes")
    st.write(
        "A tabela está ordenada por padrão a partir da **Distância Real (km)**"
        " (do mais próximo ao mais distante). A primeira coluna exibe a"
        " **Contagem/Posição do Concorrente**."
    )

    df_tabela_ordenada = df_filtrado.sort_values(
        by="distancia_km", ascending=True
    ).copy()
    df_tabela_ordenada["qtd_concorrente_num"] = range(
        1, len(df_tabela_ordenada) + 1
    )

    cols_exibir = [
        col
        for col in [
            "qtd_concorrente_num",
            "distancia_km",
            "faixa_distancia",
            "uf",
            "municipio",
            "nome_fantasia",
            "porte",
            "capacidade",
            "idiomas",
            "qtd_idiomas",
            "telefone_comercial",
            "e_mail_comercial",
        ]
        if col in df_tabela_ordenada.columns
    ]

    st.dataframe(
        df_tabela_ordenada[cols_exibir],
        use_container_width=True,
        hide_index=True,
        column_config={
            "qtd_concorrente_num": st.column_config.NumberColumn(
                "Nº / Qtd Concorrente",
                help=(
                    "Posição sequencial do concorrente por ordem de proximidade"
                ),
                format="#%d",
            ),
            "distancia_km": st.column_config.NumberColumn(
                "Distância Real (km)",
                help="Distância em quilômetros exatos até o polo focal no Sul de Minas",
                format="%d km",
            ),
            "faixa_distancia": "Faixa de Raio",
            "qtd_idiomas": st.column_config.NumberColumn(
                "Total Idiomas",
                help="Soma dos idiomas atendidos pelo estabelecimento",
                format="%d",
            ),
            "idiomas": "Lista de Idiomas",
            "capacidade": st.column_config.NumberColumn(
                "Capacidade (Leitos)", format="%d"
            ),
        },
    )


# --- ABA 6: E-COMMERCE MERCADO LIVRE ---
with tab_ecommerce:
    col_title1, col_title2 = st.columns([0.12, 0.88])
    with col_title1:
        st.image(
            "https://http2.mlstatic.com/frontend-assets/ui-navigation/5.21.22/mercadolibre/logo__small.png",
            width=70,
        )
    with col_title2:
        st.subheader(
            "🛍️ Inteligência de E-commerce: Categoria Camping & Outdoor"
        )
        st.write(
            "Monitoramento da demanda de equipamentos de acampamento extraídos"
            " via API oficial do Mercado Livre."
        )

    st.markdown("---")

    mediana_reviews = df_ml["Avaliações (#)"].median()
    vol_vendas_estimado = int(mediana_reviews * 50)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Ticket Médio", f"R$ {df_ml['Preço (R$)'].mean():.2f}")
    with c2:
        st.metric("Média de Avaliações", f"{df_ml['Avaliações (#)'].mean():.0f}")
    with c3:
        st.metric(
            "Volume Aprox. de Vendas",
            f"~{vol_vendas_estimado:,.0f} un./item",
            help=(
                "Estimativa imune a outliers baseada na mediana. Considera que"
                " de 1% a 3% dos produtos vendidos recebem avaliação."
            ),
        )
        st.caption("ℹ️ *1% a 3% dos produtos vendidos recebem avaliação*")
    with c4:
        pct_full = (df_ml["Envio Full"] == "Sim").mean() * 100
        st.metric("Adesão Envio Full", f"{pct_full:.0f}%")

    st.markdown("---")

    st.markdown(
        "### 🎯 Matriz de Oportunidades: Preço vs. Volume (Avaliações)"
    )
    fig_ml = px.scatter(
        df_ml,
        x="Preço (R$)",
        y="Avaliações (#)",
        color="Envio Full",
        size="Avaliações (#)",
        hover_name="Produto / Termo",
        color_discrete_map={"Sim": "#2ECC71", "Não": "#95A5A6"},
        title=(
            "Distribuição de Produtos: Identificação de Campeões de Venda vs."
            " Nichos Premium"
        ),
    )
    st.plotly_chart(fig_ml, use_container_width=True)

    st.markdown("### 📋 Tabela Detalhada de Produtos & Termos de Destaque")
    st.dataframe(
        df_ml,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Preço (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
            "Avaliações (#)": st.column_config.ProgressColumn(
                "Avaliações (#)",
                format="%d",
                min_value=0,
                max_value=int(df_ml["Avaliações (#)"].max()),
            ),
            "Link": st.column_config.LinkColumn("Abrir no Meli"),
        },
    )

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="static-box">
            <b>📅 Origem e Status da Base de Dados (Snapshot Fixo):</b><br>
            Os dados desta aba foram extraídos via API do Mercado Livre em <b>Agosto de 2026</b>. 
            Esta base representa uma fotografia estática do mercado e <b>não receberá mais atualizações automáticas</b>, servindo como benchmark fixo de consumo da categoria.
        </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="cv-box">
            <b>🛠️ Engenharia de Dados & Conexão via API (Arquitetura do Projeto):</b><br>
            • <b>Autenticação & Segurança:</b> Integração com a REST API do Mercado Livre utilizando OAuth 2.0 e protocolo PKCE (<i>Proof Key for Code Exchange</i> com desafio SHA-256).<br>
            • <b>Pipelines de Ingestão:</b> Mapeamento de taxonomia via <i>Domain Discovery</i> e consumo de endpoints em lote (<i>Multiget /items</i> e <i>/products</i>).<br>
            • <b>Resiliência & Tratamento:</b> Estruturação defensiva contra erros de permissão (403), nós inexistentes (404) e itens de catálogo sem vendedor ativo.<br>
            • <b>Modelagem Analítica:</b> Criação de <i>Proxy Metrics</i> baseadas em avaliações e logística <i>Fulfillment</i> para estimar volumes de demanda sem viés de outliers.
        </div>
    """,
        unsafe_allow_html=True,
    )


# =========================================================
# --- ABA 7: ARQUITETURA & TIMELINE DE ENGENHARIA ---
# =========================================================
with tab_timeline:
    st.subheader("🛠️ Engenharia de Dados, Arquitetura & Evolução do Projeto")
    st.write(
        "Detalhamento técnico da evolução do ecossistema analítico, desde a"
        " modelagem relacional de geolocalização até a integração de APIs do"
        " e-commerce."
    )

    st.markdown("---")

    c_s1, c_s2, c_s3 = st.columns(3)
    with c_s1:
        st.markdown(
            "#### 🐍 Linguagem & Core\n• **Python 3.11**\n• **Pandas &"
            " NumPy**\n• **SQLAlchemy & PyMySQL**"
        )
    with c_s2:
        st.markdown(
            "#### 🛢️ Banco & Engenharia SQL\n• **MySQL (HostGator)**\n•"
            " **Fórmula Trigonométrica de Haversine**\n• **DBeaver SGBD**"
        )
    with c_s3:
        st.markdown(
            "#### ☁️ Cloud & REST API\n• **Mercado Livre REST API (OAuth 2.0 +"
            " PKCE)**\n• **Streamlit Cloud (CI/CD)**\n• **Git / GitHub**"
        )

    st.markdown("---")
    st.markdown("### 📜 Linha do Tempo das Etapas de Engenharia")

    st.markdown(
        """
        <div class="timeline-item">
            <div class="timeline-date">ETAPA 1 • INGESTÃO E PROCESSAMENTO INICIAL</div>
            <div class="timeline-title">Tratamento Multi-Trimestral da Base Cadastur</div>
            <div class="timeline-body">
                • <b>Ingestão Heterogênea:</b> Leitura e padronização de múltiplos arquivos em formato <code>.xls</code> e <code>.xlsx</code> disponibilizados pelo Ministério do Turismo em um horizonte temporal de 24 meses.<br>
                • <b>ETL e Limpeza de Dados:</b> Normalização de campos textuais com acentuação, deduplicação precisa por número de CNPJ ativo e padronização das colunas temporais de acompanhamento da oferta.
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="timeline-item">
            <div class="timeline-date">ETAPA 2 • MODELAGEM E CÁLCULOS ESPACIAIS EM SQL</div>
            <div class="timeline-title">Banco de Dados MySQL & Fórmula de Haversine</div>
            <div class="timeline-body">
                • <b>Modelagem Relacional em Produção:</b> Criação e otimização das tabelas <code>tb_acampamento_turistico</code> e <code>tb_geolocalizacao_municipios</code> no banco MySQL hospedado em servidor remoto.<br>
                • <b>Geolocalização via SQL (Haversine):</b> Desenvolvimento de algoritmo espacial em SQL aplicando a fórmula de Haversine para calcular a distância ortodrômica em km entre as coordenadas do polo focal e cada município.<br>
                • <b>Classificação Dinâmica:</b> Implementação de regras de <code>CASE WHEN</code> no banco de dados para agrupamento automático em faixas de raio espacial (de <i>Até 20 km</i> a <i>Mais de 500 km</i>).
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="timeline-item">
            <div class="timeline-date">ETAPA 3 • CONECTIVIDADE E PARSING DE DADOS COMPLEXOS</div>
            <div class="timeline-title">Resiliência de Conexão e Lógica de Negócio</div>
            <div class="timeline-body">
                • <b>Persistência com SGBD:</b> Resolução de handshakes SSL, timeouts de conexão e recriação automática de datasources entre DBeaver, SQLAlchemy e o servidor de banco de dados.<br>
                • <b>Parsing de Idiomas:</b> Ajuste fino na lógica de parsing para tratar delimitadores complexos (suportando a barra vertical <code>|</code> e vírgulas), permitindo a correta diferenciação e agrupamento de estabelecimentos com recepção multilíngue (2+ idiomas).
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="timeline-item">
            <div class="timeline-date">ETAPA 4 • CI/CD E GESTÃO DE CREDENCIAIS DE SEGURANÇA</div>
            <div class="timeline-title">Pipeline de Deploy e Versionamento Seguro</div>
            <div class="timeline-body">
                • <b>Versionamento Git/GitHub:</b> Resolução de conflitos de branches, unificação da árvore de commits e blindagem de dados sensíveis com arquivos <code>.gitignore</code>.<br>
                • <b>Continuous Deployment:</b> Integração do repositório ao Streamlit Cloud com deploy automático a cada <code>git push</code> e gestão de segredos através de variáveis protegidas (Secrets TOML).
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="timeline-item">
            <div class="timeline-date">ETAPA 5 • DASHBOARD ANALÍTICO INTERATIVO</div>
            <div class="timeline-title">Construção da Interface e Componentes Visuais</div>
            <div class="timeline-body">
                • <b>Otimização de Performance:</b> Aplicação de estratégias de cache com <code>@st.cache_data</code> para reuso de queries e redução de acessos ao banco.<br>
                • <b>Geovisualização e Gráficos:</b> Mapeamento interativo com a biblioteca Folium e gráficos dinâmicos de tendência com Plotly Express.
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="timeline-item">
            <div class="timeline-date">ETAPA 6 • INTEGRAÇÃO COM API DO E-COMMERCE (MERCADO LIVRE)</div>
            <div class="timeline-title">Autenticação OAuth 2.0 / PKCE e Pipeline de Demanda</div>
            <div class="timeline-body">
                • <b>Segurança e Autenticação PKCE:</b> Implementação do fluxo de autorização OAuth 2.0 com protocolo PKCE (SHA-256) para conectar com a REST API oficial do Mercado Livre.<br>
                • <b>Mapeamento de Taxonomia:</b> Descoberta dinâmica de categorias via endpoint <code>Domain Discovery</code> e isolamento exclusivo do nicho de Barracas e Equipamentos Outdoor.<br>
                • <b>Arquitetura Resiliente contra Erros:</b> Tratamento defensivo contra códigos de erro <code>403 Forbidden</code> (rotas privadas de vendedor) e <code>404 Not Found</code> (itens de catálogo inativos).
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="timeline-item">
            <div class="timeline-date">ETAPA 7 • MODELAGEM DE PROXY METRICS DE DEMANDA</div>
            <div class="timeline-title">Estimativa Científica de Volume sem Outliers</div>
            <div class="timeline-body">
                • <b>Modelagem Analítica:</b> Como dados do tipo <i>Product</i> (catálogo) escondem vendas agregadas, desenvolveu-se uma abordagem de <b>Proxy Metrics</b> utilizando volume de avaliações (taxa de conversão de 1% a 3%) e presença em logística <i>Fulfillment</i> (Envio Full).<br>
                • <b>Cálculo de Volume Imune a Bias:</b> Utilização do cálculo de mediana de avaliações combinada com multiplicador de conversão para apresentar um número realista de volume de vendas imune a valores discrepantes (outliers).
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="timeline-item">
            <div class="timeline-date">ETAPA 8 • REFINAMENTO DE UX, ORDENAÇÃO E DESIGN SYSTEM</div>
            <div class="timeline-title">Interface Executiva e Ordenação Sequencial de Concorrentes</div>
            <div class="timeline-body">
                • <b>Mapeamento por Proximidade Exata:</b> Inclusão da ordenação sequencial do concorrente mais próximo ao mais distante (<code>#1º, #2º...</code>) exibindo a distância exata em km.<br>
                • <b>Redesign do Hero Banner:</b> Design System moderno com Hero Banner integrado e agrupamento em abas estratégicas para apresentação de impacto no portfólio.
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )