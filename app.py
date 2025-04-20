import os
import streamlit as st
from docx import Document
import pdfminer.high_level as pdf_hl
import pypandoc
from jinja2 import Environment, FileSystemLoader
import openai

# Configuração da API OpenAI
environment_api_key = os.getenv("OPENAI_API_KEY")
if environment_api_key:
    openai.api_key = environment_api_key
else:
    st.warning("Variável OPENAI_API_KEY não definida. Alguns recursos podem não funcionar.")

# Diretórios do projeto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Inicializa Jinja2
env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=False,
    block_start_string='{%',
    block_end_string='%}',
    variable_start_string='{{',
    variable_end_string='}}'
)
# Carrega o template
tpl = env.get_template("padrao_revista.tex.j2")

# Funções de extração

def extrair_docx(path):
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


def extrair_pdf(path):
    return pdf_hl.extract_text(path)

# Integração com OpenAI para refinamento opcional

def formatar_com_ia(trecho, instrucoes):
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Você é um conversor de texto para LaTeX seguindo o padrão da revista."},
            {"role": "user", "content": f"{instrucoes}\n\n{trecho}"}
        ],
        temperature=0
    )
    return resp.choices[0].message.content

# Processa o arquivo enviado

def processar_arquivo(uploaded_file):
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    raw_text = extrair_docx(uploaded_file) if ext == ".docx" else extrair_pdf(uploaded_file)

    # Inputs do usuário para preencher o template
    titulo = st.text_input("Título do Artigo")
    autores = [a.strip() for a in st.text_area("Autores (separar por vírgula)").split(",") if a.strip()]
    abstract_pt = st.text_area("Resumo (PT)")
    keywords_pt = [k.strip() for k in st.text_input("Palavras-chave (PT, separar por vírgula)").split(",") if k.strip()]

    # Refinamento opcional com IA
    if st.button("Refinar Resumo com IA"):
        abstract_pt = formatar_com_ia(abstract_pt, "Formate este resumo em LaTeX, sem alterar o template.")

    # Exemplo inicial de seções e bibliografia (pode ser parseado do raw_text)
    sections = []
    bibliografia = []

    context = {
        "titulo": titulo,
        "autores": autores,
        "abstract_pt": abstract_pt,
        "keywords_pt": keywords_pt,
        "abstract_en": "",
        "keywords_en": [],
        "data_recebido": "",
        "data_aceito": "",
        "sections": sections,
        "bibliografia": bibliografia
    }

    return tpl.render(**context)

# Interface Streamlit
st.title("Gerador de LaTeX para Revista com IA")
uploaded_file = st.file_uploader("Envie seu DOCX ou PDF", type=["docx","pdf"])
if uploaded_file:
    latex_code = processar_arquivo(uploaded_file)
    st.text_area("Código LaTeX gerado", latex_code, height=300)
    st.download_button(
        label="Baixar .tex",
        data=latex_code,
        file_name="artigo.tex",
        mime="text/x-tex"
    )
