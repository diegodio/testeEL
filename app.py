from pathlib import Path
import tempfile
import time

import streamlit as st
import ollama
import ebooklib

from pypdf import PdfReader
from ebooklib import epub
from bs4 import BeautifulSoup

from textoprompt import textobase

import json

# =====================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================

st.set_page_config(
    page_title="Classificação Indicativa de Livros",
    page_icon="📚",
    layout="wide"
)

# =====================================================
# CSS MODERNO
# =====================================================

st.markdown("""
<style>

.main {
    padding-top: 1rem;
}

.block-container {
    max-width: 1200px;
}

h1 {
    font-weight: 800;
}

.stButton > button {
    width: 100%;
    height: 3rem;
    font-size: 1.1rem;
    font-weight: bold;
    border-radius: 12px;
}

.upload-box {
    padding: 20px;
    border-radius: 16px;
    border: 2px dashed #666;
}

.resultado {
    padding: 20px;
    border-radius: 16px;
    background: #111;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# TÍTULO
# =====================================================

st.title("📚 Classificação Indicativa de Livros")

st.markdown(
    """
    Faça upload de um **PDF** ou **EPUB**.
    
    O sistema irá:
    
    - Extrair todo o texto
    - Enviar para o Ollama Cloud
    - Aplicar a análise completa
    - Gerar classificação indicativa detalhada
    """
)

# =====================================================
# LEITURA PDF
# =====================================================

def ler_pdf(caminho):

    reader = PdfReader(caminho)

    texto = ""

    total = len(reader.pages)

    barra = st.progress(0)

    for i, pagina in enumerate(reader.pages):

        conteudo = pagina.extract_text()

        if conteudo:
            texto += conteudo + "\n"

        barra.progress((i + 1) / total)

    barra.empty()

    return texto


# =====================================================
# LEITURA EPUB
# =====================================================

def ler_epub(caminho):

    book = epub.read_epub(caminho)

    texto = ""

    documentos = [
        item
        for item in book.get_items()
        if item.get_type() == ebooklib.ITEM_DOCUMENT
    ]

    total = len(documentos)

    barra = st.progress(0)

    for i, item in enumerate(documentos):

        soup = BeautifulSoup(
            item.get_content(),
            "html.parser"
        )

        texto += soup.get_text(
            separator=" ",
            strip=True
        )

        texto += "\n\n"

        barra.progress((i + 1) / total)

    barra.empty()

    return texto


# =====================================================
# EXTRAÇÃO
# =====================================================

def extrair_texto(upload):

    extensao = Path(upload.name).suffix.lower()

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=extensao
    ) as tmp:

        tmp.write(upload.getvalue())

        caminho = tmp.name

    if extensao == ".pdf":
        return ler_pdf(caminho)

    elif extensao == ".epub":
        return ler_epub(caminho)

    raise ValueError("Formato não suportado")


# =====================================================
# OLLAMA CLOUD
# =====================================================

def analisar_livro(texto):

    prompt = f"""
{textobase}

{texto}
"""

    client = ollama.Client(
        host="https://api.ollama.com",
        headers={
            "Authorization":
            f"Bearer {st.secrets['OLLAMA_API_KEY']}"
        }
    )

    inicio = time.perf_counter()

    response = client.chat(
        model="gemma4:31b-cloud",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "num_ctx": 262144,
            "num_predict": 8192,
            "temperature": 0.2
        }
    )

    fim = time.perf_counter()

    conteudo = response["message"]["content"]

    try:
        dados_json = json.loads(conteudo)

    except Exception:

        dados_json = {
            "erro": "Resposta não retornou JSON válido",
            "resposta_original": conteudo
        }

    return (
        dados_json,
        conteudo,
        fim - inicio,
        response
    )

# =====================================================
# UPLOAD
# =====================================================

arquivo = st.file_uploader(
    "Selecione um PDF ou EPUB",
    type=["pdf", "epub"]
)

# =====================================================
# BOTÃO
# =====================================================

if arquivo:

    st.success(f"Arquivo carregado: {arquivo.name}")

    if st.button("🚀 Iniciar análise"):

        with st.spinner("Extraindo texto..."):

            texto = extrair_texto(arquivo)

        st.info(
            f"Texto extraído: {len(texto):,} caracteres"
        )

        with st.spinner(
            "Enviando para o Ollama Cloud..."
        ):

            dados_json, resultado_bruto, tempo, response = analisar_livro(texto)

        st.success("Análise concluída!")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Caracteres",
                f"{len(texto):,}"
            )

        with col2:
            st.metric(
                "Tempo",
                f"{tempo:.1f}s"
            )

        with col3:

            if "eval_count" in response:

                st.metric(
                    "Tokens",
                    response["eval_count"]
                )

        st.divider()

        st.markdown("## Resultado")
        
        st.json(dados_json)
        
        # st.markdown(resultado)
        
        st.markdown("## Relatório Completo")
        st.markdown(
            f"```json\n{json.dumps(dados_json, ensure_ascii=False, indent=2)}\n```"
        )
       st.download_button(
    label="📥 Baixar JSON",
    data=json.dumps(
        dados_json,
        ensure_ascii=False,
        indent=2
    ),
    file_name="analise_livro.json",
    mime="application/json"
)
    st.download_button(
    label="📥 Baixar Resposta Bruta",
    data=resultado_bruto,
    file_name="resposta_bruta.txt",
    mime="text/plain"
)
