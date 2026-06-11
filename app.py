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

# ─────────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Lumina IA — Classificação Indicativa",
    page_icon="🔖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────
# CSS — Lumina IA Design System
# ─────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Lora:ital,wght@0,400;0,500;1,400&display=swap');

/* ── Esconde chrome nativo do Streamlit ── */
#MainMenu                                  { visibility: hidden !important; }
header[data-testid="stHeader"]             { display: none !important; }
footer                                     { display: none !important; }
[data-testid="stToolbar"]                  { display: none !important; }
[data-testid="stDecoration"]               { display: none !important; }
.stDeployButton                            { display: none !important; }
button[title="View fullscreen"]            { display: none !important; }
[data-testid="stStatusWidget"]             { display: none !important; }

/* ── Variáveis Lumina ── */
:root {
    --indigo:   #4F46E5;
    --indigo-d: #3730A3;
    --purple:   #7C3AED;
    --purple-l: #EDE9FE;
    --paper:    #F8FAFC;
    --surface:  #FFFFFF;
    --border:   #E2E8F0;
    --text-1:   #1E293B;
    --text-2:   #475569;
    --text-3:   #94A3B8;
    --green:    #10B981;
    --green-l:  #D1FAE5;
    --amber:    #F59E0B;
    --amber-l:  #FEF3C7;
    --red:      #EF4444;
    --red-l:    #FEE2E2;
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background-color: var(--paper) !important;
    color: var(--text-1) !important;
}

.block-container {
    max-width: 860px !important;
    padding-top: 0 !important;
    padding-bottom: 5rem !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}

/* ── Navbar / header da marca ── */
.lumina-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.4rem 0 1.8rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 3rem;
}
.lumina-brand {
    display: flex;
    align-items: center;
    gap: 10px;
}
.lumina-icon {
    width: 34px;
    height: 34px;
    background: linear-gradient(135deg, var(--indigo) 0%, var(--purple) 100%);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.lumina-icon svg {
    width: 18px;
    height: 18px;
    fill: none;
    stroke: white;
    stroke-width: 1.8;
    stroke-linecap: round;
    stroke-linejoin: round;
}
.lumina-wordmark {
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--text-1);
    letter-spacing: -0.01em;
}
.lumina-wordmark span {
    color: var(--indigo);
}
.lumina-badge {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    color: var(--indigo);
    background: var(--purple-l);
    padding: 4px 10px;
    border-radius: 999px;
}

/* ── Hero ── */
.lumina-hero {
    margin-bottom: 2.5rem;
}
.lumina-hero h1 {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 2.4rem !important;
    font-weight: 700 !important;
    color: var(--text-1) !important;
    line-height: 1.15 !important;
    letter-spacing: -0.025em !important;
    margin: 0 0 0.75rem !important;
}
.lumina-hero h1 em {
    font-style: normal;
    background: linear-gradient(90deg, var(--indigo), var(--purple));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.lumina-hero p {
    font-size: 1rem;
    color: var(--text-2);
    line-height: 1.7;
    max-width: 580px;
    margin: 0;
    font-weight: 400;
}

/* ── Upload card ── */
.upload-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 10px 25px rgba(0,0,0,0.04);
    margin-bottom: 1rem;
}
[data-testid="stFileUploader"] {
    background: var(--paper) !important;
    border: 1.5px dashed var(--border) !important;
    border-radius: 12px !important;
    transition: border-color 0.2s ease !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--indigo) !important;
}
[data-testid="stFileUploader"] section {
    padding: 1.5rem !important;
}
[data-testid="stFileUploader"] label {
    color: var(--text-2) !important;
    font-size: 0.88rem !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

/* ── Botão principal ── */
.stButton > button {
    background: linear-gradient(135deg, var(--indigo) 0%, var(--purple) 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.92rem !important;
    font-weight: 600 !important;
    height: 3.2rem !important;
    width: 100% !important;
    letter-spacing: 0.01em !important;
    box-shadow: 0 4px 14px rgba(79, 70, 229, 0.25) !important;
    transition: opacity 0.18s ease, transform 0.18s ease !important;
}
.stButton > button:hover {
    opacity: 0.9 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(79, 70, 229, 0.35) !important;
    color: white !important;
}

/* ── Métricas ── */
[data-testid="stMetric"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    padding: 1.1rem 1.3rem !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04) !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: var(--text-3) !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 1.65rem !important;
    font-weight: 700 !important;
    color: var(--indigo) !important;
}

/* ── Abas ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0 !important;
    background: var(--paper) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    border: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
    height: 38px !important;
    border-radius: 8px !important;
    padding: 0 1.2rem !important;
    font-size: 0.83rem !important;
    font-weight: 600 !important;
    color: var(--text-3) !important;
    background: transparent !important;
    transition: all 0.15s ease !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
.stTabs [aria-selected="true"] {
    background: var(--surface) !important;
    color: var(--indigo) !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.08) !important;
}

/* ── Headings do relatório ── */
h2 {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 1.3rem !important;
    font-weight: 700 !important;
    color: var(--text-1) !important;
    letter-spacing: -0.01em !important;
    margin-top: 2.5rem !important;
    margin-bottom: 1rem !important;
}

h3 {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.62rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.16em !important;
    text-transform: uppercase !important;
    color: var(--text-3) !important;
    margin-top: 2rem !important;
    margin-bottom: 0.5rem !important;
    border-bottom: none !important;
    padding-bottom: 0 !important;
}

/* ── Card de categoria (resultado) ── */
.cat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    overflow: hidden;
    margin-bottom: 0.75rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}
.cat-card-header {
    padding: 0.9rem 1.2rem;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--paper);
}
.cat-card-header-title {
    font-size: 0.82rem;
    font-weight: 700;
    color: var(--text-2);
    letter-spacing: 0.03em;
}
.cat-card-body {
    padding: 0.5rem 0;
}
.cat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.55rem 1.2rem;
    font-size: 0.84rem;
    border-bottom: 1px solid var(--border);
}
.cat-row:last-child { border-bottom: none; }
.cat-label { color: var(--text-2); font-weight: 400; }
.cat-value { color: var(--text-1); font-weight: 600; text-align: right; max-width: 55%; }

/* ── Badge nível (semáforo) ── */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 999px;
    white-space: nowrap;
}
.badge::before {
    content: '';
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: currentColor;
    flex-shrink: 0;
}
.badge-alto   { background: var(--red-l);   color: #B91C1C; }
.badge-medio  { background: var(--amber-l); color: #92400E; }
.badge-baixo  { background: var(--green-l); color: #065F46; }
.badge-neutro { background: var(--purple-l); color: #5B21B6; }

/* ── Selo Lumina (classificação etária) ── */
.lumina-selo-wrap {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.5rem 1.8rem;
    margin-bottom: 2rem;
    box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    position: relative;
    overflow: hidden;
}
.lumina-selo-wrap::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: linear-gradient(180deg, var(--indigo), var(--purple));
    border-radius: 0;
}
.lumina-selo-circle {
    width: 76px;
    height: 76px;
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    border: 2.5px solid;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-weight: 700;
}
.selo-livre  { border-color: var(--green);  color: var(--green); }
.selo-10     { border-color: var(--indigo); color: var(--indigo); }
.selo-12     { border-color: var(--indigo); color: var(--indigo); }
.selo-14     { border-color: var(--amber);  color: var(--amber); }
.selo-16     { border-color: var(--amber);  color: var(--amber); }
.selo-18     { border-color: var(--red);    color: var(--red); }
.lumina-selo-circle .n { font-size: 1.7rem; line-height: 1; }
.lumina-selo-circle .l { font-size: 0.52rem; letter-spacing: 0.06em; text-transform: uppercase; margin-top: 2px; }
.lumina-selo-info .t {
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--text-1);
    margin-bottom: 5px;
}
.lumina-selo-info .s {
    font-size: 0.84rem;
    color: var(--text-2);
    line-height: 1.5;
    font-family: 'Lora', serif;
    font-style: italic;
}

/* ── Evidência (glassmorphism leve) ── */
.evidencia-wrap {
    background: rgba(79, 70, 229, 0.03);
    border: 1px solid rgba(79, 70, 229, 0.12);
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 0.75rem;
}
.evidencia-item {
    padding: 1rem 1.2rem;
    border-bottom: 1px solid rgba(79, 70, 229, 0.08);
    font-size: 0.84rem;
    color: var(--text-2);
    line-height: 1.6;
}
.evidencia-item:last-child { border-bottom: none; }
.evidencia-item strong { color: var(--text-1); font-weight: 600; }
.evidencia-item .trecho {
    font-family: 'Lora', serif;
    font-style: italic;
    font-size: 0.88rem;
    color: var(--text-1);
    display: block;
    margin-top: 5px;
    padding: 8px 12px;
    background: rgba(124, 58, 237, 0.05);
    border-left: 3px solid var(--purple);
    border-radius: 0 6px 6px 0;
}

/* ── Status ── */
[data-testid="stStatusContainer"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04) !important;
}

/* ── Alert ── */
[data-testid="stAlert"] {
    background: var(--paper) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text-2) !important;
    font-size: 0.85rem !important;
}

/* ── JSON ── */
[data-testid="stJson"] {
    background: var(--paper) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    font-size: 0.78rem !important;
}

/* ── Divider ── */
[data-testid="stDivider"] hr {
    border-color: var(--border) !important;
}

/* ── Download ── */
[data-testid="stDownloadButton"] button {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-1) !important;
    border-radius: 10px !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.04) !important;
}
[data-testid="stDownloadButton"] button:hover {
    border-color: var(--indigo) !important;
    color: var(--indigo) !important;
}

/* ── Upload OK ── */
.upload-ok {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 0.83rem;
    color: var(--green);
    font-weight: 600;
    margin: 0.6rem 0 1.2rem;
    background: var(--green-l);
    padding: 6px 14px;
    border-radius: 999px;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: var(--paper); }
::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--indigo); }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DICIONÁRIO
# ─────────────────────────────────────────────

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
    "id": "ID",
    "nivel": "Nível",
    "confianca": "Confiança da IA",
}

def fix(texto):
    limpo = str(texto).replace("_", " ").strip().lower()
    return TERMOS_PTBR.get(limpo, str(texto).replace("_", " ").title())


# ─────────────────────────────────────────────
# HELPERS VISUAIS
# ─────────────────────────────────────────────

def badge_nivel(v):
    vl = str(v).lower()
    if any(x in vl for x in ["alto", "forte", "intenso", "explícito", "explicito", "grave", "severo"]):
        return f'<span class="badge badge-alto">{v}</span>'
    elif any(x in vl for x in ["médio", "medio", "moderado", "presente", "ocasional"]):
        return f'<span class="badge badge-medio">{v}</span>'
    elif any(x in vl for x in ["baixo", "leve", "mínimo", "minimo", "ausente", "nenhum", "nenhuma", "livre"]):
        return f'<span class="badge badge-baixo">{v}</span>'
    return f'<span class="badge badge-neutro">{v}</span>'

def selo_html(classif, justif=""):
    c = str(classif).strip()
    cl = c.lower()
    if "livre" in cl:
        css, num, lbl = "selo-livre", "L", "Livre"
    elif "18" in c:
        css, num, lbl = "selo-18", "18", "anos"
    elif "16" in c:
        css, num, lbl = "selo-16", "16", "anos"
    elif "14" in c:
        css, num, lbl = "selo-14", "14", "anos"
    elif "12" in c:
        css, num, lbl = "selo-12", "12", "anos"
    elif "10" in c:
        css, num, lbl = "selo-10", "10", "anos"
    else:
        css, num, lbl = "selo-10", "?", c

    just_block = f'<div class="s">{justif}</div>' if justif else ""
    return f"""
    <div class="lumina-selo-wrap">
        <div class="lumina-selo-circle {css}">
            <span class="n">{num}</span>
            <span class="l">{lbl}</span>
        </div>
        <div class="lumina-selo-info">
            <div class="t">{c}</div>
            {just_block}
        </div>
    </div>"""


# ─────────────────────────────────────────────
# CABEÇALHO
# ─────────────────────────────────────────────

st.markdown("""
<div class="lumina-nav">
    <div class="lumina-brand">
        <div class="lumina-icon">
            <svg viewBox="0 0 24 24">
                <path d="M12 2L8 7H4l3.5 3-1.5 5L12 12l6 3-1.5-5L20 7h-4z"/>
                <path d="M12 15v7M8 19h8"/>
            </svg>
        </div>
        <span class="lumina-wordmark">Lumina <span>IA</span></span>
    </div>
    <span class="lumina-badge">Beta</span>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="lumina-hero">
    <h1>Análise inteligente de<br><em>classificação indicativa</em></h1>
    <p>Envie um livro em PDF ou EPUB. A IA lê o conteúdo completo e gera um relatório detalhado com classificação etária, gatilhos emocionais, nível de violência e temas sensíveis.</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# EXTRAÇÃO
# ─────────────────────────────────────────────

def ler_pdf(caminho):
    reader = PdfReader(caminho)
    texto = ""
    for p in reader.pages:
        c = p.extract_text()
        if c:
            texto += c + "\n"
    return texto

def ler_epub(caminho):
    book = epub.read_epub(caminho)
    texto = ""
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), "html.parser")
            texto += soup.get_text(separator=" ", strip=True) + "\n\n"
    return texto

def extrair_texto(upload):
    ext = Path(upload.name).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(upload.getvalue())
        caminho = tmp.name
    if ext == ".pdf":   return ler_pdf(caminho)
    if ext == ".epub":  return ler_epub(caminho)
    raise ValueError("Formato não suportado.")


# ─────────────────────────────────────────────
# ANÁLISE
# ─────────────────────────────────────────────

def analisar_livro(texto):
    prompt = f"{textobase}\n\n{texto}"
    client = ollama.Client(
        host="https://api.ollama.com",
        headers={"Authorization": f"Bearer {st.secrets['OLLAMA_API_KEY']}"}
    )
    t0 = time.perf_counter()
    response = client.chat(
        model="gemma4:31b-cloud",
        messages=[{"role": "user", "content": prompt}],
        options={"num_ctx": 262144, "num_predict": 8192, "temperature": 0.2}
    )
    elapsed = time.perf_counter() - t0
    raw = response["message"]["content"]
    try:
        dados = json.loads(raw)
    except Exception:
        dados = {"erro": "A IA não retornou um JSON válido.", "resposta_original": raw}
    return dados, raw, elapsed, response


# ─────────────────────────────────────────────
# RENDERIZADOR
# ─────────────────────────────────────────────

def renderizar(dados):
    if not isinstance(dados, dict):
        st.write(dados)
        return

    # Extrai classificação e justificativa para o Selo
    classificacao = None
    justificativa = None
    for k, v in dados.items():
        kl = str(k).replace("_", " ").strip().lower()
        if "classificacao" in kl and isinstance(v, str) and not classificacao:
            classificacao = v
        if "justificativa" in kl and isinstance(v, str) and not justificativa:
            justificativa = v

    if classificacao:
        st.markdown(selo_html(classificacao, justificativa), unsafe_allow_html=True)

    for chave, valor in dados.items():
        kl = str(chave).replace("_", " ").strip().lower()
        if "classificacao" in kl or "justificativa" in kl:
            continue

        titulo = fix(chave)
        st.markdown(f"### {titulo}")

        # ── Dicionário → card com rows ──
        if isinstance(valor, dict):
            linhas = ""
            for sk, sv in valor.items():
                skl = str(sk).replace("_", " ").strip().lower()
                nome = fix(sk)
                if isinstance(sv, list):
                    sv_str = ", ".join(str(i) for i in sv) if sv else "—"
                    linhas += f'<div class="cat-row"><span class="cat-label">{nome}</span><span class="cat-value">{sv_str}</span></div>'
                elif isinstance(sv, dict):
                    linhas += f'<div class="cat-row"><span class="cat-label">{nome}</span><span class="cat-value" style="color:var(--text-3)">↓ ver detalhes</span></div>'
                    for sk2, sv2 in sv.items():
                        sk2l = str(sk2).replace("_", " ").strip().lower()
                        if sk2l == "nivel":
                            linhas += f'<div class="cat-row" style="padding-left:1.8rem;background:rgba(0,0,0,0.01)"><span class="cat-label" style="color:var(--text-3)">{fix(sk2)}</span><span class="cat-value">{badge_nivel(sv2)}</span></div>'
                        else:
                            linhas += f'<div class="cat-row" style="padding-left:1.8rem;background:rgba(0,0,0,0.01)"><span class="cat-label" style="color:var(--text-3)">{fix(sk2)}</span><span class="cat-value">{sv2}</span></div>'
                else:
                    if skl == "nivel":
                        linhas += f'<div class="cat-row"><span class="cat-label">{nome}</span><span class="cat-value">{badge_nivel(sv)}</span></div>'
                    else:
                        linhas += f'<div class="cat-row"><span class="cat-label">{nome}</span><span class="cat-value">{sv}</span></div>'
            st.markdown(
                f'<div class="cat-card">'
                f'<div class="cat-card-header"><span class="cat-card-header-title">{titulo}</span></div>'
                f'<div class="cat-card-body">{linhas}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

        # ── Lista de dicts → evidências com glassmorphism ──
        elif isinstance(valor, list):
            if not valor:
                st.markdown('<p style="color:var(--text-3);font-size:0.84rem">Nenhum item detectado.</p>', unsafe_allow_html=True)
            elif isinstance(valor[0], dict):
                blocos = ""
                for item in valor:
                    linhas_ev = ""
                    for k2, v2 in item.items():
                        k2l = str(k2).replace("_", " ").strip().lower()
                        if "trecho" in k2l or "evidencia" in k2l:
                            linhas_ev += f'<span class="trecho">{v2}</span>'
                        else:
                            linhas_ev += f'<strong>{fix(k2)}:</strong> {v2}<br>'
                    blocos += f'<div class="evidencia-item">{linhas_ev}</div>'
                st.markdown(f'<div class="evidencia-wrap">{blocos}</div>', unsafe_allow_html=True)
            else:
                items_html = "".join(
                    f'<li style="color:var(--text-2);font-size:0.84rem;margin-bottom:5px;font-family:Lora,serif">{i}</li>'
                    for i in valor
                )
                st.markdown(f'<ul style="padding-left:1.2rem;margin:0;line-height:1.7">{items_html}</ul>', unsafe_allow_html=True)

        # ── Scalar ──
        else:
            st.markdown(f'<p style="color:var(--text-1);font-size:0.9rem;line-height:1.65;font-family:Lora,serif">{valor}</p>', unsafe_allow_html=True)

        st.write("")


# ─────────────────────────────────────────────
# INTERFACE
# ─────────────────────────────────────────────

st.markdown('<div class="upload-card">', unsafe_allow_html=True)
arquivo = st.file_uploader(
    "Arraste seu arquivo aqui ou clique para selecionar",
    type=["pdf", "epub"],
    help="Processamento seguro e privativo. Nenhum arquivo é armazenado.",
    label_visibility="collapsed"
)
st.markdown('</div>', unsafe_allow_html=True)

if arquivo:
    st.markdown(
        f'<div class="upload-ok">✓&nbsp; {arquivo.name} pronto para análise</div>',
        unsafe_allow_html=True
    )

    if st.button("Analisar com Lumina IA →"):
        with st.status("Iniciando análise…", expanded=True) as status:
            st.write("Extraindo texto do documento…")
            texto = extrair_texto(arquivo)
            chars = f"{len(texto):,}".replace(",", ".")
            st.write(f"✓ {chars} caracteres extraídos.")
            st.write("Analisando conteúdo com IA…")
            dados_json, resultado_bruto, tempo, response = analisar_livro(texto)
            status.update(label="Análise concluída com sucesso.", state="complete", expanded=False)

        st.write("")
        col1, col2, col3 = st.columns(3)
        col1.metric("Caracteres", f"{len(texto):,}".replace(",", "."))
        col2.metric("Tempo", f"{tempo:.1f}s")
        if "eval_count" in response:
            col3.metric("Tokens", f"{response['eval_count']:,}".replace(",", "."))

        st.divider()

        aba1, aba2, aba3 = st.tabs(["Relatório", "JSON técnico", "Exportar"])

        with aba1:
            renderizar(dados_json)

        with aba2:
            st.info("Retorno estruturado da IA. Use para auditorias, integrações ou debug.")
            st.json(dados_json)

        with aba3:
            st.markdown("#### Exportar resultados")
            st.write("")
            c1, c2 = st.columns(2)
            with c1:
                st.download_button(
                    "Baixar JSON",
                    data=json.dumps(dados_json, ensure_ascii=False, indent=2),
                    file_name="lumina_classificacao.json",
                    mime="application/json",
                    use_container_width=True,
                )
            with c2:
                st.download_button(
                    "Baixar TXT",
                    data=resultado_bruto,
                    file_name="lumina_analise_bruta.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
