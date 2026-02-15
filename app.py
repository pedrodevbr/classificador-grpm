import streamlit as st
import streamlit.components.v1 as components
import os
import time
from classificador import ClassificadorHierarquicoOpenRouter

# Configuração da Página
st.set_page_config(
    page_title="Classificador de Materiais - ITAIPU",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Itaipu Theme - Clean and Readable
ITAIPU_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

/* Reset and Base */
.stApp {
    background-color: #f8fafc;
    font-family: 'Roboto', -apple-system, sans-serif;
}

.main .block-container {
    padding: 1.5rem 2rem;
    max-width: 1400px;
}

/* Header Banner */
.header-banner {
    background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
    padding: 1.25rem 1.5rem;
    border-radius: 10px;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.header-title {
    color: #ffffff;
    font-size: 1.6rem;
    font-weight: 600;
    margin: 0;
}

.header-subtitle {
    color: #e2e8f0;
    font-size: 0.9rem;
    margin-top: 4px;
}

/* Cards */
.card {
    background: #ffffff;
    border-radius: 10px;
    padding: 1.25rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    border: 1px solid #e2e8f0;
}

.card-header {
    color: #1e3a5f;
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #e2e8f0;
}

/* Candidates Box */
.candidates-box {
    background: #ffffff;
    border-radius: 10px;
    padding: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    border: 1px solid #e2e8f0;
    min-height: 180px;
}

.candidates-title {
    color: #1e3a5f;
    font-size: 0.95rem;
    font-weight: 600;
    margin-bottom: 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #e2e8f0;
}

/* Candidate Items */
.cand-item {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 0.6rem 0.8rem;
    margin-bottom: 0.4rem;
    display: flex;
    align-items: center;
    transition: all 0.2s ease;
}

.cand-item:hover {
    background: #f1f5f9;
}

.cand-item.analyzing {
    background: #eff6ff;
    border-color: #3b82f6;
    box-shadow: 0 0 0 1px #3b82f6;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

.cand-item.selected {
    background: #ecfdf5;
    border-color: #10b981;
}

.cand-item.selected::before {
    content: "✓";
    color: #10b981;
    font-weight: bold;
    margin-right: 6px;
}

.cand-item.rejected {
    background: #fef2f2;
    border-color: #f87171;
    opacity: 0.5;
}

.cand-code {
    background: #1e3a5f;
    color: #ffffff;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 0.6rem;
    min-width: 60px;
    text-align: center;
}

.cand-desc {
    color: #334155;
    font-size: 0.85rem;
    flex: 1;
}

/* Loading Indicator */
.loading-box {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #3b82f6;
    font-size: 0.8rem;
    margin-bottom: 0.75rem;
    padding: 0.4rem 0.6rem;
    background: #eff6ff;
    border-radius: 4px;
    border: 1px solid #bfdbfe;
}

.spin {
    width: 14px;
    height: 14px;
    border: 2px solid #bfdbfe;
    border-top-color: #3b82f6;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Path Box */
.path-box {
    background: #ffffff;
    border-radius: 10px;
    padding: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    border: 1px solid #e2e8f0;
    margin-top: 1rem;
}

.path-title {
    color: #1e3a5f;
    font-size: 0.95rem;
    font-weight: 600;
    margin-bottom: 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #e2e8f0;
}

.path-item {
    display: flex;
    align-items: center;
    padding: 0.5rem 0.6rem;
    margin: 0.2rem 0;
    background: #f8fafc;
    border-radius: 4px;
    border-left: 3px solid #1e3a5f;
}

.path-level {
    background: #64748b;
    color: #ffffff;
    padding: 0.1rem 0.4rem;
    border-radius: 3px;
    font-size: 0.65rem;
    font-weight: 600;
    margin-right: 0.5rem;
}

.path-code {
    background: #fbbf24;
    color: #1e3a5f;
    padding: 0.15rem 0.4rem;
    border-radius: 3px;
    font-size: 0.7rem;
    font-weight: 700;
    margin-right: 0.5rem;
}

.path-desc {
    color: #334155;
    font-size: 0.8rem;
}

/* Result Box */
.result-box {
    background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
    border-radius: 10px;
    padding: 1.5rem;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    margin-top: 1rem;
}

.result-label {
    color: #e2e8f0;
    font-size: 0.8rem;
    font-weight: 500;
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.result-code {
    color: #fbbf24;
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 0.25rem;
}

.result-desc {
    color: #ffffff;
    font-size: 1.1rem;
    font-weight: 500;
}

/* Suggestion Box */
.suggest-box {
    background: #fffbeb;
    border: 1px solid #fcd34d;
    border-radius: 10px;
    padding: 1rem;
    margin-top: 1rem;
}

.suggest-title {
    color: #92400e;
    font-weight: 600;
    font-size: 0.9rem;
    margin-bottom: 0.75rem;
}

/* Form Elements */
.stTextArea textarea {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 6px !important;
    color: #1e293b !important;
    font-size: 0.9rem !important;
}

.stTextArea textarea:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1) !important;
}

.stButton > button {
    background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%) !important;
    border: none !important;
    border-radius: 6px !important;
    color: white !important;
    font-weight: 500 !important;
}

.stButton > button:hover {
    opacity: 0.9 !important;
}

/* Empty State */
.empty-msg {
    text-align: center;
    color: #64748b;
    padding: 1.5rem;
}

.empty-icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
    opacity: 0.5;
}

/* Hide Streamlit Branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #1e293b;
}

[data-testid="stSidebar"] label {
    color: #e2e8f0 !important;
}
</style>
"""

st.markdown(ITAIPU_CSS, unsafe_allow_html=True)

# Header
st.markdown("""
<div class="header-banner">
    <div class="header-title">⚡ Classificador de Materiais</div>
    <div class="header-subtitle">Sistema de Classificação Hierárquica - ITAIPU Binacional</div>
</div>
""", unsafe_allow_html=True)

# --- API Key Resolution (server-side first, then user input) ---
def _resolve_api_key() -> str | None:
    """Try Streamlit secrets → env var → None."""
    try:
        return st.secrets["OPENROUTER_API_KEY"]
    except (KeyError, FileNotFoundError):
        pass
    return os.getenv("OPENROUTER_API_KEY")

server_api_key = _resolve_api_key()

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Configurações")

    if server_api_key:
        api_key = server_api_key
        st.success("✓ Chave configurada pelo servidor")
    else:
        api_key = st.text_input("OpenRouter API Key", type="password")
        if not api_key:
            st.info("ℹ️ Insira sua chave ou configure via variável de ambiente.")

    model_name = st.selectbox(
        "Modelo LLM",
        ["x-ai/grok-4.1-fast", "openai/gpt-4o-mini", "anthropic/claude-3-haiku", 
         'google/gemini-3-flash-preview', 'deepseek/deepseek-v3.2'],
        index=0
    )

# Cache
@st.cache_resource
def load_classifier(api_key_val, model_val):
    clf = ClassificadorHierarquicoOpenRouter(api_key=api_key_val, model=model_val)
    arquivo_grp = "data/grpms.xlsx"
    if os.path.exists(arquivo_grp):
        clf.carregar_hierarquia(arquivo_grp)
        return clf
    return None

# Helper functions for HTML rendering
def build_candidates_html(candidates, analyzing=False, selected_code=None, rejected_codes=None):
    """Build HTML for candidates display."""
    if rejected_codes is None:
        rejected_codes = set()
    
    html = '<div class="candidates-box">'
    html += '<div class="candidates-title">🎯 Candidatos em Análise</div>'
    
    if analyzing:
        html += '<div class="loading-box"><div class="spin"></div><span>Analisando com IA...</span></div>'
    
    for code, desc in candidates:
        cls = ""
        if code in rejected_codes:
            cls = "rejected"
        elif selected_code and code == selected_code:
            cls = "selected"
        elif analyzing:
            cls = "analyzing"
        
        html += f'<div class="cand-item {cls}"><span class="cand-code">{code}</span><span class="cand-desc">{desc}</span></div>'
    
    html += '</div>'
    return html

def build_path_html(path_data):
    """Build HTML for path display."""
    if not path_data:
        return ""
    
    html = '<div class="path-box">'
    html += '<div class="path-title">📍 Caminho de Navegação</div>'
    
    for item in path_data:
        nivel = item["Nível"]
        codigo = item["Código"]
        descricao = item["Descrição"]
        indent = nivel * 12
        
        html += f'<div class="path-item" style="margin-left: {indent}px;">'
        html += f'<span class="path-level">N{nivel}</span>'
        html += f'<span class="path-code">{codigo}</span>'
        html += f'<span class="path-desc">{descricao}</span>'
        html += '</div>'
    
    html += '</div>'
    return html

def build_result_html(codigo, descricao):
    """Build HTML for result display."""
    return f'''
    <div class="result-box">
        <div class="result-label">✅ Classificação Concluída</div>
        <div class="result-code">{codigo}</div>
        <div class="result-desc">{descricao}</div>
    </div>
    '''

def build_suggestion_html(suggestions):
    """Build HTML for suggestions."""
    html = '<div class="suggest-box">'
    html += '<div class="suggest-title">💡 Nenhum grupo encontrado - Considere:</div>'
    for code, desc in suggestions:
        html += f'<div class="cand-item"><span class="cand-code">{code}</span><span class="cand-desc">{desc}</span></div>'
    html += '</div>'
    return html

# Main Layout
col_input, col_candidates = st.columns([1, 1])

with col_input:
    st.markdown('<div class="card"><div class="card-header">📝 Entrada de Dados</div>', unsafe_allow_html=True)
    
    if 'descritivo_text' not in st.session_state:
        st.session_state.descritivo_text = ""

    uploaded_file = st.file_uploader("Anexar documento ou imagem", type=['pdf', 'jpg', 'jpeg', 'png'])
    
    if uploaded_file and api_key:
        clf_temp = load_classifier(api_key, model_name)
        if clf_temp:
            processed_key = f"processed_{uploaded_file.file_id}"
            if processed_key not in st.session_state:
                with st.spinner("Processando arquivo..."):
                    if uploaded_file.type == "application/pdf":
                        texto = clf_temp.extrair_texto_pdf(uploaded_file)
                        st.session_state.descritivo_text = texto
                    else:
                        texto = clf_temp.descrever_imagem(uploaded_file.getvalue(), uploaded_file.type)
                        st.session_state.descritivo_text = texto
                st.session_state[processed_key] = True

    descritivo_item = st.text_area(
        "Descrição do Material:",
        value=st.session_state.descritivo_text,
        height=120,
        placeholder="Ex: Luva de segurança de vaqueta...",
        key="input_descritivo"
    )
    st.session_state.descritivo_text = descritivo_item
    
    btn_classificar = st.button("🔍 Classificar Material", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_candidates:
    candidates_area = st.empty()
    # Initial empty state
    candidates_area.markdown("""
    <div class="candidates-box">
        <div class="candidates-title">🎯 Candidatos em Análise</div>
        <div class="empty-msg">
            <div class="empty-icon">📋</div>
            <div>Aguardando classificação...</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Results area
path_area = st.empty()
result_area = st.empty()

# Classification Logic
if btn_classificar:
    descritivo_item = st.session_state.descritivo_text
    if not descritivo_item:
        st.warning("⚠️ Por favor, insira uma descrição.")
    elif not api_key:
        st.error("🔑 Chave API necessária.")
    else:
        clf = load_classifier(api_key, model_name)
        
        if clf:
            try:
                path_data = []
                final_result = None
                current_candidates = []
                rejected_codes = set()
                
                progress_bar = st.progress(0, text="Iniciando...")
                step_count = 0
                
                for evento in clf.classificar_item(descritivo_item):
                    if evento["type"] == "candidates":
                        # Show candidates with analyzing animation
                        candidates = [(c.codigo, c.descricao) for c in evento["data"]["opcoes"]]
                        current_candidates = candidates
                        
                        html = build_candidates_html(candidates, analyzing=True, rejected_codes=rejected_codes)
                        candidates_area.markdown(html, unsafe_allow_html=True)
                    
                    elif evento["type"] == "step":
                        dados = evento["data"]
                        step_count += 1
                        progress_bar.progress(min(step_count / 6, 0.9), text=f"Navegando: {dados['descricao'][:40]}...")
                        
                        path_data.append({
                            "Nível": len(str(dados['codigo'])) // 2 if dados['codigo'] != "ROOT" else 0,
                            "Código": dados['codigo'],
                            "Descrição": dados['descricao']
                        })
                        
                        path_area.markdown(build_path_html(path_data), unsafe_allow_html=True)
                        
                        # Show selected candidate
                        if current_candidates:
                            html = build_candidates_html(current_candidates, analyzing=False, selected_code=dados['codigo'], rejected_codes=rejected_codes)
                            candidates_area.markdown(html, unsafe_allow_html=True)
                            time.sleep(0.3)
                        
                        rejected_codes.clear()
                        current_candidates = []
                    
                    elif evento["type"] == "backtrack":
                        dados = evento["data"]
                        rejected_codes.add(dados['codigo'])
                        
                        if path_data:
                            path_data.pop()
                        path_area.markdown(build_path_html(path_data), unsafe_allow_html=True)
                        
                        if current_candidates:
                            html = build_candidates_html(current_candidates, analyzing=False, rejected_codes=rejected_codes)
                            candidates_area.markdown(html, unsafe_allow_html=True)
                        
                        st.toast(f"↩️ {dados['razao']}", icon="🔄")
                    
                    elif evento["type"] == "info":
                        st.info(evento["data"]["msg"])
                        
                    elif evento["type"] == "final":
                        final_result = evento["data"]
                
                progress_bar.progress(100, text="✅ Concluído!")
                time.sleep(0.3)
                progress_bar.empty()
                candidates_area.empty()
                
                if final_result:
                    codigo_final = final_result['codigo_final']
                    descricao_final = final_result['descricao_final']
                    
                    if codigo_final == "ROOT" or not codigo_final:
                        # Show suggestions
                        if clf.raiz.filhos:
                            suggestions = [(code, node.descricao) for code, node in list(clf.raiz.filhos.items())[:10]]
                            result_area.markdown(build_suggestion_html(suggestions), unsafe_allow_html=True)
                    else:
                        result_area.markdown(build_result_html(codigo_final, descricao_final), unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
        else:
            st.error("📁 Arquivo data/grpms.xlsx não encontrado.")
