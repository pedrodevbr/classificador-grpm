# 🚀 Guia de Deploy — Streamlit Community Cloud

Este guia descreve como publicar o **Classificador de Materiais** de forma profissional, **gratuita**, e sem que o usuário final precise de uma API key.

---

## Por que Streamlit Community Cloud?

| Critério              | Streamlit Cloud                          |
|-----------------------|------------------------------------------|
| **Custo**             | 100% Gratuito                            |
| **Configuração**      | Deploy em 3 cliques a partir do GitHub   |
| **Secrets (API Key)** | Gerenciamento nativo e seguro            |
| **Domínio**           | `https://seu-app.streamlit.app`          |
| **SSL/HTTPS**         | Automático                               |
| **Manutenção**        | Zero — rebuild automático a cada push    |

---

## Passo a Passo

### 1. Preparar o Repositório no GitHub

Certifique-se de que o repositório contém:
```
├── .streamlit/
│   └── config.toml      ← tema visual
├── app.py
├── classificador.py
├── data/
│   └── grpms.xlsx
├── requirements.txt
├── .gitignore            ← deve ignorar .env
└── README.md
```

> ⚠️ **NUNCA** faça commit do arquivo `.env` com a chave real. Ele já está no `.gitignore`.

### 2. Criar conta no Streamlit Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io)
2. Faça login com a conta GitHub que possui o repositório
3. Clique em **"New app"**

### 3. Configurar o Deploy

| Campo             | Valor                                       |
|-------------------|---------------------------------------------|
| **Repository**    | `seu-usuario/classificador-grpm`            |
| **Branch**        | `main`                                      |
| **Main file path**| `app.py`                                    |

### 4. Configurar a API Key (Secrets)

Este é o passo mais importante — é assim que a chave fica no servidor sem o usuário ver.

1. Na tela do app no Streamlit Cloud, clique em **"⋮" → "Settings"**
2. Vá na aba **"Secrets"**
3. Cole o seguinte conteúdo:

```toml
OPENROUTER_API_KEY = "sk-or-v1-sua-chave-real-aqui"
```

4. Clique em **"Save"**

O app será reiniciado automaticamente e a chave será lida via `st.secrets["OPENROUTER_API_KEY"]`.

### 5. Pronto! 🎉

O app estará disponível em um URL como:
```
https://classificador-grpm.streamlit.app
```

---

## Atualizações

Basta fazer `git push` para o branch `main`. O Streamlit Cloud detecta automaticamente e faz redeploy.

## Monitoramento

No painel do Streamlit Cloud, você pode:
- Ver **logs** do app em tempo real
- Reiniciar o app manualmente
- Gerenciar secrets
- Ver métricas de uso

---

## Alternativa: Deploy Interno (Docker)

Se a empresa preferir hospedagem interna:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
docker build -t classificador-grpm .
docker run -d -p 8501:8501 -e OPENROUTER_API_KEY="sua-chave" classificador-grpm
```
