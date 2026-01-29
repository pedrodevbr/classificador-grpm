import streamlit as st
import os
import pandas as pd
from classificador import ClassificadorHierarquicoOpenRouter

# Configuração da Página
st.set_page_config(
    page_title="Classificador Hierárquico de Mercadorias",
    page_icon="📦",
    layout="wide"
)

# Título e Descrição
st.title("📦 Classificador de Mercadorias (Hierárquico)")
st.markdown("""
Este aplicativo utiliza Inteligência Artificial (Grok-4.1-fast) para classificar itens mercadológicos 
navegando pela árvore de hierarquia de grupos.
""")

# Sidebar para Configurações
with st.sidebar:
    st.header("Configurações")
    api_key = st.text_input("OpenRouter API Key", type="password", help="Insira sua chave API do OpenRouter")
    
    # Se não houver chave no input, tenta pegar do ambiente
    if not api_key:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if api_key:
            st.info("Usando chave definida nas variáveis de ambiente.")

    model_name = st.selectbox(
        "Modelo LLM",
        ["x-ai/grok-4.1-fast", "openai/gpt-4o-mini", "anthropic/claude-3-haiku"],
        index=0
    )

# Função de Cache para Carregar Hierarquia
@st.cache_resource
def load_classifier(api_key_val, model_val):
    """Inicializa o classificador e carrega a hierarquia (cacheado)."""
    classifier = ClassificadorHierarquicoOpenRouter(
        api_key=api_key_val,
        model=model_val
    )
    
    arquivo_grp = "data/grpms.xlsx"
    if os.path.exists(arquivo_grp):
        with st.spinner(f"Carregando hierarquia de {arquivo_grp}..."):
            classifier.carregar_hierarquia(arquivo_grp)
        return classifier
    else:
        st.error(f"Arquivo de hierarquia não encontrado: {arquivo_grp}")
        return None

# Interface Principal
col1, col2 = st.columns([2, 1])

with col1:
    descritivo_item = st.text_area(
        "Descrição do Item:",
        height=150,
        placeholder="Ex: Luva de segurança de vaqueta..."
    )
    
    btn_classificar = st.button("🔍 Classificar Item", type="primary", use_container_width=True)

# Lógica de Classificação
if btn_classificar:
    if not descritivo_item:
        st.warning("Por favor, insira uma descrição para o item.")
    elif not api_key:
        st.error("Chave API OpenRouter é necessária.")
    else:
        # Carregar classificador
        clf = load_classifier(api_key, model_name)
        
        if clf:
            try:
                # Barra de progresso visual para a navegação
                progress_text = "Navegando na hierarquia..."
                my_bar = st.progress(0, text=progress_text)
                
                # Container para updates em tempo real
                status_container = st.empty()
                status_container.info("Iniciando análise...")
                
                # Placeholder para a tabela de caminho
                st.markdown("### 🛤️ Caminho Percorrido")
                table_placeholder = st.empty()
                path_data = []
                
                # Variável para resultado final
                final_result = None
                
                # Executar classificação (Iterando sobre o gerador)
                for evento in clf.classificar_item(descritivo_item):
                    if evento["type"] == "step":
                        dados = evento["data"]
                        # Adicionar ao histórico visual
                        path_data.append({
                            "Nível": len(str(dados['codigo'])) // 2 if dados['codigo'] != "ROOT" else 0,
                            "Código": dados['codigo'],
                            "Descrição": dados['descricao']
                        })
                        # Atualizar tabela em tempo real
                        table_placeholder.table(pd.DataFrame(path_data))
                        
                    elif evento["type"] == "final":
                        final_result = evento["data"]
                
                my_bar.progress(100, text="Classificação concluída!")
                status_container.empty() # Limpar status
                
                if final_result:
                    # Exibir Resultados Finais
                    st.success("✅ Item Classificado com Sucesso!")
                    
                    # Resultado Final em Destaque
                    st.markdown("### Resultado Final")
                    st.info(f"**Código:** `{final_result['codigo_final']}`\n\n**Descrição:** {final_result['descricao_final']}")
                    
                    # Expander com JSON completo
                    with st.expander("Ver JSON Completo"):
                        st.json(final_result)
                    
            except Exception as e:
                st.error(f"Ocorreu um erro durante a classificação: {str(e)}")
