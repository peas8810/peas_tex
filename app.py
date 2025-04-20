import os
import streamlit as st
import tempfile
import pypandoc
from jinja2 import Environment, FileSystemLoader

# Configuração de diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Inicializa Jinja2
env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=False
)
tpl = env.get_template("padrao_revista.tex.j2")

st.title("Gerador de LaTeX para Revista")
uploaded_file = st.file_uploader("Envie seu arquivo (DOCX ou PDF)", type=["docx","pdf"])

if uploaded_file:
    # Salva temporariamente o arquivo enviado
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    # Converte o documento para LaTeX bruto usando Pandoc
    try:
        ext = os.path.splitext(tmp_path)[1][1:]
        latex_body = pypandoc.convert_file(tmp_path, 'latex', format=ext)
    except Exception as e:
        st.error(f"Erro na conversão com Pandoc: {e}")
        latex_body = ""

    # Usa o nome do arquivo como título do artigo
    title = os.path.splitext(uploaded_file.name)[0]

    # Contexto para o template (pode estender para extrair metadados)
    context = {
        "titulo": title,
        "autores": [],
        "abstract_pt": "",
        "keywords_pt": [],
        "abstract_en": "",
        "keywords_en": [],
        "data_recebido": "",
        "data_aceito": "",
        "sections": [
            {"secao": "Conteúdo", "conteudo": latex_body}
        ],
        "bibliografia": []
    }

    # Renderiza o .tex final
    final_tex = tpl.render(**context)

    st.subheader("Código LaTeX gerado")
    st.code(final_tex, language='latex')
    st.download_button(
        "Baixar .tex",
        final_tex,
        file_name=f"{title}.tex",
        mime="text/x-tex"
    )
