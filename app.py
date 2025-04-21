import os
import streamlit as st
import tempfile
import pypandoc
from jinja2 import Environment, FileSystemLoader

# Garante que Pandoc está disponível
try:
    pypandoc.get_pandoc_version()
except (OSError, RuntimeError):
    pypandoc.download_pandoc()

# Diretórios\ nBASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=False)

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

# Habilita edição manual
manual_mode = st.checkbox("Edição Manual")
tpl = env.get_template(template_file)

# Variáveis comuns
context = {}

if manual_mode:
    # Inputs manuais de cada parte
    context["titulo_pt"] = st.text_input("Título em Português")
    context["titulo_en"] = st.text_input("Título em Inglês")
    autores = st.text_input("Autores (separar por vírgula)")
    context["autores"] = [a.strip() for a in autores.split(",") if a.strip()]
    emails = st.text_input("E-mails (separar por vírgula)")
    context["email"] = [e.strip() for e in emails.split(",") if e.strip()]
    recebido = st.text_input("Data Recebido (dd/mm/aaaa)")
    aceito = st.text_input("Data Aceite (dd/mm/aaaa)")
    context["data_info"] = [recebido, aceito]
    context["abstract_pt"] = st.text_area("Resumo (PT)")
    kws = st.text_input("Palavras-chave PT (ponto e vírgula)")
    context["keywords_pt"] = [k.strip() for k in kws.split(";") if k.strip()]
    context["abstract_en"] = st.text_area("Abstract (EN)")
    kws_en = st.text_input("Keywords EN (ponto e vírgula)")
    context["keywords_en"] = [k.strip() for k in kws_en.split(";") if k.strip()]
    
    # Seções dinâmicas
    sections = []
    num_sec = st.number_input("Número de seções", min_value=1, max_value=20, value=3)
    for i in range(int(num_sec)):
        st.markdown(f"**Seção {i+1}**")
        sec_title = st.text_input(f"Título da Seção {i+1}", key=f"sec_title_{i}")
        sec_content = st.text_area(f"Conteúdo da Seção {i+1}", key=f"sec_content_{i}")
        sections.append({"secao": sec_title, "conteudo": sec_content})
    context["sections"] = sections

    # Bibliografia manual
    biblio_text = st.text_area("Bibliografia (uma referência por linha)")
    biblio_items = [line.strip() for line in biblio_text.splitlines() if line.strip()]
    bibliografia = [{"citekey": f"ref{i+1}", "texto": ref} for i, ref in enumerate(biblio_items)]
    context["bibliografia"] = bibliografia

    # Gera LaTeX
    if st.button("Gerar LaTeX Manual"):
        final_tex = tpl.render(**context)
        st.subheader("Código LaTeX gerado")
        st.code(final_tex, language='latex')
        st.download_button("Baixar .tex", final_tex, file_name="manual.tex", mime="text/x-tex")

else:
    # Upload e conversão automática
    uploaded_file = st.file_uploader("Envie seu arquivo (DOCX ou PDF)", type=["docx", "pdf"])
    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
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
        st.code(final_tex, language='latex')
        st.download_button("Baixar .tex", final_tex, file_name=f"{title}.tex", mime="text/x-tex")
        # Conversão para docx
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".tex") as tmp_tex:
                tmp_tex.write(final_tex.encode('utf-8'))
                tex_path = tmp_tex.name
            docx_path = tex_path.replace('.tex', '.docx')
            pypandoc.convert_file(tex_path, 'docx', outputfile=docx_path)
            with open(docx_path, 'rb') as f:
                docx_bytes = f.read()
            st.download_button("Baixar .docx formatado", docx_bytes, file_name=f"{title}_formatado.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        except Exception as e:
            st.error(f"Erro na conversão para Word: {e}")
