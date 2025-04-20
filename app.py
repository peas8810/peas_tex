from docx import Document
import pdfminer.high_level as pdf_hl
from jinja2 import Environment, FileSystemLoader
import pypandoc
import openai

# 1. Extrair texto de DOCX
def extrair_docx(path):
    doc = Document(path)
    texto = []
    for p in doc.paragraphs:
        texto.append(p.text)
    return "\n".join(texto)

# 2. Extrair texto de PDF
def extrair_pdf(path):
    return pdf_hl.extract_text(path)

# 3. Preencher template Jinja2
env = Environment(loader=FileSystemLoader("templates"))
tpl = env.get_template("padrão_revista.tex.j2")

def gerar_latex(context):
    return tpl.render(**context)

# 4. Invocar OpenAI para formatar abstrato ou seções complexas
def formatar_com_ia(trecho, instrucoes):
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system","content":"Você é um conversor de texto para LaTeX seguindo o padrão da revista."},
            {"role":"user","content":f"{instrucoes}\n\n{trecho}"}
        ],
        temperature=0
    )
    return resp.choices[0].message.content

# 5. Fluxo principal
def processar_arquivo(path, tipo):
    raw = extrair_docx(path) if tipo=="docx" else extrair_pdf(path)
    # Aqui você faria parsing para separar título, autores, abstract...
    context = {
        "titulo": "TÍTULO EXTRAÍDO",
        "autores": ["Autor A", "Autor B"],
        "abstract_pt": "Resumo extraído…",
        "keywords_pt": ["chave1","chave2"],
        "sections": [
            {"secao":"Introdução", "conteudo":"…"},
            # …
        ],
        "bibliografia":[
            {"citekey":"ref1","texto":"AUTOR…"}
        ]
    }
    # Opcional: refinar abstract com IA
    context["abstract_pt"] = formatar_com_ia(
        context["abstract_pt"],
        "Formate este resumo em LaTeX, sem alterar o template."
    )
    return gerar_latex(context)
