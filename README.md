# 📦 Classificador Hierárquico de Mercadorias

Este projeto é uma ferramenta inteligente para classificação de materiais e serviços industriais utilizando a API LLM do OpenRouter (Grok-4.1-fast, GPT-4o, etc). Ele navega recursivamente por uma árvore de hierarquia de grupos para encontrar a classificação mais específica para um dado item.

## ✨ Funcionalidades

*   **Navegação Hierárquica:** Percorre a árvore de grupos nível a nível (Grupo -> Subgrupo -> Classe -> Subclasse).
*   **LLM Powered:** Usa Inteligência Artificial (recomendado: x-ai/grok-4.1-fast) para tomar decisões semânticas em cada nó.
*   **Interface Streamlit:** UI amigável para testes rápidos e visualização do caminho de decisão em tempo real.
*   **Cache Inteligente:** Carregamento otimizado da estrutura hierárquica.

## 🚀 Como Rodar

### Pré-requisitos

*   Python 3.10+
*   Chave de API do OpenRouter (obtenha em [openrouter.ai](https://openrouter.ai))

### Instalação

1.  Clone o repositório:
    ```bash
    git clone https://github.com/SEU_USUARIO/classificador-grpm.git
    cd classificador-grpm
    ```

2.  Instale as dependências:
    ```bash
    pip install -r requirements.txt
    ```

3.  Configure sua chave de API (Opcional, pode inserir na UI):
    ```bash
    # Windows PowerShell
    $env:OPENROUTER_API_KEY="sua-chave-aqui"
    ```

### Executando o App

```bash
streamlit run app.py
```

## 📂 Estrutura do Projeto

*   `app.py`: Interface do usuário (Frontend Streamlit).
*   `classificador.py`: Lógica de classificação e integração com LLM.
*   `data/grpms.xlsx`: Banco de dados com a estrutura hierárquica dos grupos.

## 🛠️ Tecnologias

*   [Streamlit](https://streamlit.io/)
*   [OpenAI Python Library](https://github.com/openai/openai-python) (Compatível com OpenRouter)
*   [Pydantic](https://docs.pydantic.dev/) (Validação de dados)
*   [Pandas](https://pandas.pydata.org/)

---
**Nota:** Este projeto busca por `data/grpms.xlsx`. Certifique-se de que este arquivo existe na pasta `data`.
