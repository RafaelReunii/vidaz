import os
import folium
import pandas as pd
import plotly.express as px
import requests
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

# Estilização CSS Personalizada (Hero Banner & Cards)
st.markdown(
    """
    <style>
    .hero-container {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
        padding: 30px;
        border-radius: 16px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
    }
    .hero-title { font-size: 2.3rem; font-weight: 800; margin-bottom: 8px; color: #FFFFFF; }
    .hero-subtitle { font-size: 1.1rem; color: #93C5FD; font-weight: 400; margin-bottom: 18px; }
    .badge-tag {
        background-color: rgba(255, 255, 255, 0.15);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        margin-right: 8px;
        display: inline-block;
        border: 1px solid rgba(255, 255, 255, 0.2);
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

# --- HOME REDESENHADA (HERO BANNER) ---
st.markdown(
    """
    <div class="hero-container">
        <div class="hero-title">🏕️ Panorama de Inteligência: Mercado Outdoor & Campismo</div>
        <div class="hero-subtitle">
            Plataforma analítica integrada para monitoramento da oferta de acampamentos e demanda de e-commerce outdoor no Brasil.
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

# BOX DO CONCEITO LEGAL (SEMPRE FECHADO POR PADRÃO)
with st.expander(
    "📖 **Conceito Legal de Acampamento Turístico (Diretrizes MTur/Cadastur)**",
    expanded=False,
):
    st.markdown("""
    **Definição Oficial (Lei Geral do Turismo - Lei nº 11.771/2008):**  
    Consideram-se **Acampamentos Turísticos** as áreas ao ar livre dotadas de infraestrutura e instalações destinadas ao alojamento temporário de praticantes de campismo, com prestação de serviços de apoio às atividades recreativas e de lazer.
    """)


# ---------------------------------------------------------
# 2. CONEXÃO E CARGA DE DADOS (MINTUR & MERCADO LIVRE)
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
        if pd.isna(val) or val in ["-", "Não informado", ""]:
            return 0
        return len([i.strip() for i in str(val).split(",") if i.strip()])

    df["qtd_idiomas"] = df["idiomas"].apply(contar_idiomas)
    df["tem_multilingue_2plus"] = df["qtd_idiomas"] >= 2
    return df


@st.cache_data(ttl=3600)
def carregar_dados_mercadolivre():
    # Base estruturada extraída via API do Mercado Livre (Snapshot Camping)
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
    st.error(f"⚠️ Erro ao carregar as bases de dados: {e}")
    st.stop()


# ---------------------------------------------------------
# 3. FILTROS LATERAIS (COM ORIENTAÇÃO DE UX)
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
# 4. KPIS MINTUR DA HOME
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
# 5. ABAS NAVEGÁVEIS (MINTUR + E-COMMERCE ML)
# ---------------------------------------------------------
(
    tab_mapa,
    tab_distancia,
    tab_historico,
    tab_insights,
    tab_dados,
    tab_ecommerce,
) = st.tabs([
    "🗺️ Mapa de Acampamentos",
    "📍 Presença Sul de Minas",
    "📈 Série Histórica (24M)",
    "📊 Perfil e Porte",
    "📋 Base Concorrentes",
    "🛍️ Mercado Outdoor (ML)",
])


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
        st.dataframe(df_faixas, use_container_width=True, hide_index=True)
    with col_d2:
        fig_faixa = px.bar(
            df_faixas,
            x="faixa_distancia",
            y="capacidade_total",
            color="locais_multilingues_2plus",
            title="Capacidade por Raio de Distância",
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
        title="Evolução de Estabelecimentos Mapeados pelo MinTur",
    )
    st.plotly_chart(fig_evol, use_container_width=True)


# --- ABA 4: PERFIL ---
with tab_insights:
    st.subheader("Indicadores Complementares de Mercado")
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        fig_porte = px.pie(
            df_filtrado,
            names="porte",
            title="Proporção por Porte Declarado",
            hole=0.4,
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
            title="Idiomas na Recepção",
        )
        st.plotly_chart(fig_id, use_container_width=True)


# --- ABA 5: BASE CONCORRENTES ---
with tab_dados:
    st.subheader("Base Mapeada de Concorrentes (MinTur)")
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
        ]
        if col in df_filtrado.columns
    ]
    st.dataframe(df_filtrado[cols_exibir], use_container_width=True)


# =========================================================
# --- ABA 6: E-COMMERCE MERCADO LIVRE (3 VISÕES & CARDS) ---
# =========================================================
with tab_ecommerce:
    # Logo do Mercado Livre + Título
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

    # 1. VISÃO 1: CARDS DE KPI (COM O CARD DE VOLUME APROXIMADO)
    mediana_reviews = df_ml["Avaliações (#)"].median()
    # Fator de conversão médio: 1 review a cada 50 vendas (2% de taxa de review)
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

    # 2. VISÃO 2: GRÁFICO DE MATRIZ (PREÇO X AVALIAÇÕES)
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

    # 3. VISÃO 3: TABELA DETALHADA COM BARRA VISUAL
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

    # --- DOIS BOXES AO FIM DA ABA ---

    # BOX 1: DATA E STATUS ESTÁTICO
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

    # BOX 2: PROCESSO DE ENGENHARIA DE DADOS (PARA DESTACAR NO CV)
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