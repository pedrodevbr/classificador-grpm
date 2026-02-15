# ⚡ Classificador Hierárquico de Materiais

Ferramenta inteligente para classificação de materiais e serviços industriais utilizando IA (LLM via OpenRouter). Navega recursivamente por uma árvore hierárquica de grupos de mercadorias para encontrar a classificação mais específica.

## ✨ Funcionalidades

- 🔍 **Classificação por Texto** — Descreva o material em linguagem natural
- 📄 **Suporte a PDF** — Upload de documentos com extração automática de texto
- 🖼️ **Suporte a Imagens** — Envie fotos para classificação visual
- 📍 **Caminho em Tempo Real** — Visualize cada etapa via SSE streaming
- ⚡ **Velocidade** — 5-15 segundos para classificação completa

## 🚀 Como Rodar

### Pré-requisitos

- Python 3.10+
- Chave de API do [OpenRouter](https://openrouter.ai)

### Instalação

```bash
git clone https://github.com/pedrodevbr/classificador-grpm.git
cd classificador-grpm
pip install -r requirements.txt
```

### Executando

```bash
# Windows PowerShell
$env:OPENROUTER_API_KEY="sua-chave-aqui"

# Linux/Mac
export OPENROUTER_API_KEY="sua-chave-aqui"

# Iniciar
uvicorn main:app --port 8000
```

Acesse: `http://localhost:8000`

## 📂 Estrutura do Projeto

| Arquivo | Descrição |
|---|---|
| `main.py` | Backend FastAPI (SSE streaming, file upload) |
| `classificador.py` | Lógica de classificação hierárquica + LLM |
| `static/index.html` | Frontend (HTML/CSS/JS) |
| `data/grpms.xlsx` | Árvore hierárquica de grupos de mercadorias |
| `Dockerfile` | Container para deploy |
| `render.yaml` | Blueprint para deploy no Render |

## 🌐 API Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/` | Frontend HTML |
| `GET` | `/api/models` | Lista modelos LLM disponíveis |
| `POST` | `/api/classify` | Classifica material (SSE streaming) |
| `POST` | `/api/describe-file` | Extrai texto de PDF/imagem |

## 🚀 Deploy

**Render (gratuito):** Conecte o repositório, adicione `OPENROUTER_API_KEY` nas env vars.

**Docker:**
```bash
docker build -t classificador .
docker run -p 8000:8000 -e OPENROUTER_API_KEY="sua-chave" classificador
```

Veja o [guia completo de deploy](docs/deployment_guide_fastapi.md).

## 🛠️ Tecnologias

- [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/)
- [OpenAI Python Library](https://github.com/openai/openai-python) (via OpenRouter)
- [Pydantic](https://docs.pydantic.dev/)
- [Pandas](https://pandas.pydata.org/)

---
**Nota:** O arquivo `data/grpms.xlsx` é necessário para a classificação.
