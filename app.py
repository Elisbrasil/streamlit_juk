import streamlit as st
import pandas as pd
from datetime import date
import json
import os

st.set_page_config(page_title="Cadastro de Equipamentos", layout="wide")
st.title("💼 Cadastro de Equipamentos do Escritório")

ARQUIVO_JSON = "data.json"

# Carregar dados do JSON
def carregar_dados():
    if not os.path.exists(ARQUIVO_JSON):
        return pd.DataFrame(columns=[
            "tombamento", "nome", "marca", "modelo", "num_serie",
            "tipo", "valor", "data_aquisicao", "estado", "potencia"
        ])

    try:
        with open(ARQUIVO_JSON, "r", encoding="utf-8") as f:
            dados = json.load(f)
        return pd.DataFrame(dados)
    except json.JSONDecodeError:
        st.error("⚠️ O arquivo JSON está corrompido. Apague o conteúdo e recomece.")
        return pd.DataFrame(columns=[
            "tombamento", "nome", "marca", "modelo", "num_serie",
            "tipo", "valor", "data_aquisicao", "estado", "potencia"
        ])

df = carregar_dados()

# Formulário de cadastro
st.sidebar.header("➕ Cadastrar Novo Equipamento")
with st.sidebar.form("form_cadastro"):
    tombamento = st.text_input("Número de Tombamento", key="tombamento", help="Ex: EQP001")
    nome = st.text_input("Nome do Equipamento", key="nome")
    marca = st.text_input("Marca", key="marca")
    modelo = st.text_input("Modelo", key="modelo")
    num_serie = st.text_input("Número de Série", key="num_serie", help="Único por fabricante")
    tipo = st.selectbox("Tipo", ["Móvel", "Periféricos", "Computador", "Carregador", "Monitor", "Eletrodomésticos", "Outro"])
    valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f", key="valor")
    data_aquisicao = st.date_input("Data de Aquisição", value=date.today())
    estado = st.selectbox("Estado", ["Novo", "Usado", "Depreciado"], key="estado")
    potencia = st.selectbox("Potência do Carregador", ["45W", "65W", "Outro"], index=["45W", "65W", "Outro"].index(st.session_state.get("potencia_val", "65W")))
    submit = st.form_submit_button("Salvar")

if submit and nome and tombamento:
    # Verificar se o número de tombamento já existe
    if tombamento in df["tombamento"].values:
        st.warning("⚠️ Número de tombamento já cadastrado!")
    else:
        novo_registro = {
            "tombamento": tombamento,
            "nome": nome,
            "marca": marca,
            "modelo": modelo,
            "num_serie": num_serie,
            "tipo": tipo,
            "valor": round(valor, 2),
            "data_aquisicao": str(data_aquisicao),  # Salva como string
            "estado": estado,
            "potencia": potencia
        }

        dados_existentes = df.to_dict(orient="records") if not df.empty else []
        dados_existentes.append(novo_registro)

        with open(ARQUIVO_JSON, "w", encoding="utf-8") as f:
            json.dump(dados_existentes, f, indent=4, ensure_ascii=False)

        st.success("✅ Equipamento cadastrado com sucesso!")
        st.rerun()
elif submit and not tombamento:
    st.warning("⚠️ O número de tombamento é obrigatório!")

# Exibir dados com filtros
st.subheader("📋 Equipamentos Cadastrados")

df_atualizado = carregar_dados()

# Função para extrair o número do tombamento (ignora letras)
def extrair_numero_tombamento(tombamento):
    import re
    numeros = re.findall(r'\d+', str(tombamento))
    return int(numeros[0]) if numeros else 0

# Campo para escolher a ordenação
ordem_tombamento = st.radio(
    "🔢 Ordenar Equipamentos por Número de Tombamento",
    ["Maior para o menor", "Menor para o maior"],
    horizontal=True
)

# Adicionar coluna auxiliar com o número extraído e ordenar
df_atualizado['numero_tombamento'] = df_atualizado['tombamento'].apply(extrair_numero_tombamento)

# Definir se é ascendente ou descendente
ascending = ordem_tombamento == "Menor para o maior"

# Aplicar ordenação
df_atualizado = df_atualizado.sort_values(by='numero_tombamento', ascending=ascending).drop(columns=['numero_tombamento'])

# Campos de filtro
col1, col2, col3 = st.columns(3)

with col1:
    filtro_nome = st.text_input("Filtrar por Nome")

with col2:
    filtro_marca = st.text_input("Filtrar por Marca")

with col3:
    filtro_tipo = st.selectbox("Filtrar por Tipo", ["Todos"] + list(df_atualizado["tipo"].unique()))

# Aplicando os filtros
df_filtrado = df_atualizado.copy()

if filtro_nome:
    df_filtrado = df_filtrado[df_filtrado["nome"].str.contains(filtro_nome, case=False, na=False)]

if filtro_marca:
    df_filtrado = df_filtrado[df_filtrado["marca"].str.contains(filtro_marca, case=False, na=False)]

if filtro_tipo != "Todos":
    df_filtrado = df_filtrado[df_filtrado["tipo"] == filtro_tipo]

# Mostrar tabela filtrada com valor formatado
df_exibicao = df_filtrado.copy()
df_exibicao['valor'] = df_exibicao['valor'].apply(
    lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

st.dataframe(df_exibicao, use_container_width=True, hide_index=True)

# Mostrar valor total
valor_total = df_atualizado["valor"].sum()
st.metric("💰 Valor Total dos Equipamentos", f"R$ {valor_total:,.2f}")

# Gráfico de tipos de equipamentos
if not df_atualizado.empty:
    st.subheader("📊 Distribuição por Tipo")
    grafico = df_atualizado["tipo"].value_counts().reset_index()
    grafico.columns = ["Tipo", "Quantidade"]
    st.bar_chart(grafico.set_index("Tipo"))