import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

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


# ----------------------------------------------------------------------------
# Carregamento e limpeza dos dados (mesmos passos do notebook)
# ----------------------------------------------------------------------------
@st.cache_data
def carregar_dados(caminho: str) -> pd.DataFrame:
    df = pd.read_csv(caminho)

    # remove linhas totalmente vazias / com valores ausentes, como no notebook
    df = df.dropna(how="all")
    df = df.dropna()

    # normaliza espaços em texto
    for coluna in ["Star color", "Spectral Class"]:
        df[coluna] = df[coluna].astype(str).str.strip()

    # traduz os nomes das cores para português (e nomeia os casos vazios)
    df["Star color"] = df["Star color"].map(NOMES_CORES_PT).fillna(df["Star color"])

    # conversão para numérico (algumas colunas vêm como string, com espaços)
    colunas_numericas = [
        "Temperature (K)",
        "Luminosity(L/Lo)",
        "Radius(R/Ro)",
        "Absolute magnitude(Mv)",
        "Star type",
    ]
    for coluna in colunas_numericas:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    df = df.dropna(subset=colunas_numericas)
    df["Star type"] = df["Star type"].astype(int)
    df["Nome do tipo"] = df["Star type"].map(NOMES_TIPO_ESTRELA)

    return df


df_bruto = carregar_dados("cleaned_star_data.csv")

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

c1, c2, c3, c4 = st.columns(4)
c1.metric("Linhas", df_bruto.shape[0])
c2.metric("Colunas", df_bruto.shape[1])
c3.metric("Valores ausentes (original)", int(pd.read_csv("cleaned_star_data.csv").isnull().sum().sum()))
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