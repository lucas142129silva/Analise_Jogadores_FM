import json
import pandas as pd
import polars as pl
import polars.selectors as cs
import numpy as np
import streamlit as st

MAP_PRECISAO_PES = {
    'Muito Forte': 5,
    'Bastante Forte': 3,
    'Forte': 4,
    'Fraco': 1,
    'Razoável': 2,
    'Muito Fraco': 0
}
PESOS_PRE_DEFINIDOS = {
    "Atacante Matador": "Pesos/pesos_atacantes_v2.json",
    "Atacante Criação": "Pesos/pesos_atacantes_criacao_teste.json"
}

COLS_FLOAT_E_GRADIENTE = [
    'Nota com liga', 'Multiplicador Liga', '% de jogos titular', 'Classificação Média', 'Performance XG',
    'XG', 'Gols/90', 'XG/90', '% Remates no gol', 'Remates ao gol/90', 'Remates/90', 'Cabeceios ganhos/90',
    'Performance XA', 'XA', 'Assistencias/90', 'XA/90', '% Passe certos',
    'Oportunidades criadas/90', 'Passes progressivos/90', 'Passes decisivos abertos/90', 'Passes completos/90',
    'Passes decisivos/90', 'Fintas/90', 'Cruzamentos certos/90', 'Cruzamentos tentados/90',
    'Posses ganhas/90', 'Desarmes/90', 'Desarmes decisivos/90', '% Desarmes com sucesso',
    'Alívios/90', 'Cabeceios decisivos/90', '% Cabeceios ganhos', 'Bloqueios/90',
    'Interceptações/90', 'Lances disputados pelo ar/90',
    'Pressões com sucesso/90', 'Pressões tentadas/90', 'Sprints/90', '% Pressões com sucesso'
]
COLS_INT_E_GRADIENTE = ['Altura', 'Jogos', 'Mins', 'Mins / Jogo', 'Gols', 'Assistencias']
COLS_FLOAT_E_INVERSO_GRADIENTE = ['Posses perdidas/90', 'Impedimentos/90']
COLS_INT_E_INVERSO_GRADIENTE = ['Idade', 'Salário', 'Valor Estimado', 'Dias Restantes Contrato']


@st.cache_data
def ler_e_processar_dados(dados_html):
    dados_brutos = ler_dados_local(dados_html)

    dados_tratados = tratamento_dados(dados_brutos)
    dados_tratados = normalizacao_dados_noventa_minutos(dados_tratados)

    return dados_tratados


def ler_dados_local(dados_html):
    dados = pd.read_html(dados_html, encoding="utf8")[0]
    dados = pl.from_pandas(dados)
    return dados


def corrigir_valor_estimado(valores):
    corrigidos = list()
    for val in valores:
        if "M" in val:
            val_corrigido = float(val.strip().replace("M", "").replace(",", ".")) * 1e6
        elif "m" in val:
            val_corrigido = float(val.strip().replace("m", "").replace(",", ".")) * 1e3
        else:
            val_corrigido = 0.0

        corrigidos.append(val_corrigido)

    return np.mean(corrigidos)


def tratamento_dados(dados_brutos):
    df = dados_brutos.select(
        # Nome corrigido - se houver duplicados ele adiciona 2, 3 no fim
        (pl.col("Nome") + " " + pl.cum_count("Nome").over("Nome").cast(str)).str.replace(" 1", "").
        alias("Nome"),

        pl.col("Divisão"),
        pl.col("Posição"),
        pl.col("Altura").str.extract(r"(\d+)").cast(pl.Int64),
        pl.col("Personalidade"),
        pl.col("Idade").cast(pl.Int64),
        pl.col("Pé Direito", "Pé Esquerdo").replace(MAP_PRECISAO_PES).cast(pl.Int64, strict=False),
        pl.col("Salário").str.split("€").list.first().str.strip_chars().str.replace_all("\.", "").cast(pl.Int64,
                                                                                                       strict=False),
        pl.col("Valor Estimado").str.replace_all("€", "").str.split(" - ").map_elements(corrigir_valor_estimado,
                                                                                        return_dtype=pl.Float64).alias(
            "Valor Estimado"),

        pl.col("Expira").str.strptime(pl.Date, "%d/%m/%Y", strict=False).alias("Data final contrato"),

        (pl.col("Expira").str.strptime(pl.Date, "%d/%m/%Y", strict=False) - st.session_state.cache["data_selecionada"])
        .dt.total_days().alias("Dias Restantes Contrato"),

        pl.col("Jogos").str.split(" (").list.first().cast(pl.Int64, strict=False).alias("Jogos como titular"),

        pl.when(pl.col("Jogos").str.contains(" \("))
        .then(pl.col("Jogos").str.split(" (").list.last().str.extract("(\d+)").cast(pl.Int64))
        .otherwise(pl.lit(0)).alias("Jogos como reserva"),

        pl.col("Mins").cast(str).str.replace("\.", "").str.pad_start(4, "0").cast(pl.Int64, strict=False),
        pl.col("Cl Med").cast(pl.Float64, strict=False).alias("Classificação Média"),

        # Ataque
        pl.col("Gls").cast(pl.Int64, strict=False).alias("Gols"),
        (pl.col("Gls/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("Gls/90").cast(str).str.zfill(4).str.tail(
            2)).cast(pl.Float64, strict=False).abs().fill_null(0).alias("Gols/90"),
        (pl.col("xG").cast(str).str.zfill(4).str.head(2) + "." + pl.col("xG").cast(str).str.zfill(4).str.tail(2)).cast(
            pl.Float64, strict=False).abs().alias("XG"),
        (pl.col("xG/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("xG/90").cast(str).str.zfill(4).str.tail(
            2)).cast(pl.Float64, strict=False).abs().alias("XG/90"),
        pl.col('% Remates').str.replace("\%", "").cast(pl.Int64, strict=False).truediv(100).abs().alias(
            "% Remates no gol"),
        (pl.col("Remt/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("Remt/90").cast(str).str.zfill(4).str.tail(
            2)).cast(pl.Float64, strict=False).abs().alias("Remates ao gol/90"),
        (pl.col("Remt/90.1").cast(str).str.zfill(4).str.head(2) + "." + pl.col("Remt/90.1").cast(str).str.zfill(
            4).str.tail(2)).cast(pl.Float64, strict=False).abs().alias("Remates/90"),
        (pl.col("Cab G/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("Cab G/90").cast(str).str.zfill(
            4).str.tail(2)).cast(pl.Float64, strict=False).abs().alias("Cabeceios ganhos/90"),

        # Passes
        pl.col("Ast").cast(pl.Int64, strict=False).alias("Assistencias"),
        (pl.col("xA").cast(str).str.zfill(4).str.head(2) + "." + pl.col("xA").cast(str).str.zfill(4).str.tail(2)).cast(
            pl.Float64, strict=False).abs().alias("XA"),
        (pl.col("xA/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("xA/90").cast(str).str.zfill(4).str.tail(
            2)).cast(pl.Float64, strict=False).abs().alias("XA/90"),
        pl.col('% Passe').str.replace("\%", "").cast(pl.Int64, strict=False).truediv(100).abs().alias("% Passe certos"),
        (pl.col("Op C/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("Op C/90").cast(str).str.zfill(4).str.tail(
            2)).cast(pl.Float64, strict=False).abs().alias("Oportunidades criadas/90"),
        (pl.col("Passes Pr/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("Passes Pr/90").cast(str).str.zfill(
            4).str.tail(2)).cast(pl.Float64, strict=False).abs().alias("Passes progressivos/90"),
        (pl.col("PD-JC/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("PD-JC/90").cast(str).str.zfill(
            4).str.tail(2)).cast(pl.Float64, strict=False).abs().alias("Passes decisivos abertos/90"),
        (pl.col("Ps C/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("Ps C/90").cast(str).str.zfill(4).str.tail(
            2)).cast(pl.Float64, strict=False).abs().alias("Passes completos/90"),
        (pl.col("PC/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("PC/90").cast(str).str.zfill(4).str.tail(
            2)).cast(pl.Float64, strict=False).abs().alias("Passes decisivos/90"),
        (pl.col("Fnt/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("Fnt/90").cast(str).str.zfill(4).str.tail(
            2)).cast(pl.Float64, strict=False).abs().alias("Fintas/90"),

        # Defesa
        (pl.col("Des/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("Des/90").cast(str).str.zfill(4).str.tail(
            2)).cast(pl.Float64, strict=False).abs().alias("Desarmes/90"),
        (pl.col("Des Dec/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("Des Dec/90").cast(str).str.zfill(
            4).str.tail(2)).cast(pl.Float64, strict=False).abs().alias("Desarmes decisivos/90"),
        pl.col('M Des').str.replace("\%", "").cast(pl.Int64, strict=False).truediv(100).abs().alias(
            "% Desarmes com sucesso"),
        pl.col("T Desa").cast(pl.Int64, strict=False).alias("Desarmes tentados"),
        (pl.col("Alí/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("Alí/90").cast(str).str.zfill(4).str.tail(
            2)).cast(pl.Float64, strict=False).abs().alias("Alívios/90"),
        (pl.col("Cab Dec/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("Cab Dec/90").cast(str).str.zfill(
            4).str.tail(2)).cast(pl.Float64, strict=False).abs().alias("Cabeceios decisivos/90"),
        pl.col('Cab %').str.replace("\%", "").cast(pl.Int64, strict=False).truediv(100).abs().alias(
            "% Cabeceios ganhos"),
        (pl.col("Blq/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("Blq/90").cast(str).str.zfill(4).str.tail(
            2)).cast(pl.Float64, strict=False).abs().alias("Bloqueios/90"),
        (pl.col("Int/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("Int/90").cast(str).str.zfill(4).str.tail(
            2)).cast(pl.Float64, strict=False).abs().alias("Interceptações/90"),
        (pl.col("JAr T/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("JAr T/90").cast(str).str.zfill(
            4).str.tail(2)).cast(pl.Float64, strict=False).abs().alias("Lances disputados pelo ar/90"),
        (pl.col("Crz Con/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("Crz Con/90").cast(str).str.zfill(
            4).str.tail(2)).cast(pl.Float64, strict=False).abs().alias("Cruzamentos certos/90"),
        (pl.col("Crz T/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("Crz T/90").cast(str).str.zfill(
            4).str.tail(2)).cast(pl.Float64, strict=False).abs().alias("Cruzamentos tentados/90"),

        # Físico
        (pl.col("Poss Con/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("Poss Con/90").cast(str).str.zfill(
            4).str.tail(2)).cast(pl.Float64, strict=False).abs().alias("Posses ganhas/90"),
        (pl.col("Poss Perd/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("Poss Perd/90").cast(str).str.zfill(
            4).str.tail(2)).cast(pl.Float64, strict=False).abs().alias("Posses perdidas/90"),
        (pl.col("Pr C/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("Pr C/90").cast(str).str.zfill(4).str.tail(
            2)).cast(pl.Float64, strict=False).abs().alias("Pressões com sucesso/90"),
        (pl.col("Pr T/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("Pr T/90").cast(str).str.zfill(4).str.tail(
            2)).cast(pl.Float64, strict=False).abs().alias("Pressões tentadas/90"),
        (pl.col("Sprints/90").cast(str).str.zfill(4).str.head(2) + "." + pl.col("Sprints/90").cast(str).str.zfill(
            4).str.tail(2)).cast(pl.Float64, strict=False).abs().alias("Sprints/90"),
        pl.col("Fj").cast(pl.Int64, strict=False).alias("Impedimentos")
    )

    return df


def normalizacao_dados_noventa_minutos(dados):
    # Proporções
    df = dados.with_columns(
        pl.when(pl.col("Pressões tentadas/90").is_null().or_(pl.col("Pressões tentadas/90").eq(0))).then(None)
        .otherwise(pl.col("Pressões com sucesso/90") / pl.col("Pressões tentadas/90"))
        .alias("% Pressões com sucesso"),
    )

    # 90 minutos
    df = df.with_columns(
        pl.when(pl.col("Mins").is_null().or_(pl.col("Mins").eq(0))).then(0).otherwise(
            (pl.col("Assistencias") * 90) / pl.col("Mins")).alias("Assistencias/90"),
        pl.when(pl.col("Mins").is_null().or_(pl.col("Mins").eq(0))).then(0).otherwise(
            (pl.col("Impedimentos") * 90) / pl.col("Mins")).alias("Impedimentos/90"),
        pl.col("Salário").add(pl.col("Valor Estimado")).alias("Valor total"),
    )

    # Performance xG e xA
    df = df.with_columns(
        pl.when(pl.col("XG/90").is_null().or_(pl.col("XG/90").eq(0))).then(None).otherwise(
            pl.col("Gols/90") - pl.col("XG/90")).alias("Performance XG"),
        pl.when(pl.col("XA/90").is_null().or_(pl.col("XA/90").eq(0))).then(None).otherwise(
            pl.col("Assistencias/90") - pl.col("XA/90")).alias("Performance XA"),
    )

    # Jogos como reserva e titular
    df = df.with_columns(
        pl.col("Jogos como titular").add(pl.col("Jogos como reserva")).alias("Jogos"),

        (pl.col("Jogos como titular") / (pl.col("Jogos como reserva") + pl.col("Jogos como titular")))
        .alias("% de jogos titular")
    )

    df = df.with_columns(
        pl.when(pl.col("Jogos").gt(0))
        .then(pl.col("Mins").truediv(pl.col("Jogos")))
        .otherwise(pl.lit(0)).alias("Mins / Jogo")
    )

    return df


def minmax_scaler(dataframe, name_column):
    result = dataframe.select(
        (pl.col(name_column) - pl.col(name_column).min()) / (
                    pl.col(name_column).max() - pl.col(name_column).min()) * 100
    )

    return result


def dados_rank_ligas():
    ranking_ligas = pd.read_html("Dados/Rank_Ligas_Mundo.html", encoding="utf8")[0]
    ranking_ligas = pl.from_pandas(ranking_ligas)

    ranking_ligas = ranking_ligas.select(
        pl.col("Nome").alias("Divisão"),
        pl.Series(name="Multiplicador Liga", values=np.linspace(1.2, 1, ranking_ligas.shape[0]))
    )

    return ranking_ligas


def usar_pesos_json(path):
    with open(path, "r") as f:
        pesos = json.load(f)

    return pesos


def aplicar_pesos_escalados(dados_filtrados, pesos):
    scaled_df = dados_filtrados.select(
        pl.col("Nome", "Divisão", "Posição", "Valor total"),
        pl.col("Mins").alias("total_minutos")
    )

    for col, peso in pesos.items():
        scaled_df = scaled_df.with_columns(
            pl.Series(name=col, values=minmax_scaler(dados_filtrados, col)) * peso,
        )

    scaled_df = scaled_df.with_columns(
        pl.sum_horizontal(cs.numeric().exclude(["total_minutos", "Valor total"])).alias("nota_jogador")
    )

    dados_com_nota = dados_filtrados.join(scaled_df[["Nome", "nota_jogador"]], on="Nome", how="left")

    # Aplicando coeficiente de ligas
    ranking_ligas = dados_rank_ligas()

    dados_com_nota_liga = dados_com_nota.join(
        ranking_ligas, on="Divisão", how="left"
    ).with_columns(
        pl.col("Multiplicador Liga").fill_null(1)
    )

    dados_com_nota_liga = dados_com_nota_liga.drop_nulls("nota_jogador").select(
        pl.col("Nome"), (pl.col("nota_jogador") * pl.col("Multiplicador Liga")).alias("Nota com liga"),
        pl.all().exclude("Nome")
    ).sort("Nota com liga", descending=True)

    return dados_com_nota_liga


def estilizar_tabela(tabela_notas):
    tabela_com_notas_ordenada = tabela_notas.to_pandas().set_index("Nome")

    # Colunas de FLOAT e gradiente
    colunas_selecionadas_f_g = [col for col in COLS_FLOAT_E_GRADIENTE
                                if col in st.session_state.cache['colunas_para_mostrar']
                                or col in st.session_state["colunas_fixas"]]
    tabela_estilizada = tabela_com_notas_ordenada.style \
        .background_gradient(subset=colunas_selecionadas_f_g, cmap="coolwarm_r") \
        .format("{:_.2f}", subset=colunas_selecionadas_f_g) \
        .set_properties(**{'text-align': 'center'})

    # Colunas de INT e gradiente
    colunas_selecionadas_i_g = [col for col in COLS_INT_E_GRADIENTE if
                                col in st.session_state.cache['colunas_para_mostrar']
                                or col in st.session_state["colunas_fixas"]]
    tabela_estilizada = tabela_estilizada \
        .background_gradient(subset=colunas_selecionadas_i_g, cmap="coolwarm_r") \
        .format("{:_.0f}", subset=colunas_selecionadas_i_g) \
        .set_properties(**{'text-align': 'center'})

    # Colunas de FLOAT e gradiente inverso
    colunas_selecionadas_f_invg = [col for col in COLS_FLOAT_E_INVERSO_GRADIENTE if
                                   col in st.session_state.cache['colunas_para_mostrar']
                                   or col in st.session_state["colunas_fixas"]]
    tabela_estilizada = tabela_estilizada \
        .background_gradient(subset=colunas_selecionadas_f_invg, cmap="coolwarm") \
        .format("{:_.2f}", subset=colunas_selecionadas_f_invg) \
        .set_properties(**{'text-align': 'center'})

    # Colunas de INT e gradiente inverso
    colunas_selecionadas_i_invg = [col for col in COLS_INT_E_INVERSO_GRADIENTE if
                                   col in st.session_state.cache['colunas_para_mostrar']
                                   or col in st.session_state["colunas_fixas"]]
    tabela_estilizada = tabela_estilizada \
        .background_gradient(subset=colunas_selecionadas_i_invg, cmap="coolwarm") \
        .format("{:_.0f}", subset=colunas_selecionadas_i_invg) \
        .set_properties(**{'text-align': 'center'})

    return tabela_estilizada


def distribuir_pesos_atributos(lista_atributos):
    """Distribui os atributos em colunas e ajusta os pesos na lista_de_colunas em cache"""
    colunas = st.columns(5)
    col = 0

    for idx, atributo in enumerate(lista_atributos):

        st.session_state["pesos_escolhidos"][atributo] = colunas[col].number_input(
            atributo, step=1.0,
            value=float(st.session_state["pesos_escolhidos"][atributo]),
            format="%.1f"
        )

        col += 1

        if (idx + 1) % 5 == 0:
            colunas = st.columns(5)
            col = 0


def update_pesos_cache():
    st.session_state["pesos_escolhidos"] = usar_pesos_json(PESOS_PRE_DEFINIDOS[st.session_state["peso_selecionado"]])


def download_json_data(data):
    json_data = json.dumps(data)
    json_bytes = json_data.encode('utf-8')
    return json_bytes


def atualizar_variavel_em_cache(nome_variavel):
    st.session_state.cache[nome_variavel] = st.session_state[nome_variavel]


def atualizar_colunas_para_mostrar():
    # Junta todas as colunas selecionadas nos expanders
    st.session_state.cache["colunas_para_mostrar"] = \
        sorted(st.session_state["colunas_selecionadas_info"]) + \
        sorted(st.session_state["colunas_selecionadas_ofe"]) + \
        sorted(st.session_state["colunas_selecionadas_cria"]) + \
        sorted(st.session_state["colunas_selecionadas_def"])

    # Se tem alguma coluna que foi colocada um peso, ela aparece nas colunas mostradas
    colunas_importantes_pesos = [col for col, peso in st.session_state["pesos_escolhidos"].items() if peso != 0]
    colunas_importantes_pesos_nao_no_cache = [col for col in colunas_importantes_pesos
                                              if col not in st.session_state.cache["colunas_para_mostrar"]]
    st.session_state.cache["colunas_para_mostrar"] += colunas_importantes_pesos_nao_no_cache


def atualizar_colunas_importantes_pesos():
    colunas_importantes_pesos = [col for col, peso in st.session_state["pesos_escolhidos"].items() if peso != 0]
    st.session_state.cache["colunas_para_mostrar"] = colunas_importantes_pesos