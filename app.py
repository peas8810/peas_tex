import os
import streamlit as st
import tempfile
import pypandoc
from jinja2 import Environment, FileSystemLoader

# Garante que Pandoc esteja disponível (download automático se necessário)
try:
    pypandoc.get_pandoc_version()
except (OSError, RuntimeError):
    pypandoc.download_pandoc()

# Configuração de diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Inicializa Jinja2
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=False)

# Título da aplicação
st.title("Gerador de Artigo no Padrão da Revista")

# Seleção de template
article_type = st.selectbox(
    "Tipo de Artigo:",
    ["Estudo de Caso", "Revisão Bibliográfica"]
)
template_file = (
    "estudo_caso.tex.j2" if article_type == "Estudo de Caso"
    else "revisao_bibliografica.tex.j2"
)
tpl = env.get_template(template_file)

# Modo de edição manual
manual_mode = st.checkbox("Edição Manual")

if manual_mode:
    # Campos de edição manual
    titulo_pt = st.text_input("Título em Português")
    titulo_en = st.text_input("Título em Inglês")
    autores_input = st.text_input("Autores (separar por vírgula)")
    autores = [a.strip() for a in autores_input.split(",") if a.strip()]
    email_input = st.text_input("E-mails (separar por vírgula)")
    emails = [e.strip() for e in email_input.split(",") if e.strip()]
    recebido = st.text_input("Data Recebido (dd/mm/aaaa)")
    aceito = st.text_input("Data Aceito (dd/mm/aaaa)")
    abstract_pt = st.text_area("Resumo (PT)")
    keywords_pt_input = st.text_input("Palavras-chave PT (ponto e vírgula)")
    keywords_pt = [k.strip() for k in keywords_pt_input.split(";") if k.strip()]
    abstract_en = st.text_area("Abstract (EN)")
    keywords_en_input = st.text_input("Keywords EN (ponto e vírgula)")
    keywords_en = [k.strip() for k in keywords_en_input.split(";") if k.strip()]

    num_sec = st.number_input(
        "Número de seções", min_value=1, max_value=20, value=1
    )
    sections = []
    for i in range(int(num_sec)):
        sec_title = st.text_input(f"Título da Seção {i+1}", key=f"sec_title_{i}")
        sec_content = st.text_area(f"Conteúdo da Seção {i+1}", key=f"sec_content_{i}")
        sections.append({"secao": sec_title, "conteudo": sec_content})

    biblio_input = st.text_area("Bibliografia (uma referência por linha)")
    bibliografia = []
    for idx, line in enumerate(biblio_input.splitlines()):
        if line.strip():
            bibliografia.append({"citekey": f"ref{idx+1}", "texto": line.strip()})

    if st.button("Gerar LaTeX"):
        context = {
            "titulo_pt": titulo_pt,
            "titulo_en": titulo_en,
            "autores": autores,
            "email": emails,
            "data_info": [recebido, aceito],
            "abstract_pt": abstract_pt,
            "keywords_pt": keywords_pt,
            "abstract_en": abstract_en,
            "keywords_en": keywords_en,
            "sections": sections,
            "bibliografia": bibliografia
        }
        final_tex = tpl.render(**context)
        st.subheader("Código LaTeX gerado")
        st.code(final_tex, language="latex")
        st.download_button(
            "Baixar .tex", final_tex,
            file_name="manual.tex", mime="text/x-tex"
        )

else:
    # Upload e conversão automática
    uploaded_file = st.file_uploader(
        "Envie seu arquivo (DOCX ou PDF)", type=["docx", "pdf"]
    )
    if uploaded_file:
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(uploaded_file.name)[1]
        ) as tmp:
            tmp.write(uploaded_file.getbuffer())
            tmp_path = tmp.name
        ext = os.path.splitext(tmp_path)[1][1:]
        try:
            body = pypandoc.convert_file(tmp_path, 'latex', format=ext)
        except Exception as e:
            st.error(f"Erro na conversão: {e}")
            body = ""

        title = os.path.splitext(uploaded_file.name)[0]
        context = {
            "titulo_pt": title,
            "titulo_en": "",
            "autores": [],
            "email": [],
            "data_info": ["", ""],
            "abstract_pt": "",
            "keywords_pt": [],
            "abstract_en": "",
            "keywords_en": [],
            "sections": [{"secao": "Conteúdo", "conteudo": body}],
            "bibliografia": []
        }
        final_tex = tpl.render(**context)
        st.subheader("Código LaTeX gerado")
        st.code(final_tex, language="latex")
        st.download_button(
            "Baixar .tex", final_tex,
            file_name=f"{title}.tex", mime="text/x-tex"
        )

        # Conversão para Word
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".tex") as tmp_tex:
                tmp_tex.write(final_tex.encode('utf-8'))
                tex_path = tmp_tex.name
            docx_path = tex_path.replace('.tex', '.docx')
            pypandoc.convert_file(tex_path, 'docx', outputfile=docx_path)
            with open(docx_path, 'rb') as f:
                docx_bytes = f.read()
            st.download_button(
                "Baixar .docx formatado",
                docx_bytes,
                file_name=f"{title}_formatado.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        except Exception as e:
            st.error(f"Erro na conversão para Word: {e}")
