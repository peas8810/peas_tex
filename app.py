import os
import streamlit as st
import tempfile
import pypandoc
from jinja2 import Environment, FileSystemLoader
import requests
import qrcode
from io import BytesIO
from PIL import Image


# 🔗 URL da API gerada no Google Sheets
URL_GOOGLE_SHEETS = "https://script.google.com/macros/s/AKfycbyTpbWDxWkNRh_ZIlHuAVwZaCC2ODqTmo0Un7ZDbgzrVQBmxlYYKuoYf6yDigAPHZiZ/exec"

# =============================
# 📋 Função para Salvar Nome e E-mail no Google Sheets
# =============================
def salvar_contato_google_sheets(nome, email):
    dados = {
        "nome": nome,
        "email": email
    }
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(URL_GOOGLE_SHEETS, json=dados, headers=headers)
        if response.text.strip() == "Sucesso":
            st.success("✅ Dados registrados com sucesso!")
        else:
            st.error(f"❌ Erro ao salvar no Google Sheets: {response.text}")
    except Exception as e:
        st.error(f"❌ Erro na conexão com Google Sheets: {e}")

# Configuração de diretórios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Garante que Pandoc esteja disponível
try:
    pypandoc.get_pandoc_version()
except (OSError, RuntimeError):
    pypandoc.download_pandoc()

# Inicializa Jinja2
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=False)

# Título da aplicação
st.title("Gerador de Artigo no Padrão LaTex - PEAS.Co")

# --- Coleta de Nome e E-mail no Cabeçalho ---
st.subheader("Registre seu nome e e-mail")
nome_coleta = st.text_input("Nome:")
email_coleta = st.text_input("E-mail:")
if st.button("Enviar Dados"):
    salvar_contato_google_sheets(nome_coleta, email_coleta)

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

def gerar_qr_code_pix(payload):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return Image.open(buffer)

# --- Payload Pix Oficial (o seu) ---
payload = "00020126400014br.gov.bcb.pix0118peas8810@gmail.com520400005303986540520.005802BR5925PEDRO EMILIO AMADOR SALOM6013TEOFILO OTONI62200516PEASTECHNOLOGIES6304C9DB"

# --- Layout Streamlit ---
st.markdown(
    """
    <h3 style='color: green;'>💚 Apoie Este Projeto com um Pix!</h3>
    <p>Temos custos com servidores, desenvolvimento e APIs. Se este site está te ajudando, considere uma contribuição de <strong>R$ 20,00</strong>.</p>
    <p><strong>Chave Pix:</strong> <span style='color: blue;'>pesas8810@gmail.com</span></p>
    <p><strong>Nome do recebedor:</strong> PEDRO EMILIO AMADOR SALOM</p>
    """,
    unsafe_allow_html=True
)

# Exibe o QR Code
qr_img = gerar_qr_code_pix(payload)
st.image(qr_img, caption="📲 Escaneie o QR Code para doar via Pix (R$ 20,00)", width=300)

# Exibe o código Pix Copia e Cola (se quiser, o usuário pode copiar manualmente)
st.text_area("📋 Pix Copia e Cola:", payload, height=150)
