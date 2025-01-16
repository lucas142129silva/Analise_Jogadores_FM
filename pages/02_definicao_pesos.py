import navbar
import streamlit as st
import Funcoes
import json

PESOS_PRE_DEFINIDOS = {
    "Pesos zerados": "Pesos/pesos_zerados.json",
    "Atacante Matador": "Pesos/atacante_matador.json",
    "Atacante Fixo / Cone": "Pesos/atacante_cone.json",
    "Ponta driblador": "Pesos/ponta_driblador.json",
    "Meia criativo": "Pesos/meia_criativo.json",
    "Meia Box to Box": "Pesos/meia_box_to_box.json",
    "Recuperador de bolas": "Pesos/recuperador_de_bolas.json",
    "Lateral ofensivo": "Pesos/lateral_ofensivo.json",
    "Defensor xerife": "Pesos/zagueiro_xerife.json"
}


navbar.nav('Definição pesos')

st.title("Ajuste de pesos")
st.markdown("\nNesta aba, é possível selecionar pesos já feitos ou ajustar para os deixar personalizado e suprir a "
            "necessidade do time.\n")

col1, col2, col3 = st.columns([3, 2, 1], vertical_alignment="center")


with col1:
    st.selectbox(
        "Escolha um peso pré-definido",
        PESOS_PRE_DEFINIDOS.keys(),
        placeholder="Escolha um peso pré-definido",
        on_change=Funcoes.update_pesos_cache,
        key="peso_selecionado",
        index=None
    )

with col2:
    uploaded_arq = st.file_uploader("Escolha um arquivo de pesos personalizados:", type=["json"])

    if uploaded_arq is not None:
        pesos_upload = json.load(uploaded_arq)
        st.session_state["pesos_escolhidos"] = pesos_upload

        Funcoes.atualizar_colunas_importantes_pesos()

with col3:
    st.download_button(
        label="Download dos pesos personalizados",
        data=Funcoes.download_json_data(st.session_state["pesos_escolhidos"]),
        file_name="pesos_personalizados.json",
        mime='application/json'
    )


ATRIBUTOS_INFOS_GERAIS = [
    "Altura",
    "Idade",
    "Pé Direito",
    "Pé Esquerdo",
    "Salário",
    "Valor Estimado",
    "Classificação Média"
]

ATRIBUTOS_ATAQUE = [
    'Performance XG',
    'Gols',
    'Gols/90',
    'XG',
    'XG/90',
    '% Remates no gol',
    'Remates ao gol/90',
    'Remates/90',
    'Cabeceios ganhos/90',
    'Impedimentos/90'
]

ATRIBUTOS_CRIACAO = [
    'Performance XA',
    'Assistencias/90',
    'Assistencias',
    'XA',
    'XA/90',
    '% Passe certos',
    'Oportunidades criadas/90',
    'Passes progressivos/90',
    'Passes decisivos abertos/90',
    'Passes completos/90',
    'Passes decisivos/90',
    'Fintas/90',
    'Cruzamentos certos/90',
    'Cruzamentos tentados/90'
]

ATRIBUTOS_DEFESA = [
    'Desarmes/90',
    'Desarmes decisivos/90',
    '% Desarmes com sucesso',
    'Alívios/90',
    'Cabeceios decisivos/90',
    '% Cabeceios ganhos',
    'Bloqueios/90',
    'Interceptações/90',
    'Lances disputados pelo ar/90',
    'Posses ganhas/90',
    'Posses perdidas/90'
]

ATRIBUTOS_FISICO = [
    'Pressões com sucesso/90',
    'Pressões tentadas/90',
    'Sprints/90',
    '% Pressões com sucesso'
]


st.markdown("----")
st.markdown("\n**Ajuste personalizado de pesos**")


with st.expander("Atributos ataque"):
    Funcoes.distribuir_pesos_atributos(ATRIBUTOS_ATAQUE)

with st.expander("Atributos criação de jogadas"):
    Funcoes.distribuir_pesos_atributos(ATRIBUTOS_CRIACAO)

with st.expander("Atributos defesa"):
    Funcoes.distribuir_pesos_atributos(ATRIBUTOS_DEFESA)

with st.expander("Atributos físicos"):
    Funcoes.distribuir_pesos_atributos(ATRIBUTOS_FISICO)

with st.expander("Atributos informações gerais"):
    Funcoes.distribuir_pesos_atributos(ATRIBUTOS_INFOS_GERAIS)