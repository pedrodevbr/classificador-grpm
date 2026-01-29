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
st.title("📦 Classificador de Materiais ")
st.markdown("""
Este aplicativo utiliza Inteligência Artificial para classificar materiais
navegando pela árvore de hierarquia de grupos.
""")

# Sidebar para Configurações
with st.sidebar:
    st.header("Configurações")
    #api_key = st.text_input("OpenRouter API Key", type="password", help="Insira sua chave API do OpenRouter")
    api_key="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"
    # Se não houver chave no input, tenta pegar do ambiente
    if not api_key:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if api_key:
            st.info("Usando chave definida nas variáveis de ambiente.")

    model_name = st.selectbox(
        "Modelo LLM",
        ["x-ai/grok-4.1-fast", "openai/gpt-5-nano", "anthropic/claude-3-haiku",'google/gemini-3-flash-preview','deepseek/deepseek-v3.2'],
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
    # Gerenciamento de Estado para o Texto
    if 'descritivo_text' not in st.session_state:
        st.session_state.descritivo_text = ""

    # Uploader de Arquivo
    uploaded_file = st.file_uploader("📄 Anexar documento ou imagem (PDF, JPG, PNG)", type=['pdf', 'jpg', 'jpeg', 'png'])
    
    # Processamento do Arquivo
    if uploaded_file and api_key:
        # Carrega classificador apenas para usar as ferramentas de extração/visão
        clf_temp = load_classifier(api_key, model_name)
        
        if clf_temp:
            processed_key = f"processed_{uploaded_file.file_id}"
            if processed_key not in st.session_state:
                with st.spinner("Processando arquivo..."):
                    if uploaded_file.type == "application/pdf":
                        texto = clf_temp.extrair_texto_pdf(uploaded_file)
                        st.session_state.descritivo_text = texto
                        st.success("Texto extraído do PDF!")
                    else:
                         # Imagem
                        texto = clf_temp.descrever_imagem(uploaded_file.getvalue(), uploaded_file.type)
                        st.session_state.descritivo_text = texto
                        st.success("Imagem analisada com IA!")
                
                st.session_state[processed_key] = True

    descritivo_item = st.text_area(
        "Descrição do Item:",
        value=st.session_state.descritivo_text,
        height=150,
        placeholder="Ex: Luva de segurança de vaqueta...",
        key="input_descritivo" # Key separada para evitar conflito direto, mas sync via value
    )
    
    # Atualiza state se usuário digitar
    st.session_state.descritivo_text = descritivo_item
    
    btn_classificar = st.button("🔍 Classificar Item", type="primary", use_container_width=True)

# Lógica de Classificação
if btn_classificar:
    # Atualiza descritivo com o valor atual do widget
    descritivo_item = st.session_state.descritivo_text
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
                #status_container.info("Iniciando análise...")
                
                # Placeholder para a tabela de caminho
                #st.markdown("### Caminho Percorrido")
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
                    
                    elif evento["type"] == "backtrack":
                         dados = evento["data"]
                         # Remove o último passo pois falhou
                         if path_data:
                             path_data.pop()
                         table_placeholder.table(pd.DataFrame(path_data))
                         st.toast(f"↩️ Backtracking: {dados['razao']}")
                    
                    elif evento["type"] == "info":
                        st.info(evento["data"]["msg"])
                        
                    elif evento["type"] == "final":
                        final_result = evento["data"]
                
                my_bar.progress(100, text="Classificação concluída!")
                status_container.empty() # Limpar status
                
                if final_result:
                    # Exibir Resultados Finais
                    #st.success("✅ Item Classificado com Sucesso!")
                    
                    # Resultado Final em Destaque
                    st.markdown("### Resultado Final")
                    st.info(f"**Código:** `{final_result['codigo_final']}`\n\n**Descrição:** {final_result['descricao_final']}")
                    
                    
            except Exception as e:
                st.error(f"Ocorreu um erro durante a classificação: {str(e)}")
