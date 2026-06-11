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
# CONFIGURAÇÃO DA PÁGINA
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Leitura Segura — Classificação Indicativa",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────
# CSS — Editorial Light
# ─────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600&display=swap');

/* ── Esconde chrome do Streamlit ── */
#MainMenu                          { visibility: hidden; }
header[data-testid="stHeader"]     { display: none !important; }
footer                             { display: none !important; }
[data-testid="stToolbar"]          { display: none !important; }
[data-testid="stDecoration"]       { display: none !important; }
[data-testid="stStatusWidget"]     { display: none !important; }
.stDeployButton                    { display: none !important; }
button[title="View fullscreen"]    { display: none !important; }

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #FAFAF8;
    color: #1A1A1A;
}

.block-container {
    max-width: 780px;
    padding-top: 4rem;
    padding-bottom: 6rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

/* ── Logotipo / topo ── */
.app-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 3rem;
}
.app-logo-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #2D5BE3;
}
.app-logo-text {
    font-family: 'Inter', sans-serif;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #2D5BE3;
}

/* ── Título ── */
h1 {
    font-family: 'Instrument Serif', serif !important;
    font-size: 3rem !important;
    font-weight: 400 !important;
    line-height: 1.08 !important;
    color: #1A1A1A !important;
    letter-spacing: -0.02em;
    margin-bottom: 1rem !important;
}

/* ── Subtítulo ── */
.subtitulo {
    font-size: 1rem;
    color: #6B6B6B;
    line-height: 1.65;
    max-width: 560px;
    margin-bottom: 3rem;
    font-weight: 400;
}

/* ── Divisor fino ── */
.divider {
    border: none;
    border-top: 1px solid #E8E4DC;
    margin: 2.5rem 0;
}

/* ── Zona de upload ── */
[data-testid="stFileUploader"] {
    background: #F5F4F0 !important;
    border: 1.5px dashed #D0CBC0 !important;
    border-radius: 12px !important;
    padding: 1.5rem !important;
    transition: border-color 0.2s ease, background 0.2s ease;
}
[data-testid="stFileUploader"]:hover {
    border-color: #2D5BE3 !important;
    background: #F0F3FD !important;
}
[data-testid="stFileUploader"] label {
    color: #6B6B6B !important;
    font-size: 0.88rem !important;
}
[data-testid="stFileUploader"] small {
    color: #A0A0A0 !important;
}

/* ── Botão principal ── */
.stButton > button {
    background: #1A1A1A;
    color: #FAFAF8;
    border: none;
    border-radius: 8px;
    font-family: 'Inter', sans-serif;
    font-size: 0.9rem;
    font-weight: 600;
    height: 3rem;
    width: 100%;
    letter-spacing: 0.02em;
    transition: background 0.18s ease;
}
.stButton > button:hover {
    background: #2D5BE3;
    color: #FFFFFF;
}
.stButton > button:active {
    background: #1E45C4;
}

/* ── Métricas ── */
[data-testid="stMetric"] {
    background: #F5F4F0;
    border: 1px solid #E8E4DC;
    border-radius: 10px;
    padding: 1.1rem 1.3rem;
}
[data-testid="stMetricLabel"] {
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: #A0A0A0 !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Instrument Serif', serif !important;
    font-size: 1.8rem !important;
    font-weight: 400 !important;
    color: #1A1A1A !important;
}

/* ── Abas ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: #F0EFE9;
    border-radius: 8px;
    padding: 3px;
    border: none;
}
.stTabs [data-baseweb="tab"] {
    height: 36px;
    border-radius: 6px;
    padding: 0 1.1rem;
    font-size: 0.82rem;
    font-weight: 500;
    color: #888;
    background: transparent;
    transition: all 0.15s ease;
    border: none;
}
.stTabs [aria-selected="true"] {
    background: #FFFFFF !important;
    color: #1A1A1A !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08) !important;
}

/* ── Headings do relatório ── */
h2 {
    font-family: 'Instrument Serif', serif !important;
    font-size: 1.6rem !important;
    font-weight: 400 !important;
    color: #1A1A1A !important;
    letter-spacing: -0.01em;
    margin-top: 2.5rem !important;
    margin-bottom: 1.2rem !important;
}

h3 {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.65rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    color: #A0A0A0 !important;
    margin-top: 2rem !important;
    margin-bottom: 0.6rem !important;
    border-bottom: none !important;
    padding-bottom: 0 !important;
}

/* ── Card de categoria ── */
.cat-card {
    background: #FFFFFF;
    border: 1px solid #E8E4DC;
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.6rem;
}
.cat-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding: 4px 0;
    border-bottom: 1px solid #F0EFE9;
    font-size: 0.85rem;
}
.cat-row:last-child { border-bottom: none; }
.cat-label { color: #6B6B6B; }
.cat-value { color: #1A1A1A; font-weight: 500; }

/* ── Badge nível ── */
.badge {
    display: inline-block;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 2px 9px;
    border-radius: 999px;
    vertical-align: middle;
}
.badge-alto   { background: #FEE2E2; color: #B91C1C; }
.badge-medio  { background: #FEF9C3; color: #92400E; }
.badge-baixo  { background: #DCFCE7; color: #15803D; }
.badge-neutro { background: #EEF2FF; color: #3730A3; }

/* ── Selo de classificação etária (assinatura do design) ── */
.selo-wrapper {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    background: #FFFFFF;
    border: 1px solid #E8E4DC;
    border-radius: 12px;
    padding: 1.4rem 1.8rem;
    margin-bottom: 2rem;
}
.selo-circulo {
    width: 72px;
    height: 72px;
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    border: 3px solid currentColor;
}
.selo-circulo span:first-child {
    font-family: 'Instrument Serif', serif;
    font-size: 1.6rem;
    font-weight: 400;
    line-height: 1;
}
.selo-circulo span:last-child {
    font-size: 0.55rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-top: 1px;
}
.selo-livre   { color: #15803D; }
.selo-10      { color: #1D4ED8; }
.selo-12      { color: #0E7490; }
.selo-14      { color: #92400E; }
.selo-16      { color: #C2410C; }
.selo-18      { color: #B91C1C; }
.selo-info { }
.selo-info p { margin: 0; }
.selo-info .selo-titulo {
    font-family: 'Instrument Serif', serif;
    font-size: 1.1rem;
    color: #1A1A1A;
}
.selo-info .selo-sub {
    font-size: 0.82rem;
    color: #6B6B6B;
    margin-top: 4px;
    line-height: 1.4;
}

/* ── Evidência ── */
.evidencia-box {
    border-top: 1px solid #E8E4DC;
    padding: 1rem 0;
    font-size: 0.85rem;
    color: #6B6B6B;
    line-height: 1.6;
}
.evidencia-box:first-child { border-top: none; }
.evidencia-box strong { color: #1A1A1A; font-weight: 500; }

/* ── Alert / info ── */
[data-testid="stAlert"] {
    background: #F5F4F0 !important;
    border: 1px solid #E8E4DC !important;
    border-radius: 8px !important;
    color: #6B6B6B !important;
    font-size: 0.85rem !important;
}

/* ── Download ── */
[data-testid="stDownloadButton"] button {
    background: #FFFFFF !important;
    border: 1px solid #E8E4DC !important;
    color: #1A1A1A !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    transition: border-color 0.15s ease, background 0.15s ease !important;
}
[data-testid="stDownloadButton"] button:hover {
    border-color: #2D5BE3 !important;
    color: #2D5BE3 !important;
    background: #F0F3FD !important;
}

/* ── Status box ── */
[data-testid="stStatusContainer"] {
    background: #F5F4F0 !important;
    border: 1px solid #E8E4DC !important;
    border-radius: 10px !important;
}

/* ── JSON viewer ── */
[data-testid="stJson"] {
    background: #F5F4F0 !important;
    border: 1px solid #E8E4DC !important;
    border-radius: 10px !important;
    font-size: 0.8rem !important;
}

/* ── Divider nativo ── */
[data-testid="stDivider"] hr {
    border-color: #E8E4DC !important;
}

/* ── Sucesso de upload ── */
.upload-ok {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    font-size: 0.84rem;
    color: #15803D;
    font-weight: 500;
    margin-top: 0.5rem;
    margin-bottom: 1.2rem;
}
.upload-ok-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #15803D;
    flex-shrink: 0;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #FAFAF8; }
::-webkit-scrollbar-thumb { background: #D0CBC0; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #2D5BE3; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DICIONÁRIO DE ACENTUAÇÃO
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
    "id": "Identificação",
    "nivel": "Nível",
    "confianca": "Confiança da IA",
}

def corrigir_texto(texto):
    limpo = str(texto).replace("_", " ").strip().lower()
    return TERMOS_PTBR.get(limpo, str(texto).replace("_", " ").title())


# ─────────────────────────────────────────────
# HELPERS VISUAIS
# ─────────────────────────────────────────────

def badge_nivel(valor_str):
    v = str(valor_str).lower()
    if any(x in v for x in ["alto", "forte", "intenso", "explícito", "explicito", "grave", "severo"]):
        return f'<span class="badge badge-alto">{valor_str}</span>'
    elif any(x in v for x in ["médio", "medio", "moderado", "presente", "ocasional"]):
        return f'<span class="badge badge-medio">{valor_str}</span>'
    elif any(x in v for x in ["baixo", "leve", "mínimo", "minimo", "ausente", "nenhum", "nenhuma"]):
        return f'<span class="badge badge-baixo">{valor_str}</span>'
    return f'<span class="badge badge-neutro">{valor_str}</span>'

def selo_classificacao(classificacao_str):
    """Renderiza o selo circular de classificação indicativa."""
    c = str(classificacao_str).strip()
    c_low = c.lower()

    if "livre" in c_low:
        cls, numero, label = "selo-livre", "L", "Livre"
    elif "18" in c:
        cls, numero, label = "selo-18", "18", "anos"
    elif "16" in c:
        cls, numero, label = "selo-16", "16", "anos"
    elif "14" in c:
        cls, numero, label = "selo-14", "14", "anos"
    elif "12" in c:
        cls, numero, label = "selo-12", "12", "anos"
    elif "10" in c:
        cls, numero, label = "selo-10", "10", "anos"
    else:
        cls, numero, label = "selo-neutro", "?", c

    return f"""
    <div class="selo-circulo {cls}">
        <span>{numero}</span>
        <span>{label}</span>
    </div>
    """


# ─────────────────────────────────────────────
# CABEÇALHO
# ─────────────────────────────────────────────

st.markdown("""
<div class="app-logo">
    <div class="app-logo-dot"></div>
    <span class="app-logo-text">Leitura Segura</span>
</div>
""", unsafe_allow_html=True)

st.title("Classificação\nIndicativa IA")
st.markdown(
    '<p class="subtitulo">Envie um livro em PDF ou EPUB. '
    'A IA lê o conteúdo completo e devolve um relatório detalhado '
    'de classificação etária, gatilhos emocionais e temas sensíveis.</p>',
    unsafe_allow_html=True
)


# ─────────────────────────────────────────────
# EXTRAÇÃO DE TEXTO
# ─────────────────────────────────────────────

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
    documentos = [item for item in book.get_items()
                  if item.get_type() == ebooklib.ITEM_DOCUMENT]
    for item in documentos:
        soup = BeautifulSoup(item.get_content(), "html.parser")
        texto += soup.get_text(separator=" ", strip=True) + "\n\n"
    return texto

def extrair_texto(upload):
    extensao = Path(upload.name).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=extensao) as tmp:
        tmp.write(upload.getvalue())
        caminho = tmp.name
    if extensao == ".pdf":
        return ler_pdf(caminho)
    elif extensao == ".epub":
        return ler_epub(caminho)
    raise ValueError("Formato não suportado.")


# ─────────────────────────────────────────────
# ANÁLISE VIA OLLAMA
# ─────────────────────────────────────────────

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
        dados_json = {
            "erro": "A resposta da IA não retornou um JSON válido.",
            "resposta_original": conteudo,
        }
    return dados_json, conteudo, fim - inicio, response


# ─────────────────────────────────────────────
# RENDERIZADOR DO RELATÓRIO
# ─────────────────────────────────────────────

def renderizar_relatorio(dados):
    if not isinstance(dados, dict):
        st.write(dados)
        return

    # Tenta extrair e renderizar o selo de classificação no topo
    classificacao = None
    justificativa = None
    for k, v in dados.items():
        k_clean = str(k).replace("_", " ").strip().lower()
        if "classificacao final" in k_clean or "classificacao" in k_clean:
            if isinstance(v, str):
                classificacao = v
            elif isinstance(v, dict):
                for sk, sv in v.items():
                    classificacao = str(sv)
                    break
        if "justificativa" in k_clean:
            justificativa = str(v)

    if classificacao:
        circulo_html = selo_classificacao(classificacao)
        just_html = f'<p class="selo-sub">{justificativa}</p>' if justificativa else ""
        st.markdown(f"""
        <div class="selo-wrapper">
            {circulo_html}
            <div class="selo-info">
                <p class="selo-titulo">{classificacao}</p>
                {just_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Renderiza o restante
    for chave, valor in dados.items():
        k_clean = str(chave).replace("_", " ").strip().lower()
        # Pula o que já foi exibido no selo
        if "classificacao" in k_clean or "justificativa" in k_clean:
            continue

        titulo = corrigir_texto(chave)
        st.markdown(f"### {titulo}")

        if isinstance(valor, dict):
            linhas_html = ""
            for sk, sv in valor.items():
                sk_clean = str(sk).replace("_", " ").strip().lower()
                nome = corrigir_texto(sk)
                if isinstance(sv, list):
                    sv_str = ", ".join(str(i) for i in sv) if sv else "—"
                    linhas_html += f'<div class="cat-row"><span class="cat-label">{nome}</span><span class="cat-value">{sv_str}</span></div>'
                elif isinstance(sv, dict):
                    # sub-dicionário: exibe com recuo simples
                    linhas_html += f'<div class="cat-row"><span class="cat-label">{nome}</span><span class="cat-value">↓</span></div>'
                    for sk2, sv2 in sv.items():
                        linhas_html += f'<div class="cat-row" style="padding-left:1rem"><span class="cat-label" style="color:#A0A0A0">{corrigir_texto(sk2)}</span><span class="cat-value">{sv2}</span></div>'
                else:
                    if sk_clean == "nivel":
                        linhas_html += f'<div class="cat-row"><span class="cat-label">{nome}</span><span class="cat-value">{badge_nivel(sv)}</span></div>'
                    else:
                        linhas_html += f'<div class="cat-row"><span class="cat-label">{nome}</span><span class="cat-value">{sv}</span></div>'
            st.markdown(f'<div class="cat-card">{linhas_html}</div>', unsafe_allow_html=True)

        elif isinstance(valor, list):
            if not valor:
                st.markdown('<p style="color:#A0A0A0;font-size:0.85rem;">Nenhum item detectado.</p>', unsafe_allow_html=True)
            elif isinstance(valor[0], dict):
                blocos = ""
                for item in valor:
                    linhas = ""
                    for k2, v2 in item.items():
                        linhas += f"<strong>{corrigir_texto(k2)}:</strong> {v2}<br>"
                    blocos += f'<div class="evidencia-box">{linhas}</div>'
                st.markdown(blocos, unsafe_allow_html=True)
            else:
                items_html = "".join(
                    f'<li style="color:#6B6B6B;font-size:0.85rem;margin-bottom:4px">{i}</li>'
                    for i in valor
                )
                st.markdown(f'<ul style="padding-left:1.2rem;margin:0">{items_html}</ul>', unsafe_allow_html=True)

        else:
            st.markdown(f'<p style="color:#1A1A1A;font-size:0.9rem;line-height:1.6">{valor}</p>', unsafe_allow_html=True)

        st.write("")


# ─────────────────────────────────────────────
# INTERFACE
# ─────────────────────────────────────────────

arquivo = st.file_uploader(
    "Selecione um arquivo PDF ou EPUB",
    type=["pdf", "epub"],
    help="Processamento seguro. O arquivo não é armazenado.",
    label_visibility="collapsed"
)

if arquivo:
    st.markdown(
        f'<div class="upload-ok"><div class="upload-ok-dot"></div>{arquivo.name}</div>',
        unsafe_allow_html=True
    )

    if st.button("Analisar livro"):
        with st.status("Lendo documento…", expanded=True) as status:
            st.write("Extraindo texto…")
            texto = extrair_texto(arquivo)
            chars = f"{len(texto):,}".replace(",", ".")
            st.write(f"{chars} caracteres extraídos.")
            st.write("Analisando com IA…")
            dados_json, resultado_bruto, tempo, response = analisar_livro(texto)
            status.update(label="Pronto.", state="complete", expanded=False)

        st.write("")
        col1, col2, col3 = st.columns(3)
        col1.metric("Caracteres", f"{len(texto):,}".replace(",", "."))
        col2.metric("Tempo", f"{tempo:.1f}s")
        if "eval_count" in response:
            col3.metric("Tokens", f"{response['eval_count']:,}".replace(",", "."))

        st.divider()

        aba1, aba2, aba3 = st.tabs(["Relatório", "JSON", "Exportar"])

        with aba1:
            renderizar_relatorio(dados_json)

        with aba2:
            st.info("Retorno bruto estruturado — útil para auditoria e integrações de sistema.")
            st.json(dados_json)

        with aba3:
            st.markdown("#### Exportar resultados")
            st.write("")
            c1, c2 = st.columns(2)
            with c1:
                st.download_button(
                    "Baixar JSON",
                    data=json.dumps(dados_json, ensure_ascii=False, indent=2),
                    file_name="classificacao.json",
                    mime="application/json",
                    use_container_width=True,
                )
            with c2:
                st.download_button(
                    "Baixar TXT",
                    data=resultado_bruto,
                    file_name="analise_bruta.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
