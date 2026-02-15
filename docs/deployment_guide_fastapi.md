# 🚀 Guia de Deploy — FastAPI (Render / Railway / Docker)

Este guia descreve como publicar a versão **FastAPI** do Classificador de Materiais.

---

## Comparação de Plataformas

| Critério               | Render (Grátis)          | Railway (~$5/mês)        | Docker (Self-hosted)     |
|------------------------|--------------------------|--------------------------|--------------------------|
| **Custo**              | $0 (free tier)           | ~$5/mês                  | Custo do servidor        |
| **Configuração**       | GitHub → Deploy          | GitHub → Deploy          | Manual                   |
| **Cold Start**         | Sim (15s no free tier)   | Não                      | Não                      |
| **SSL/HTTPS**          | Automático               | Automático               | Manual (nginx/traefik)   |
| **Custom Domain**      | Sim                      | Sim                      | Sim                      |

---

## Opção 1: Render (Gratuito)

### Passo a Passo

1. **Crie uma conta** em [render.com](https://render.com) (login via GitHub)
2. Clique em **"New" → "Web Service"**
3. Conecte o repositório GitHub
4. Configure:

| Campo              | Valor                                  |
|--------------------|----------------------------------------|
| **Name**           | `classificador-materiais`              |
| **Region**         | Oregon (US West)                       |
| **Runtime**        | Docker                                 |
| **Instance Type**  | Free                                   |

5. Em **"Environment Variables"**, adicione:

```
OPENROUTER_API_KEY = sk-or-v1-sua-chave-real-aqui
```

6. Clique em **"Create Web Service"**

O app estará online em ~2 minutos em:
```
https://classificador-materiais.onrender.com
```

> ⚠️ No plano gratuito, o app "dorme" após 15 min sem requisições. A primeira visita pode demorar ~15s.

---

## Opção 2: Railway (~$5/mês)

### Passo a Passo

1. Acesse [railway.app](https://railway.app) e faça login via GitHub
2. Clique em **"New Project" → "Deploy from GitHub Repo"**
3. Selecione o repositório
4. Railway detecta o `Dockerfile` automaticamente
5. Vá em **"Variables"** e adicione:

```
OPENROUTER_API_KEY = sk-or-v1-sua-chave-real-aqui
PORT = 8000
```

6. Em **"Settings" → "Networking"**, clique em **"Generate Domain"**

O app estará disponível em:
```
https://classificador-materiais.up.railway.app
```

---

## Opção 3: Docker (Self-hosted)

### Build e Run

```bash
# Build
docker build -t classificador-materiais .

# Run
docker run -d \
  -p 8000:8000 \
  -e OPENROUTER_API_KEY="sk-or-v1-sua-chave-real-aqui" \
  --name classificador \
  classificador-materiais
```

### Docker Compose (Opcional)

```yaml
# docker-compose.yml
version: '3.8'
services:
  classificador:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
    restart: unless-stopped
```

```bash
# .env (NÃO commitar)
OPENROUTER_API_KEY=sk-or-v1-sua-chave-real-aqui
```

```bash
docker compose up -d
```

---

## Rodar Localmente (Desenvolvimento)

```bash
# Instalar dependências
pip install -r requirements.txt

# Setar variável de ambiente
# Windows PowerShell:
$env:OPENROUTER_API_KEY="sua-chave"

# Linux/Mac:
export OPENROUTER_API_KEY="sua-chave"

# Iniciar
uvicorn main:app --reload --port 8000
```

Acesse: `http://localhost:8000`

---

## Atualizações

Basta fazer `git push`. Render e Railway detectam automaticamente e fazem redeploy.

## Endpoints da API

| Método | Rota               | Descrição                                   |
|--------|---------------------|---------------------------------------------|
| GET    | `/`                | Frontend HTML                               |
| GET    | `/api/models`      | Lista modelos disponíveis                   |
| POST   | `/api/classify`    | Classifica material (SSE streaming)         |
| POST   | `/api/describe-file`| Extrai texto de PDF/imagem                 |
