import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# ----------------------------------------------------------------------------
# Configuração da página
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Análise Exploratória de Estrelas",
    layout="wide",
)

NOMES_TIPO_ESTRELA = {
    0: "Anã Marrom",
    1: "Anã Vermelha",
    2: "Anã Branca",
    3: "Sequência Principal",
    4: "Supergigante",
    5: "Hipergigante",
}

NOMES_CORES_PT = {
    "Red": "Vermelho",
    "Blue": "Azul",
    "Blue White": "Azul-Branco",
    "Blue-White": "Azul-Branco",
    "White": "Branco",
    "Yellowish White": "Amarelo-Branco",
    "Yellow-White": "Amarelo-Branco",
    "White-Yellow": "Amarelo-Branco",
    "Whitish": "Branco",
    "Pale yellow orange": "Laranja-Amarelado",
    "Orange": "Laranja",
    "Yellowish": "Amarelado",
    "": "Não informado",
}
CORES_PT_PARA_INGLES = {v: k for k, v in NOMES_CORES_PT.items()}

MAPA_CORES = {
    "Vermelho": "#c0392b",
    "Azul": "#2980b9",
    "Azul-Branco": "#5dade2",
    "Branco": "#ecf0f1",
    "Amarelo-Branco": "#f7e9a0",
    "Laranja-Amarelado": "#e0a96d",
    "Laranja": "#e67e22",
    "Amarelado": "#f1c40f",
    "Não informado": "#7f8c8d",
}

COLUNAS_NUMERICAS = [
    "Temperature (K)",
    "Luminosity(L/Lo)",
    "Radius(R/Ro)",
    "Absolute magnitude(Mv)",
    "Star type",
]

ESCOPOS = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ----------------------------------------------------------------------------
# Conexão com o Google Sheets
# ----------------------------------------------------------------------------
@st.cache_resource
def conectar_planilha():
    credenciais = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=ESCOPOS
    )
    cliente = gspread.authorize(credenciais)
    return cliente.open_by_key(st.secrets["sheets"]["spreadsheet_id"]).sheet1


@st.cache_data(ttl=60)
def carregar_dados_brutos_da_planilha() -> pd.DataFrame:
    planilha = conectar_planilha()
    dados = planilha.get_all_records()
    return pd.DataFrame(dados)


@st.cache_data(ttl=60)
def carregar_dados() -> pd.DataFrame:
    df = carregar_dados_brutos_da_planilha()

    df = df.dropna(how="all")
    df = df.dropna()

    for coluna in ["Star color", "Spectral Class"]:
        df[coluna] = df[coluna].astype(str).str.strip()

    df["Star color"] = df["Star color"].map(NOMES_CORES_PT).fillna(df["Star color"])

    for coluna in COLUNAS_NUMERICAS:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    df = df.dropna(subset=COLUNAS_NUMERICAS)
    df["Star type"] = df["Star type"].astype(int)
    df["Nome do tipo"] = df["Star type"].map(NOMES_TIPO_ESTRELA)

    return df


df_bruto = carregar_dados()

# ----------------------------------------------------------------------------
# Cabeçalho
# ----------------------------------------------------------------------------
st.title("Análise Exploratória de Dados Astronômicos")
st.markdown(
    "Visualização interativa da análise exploratória do dataset de estrelas, "
    "com base no notebook original. Explore a estrutura dos dados, "
    "estatísticas descritivas e a distribuição das variáveis."
)

# ----------------------------------------------------------------------------
# Barra lateral — filtros
# ----------------------------------------------------------------------------
st.sidebar.header("Filtros")

tipos_disponiveis = sorted(df_bruto["Star type"].unique())
tipos_selecionados = st.sidebar.multiselect(
    "Tipo de estrela",
    options=tipos_disponiveis,
    default=tipos_disponiveis,
    format_func=lambda t: f"{t} - {NOMES_TIPO_ESTRELA.get(t, t)}",
)

cores_disponiveis = sorted(df_bruto["Star color"].unique())
cores_selecionadas = st.sidebar.multiselect(
    "Cor da estrela", options=cores_disponiveis, default=cores_disponiveis
)

temp_min, temp_max = int(df_bruto["Temperature (K)"].min()), int(df_bruto["Temperature (K)"].max())
faixa_temp = st.sidebar.slider(
    "Temperatura (K)", min_value=temp_min, max_value=temp_max, value=(temp_min, temp_max)
)

df = df_bruto[
    df_bruto["Star type"].isin(tipos_selecionados)
    & df_bruto["Star color"].isin(cores_selecionadas)
    & df_bruto["Temperature (K)"].between(*faixa_temp)
]

st.sidebar.markdown(f"**{len(df)}** estrelas selecionadas de {len(df_bruto)} no total.")

if df.empty:
    st.warning("Nenhuma estrela corresponde aos filtros selecionados.")
    st.stop()

# ----------------------------------------------------------------------------
# 1. Estrutura do dataset
# ----------------------------------------------------------------------------
st.header("1. Estrutura do dataset")

df_original = carregar_dados_brutos_da_planilha()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Linhas", df_bruto.shape[0])
c2.metric("Colunas", df_bruto.shape[1])
c3.metric("Valores ausentes (original)", int(df_original.isnull().sum().sum()))
c4.metric("Estrelas após limpeza", df_bruto.shape[0])

with st.expander("Visualizar amostra dos dados"):
    st.dataframe(df.head(10), use_container_width=True)

with st.expander("Informações das colunas (equivalente a df.info())"):
    df_info = pd.DataFrame(
        {
            "Coluna": df_bruto.columns,
            "Tipo": df_bruto.dtypes.astype(str).values,
            "Valores não nulos": df_bruto.notnull().sum().values,
        }
    )
    st.dataframe(df_info, use_container_width=True, hide_index=True)

# ----------------------------------------------------------------------------
# 2. Estatísticas descritivas
# ----------------------------------------------------------------------------
st.header("2. Estatísticas descritivas")
st.dataframe(df.describe().T, use_container_width=True)

# ----------------------------------------------------------------------------
# 3. Distribuição por tipo de estrela
# ----------------------------------------------------------------------------
st.header("3. Distribuição dos tipos de estrela")

coluna1, coluna2 = st.columns([1, 1])

with coluna1:
    contagem_tipo = df["Nome do tipo"].value_counts().reset_index()
    contagem_tipo.columns = ["Tipo", "Quantidade"]
    fig_tipo = px.bar(
        contagem_tipo,
        x="Tipo",
        y="Quantidade",
        title="Quantidade por tipo de estrela",
        color="Tipo",
        text="Quantidade",
    )
    fig_tipo.update_layout(showlegend=False)
    st.plotly_chart(fig_tipo, use_container_width=True)

with coluna2:
    contagem_cor = df["Star color"].value_counts().reset_index()
    contagem_cor.columns = ["Cor", "Quantidade"]
    fig_cor = px.pie(
        contagem_cor,
        names="Cor",
        values="Quantidade",
        title="Distribuição por cor da estrela",
        color="Cor",
        color_discrete_map=MAPA_CORES,
    )
    st.plotly_chart(fig_cor, use_container_width=True)

# ----------------------------------------------------------------------------
# 4. Distribuição da temperatura
# ----------------------------------------------------------------------------
st.header("4. Distribuição da temperatura")

coluna3, coluna4 = st.columns([1, 1])

with coluna3:
    fig_box = px.box(
        df,
        y="Temperature (K)",
        points="all",
        title="Boxplot da Temperatura",
        color_discrete_sequence=["#e67e22"],
    )
    st.plotly_chart(fig_box, use_container_width=True)

with coluna4:
    fig_hist = px.histogram(
        df,
        x="Temperature (K)",
        nbins=30,
        title="Histograma da Temperatura",
        color_discrete_sequence=["#2980b9"],
    )
    st.plotly_chart(fig_hist, use_container_width=True)

st.info(
    "O boxplot evidencia a assimetria à direita: a mediana não está centralizada "
    "na caixa, e há estrelas com temperaturas bem acima da maioria, reforçando "
    "a grande variabilidade térmica entre os diferentes tipos estelares."
)

# ----------------------------------------------------------------------------
# 5. Cadastro de nova estrela
# ----------------------------------------------------------------------------
st.header("5. Adicionar nova estrela ao dataset")

with st.form("form_nova_estrela"):
    col_a, col_b = st.columns(2)

    with col_a:
        nova_temperatura = st.number_input("Temperatura (K)", min_value=0.0, step=100.0)
        nova_luminosidade = st.number_input("Luminosidade (L/Lo)", min_value=0.0, format="%.5f")
        novo_raio = st.number_input("Raio (R/Ro)", min_value=0.0, format="%.4f")

    with col_b:
        nova_magnitude = st.number_input("Magnitude absoluta (Mv)", format="%.2f")
        novo_tipo = st.selectbox(
            "Tipo de estrela",
            options=list(NOMES_TIPO_ESTRELA.keys()),
            format_func=lambda t: f"{t} - {NOMES_TIPO_ESTRELA[t]}",
        )
        nova_cor = st.selectbox("Cor da estrela", options=list(MAPA_CORES.keys()))
        nova_classe = st.text_input("Classe espectral (ex: O, B, A, F, G, K, M)", max_chars=1)

    enviado = st.form_submit_button("Adicionar estrela")

    if enviado:
        cor_original = CORES_PT_PARA_INGLES.get(nova_cor, nova_cor)

        planilha = conectar_planilha()
        planilha.append_row([
            nova_temperatura,
            nova_luminosidade,
            novo_raio,
            nova_magnitude,
            novo_tipo,
            cor_original,
            nova_classe.upper(),
        ])

        st.success("Estrela adicionada com sucesso!")
        st.cache_data.clear()
        st.rerun()

# ----------------------------------------------------------------------------
# Conclusão
# ----------------------------------------------------------------------------
st.header("Conclusão")
st.markdown(
    """
A análise exploratória permitiu compreender a estrutura do dataset, identificar
padrões e observar a distribuição das variáveis. Foi possível verificar a
presença de valores extremos e interpretar o comportamento das temperaturas
das estrelas, contribuindo para uma compreensão inicial dos dados. A presença
de valores extremos indica uma grande variabilidade na temperatura das
estrelas, o que pode estar relacionado a diferentes classificações estelares.
"""
)