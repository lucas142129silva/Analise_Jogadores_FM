import streamlit as st
import polars as pl
import Funcoes
import navbar
import datetime

navbar.nav('Análise jogadores')

# Retira um espaço em branco acima do header
st.markdown(
    """
        <style>
                .stAppHeader {
                    background-color: rgba(255, 255, 255, 0.0);  /* Transparent background */
                    visibility: visible;  /* Ensure the header is visible */
                }

               .block-container {
                    padding-top: 1rem;
                    padding-bottom: 0rem;
                    padding-left: 5rem;
                    padding-right: 5rem;
                }
        </style>
        """,
    unsafe_allow_html=True,
)

st.header("Análise jogadores")

# Filtro de posição
TRADUCAO_POSICOES = {
    "Defesa": "D",
    "Defesa ala": "DA",
    "Meia defensivo": "MD",
    "Meia central": "M",
    "Meia ofensivo": "MO",
    "Atacante": 'PL'
}
LADOS_POSICOES = ["D", "E", "C"]

pos_col1, pos_col2, pos_col3, pos_col4, pos_col5 = st.columns(5, border=True)

with pos_col1:
    # Posições traduzidas (D, DA, MD, M, MO, PL)
    st.selectbox("Seleciona a posição analisada:", TRADUCAO_POSICOES.keys(),
                 index=list(TRADUCAO_POSICOES.keys()).index(st.session_state.cache["posicao_selecionada"]),
                 key="posicao_selecionada",
                 on_change=Funcoes.atualizar_variavel_em_cache,
                 args=["posicao_selecionada"])
with pos_col2:
    # Data para calcular o tempo restante de contrato
    st.date_input("Data no jogo", value=st.session_state.cache["data_selecionada"], key="data_selecionada",
                  on_change=Funcoes.atualizar_variavel_em_cache,
                  args=(["data_selecionada"]),
                  min_value=datetime.datetime(year=2023, month=6, day=1),
                  max_value=datetime.datetime(year=2040, month=6, day=1)
                  )

with pos_col3:
    # Lados para posições que possuem (D, E, C)
    lados_selecionados = st.pills("Lados do campo:", LADOS_POSICOES, selection_mode="multi", default=[])
with pos_col4:
    # Mínimo de jogos na temporada
    minimo_jogos = st.number_input("Mínimo de jogos", step=1, value=15, format="%d")
with pos_col5:
    # Mínimo de minutos na temporada
    minimo_minutos = st.number_input("Mínimo de minutos", step=100, value=1_000, format="%d")

# Textos para criar regex das posições
texto_direita = ".?" if "D" not in lados_selecionados else "D"
texto_esquerda = ".?" if "E" not in lados_selecionados else "E"
texto_centro = ".?" if "C" not in lados_selecionados else "C"
filtro_lado_regex = f"\({texto_direita}{texto_esquerda}{texto_centro}\)"

# Regex da posição (ela pode ser primária, secundária)
filtro_posicao_regex = (f"(^{TRADUCAO_POSICOES[st.session_state.cache["posicao_selecionada"]]})"
                        f"|(/{TRADUCAO_POSICOES[st.session_state.cache["posicao_selecionada"]]})"
                        f"|(\, {TRADUCAO_POSICOES[st.session_state.cache["posicao_selecionada"]]})")

# Filtros principais
col1, col2, col3 = st.columns([1, 2, 3], border=True)

with col1:
    # Mínimo de classificação média
    minimo_classificacao_media = st.number_input("Mínimo de classificação média",
                                                 step=0.01, value=0.0, format="%.2f")

with col2:
    # Tempo máximo de contrato restante
    tempo_maximo_contrato = st.slider("Tempo contrato (dias)",
                                      min_value=0, max_value=2_500, step=30, value=2_500,
                                      format="%d")

with col3:
    # Salário máximo
    salario_maximo = st.slider("Salário máximo (em M)", min_value=0.0,
                               max_value=35.0,
                               format="%.2fM", value=35.0, step=0.1)

# FILTROS ANTES PARA PESOS: Filtrar com posição escolhida, minutos
dados_posicao_escolhida = st.session_state["dados_brutos_analise"].filter(
    pl.col("Posição").str.contains(filtro_posicao_regex) &
    pl.col("Mins").gt(minimo_minutos)
)

if len(lados_selecionados) > 0:
    dados_posicao_escolhida = dados_posicao_escolhida.filter(
        pl.col("Posição").str.contains(filtro_lado_regex)
    )

pesos_escolhidos = st.session_state["pesos_escolhidos"]
colunas_importantes_pesos = [col for col, peso in pesos_escolhidos.items() if peso != 0]
notas_jogadores = Funcoes.aplicar_pesos_escalados(dados_posicao_escolhida, pesos_escolhidos)

# FILTRO PÓS-NOTA
filtrada_notas_jogadores = notas_jogadores.filter(
    pl.col("Jogos").gt(minimo_jogos) &
    pl.col("Salário").lt(salario_maximo * 1e6) &
    pl.col("Classificação Média").gt(minimo_classificacao_media) &
    pl.col("Dias Restantes Contrato").lt(tempo_maximo_contrato)
)

# Seleção de colunas a se mostrar
st.session_state["colunas_fixas"] = ['Nome', 'Nota com liga', 'Divisão', 'Posição', 'Altura', 'Idade', 'Salário',
                                     'Valor Estimado', 'Dias Restantes Contrato', 'Jogos', 'Mins',
                                     'Mins / Jogo', 'Classificação Média']
COLS_INFOS_GERAIS = [
    'Personalidade', 'Multiplicador Liga', '% de jogos titular'
]
COLS_STATS_OFENSIVO = [
    'Performance XG', 'Gols', 'XG', 'Gols/90', 'XG/90', '% Remates no gol', 'Remates ao gol/90', 'Remates/90',
    'Cabeceios ganhos/90', 'Impedimentos/90', 'Sprints/90'
]
COLS_STATS_CRIACAO = [
    'Performance XA', 'Assistencias', 'XA', 'Assistencias/90', 'XA/90', '% Passe certos',
    'Oportunidades criadas/90', 'Passes progressivos/90', 'Passes decisivos abertos/90', 'Passes completos/90',
    'Passes decisivos/90', 'Fintas/90', 'Cruzamentos certos/90', 'Cruzamentos tentados/90'
]
COLS_STATS_DEFENSIVO = [
    'Posses ganhas/90', 'Posses perdidas/90', 'Desarmes/90', 'Desarmes decisivos/90', '% Desarmes com sucesso',
    'Alívios/90', 'Cabeceios decisivos/90', '% Cabeceios ganhos', 'Bloqueios/90',
    'Interceptações/90', 'Lances disputados pelo ar/90', 'Pressões com sucesso/90', 'Pressões tentadas/90',
    '% Pressões com sucesso'
]

variaveis_colunas_em_cache = [
    "colunas_selecionadas_info",
    "colunas_selecionadas_ofe",
    "colunas_selecionadas_cria",
    "colunas_selecionadas_def"
]
lista_de_colunas = [COLS_INFOS_GERAIS, COLS_STATS_OFENSIVO, COLS_STATS_CRIACAO,
                    COLS_STATS_DEFENSIVO]
labels_de_colunas = ["Informações gerais", "Stats ofensivo", "Stats de criação", "Stats defensivo"]


#  Seleção de colunas através expanders e multiselects
st.markdown("------")
cols = st.columns(4)
for i, x in enumerate(cols):
    with cols[i].expander(labels_de_colunas[i], False):
        st.multiselect(
            labels_de_colunas[i],
            options=lista_de_colunas[i],
            default=[coluna for coluna in lista_de_colunas[i]
                     if coluna in st.session_state.cache['colunas_para_mostrar'] or coluna in colunas_importantes_pesos],
            key=variaveis_colunas_em_cache[i],
            on_change=Funcoes.atualizar_colunas_para_mostrar,
            label_visibility="collapsed"
        )


colunas_selecionadas = filtrada_notas_jogadores.select(
    pl.col(st.session_state["colunas_fixas"]),
    pl.col(st.session_state.cache["colunas_para_mostrar"]).exclude(st.session_state["colunas_fixas"])
)

# Retirar duplicadas de nome - bug de mesmo jogador aparecer em duas linhas diferentes
colunas_selecionadas = colunas_selecionadas.unique("Nome", keep="first").sort("Nota com liga", descending=True)

# Mostrar tabela
tabela_estilizada = Funcoes.estilizar_tabela(colunas_selecionadas)
st.dataframe(tabela_estilizada, hide_index=False)