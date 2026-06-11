from pathlib import Path
import tempfile
import time
import json

import streamlit as st
import ollama
import ebooklib

from pypdf import PdfReader
from ebooklib import epub
from bs4 import BeautifulSoup

from textoprompt import textobase

# =====================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================

st.set_page_config(
    page_title="Leitura Segura — Classificação Indicativa IA",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =====================================================
# CSS REDESIGN — Dark Editorial
# =====================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;600&display=swap');

    /* ── Reset e base ── */
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        background-color: #0A0F1E;
        color: #E8EAF0;
    }

    .block-container {
        max-width: 860px;
        padding-top: 3.5rem;
        padding-bottom: 5rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    /* ── Eyebrow acima do título ── */
    .eyebrow {
        font-family: 'DM Sans', sans-serif;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: #6366F1;
        margin-bottom: 0.6rem;
    }

    /* ── Título principal ── */
    h1 {
        font-family: 'Syne', sans-serif !important;
        font-size: 2.6rem !important;
        font-weight: 800 !important;
        line-height: 1.1 !important;
        color: #F0F2FF !important;
        letter-spacing: -0.02em;
        margin-bottom: 0.75rem !important;
    }

    /* ── Subtítulo descritivo ── */
    .subtitulo {
        font-size: 1rem;
        color: #8B90A8;
        line-height: 1.6;
        max-width: 600px;
        margin-bottom: 2.5rem;
    }

    /* ── Separador fino ── */
    hr {
        border: none;
        border-top: 1px solid #1E2A45;
        margin: 2rem 0;
    }

    /* ── Upload container ── */
    .upload-wrapper {
        background: #111827;
        border: 1.5px dashed #2A3352;
        border-radius: 16px;
        padding: 2.5rem 2rem;
        text-align: center;
        transition: border-color 0.25s ease;
        margin-bottom: 1.5rem;
    }
    .upload-wrapper:hover {
        border-color: #6366F1;
    }

    /* ── Streamlit file uploader ── */
    [data-testid="stFileUploader"] {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }
    [data-testid="stFileUploader"] label {
        color: #8B90A8 !important;
        font-size: 0.9rem;
    }

    /* ── Botão principal ── */
    .stButton > button {
        background: #6366F1;
        color: #FFFFFF;
        border: none;
        border-radius: 10px;
        font-family: 'DM Sans', sans-serif;
        font-size: 0.95rem;
        font-weight: 600;
        height: 3.2rem;
        width: 100%;
        letter-spacing: 0.01em;
        transition: background 0.2s ease, box-shadow 0.2s ease;
        box-shadow: 0 0 0 0 rgba(99, 102, 241, 0);
    }
    .stButton > button:hover {
        background: #4F52D9;
        box-shadow: 0 0 30px rgba(99, 102, 241, 0.35);
        color: white;
    }
    .stButton > button:active {
        background: #4044C4;
    }

    /* ── Métricas ── */
    [data-testid="stMetric"] {
        background: #111827;
        border: 1px solid #1E2A45;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.72rem !important;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #5A6080 !important;
    }
    [data-testid="stMetricValue"] {
        font-family: 'Syne', sans-serif !important;
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        color: #A78BFA !important;
    }

    /* ── Abas ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: #111827;
        border-radius: 10px;
        padding: 4px;
        border: 1px solid #1E2A45;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        border-radius: 7px;
        padding: 0 1.2rem;
        font-size: 0.85rem;
        font-weight: 500;
        color: #5A6080;
        background: transparent;
        transition: all 0.2s ease;
    }
    .stTabs [aria-selected="true"] {
        background: #1E2A45 !important;
        color: #A78BFA !important;
    }

    /* ── Headings no relatório ── */
    h2 {
        font-family: 'Syne', sans-serif !important;
        font-size: 1.4rem !important;
        font-weight: 700 !important;
        color: #E8EAF0 !important;
        letter-spacing: -0.01em;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
    }

    h3 {
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.16em !important;
        text-transform: uppercase !important;
        color: #6366F1 !important;
        margin-top: 2rem !important;
        margin-bottom: 0.75rem !important;
        padding-bottom: 0;
        border-bottom: none !important;
    }

    /* ── Card de categoria ── */
    .categoria-card {
        background: #111827;
        border: 1px solid #1E2A45;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        margin-bottom: 0.75rem;
        transition: border-color 0.2s ease, background 0.2s ease;
    }
    .categoria-card:hover {
        border-color: #2E3A5E;
        background: #141C2E;
    }

    /* ── Badge de nível (semáforo) ── */
    .badge {
        display: inline-block;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        padding: 3px 10px;
        border-radius: 999px;
        margin-left: 8px;
        vertical-align: middle;
    }
    .badge-alto    { background: rgba(239,68,68,0.15);  color: #F87171; border: 1px solid rgba(239,68,68,0.25); }
    .badge-medio   { background: rgba(234,179,8,0.15);  color: #FBBF24; border: 1px solid rgba(234,179,8,0.25); }
    .badge-baixo   { background: rgba(34,197,94,0.15);  color: #4ADE80; border: 1px solid rgba(34,197,94,0.25); }
    .badge-neutro  { background: rgba(99,102,241,0.12); color: #A78BFA; border: 1px solid rgba(99,102,241,0.2); }

    /* ── Evidência box ── */
    .evidencia-box {
        background: #0D1424;
        border-left: 3px solid #6366F1;
        border-radius: 0 10px 10px 0;
        padding: 1rem 1.2rem;
        margin-bottom: 0.75rem;
        font-size: 0.88rem;
        color: #9BA3C2;
        line-height: 1.6;
        transition: border-color 0.2s ease;
    }
    .evidencia-box:hover {
        border-left-color: #A78BFA;
        color: #C4C9E0;
    }
    .evidencia-box strong {
        color: #7C82C8;
        font-weight: 600;
    }

    /* ── Success / info ── */
    [data-testid="stAlert"] {
        background: #111827 !important;
        border: 1px solid #1E2A45 !important;
        border-radius: 10px !important;
        color: #8B90A8 !important;
    }

    /* ── Download buttons ── */
    [data-testid="stDownloadButton"] button {
        background: #111827 !important;
        border: 1px solid #2A3352 !important;
        color: #A78BFA !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stDownloadButton"] button:hover {
        background: #1E2A45 !important;
        border-color: #6366F1 !important;
        color: #C4C6FF !important;
    }

    /* ── Status box ── */
    [data-testid="stStatusWidget"] {
        background: #111827 !important;
        border: 1px solid #1E2A45 !important;
        border-radius: 12px !important;
    }

    /* ── JSON viewer ── */
    [data-testid="stJson"] {
        background: #0D1424 !important;
        border-radius: 12px !important;
        border: 1px solid #1E2A45 !important;
    }

    /* ── Divider ── */
    [data-testid="stDivider"] hr {
        border-color: #1E2A45 !important;
    }

    /* ── Scrollbar personalizada ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0A0F1E; }
    ::-webkit-scrollbar-thumb { background: #2A3352; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #6366F1; }
</style>
""", unsafe_allow_html=True)


# =====================================================
# DICIONÁRIO DE CORREÇÃO ORTOGRÁFICA
# =====================================================

TERMOS_PTBR = {
    "metadados": "Metadados",
    "titulo": "Título da Obra",
    "autor": "Autor(a)",
    "classificacao final": "Classificação Final",
    "confianca geral": "Confiança Geral",
    "data analise": "Data da Análise",
    "resumo executivo": "Resumo Executivo",
    "avaliacao": "Avaliação Detalhada",
    "violencia": "Violência",
    "sexo nudez": "Sexo e Nudez",
    "linguagem": "Linguagem",
    "drogas alcool tabaco": "Drogas, Álcool e Tabaco",
    "medo horror tensao": "Medo, Horror e Tensão",
    "temas sensiveis": "Temas Sensíveis",
    "complexidade cognitiva": "Complexidade Cognitiva",
    "potencial educacional": "Potencial Educacional",
    "temas sensiveis detectados": "Temas Sensíveis Detectados",
    "impacto emocional": "Impacto Emocional",
    "descricao": "Descrição",
    "frequencia": "Frequência",
    "gatilhos": "Gatilhos Identificados",
    "subcategorias detectadas": "Subcategorias Detectadas",
    "evidencias": "Evidências Extraídas do Texto",
    "explicacao": "Explicação",
    "localizacao": "Localização",
    "estatisticas": "Estatísticas da Análise",
    "quantidade evidencias": "Quantidade de Evidências",
    "quantidade gatilhos": "Quantidade de Gatilhos",
    "quantidade temas sensiveis": "Quantidade de Temas Sensíveis",
    "recomendacao pais educadores": "Recomendação para Pais e Educadores",
    "justificativa final": "Justificativa Final",
    "criterio": "Critério",
    "subcategoria": "Subcategoria",
    "trecho": "Trecho Original",
    "id": "Identificação",
    "nivel": "Nível",
    "confianca": "Confiança da IA"
}

def corrigir_texto(texto):
    texto_limpo = str(texto).replace('_', ' ').strip().lower()
    return TERMOS_PTBR.get(texto_limpo, str(texto).replace('_', ' ').title())

def badge_nivel(valor_str):
    """Retorna HTML de badge colorido baseado no nível detectado."""
    v = str(valor_str).lower()
    if any(x in v for x in ["alto", "forte", "intenso", "explícito", "explicito", "grave", "severo"]):
        return f'<span class="badge badge-alto">{valor_str}</span>'
    elif any(x in v for x in ["médio", "medio", "moderado", "presente", "ocasional"]):
        return f'<span class="badge badge-medio">{valor_str}</span>'
    elif any(x in v for x in ["baixo", "leve", "mínimo", "minimo", "ausente", "nenhum", "nenhuma"]):
        return f'<span class="badge badge-baixo">{valor_str}</span>'
    else:
        return f'<span class="badge badge-neutro">{valor_str}</span>'


# =====================================================
# CABEÇALHO
# =====================================================

st.markdown('<p class="eyebrow">Ferramenta de Análise Editorial</p>', unsafe_allow_html=True)
st.title("Classificação Indicativa IA")
st.markdown(
    '<p class="subtitulo">Envie um livro em PDF ou EPUB e receba em minutos um relatório completo '
    'de classificação etária, gatilhos emocionais, nível de violência e temas sensíveis — '
    'gerado por inteligência artificial.</p>',
    unsafe_allow_html=True
)

# =====================================================
# FUNÇÕES DE EXTRAÇÃO
# =====================================================

def ler_pdf(caminho):
    reader = PdfReader(caminho)
    texto = ""
    for pagina in reader.pages:
        conteudo = pagina.extract_text()
        if conteudo:
            texto += conteudo + "\n"
    return texto

def ler_epub(caminho):
    book = epub.read_epub(caminho)
    texto = ""
    documentos = [item for item in book.get_items() if item.get_type() == ebooklib.ITEM_DOCUMENT]
    for item in documentos:
        soup = BeautifulSoup(item.get_content(), "html.parser")
        texto += soup.get_text(separator=" ", strip=True) + "\n\n"
    return texto

def extrair_texto(upload):
    extensao = Path(upload.name).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=extensao) as tmp:
        tmp.write(upload.getvalue())
        caminho = tmp.name
    if extensao == ".pdf": return ler_pdf(caminho)
    elif extensao == ".epub": return ler_epub(caminho)
    raise ValueError("Formato não suportado")

# =====================================================
# OLLAMA CLOUD
# =====================================================

def analisar_livro(texto):
    prompt = f"{textobase}\n\n{texto}"
    client = ollama.Client(
        host="https://api.ollama.com",
        headers={"Authorization": f"Bearer {st.secrets['OLLAMA_API_KEY']}"}
    )
    inicio = time.perf_counter()
    response = client.chat(
        model="gemma4:31b-cloud",
        messages=[{"role": "user", "content": prompt}],
        options={"num_ctx": 262144, "num_predict": 8192, "temperature": 0.2}
    )
    fim = time.perf_counter()
    conteudo = response["message"]["content"]
    try:
        dados_json = json.loads(conteudo)
    except Exception:
        dados_json = {"erro": "A resposta da IA não retornou um JSON válido.", "resposta_original": conteudo}
    return dados_json, conteudo, fim - inicio, response

# =====================================================
# FORMATADOR VISUAL DO RELATÓRIO
# =====================================================

def renderizar_relatorio_bonito(dados):
    if not isinstance(dados, dict):
        st.write(dados)
        return

    for chave, valor in dados.items():
        titulo_formatado = corrigir_texto(chave)
        st.markdown(f"### {titulo_formatado}")

        if isinstance(valor, dict):
            st.markdown('<div class="categoria-card">', unsafe_allow_html=True)
            for subchave, subvalor in valor.items():
                nome_subchave = corrigir_texto(subchave)
                if isinstance(subvalor, dict):
                    st.markdown(f"**{nome_subchave}**")
                    for k, v in subvalor.items():
                        st.markdown(f"<span style='color:#5A6080;font-size:0.85rem;'>— <b style='color:#9BA3C2'>{corrigir_texto(k)}:</b> {v}</span>", unsafe_allow_html=True)
                elif isinstance(subvalor, list):
                    if len(subvalor) == 0:
                        st.markdown(f"<span style='color:#5A6080;font-size:0.85rem;'>— <b style='color:#9BA3C2'>{nome_subchave}:</b> <i>Nenhuma</i></span>", unsafe_allow_html=True)
                    else:
                        itens = ", ".join([str(item) for item in subvalor])
                        st.markdown(f"<span style='color:#5A6080;font-size:0.85rem;'>— <b style='color:#9BA3C2'>{nome_subchave}:</b> {itens}</span>", unsafe_allow_html=True)
                else:
                    # Chave "nivel" recebe badge colorido
                    chave_limpa = str(subchave).replace('_', ' ').strip().lower()
                    if chave_limpa == "nivel":
                        st.markdown(
                            f"<span style='color:#5A6080;font-size:0.85rem;'>— <b style='color:#9BA3C2'>{nome_subchave}:</b> {badge_nivel(subvalor)}</span>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(f"<span style='color:#5A6080;font-size:0.85rem;'>— <b style='color:#9BA3C2'>{nome_subchave}:</b> {subvalor}</span>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        elif isinstance(valor, list):
            if len(valor) == 0:
                st.markdown("<span style='color:#3A4060;font-size:0.85rem;font-style:italic;'>Nenhum item detectado nesta categoria.</span>", unsafe_allow_html=True)
            elif isinstance(valor[0], dict):
                for item in valor:
                    linhas = ""
                    for k, v in item.items():
                        linhas += f"<strong>{corrigir_texto(k)}:</strong> {v}<br>"
                    st.markdown(f'<div class="evidencia-box">{linhas}</div>', unsafe_allow_html=True)
            else:
                for item in valor:
                    st.markdown(f"<span style='color:#9BA3C2;font-size:0.88rem;'>· {item}</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color:#C4C9E0;'>{valor}</span>", unsafe_allow_html=True)

        st.write("")


# =====================================================
# INTERFACE PRINCIPAL
# =====================================================

with st.container(border=False):
    st.markdown('<div class="upload-wrapper">', unsafe_allow_html=True)
    arquivo = st.file_uploader(
        "Arraste seu PDF ou EPUB aqui, ou clique para selecionar",
        type=["pdf", "epub"],
        help="Processamento seguro e privativo. O arquivo não é armazenado.",
        label_visibility="visible"
    )
    st.markdown('</div>', unsafe_allow_html=True)

if arquivo:
    st.markdown(
        f"<span style='color:#4ADE80;font-size:0.85rem;font-weight:600;'>✓ {arquivo.name} carregado</span>",
        unsafe_allow_html=True
    )
    st.write("")

    if st.button("Analisar livro →"):

        with st.status("Processando documento...", expanded=True) as status:
            st.write("Extraindo texto do arquivo...")
            texto = extrair_texto(arquivo)
            st.write(f"✓ {len(texto):,} caracteres extraídos.".replace(',', '.'))
            st.write("Enviando ao modelo de linguagem para análise profunda...")
            dados_json, resultado_bruto, tempo, response = analisar_livro(texto)
            status.update(label="Análise concluída.", state="complete", expanded=False)

        st.write("")
        col1, col2, col3 = st.columns(3)
        col1.metric("Caracteres", f"{len(texto):,}".replace(',', '.'))
        col2.metric("Tempo", f"{tempo:.1f}s")
        if "eval_count" in response:
            col3.metric("Tokens", f"{response['eval_count']:,}".replace(',', '.'))

        st.divider()

        aba_relatorio, aba_dados, aba_downloads = st.tabs([
            "Relatório",
            "JSON técnico",
            "Exportar"
        ])

        with aba_relatorio:
            st.markdown("## Resultado da Análise")
            renderizar_relatorio_bonito(dados_json)

        with aba_dados:
            st.info("Retorno estruturado da IA — útil para auditoria e integrações.")
            st.json(dados_json)

        with aba_downloads:
            st.markdown("## Exportar relatório")
            st.markdown("<span style='color:#5A6080;font-size:0.9rem;'>Salve os resultados para uso externo ou integração com outros sistemas.</span>", unsafe_allow_html=True)
            st.write("")
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.download_button(
                    label="Baixar JSON",
                    data=json.dumps(dados_json, ensure_ascii=False, indent=2),
                    file_name="classificacao_livro.json",
                    mime="application/json",
                    use_container_width=True
                )
            with col_dl2:
                st.download_button(
                    label="Baixar TXT bruto",
                    data=resultado_bruto,
                    file_name="analise_bruta.txt",
                    mime="text/plain",
                    use_container_width=True
                )
