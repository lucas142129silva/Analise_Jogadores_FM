import streamlit as st
from streamlit_option_menu import option_menu

# Define the pages and their file paths
pages = {
    'Home': 'Home.py',
    'Análise jogadores': 'pages/01_análise_jogadores.py',
    'Definição pesos': 'pages/02_definicao_pesos.py'
}

# Create a list of the page names
page_list = list(pages.keys())


def nav(current_page=page_list[0]):
    with st.sidebar:
        st.set_page_config(page_title="Análise FM", page_icon="ball", layout="wide",
                           initial_sidebar_state="auto", menu_items=None)

        p = option_menu("", page_list,
                        default_index=page_list.index(current_page),
                        orientation="vertical",
                        icons=["house", "list-task", "gear"],
                        styles={
                            "container": {"padding": "0!important", "background-color": "#beceea"},
                            "icon": {"font-size": "20px"},
                            "nav-link": {"font-size": "20px", "text-align": "left", "margin": "0px",
                                         "--hover-color": "#eee"},
                            "nav-link-selected": {"background-color": "blue"},
                        }
                        )

        if current_page != p:
            st.switch_page(pages[p])