import os
import streamlit as st
import tempfile
import pypandoc
from jinja2 import Environment, FileSystemLoader

# Garante que Pandoc está disponível (faz download automático se necessário)
try:
    pypandoc.get_pandoc_version()
except (OSError, RuntimeError):
    pypandoc.download_pandoc()

# Configuração de diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Inicializa Jinja2
env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=False
)

# Interface
st.title("Gerador de Artigo no Padrão da Revista")

# Escolha do tipo de artigo
article_type = st.selectbox(
    "Tipo de Artigo:",
    ["Estudo de Caso", "Revisão Bibliográfica"]
)
# Define o template conforme a escolha
template_file = (
    "estudo_caso.tex.j2"
    if article_type == "Estudo de Caso"
    else "revisao_bibliografica.tex.j2"
)
tpl = env.get_template(template_file)

# Upload do documento
uploaded_file = st.file_uploader("Envie seu arquivo (DOCX ou PDF)", type=["docx", "pdf"])

if uploaded_file:
    # Salva o arquivo em disco temporário
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    # Detecta extensão sem ponto
    ext = os.path.splitext(tmp_path)[1][1:]

    # Converte para LaTeX bruto
    try:
        latex_body = pypandoc.convert_file(tmp_path, 'latex', format=ext)
    except Exception as e:
        st.error(f"Erro na conversão com Pandoc: {e}")
        latex_body = ""

    # Usa nome do arquivo como título
    title = os.path.splitext(uploaded_file.name)[0]

    # Monta contexto para o template
    context = {
        "titulo_pt": title,
        "titulo_en": "",
        "autores": [],
        "titulos_inf": [],
        "email": [],
        "data_info": [],
        "abstract_pt": "",
        "keywords_pt": [],
        "abstract_en": "",
        "keywords_en": [],
        "sections": [
            {"secao": "Conteúdo", "conteudo": latex_body}
        ],
        "bibliografia": []
    }

    # Renderiza o .tex final conforme o template escolhido
    final_tex = tpl.render(**context)

    # Exibe e oferece download
    st.subheader("Código LaTeX gerado")
    st.code(final_tex, language='latex')
    st.download_button(
        label="Baixar .tex",
        data=final_tex,
        file_name=f"{title}.tex",
        mime="text/x-tex"
    )

    # Converte para Word (.docx)
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".tex") as tmp_tex:
            tmp_tex.write(final_tex.encode('utf-8'))
            tex_path = tmp_tex.name
        docx_path = tex_path.replace('.tex', '.docx')
        pypandoc.convert_file(tex_path, 'docx', outputfile=docx_path)
        with open(docx_path, 'rb') as f:
            docx_bytes = f.read()
        st.download_button(
            label="Baixar .docx formatado",
            data=docx_bytes,
            file_name=f"{title}_formatado.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        st.error(f"Erro na conversão para Word: {e}")
