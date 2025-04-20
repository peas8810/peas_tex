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
# Carrega o template LaTeX
tpl = env.get_template("padrao_revista.tex.j2")

# Título da aplicação
st.title("Gerador de LaTeX para Revista")

# Uploader de arquivos
uploaded_file = st.file_uploader("Envie seu arquivo (DOCX ou PDF)", type=["docx", "pdf"])

if uploaded_file:
    # Salva o arquivo enviado em disco temporário
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    # Extensão sem ponto
    ext = os.path.splitext(tmp_path)[1][1:]

    # Converte documento para LaTeX bruto usando Pandoc
    try:
        latex_body = pypandoc.convert_file(tmp_path, 'latex', format=ext)
    except Exception as e:
        st.error(f"Erro na conversão com Pandoc: {e}")
        latex_body = ""

    # Usa o nome do arquivo como título do artigo
    title = os.path.splitext(uploaded_file.name)[0]

    # Monta contexto para preencher o template
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

    # Exibe e oferece download do .tex
    st.subheader("Código LaTeX gerado")
    st.code(final_tex, language='latex')
    st.download_button(
        label="Baixar .tex",
        data=final_tex,
        file_name=f"{title}.tex",
        mime="text/x-tex"
    )

    # Converte o LaTeX para Word formatado e oferece download
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
