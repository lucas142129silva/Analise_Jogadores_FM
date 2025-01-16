import streamlit as st
import Funcoes
import navbar
import datetime


navbar.nav("Home")

# Criação das variáveis de cache
if 'cache' not in st.session_state:
    st.session_state["cache"] = {
        "posicao_selecionada": "Defesa",
        "data_selecionada": datetime.datetime(year=2024, month=5, day=25),
        "colunas_para_mostrar": list()
    }

# Construção de pesos e notas dos jogadores
if "pesos_escolhidos" not in st.session_state:
    st.session_state["pesos_escolhidos"] = Funcoes.usar_pesos_json("Pesos/pesos_atacantes_v2.json")

    colunas_importantes_pesos = [col for col, peso in st.session_state["pesos_escolhidos"].items() if peso != 0]
    st.session_state.cache["colunas_para_mostrar"] = colunas_importantes_pesos


st.header("Análise de jogadores FM")

st.markdown("")
st.markdown("")
st.markdown("")
st.markdown("Baixe o arquivo .fmf e abra a aba de **jogadores abrangidos**. Adicione a view aos jogadores")
st.download_button(
    label="Download da view de análise dos jogadores",
    data=open("Arquivos para download/dados_analise_jogadores.fmf", "rb"),
    file_name="dados_analise_jogadores.fmf",
    mime='application/fmf'
)

st.markdown("")
st.markdown("")
st.markdown("")
st.markdown("\n\nSelecione o primeiro jogador e aperte CTRL + A, em seguida, aperte CTRL + P e salve o arquivo como "
            "arquivo web")

arquivo_upload = st.file_uploader("Faça o upload do arquivo dos jogadores para iniciar a análise:", type=["html"])

if arquivo_upload is not None:
    st.session_state["dados_brutos_analise"] = Funcoes.ler_e_processar_dados(arquivo_upload)
    trocar_pagina = st.button("Iniciar análise")

    if trocar_pagina:
        st.switch_page("pages/01_análise_jogadores.py")