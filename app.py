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

# Certifique-se de que o arquivo textoprompt.py está na mesma pasta
from textoprompt import textobase

# =====================================================
# CONFIGURAÇÃO DA PÁGINA
# =====================================================

st.set_page_config(
    page_title="Classificação Indicativa IA",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =====================================================
# CSS PREMIUM (Estilo Moderno)
# =====================================================

st.markdown("""
<style>
    /* Tipografia e espaçamento geral */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }

    .block-container {
        max-width: 1000px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    
    /* Títulos com Gradiente */
    h1 {
        font-weight: 800 !important;
        background: -webkit-linear-gradient(45deg, #2563EB, #9333EA);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    h3 {
        color: #4F46E5;
        font-weight: 600;
        margin-top: 1.5rem;
        border-bottom: 2px solid rgba(79, 70, 229, 0.1);
        padding-bottom: 0.5rem;
    }

    /* Botão Principal Animado */
    .stButton > button {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        color: white;
        border: none;
        border-radius: 12px;
        font-size: 1.1rem;
        font-weight: 600;
        height: 3.5rem;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(124, 58, 237, 0.4);
        color: white;
    }

    /* Abas customizadas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }

    /* Estilização das Evidências (Glassmorphism sutil) */
    .evidencia-box {
        padding: 18px;
        border-radius: 12px;
        background: rgba(124, 58, 237, 0.03);
        border-left: 5px solid #7C3AED;
        border-top: 1px solid rgba(124, 58, 237, 0.1);
        border-right: 1px solid rgba(124, 58, 237, 0.1);
        border-bottom: 1px solid rgba(124, 58, 237, 0.1);
        margin-bottom: 15px;
        transition: transform 0.2s ease;
    }
    
    .evidencia-box:hover {
        transform: translateX(5px);
        background: rgba(124, 58, 237, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# =====================================================
# DICIONÁRIO DE CORREÇÃO ORTOGRÁFICA (Acentuação Perfeita)
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
    """Substitui chaves de JSON sem acento por texto formatado e acentuado."""
    texto_limpo = str(texto).replace('_', ' ').strip().lower()
    return TERMOS_PTBR.get(texto_limpo, str(texto).replace('_', ' ').title())

# =====================================================
# CABEÇALHO
# =====================================================

st.title("Classificador Indicativo IA")
st.markdown("Analise o conteúdo de livros automaticamente através de Inteligência Artificial para identificar classificação de idade, gatilhos, níveis de violência e temas sensíveis.")
st.write("")

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
    """Renderiza o relatório iterando pelo dicionário e aplicando estilos dinâmicos."""
    if not isinstance(dados, dict):
        st.write(dados)
        return

    for chave, valor in dados.items():
        titulo_formatado = corrigir_texto(chave)
        st.markdown(f"### 🔹 {titulo_formatado}")
        
        if isinstance(valor, dict):
            for subchave, subvalor in valor.items():
                nome_subchave = corrigir_texto(subchave)
                
                if isinstance(subvalor, dict):
                    st.markdown(f"**{nome_subchave}**")
                    for k, v in subvalor.items():
                        st.markdown(f"- **{corrigir_texto(k)}:** {v}")
                elif isinstance(subvalor, list):
                    if len(subvalor) == 0:
                        st.markdown(f"- **{nome_subchave}:** *Nenhuma*")
                    else:
                        itens = ", ".join([str(item) for item in subvalor])
                        st.markdown(f"- **{nome_subchave}:** {itens}")
                else:
                    st.markdown(f"- **{nome_subchave}:** {subvalor}")
                    
        elif isinstance(valor, list):
            if len(valor) == 0:
                st.markdown("*Nenhum item detectado nesta categoria.*")
            elif isinstance(valor[0], dict):
                # Design premium para as Evidências
                for item in valor:
                    st.markdown('<div class="evidencia-box">', unsafe_allow_html=True)
                    for k, v in item.items():
                        st.markdown(f"**{corrigir_texto(k)}:** {v}")
                    st.markdown('</div>', unsafe_allow_html=True)
            else:
                for item in valor:
                    st.markdown(f"- {item}")
        else:
            st.markdown(str(valor))
            
        st.write("") 

# =====================================================
# INTERFACE PRINCIPAL
# =====================================================

with st.container(border=True):
    arquivo = st.file_uploader(
        "📄 Arraste seu PDF ou EPUB para cá",
        type=["pdf", "epub"],
        help="O processamento é seguro e privativo."
    )

if arquivo:
    st.success(f"✔️ Arquivo carregado com sucesso: **{arquivo.name}**")

    if st.button("🚀 Iniciar Análise Profissional"):
        
        # STATUS MODERNO INTERATIVO
        with st.status("⚙️ Iniciando processamento...", expanded=True) as status:
            
            st.write("📄 Extraindo texto do documento...")
            texto = extrair_texto(arquivo)
            st.write(f"✔️ Leitura concluída: **{len(texto):,}** caracteres extraídos.")
            
            st.write("🤖 Conectando ao Ollama Cloud e analisando contexto profundo...")
            dados_json, resultado_bruto, tempo, response = analisar_livro(texto)
            
            status.update(label="Análise finalizada com sucesso!", state="complete", expanded=False)

        # MÉTRICAS
        st.write("")
        col1, col2, col3 = st.columns(3)
        col1.metric("Caracteres Lidos", f"{len(texto):,}".replace(',', '.'))
        col2.metric("Tempo de Processamento", f"{tempo:.1f}s")
        if "eval_count" in response:
            col3.metric("Tokens Estruturados", f"{response['eval_count']:,}".replace(',', '.'))

        st.divider()

        # SISTEMA DE ABAS (TABS) MODERNAS
        aba_relatorio, aba_dados, aba_downloads = st.tabs([
            "📊 Relatório Estruturado", 
            "⚙️ Dados Técnicos JSON", 
            "📥 Exportação"
        ])

        with aba_relatorio:
            st.markdown("## Resumo da Avaliação")
            renderizar_relatorio_bonito(dados_json)

        with aba_dados:
            st.markdown("### Retorno Bruto da IA")
            st.info("Visualização técnica estruturada para auditoria de dados e integração de API.")
            st.json(dados_json)

        with aba_downloads:
            st.markdown("### 💾 Salvar Arquivos")
            st.markdown("Faça o download do relatório completo para uso posterior ou integração em outros sistemas.")
            st.write("")
            
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.download_button(
                    label="📄 Exportar como JSON",
                    data=json.dumps(dados_json, ensure_ascii=False, indent=2),
                    file_name="classificacao_livro.json",
                    mime="application/json",
                    use_container_width=True
                )
            with col_dl2:
                st.download_button(
                    label="📝 Exportar Resposta em Texto (TXT)",
                    data=resultado_bruto,
                    file_name="analise_bruta.txt",
                    mime="text/plain",
                    use_container_width=True
                )
