import os
import base64
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px

# =====================================================
# CONFIGURAÇÃO E IDENTIDADE VISUAL
# =====================================================

st.set_page_config(
    page_title="Dashboard do serviço de Impressão Corporativa",
    page_icon="🖨️",
    layout="wide",
)


# Função para converter a logo local em string Base64
def obter_base64_da_imagem(caminho_imagem):
    if os.path.exists(caminho_imagem):
        with open(caminho_imagem, "rb") as arquivo_imagem:
            return base64.b64encode(arquivo_imagem.read()).decode()
    return ""


string_base64_logo = obter_base64_da_imagem("static/logo_ufjf.png")

if string_base64_logo:
    url_logo = f"data:image/png;base64,{string_base64_logo}"
else:
    url_logo = "https://via.placeholder.com/150?text=Logo+UFJF"

# Injeção de CSS Customizado
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

/* ==========================================
   REMOÇÃO DA TARJA DE DEPLOY E MENU NATIVO
   ========================================== */
header, [data-testid="stHeader"] {
    visibility: hidden !important;
    display: none !important;
    height: 0px !important;
}

div.block-container {
    padding-top: 1.5rem !important;
}

/* Configuração global de fontes e cores de texto */
html, body, [class*="st-emotion-cache"] {
    font-family: 'Outfit', sans-serif;
    color: #1e293b;
}

/* Fundo em degradê suave */
.stApp {
    background: linear-gradient(135deg, #e0f2fe 0%, #f0f9ff 100%);
}

/* Título Principal Ajustado */
h1 {
    font-family: 'Outfit', sans-serif;
    color: #1e3a8a !important; 
    font-size: 2.1rem !important;
    font-weight: 700;
    text-align: center;
    margin-top: 10px !important;
    margin-bottom: 5px !important;
}

/* Demais subtítulos */
h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif;
    color: #0f172a !important;
    font-weight: 600;
}

/* SEPARAÇÃO DE CORES NOS CARD DE MÉTRICAS */
div[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.6);
    padding: 15px 12px;
    border-radius: 16px;
    box-shadow: 0 10px 25px rgba(148, 163, 184, 0.08);
}

div[data-testid="stMetricLabel"] p {
    color: #475569 !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}

div[data-testid="stMetricValue"] > div {
    color: #0284c7 !important;
    font-weight: 700 !important;
    font-size: 1.35rem !important; 
    white-space: nowrap !important;
}

/* Customização da Barra Lateral (Sidebar) */
section[data-testid="stSidebar"] {
    background-color: rgba(255, 255, 255, 0.45);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    border-right: 1px solid rgba(255, 255, 255, 0.5);
}

.header-logo {
    max-height: 75px;
    display: block;
    margin: 0 auto 12px auto;
    object-fit: contain;
}
</style>
""",
    unsafe_allow_html=True,
)

# Bloco do cabeçalho institucional
st.markdown(
    f"""
<div style="text-align: center; margin-bottom: 10px;">
    <img src="{url_logo}" alt="Logo UFJF" class="header-logo">
    <div style="font-size: 0.9rem; color: #475569; font-weight: 700; line-height: 1.5; font-family: 'Outfit', sans-serif; text-transform: uppercase; letter-spacing: 0.5px;">
        PROSDAV - Pró-Reitoria de Sistemas de Dados e Avaliação<br>
        CGCO - Centro de Gestão do Conhecimento Organizacional
    </div>
</div>
""",
    unsafe_allow_html=True,
)

st.title("Serviço de Impressão Corporativa (Dashboard)")

# =====================================================
# DADOS (Carregamento com Tratamento de Erros de Tipo)
# =====================================================


@st.cache_data
def carregar_dados():
    conn = sqlite3.connect(os.environ.get("DB_PATH", "impressao.db"))
    query = """
        SELECT 
            p.ano,
            p.mes,
            e.serial,
            e.controle,
            e.local,
            e.tipo,
            e.marca,
            e.modelo,
            p.paginas
        FROM producao p
        JOIN equipamento e ON p.id_equipamento = e.id
    """
    df = pd.read_sql(query, conn)
    conn.close()

    df["ano"] = pd.to_numeric(df["ano"], errors="coerce").fillna(0).astype(int)
    df["mes"] = pd.to_numeric(df["mes"], errors="coerce").fillna(0).astype(int)

    df = df[(df["ano"] > 0) & (df["mes"] > 0)].copy()

    ano_str = df["ano"].astype(str)
    mes_str = df["mes"].astype(str).str.zfill(2)

    df["periodo"] = pd.to_datetime(ano_str + "-" + mes_str + "-01")

    df["equipamento"] = df["controle"].astype(str) + " - " + df["local"].astype(str)

    return df


df = carregar_dados()

# =====================================================
# PERÍODOS DISPONÍVEIS (Padrão de 12 meses iniciais)
# =====================================================

periodos = sorted(df["periodo"].unique())

ultimo_periodo = pd.Timestamp(max(periodos))
indice_final = periodos.index(ultimo_periodo)

indice_inicial = max(0, indice_final - 11)

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.header("Filtros")

periodo_inicial = st.sidebar.selectbox(
    "Período Inicial",
    periodos,
    index=indice_inicial,
    format_func=lambda x: pd.Timestamp(x).strftime("%m/%Y"),
)

periodo_final = st.sidebar.selectbox(
    "Período Final",
    periodos,
    index=indice_final,
    format_func=lambda x: pd.Timestamp(x).strftime("%m/%Y"),
)

unidades = sorted(df["local"].unique())
unidade = st.sidebar.selectbox("Unidade", ["Todas"] + list(unidades))

tipo_selecionado = st.sidebar.selectbox("Tipo", ["Todos", "Tipo I", "Tipo III"])

# =====================================================
# FILTRAGEM
# =====================================================

df_filtrado = df.copy()

df_filtrado = df_filtrado[
    (df_filtrado["periodo"] >= periodo_inicial)
    & (df_filtrado["periodo"] <= periodo_final)
]

if unidade != "Todas":
    df_filtrado = df_filtrado[df_filtrado["local"] == unidade]

if tipo_selecionado != "Todos":
    tipo_filtro = "I" if tipo_selecionado == "Tipo I" else "III"
    df_filtrado = df_filtrado[df_filtrado["tipo"] == tipo_filtro]
else:
    tipo_filtro = "Todos"

if df_filtrado.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()

# =====================================================
# MENSAGEM DO PERÍODO BLINDADA CONTRA TRADUTORES
# =====================================================

str_inicial = periodo_inicial.strftime("%m/%Y")
str_final = periodo_final.strftime("%m/%Y")

st.markdown(
    f"""
<div translate="no" class="notranslate" style="font-size: 1.05rem; color: #475569; text-align: center; margin-top: 5px; margin-bottom: 25px; font-family: 'Outfit', sans-serif;">
    Período de análise: entre <span style="font-size: 1.2rem; font-weight: 700; color: #0284c7;">{str_inicial}</span> a <span style="font-size: 1.2rem; font-weight: 700; color: #0284c7;">{str_final}</span>
</div>
""",
    unsafe_allow_html=True,
)

# =====================================================
# CONSOLIDAÇÃO MENSAL DO GRÁFICO
# =====================================================

mensal = (
    df_filtrado.groupby("periodo")["paginas"].sum().reset_index().sort_values("periodo")
)

meses_map = {
    "01": "Janeiro",
    "02": "Fevereiro",
    "03": "Março",
    "04": "Abril",
    "05": "Maio",
    "06": "Junho",
    "07": "Julho",
    "08": "Agosto",
    "09": "Setembro",
    "10": "Outubro",
    "11": "Novembro",
    "12": "Dezembro",
}

mensal["mes_extenso"] = mensal["periodo"].dt.strftime("%m").map(meses_map)
mensal["ano_str"] = mensal["periodo"].dt.strftime("%Y")
mensal["eixo_x"] = mensal["mes_extenso"] + "/" + mensal["ano_str"]

# =====================================================
# CÁLCULO DOS INDICADORES
# =====================================================

total_paginas = int(df_filtrado["paginas"].sum())
media_mensal = mensal["paginas"].mean()
mediana_mensal = mensal["paginas"].median()

maior_linha = mensal.loc[mensal["paginas"].idxmax()]
menor_linha = mensal.loc[mensal["paginas"].idxmin()]

maior_consumo = int(maior_linha["paginas"])
maior_mes = maior_linha["eixo_x"]

menor_consumo = int(menor_linha["paginas"])
menor_mes = menor_linha["eixo_x"]

equipamentos_ativos = df_filtrado["controle"].astype(str).str.strip().nunique()

# =====================================================
# EXIBIÇÃO DOS CARDS DE MÉTRICAS
# =====================================================

c1, c2, c3, c4, c5, c6 = st.columns(6)

c1.metric("Total Impressões", f"{total_paginas:,.0f}".replace(",", "."))
c2.metric("Média Mensal", f"{media_mensal:,.0f}".replace(",", "."))
c3.metric("Mediana Mensal", f"{mediana_mensal:,.0f}".replace(",", "."))
c4.metric("Maior Consumo", f"{maior_consumo:,.0f}".replace(",", "."), maior_mes)
c5.metric("Menor Consumo", f"{menor_consumo:,.0f}".replace(",", "."), menor_mes)
c6.metric("Equipamentos", equipamentos_ativos)

st.divider()

# =====================================================
# GRAFICO: EVOLUÇÃO MENSAL
# =====================================================

fig_evolucao = px.line(
    mensal, x="eixo_x", y="paginas", markers=True, title="Evolução Mensal de Impressões"
)

fig_evolucao.update_xaxes(tickangle=-45, title_text="Período")

st.plotly_chart(fig_evolucao, use_container_width=True)

# =====================================================
# RENDERIZAÇÃO DOS GRÁFICOS INFERIORES
# =====================================================

col1, col2 = st.columns(2)

# Gráfico 1: Top 10 Equipamentos
top_equip = (
    df_filtrado.groupby("equipamento")["paginas"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)

fig_equip = px.bar(
    top_equip,
    x="paginas",
    y="equipamento",
    orientation="h",
    title="Top 10 Equipamentos de Maior Consumo",
)
fig_equip.update_layout(yaxis={"categoryorder": "total ascending"})
col1.plotly_chart(fig_equip, use_container_width=True)

# Gráfico 2: Top Unidades com Detalhamento
unidade_equip = (
    df_filtrado.groupby(["local", "equipamento"])["paginas"].sum().reset_index()
)

top_locais = df_filtrado.groupby("local")["paginas"].sum().nlargest(10).index
unidade_equip_top = unidade_equip[unidade_equip["local"].isin(top_locais)]

fig_unidades = px.bar(
    unidade_equip_top,
    x="paginas",
    y="local",
    color="equipamento",
    orientation="h",
    title="Top 10 Unidades (Detalhado por Impressora)",
)
fig_unidades.update_layout(yaxis={"categoryorder": "total ascending"}, showlegend=False)
col2.plotly_chart(fig_unidades, use_container_width=True)

# =====================================================
# DISTRIBUIÇÃO EM PIZZA
# =====================================================

col3, col4 = st.columns(2)

# Gráfico 3: Participação percentual
participacao = (
    df_filtrado.groupby("equipamento")["paginas"].sum().sort_values(ascending=False)
)

top10_part = participacao.head(10)
outros_part = participacao.iloc[10:].sum()
dados_pizza = top10_part.reset_index()

if outros_part > 0:
    dados_pizza.loc[len(dados_pizza)] = ["Outros", outros_part]

# APLICANDO A SUA REGRA DE ABREVIAÇÃO PARA A LEGENDA DO GRÁFICO DE PIZZA
dados_pizza["equipamento_curto"] = dados_pizza["equipamento"].apply(
    lambda x: x if x == "Outros" else (x[:22] + "..." if len(x) > 22 else x)
)

titulo_pizza_equip = (
    f"Participação no Consumo ({tipo_selecionado})"
    if tipo_selecionado != "Todos"
    else "Participação no Consumo (Top 10 + Outros)"
)

fig_participacao = px.pie(
    dados_pizza,
    names="equipamento_curto",  # Usando a coluna abreviada na legenda
    values="paginas",
    title=titulo_pizza_equip,
)

# Ajuste fino: Reduz margens vazias e oculta o título "equipamento_curto" da legenda para ganhar mais espaço para o gráfico
fig_participacao.update_layout(
    legend=dict(title=None), margin=dict(l=0, r=0, t=40, b=20)
)

col3.plotly_chart(fig_participacao, use_container_width=True)

# Gráfico 4: Distribuição por Tipo (I vs III)
dist_tipo = df_filtrado.groupby("tipo")["paginas"].sum().reset_index()

dist_tipo["tipo_nome"] = "Tipo " + dist_tipo["tipo"]

fig_tipo = px.pie(
    dist_tipo,
    names="tipo_nome",
    values="paginas",
    title="Distribuição por Tipo de Equipamento",
    hole=0.4,
)

# Mesmas margens do gráfico 3 para ficarem perfeitamente alinhados
fig_tipo.update_layout(legend=dict(title=None), margin=dict(l=0, r=0, t=40, b=20))

col4.plotly_chart(fig_tipo, use_container_width=True)
