# 📚 AutoDocGen - Gerador Automático de Documentação Técnica

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![LM Studio](https://img.shields.io/badge/LM_Studio-Qwen3_4B-orange.svg)](https://lmstudio.ai/)
[![Ollama](https://img.shields.io/badge/Ollama-Qwen3-orange.svg)](https://ollama.ai/)

Uma ferramenta web inteligente que analisa repositórios públicos do GitHub e gera automaticamente documentação técnica completa usando IA Generativa (LLM) local.

## 🎯 Sobre o Projeto

O **AutoDocGen** é uma plataforma web que automatiza a criação de documentação técnica para projetos de software. Utilizando o poder da Inteligência Artificial Generativa através do LM Studio ou Ollama, a ferramenta analisa repositórios do GitHub e produz documentação estruturada incluindo:

- ✅ **Requisitos Funcionais e Não-Funcionais**
- ✅ **Arquitetura de Software** com Diagramas Mermaid
- ✅ **Diagramas Mermaid (graph TD)**
- ✅ **Stack Tecnológica e Dependências**
- ✅ **Resumo Executivo do Projeto**

## 🚀 Funcionalidades

- 🔐 **Autenticação segura** com JWT
- 📦 **Análise de repositórios públicos** do GitHub
- 🤖 **Geração automática de documentação** com IA (Modelos LLM)
- 💬 **Chat persistente** por repositório com histórico em SQLite
- 📊 **Dashboard interativo** com histórico de análises
- 📄 **Exportação em Markdown e PDF**
- 🎨 **Diagramas arquiteturais** em Mermaid (graph TD com sanitização automática)
- ⚡ **Processamento assíncrono** de análises (background tasks)
- 💾 **Armazenamento persistente** de resultados
- 📡 **Monitoramento em tempo real** das etapas de análise (terminal interativo no frontend)
- 🔄 **Provedor LLM duplo** — detecta automaticamente LM Studio (porta 1234) ou Ollama (porta 11434)
- 📝 **Sistema de logs estruturado** com arquivo de log por componente (backend e frontend)
- 🩺 **Verificações de saúde na inicialização** — banco de dados, LLM, dependências e diretórios

## 📋 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **Python 3.8+**
- **uv** (para gerenciar bibliotecas Python)
- **Git** (para clonar o repositório)
- **Um provedor LLM:**
  - **LM Studio** (recomendado) com modelo Qwen3-4B-2507 carregado na porta 1234, OU
  - **Ollama** com modelo Qwen3 na porta 11434

### Instalando o LM Studio (Recomendado)

1. Baixe e instale o LM Studio em: https://lmstudio.ai
2. Pesquise e baixe o modelo `qwen3-4b-2507`
3. Carregue o modelo e inicie o servidor local na porta 1234

### Instalando o Ollama (Alternativa)

1. Baixe e instale o Ollama em: https://ollama.ai/download
2. Baixe o modelo Qwen3:
   ```bash
   ollama pull qwen3
   ```
3. Inicie o servidor:
   ```bash
   ollama serve
   ```

> ⚠️ O backend detecta automaticamente qual provedor está rodando — não é necessário configurar nada.

### Troubleshooting do xhtml2pdf (Linux)

O xhtml2pdf depende indiretamente do pycairo (via rlpycairo → svglib), que requer bibliotecas de desenvolvimento do Cairo:

```bash
sudo apt update
sudo apt install -y \
    libcairo2-dev \
    pkg-config \
    libpango1.0-dev \
    libglib2.0-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    python3-dev
```

## 🛠️ Instalação

### 1. Clone o Repositório

```bash
git clone https://github.com/seu-usuario/autodocgen.git
cd autodocgen
```

### 2. Estrutura do Projeto

```
autodocgen/
├── backend/          # API FastAPI
│   └── logs/         # Logs estruturados por componente (gerados em runtime)
├── frontend/         # Interface Flask
│   └── logs/         # Logs do frontend (gerados em runtime)
├── storage/          # Arquivos temporários e documentos gerados
├── README.md
└── LICENSE
```

### 3. Instalação das Dependências

**Backend (FastAPI):**
```bash
cd backend
uv venv
uv pip install -r requirements.txt
```

**Frontend (Flask):**
```bash
cd ../frontend
uv venv
uv pip install -r requirements.txt
```

## 🏃 Executando a Aplicação

Você precisará de **dois terminais** abertos simultaneamente.

### Terminal 1: Backend (FastAPI)

```bash
cd backend
uv run uvicorn app.main:app --port 8000
```

✅ O backend estará rodando em: **http://127.0.0.1:8000**

### Terminal 2: Frontend (Flask)

```bash
cd frontend
uv run app.py
```

✅ O frontend estará rodando em: **http://127.0.0.1:5001**

## 📖 Usando o Sistema

### Passo a Passo

1. **Acesse a aplicação**
   - Abra seu navegador e vá para: http://127.0.0.1:5001

2. **Crie sua conta**
   - Clique em "Register" no menu
   - Preencha seus dados e crie uma conta

3. **Faça login**
   - Use suas credenciais para acessar o dashboard

4. **Adicione um repositório**
   - No dashboard, clique em "Adicionar Repositório"
   - Insira a URL de um repositório público do GitHub
   - Exemplo: `https://github.com/psf/requests`

5. **Inicie a análise**
   - Clique em "Analyze 🚀"
   - A tela de análise exibirá um **terminal interativo** mostrando cada etapa do processo em tempo real (download do ZIP, indexação, chamada ao LLM, etc.) via polling AJAX a cada 2 segundos
   - Você pode fechar a página a qualquer momento; a análise continua em background no servidor
   - Ao reabrir a página da análise, o terminal será recarregado com todos os passos já executados

6. **Visualize e baixe a documentação**
   - Acesse o histórico de análises
   - Visualize a documentação gerada em Markdown renderizado (com suporte a diagramas Mermaid)
   - Expanda o accordion **"Ver log de execução da análise"** para revisar todas as etapas
   - Baixe em formato PDF

7. **Chat com o repositório**
   - No dashboard, clique em "Chat 💬" ao lado de qualquer repositório
   - Faça perguntas em linguagem natural sobre arquitetura, requisitos ou código
   - As sessões são persistidas em SQLite — feche e reabra a página sem perder o histórico

## 🛠️ Tecnologias Utilizadas

### Backend
- **FastAPI** - Framework web moderno e rápido
- **SQLAlchemy** - ORM para banco de dados
- **bcrypt** - Hash de senhas (nativo, sem passlib)
- **PyJWT / python-jose** - Autenticação JWT
- **HTTPX** - Cliente HTTP assíncrono
- **xhtml2pdf** - Geração de PDF a partir de HTML/Markdown
- **LLM Provider** - Detecta automaticamente LM Studio ou Ollama
- **logging (stdlib)** - Sistema de logs estruturado com handlers para console e arquivo

### Frontend
- **Flask** - Framework web leve
- **Bootstrap 5.2** - Design responsivo
- **JavaScript (Fetch API)** - Polling AJAX para monitoramento em tempo real
- **marked.js** - Renderização de Markdown no browser
- **mermaid.js** - Renderização de diagramas arquiteturais (render individual com fallback)
- **logging (stdlib)** - Sistema de logs estruturado com handlers para console e arquivo

### Banco de Dados
- **SQLite** - Banco de dados relacional (MVP)
- **PostgreSQL** - Recomendado para produção

### IA Generativa
- **LM Studio** (recomendado) - Servidor LLM local com Qwen3-4B-2507
- **Ollama** (alternativa) - Servidor LLM local com Qwen3
- **OpenCode API** (opcional) - Enriquecimento de análise pré-computada, porta 7000

## 📁 Estrutura de Arquivos

```
backend/
├── app/
│   ├── routers/
│   │   ├── auth.py              # Endpoints de autenticação e registro
│   │   ├── repos.py             # Endpoints de gerenciamento de repositórios
│   │   ├── analyses.py          # Endpoints de análise + endpoint GET /{id}/steps
│   │   └── chat.py              # Endpoints de chat (send, sessions, history, delete)
│   ├── services/
│   │   ├── llm_provider.py      # Detecta automaticamente LM Studio ou Ollama
│   │   ├── lm_studio_client.py  # Integração com API do LM Studio (porta 1234)
│   │   ├── ollama_client.py     # Integração com API do Ollama (porta 11434)
│   │   ├── opencode_client.py   # Integração com OpenCode API (opcional, porta 7000)
│   │   ├── chat_service.py      # Gerenciamento de sessões de chat com persistência SQLite
│   │   ├── github_fetcher.py    # Download de ZIP do GitHub
│   │   ├── repo_indexer.py      # Travessia e indexação de arquivos
│   │   ├── context_builder.py   # Construção do pacote de evidências
│   │   ├── doc_generator.py     # Orquestração da geração de documentação
│   │   └── pdf_generator.py     # Conversão Markdown → PDF (xhtml2pdf)
│   ├── logging_config.py        # Utilitário de loggers dual-channel (console + arquivo)
│   ├── models.py                # Modelos SQLAlchemy (User, Repository, AnalysisJob, Document, ChatSession, ChatMessage)
│   ├── schemas.py               # Schemas Pydantic v2
│   ├── database.py              # Configuração do SQLAlchemy e SessionLocal
│   ├── security.py              # Hash/verificação de senhas com bcrypt nativo
│   └── main.py                  # App FastAPI com lifespan e verificações de inicialização
├── logs/                        # Arquivos de log gerados em runtime
│   ├── initialization.log
│   ├── analyses.log
│   ├── repos.log
│   ├── llm_provider.log
│   ├── ollama_client.log
│   ├── github_fetcher.log
│   ├── context_builder.log
│   ├── repo_indexer.log
│   ├── doc_generator.log
│   └── pdf_generator.log
├── storage/
│   ├── repos/                   # ZIPs extraídos temporariamente por job
│   └── docs/                    # PDFs gerados
└── requirements.txt
```

```
frontend/
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── analysis_result.html     # Terminal interativo com polling AJAX + renderização Mermaid
│   ├── analyzed_repos.html
│   └── chat.html                # Interface de chat com listagem de sessões
├── static/
│   └── css/
├── logging_config.py            # Utilitário de loggers dual-channel (console + arquivo)
├── logs/                        # Arquivos de log gerados em runtime
│   └── initialization.log
├── app.py                       # App Flask com startup checks e rota de chat
└── requirements.txt
```

## 🔧 Configuração Avançada

### Variáveis de Ambiente

Crie um arquivo `.env` na pasta `backend/`:

```env
# Database
DATABASE_URL=sqlite:///./storage/app.db

# JWT
SECRET_KEY=sua_chave_secreta_aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# GitHub
GITHUB_API_TOKEN=seu_token_aqui (opcional)

# Limits
MAX_REPO_SIZE_MB=100
MAX_FILE_COUNT=500
ANALYSIS_TIMEOUT_SECONDS=300
```

Não é necessário configurar o LLM — o backend detecta automaticamente o LM Studio (porta 1234) ou Ollama (porta 11434) na inicialização.

### Docker (Opcional)

Para executar com Docker:

Crie os arquivos Dockerfile para a aplicação backend e frontend.

```bash
docker-compose up --build
```

## 🐛 Troubleshooting

### Provedor LLM não está respondendo
```bash
# Verifique o LM Studio
curl http://localhost:1234/v1/models

# Verifique o Ollama
curl http://localhost:11434/api/version
```

> ⚠️ O log de inicialização do backend (`logs/initialization.log`) informa qual provedor foi detectado e lista os modelos disponíveis.

### Erro de dependências
```bash
# Atualize o pip
pip install --upgrade pip

# Reinstale as dependências
pip install -r requirements.txt --force-reinstall
```

### Banco de dados corrompido ou com schema desatualizado
```bash
# Remova o banco de dados (cuidado: apaga todos os dados)
rm -f backend/app.db

# O banco será recriado automaticamente na próxima inicialização do backend
uv run uvicorn app.main:app --port 8000
```

### Verificando logs de inicialização
```bash
# Backend
cat backend/logs/initialization.log

# Frontend
cat frontend/logs/initialization.log
```

### Verificando logs de uma análise específica
```bash
# Pipeline completo de análise
cat backend/logs/analyses.log

# Chamadas ao LLM
cat backend/logs/llm_provider.log
```

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, siga estes passos:

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📝 Melhorias Futuras

- [ ] Suporte a repositórios privados (OAuth GitHub)
- [ ] Análise incremental (detectar mudanças)
- [ ] Comparação de versões de documentação
- [ ] Integração com CI/CD pipelines
- [ ] Interface de administração de usuários
- [ ] Sistema de notificações (e-mail/webhook ao concluir análise)
- [ ] API pública para integrações externas
- [ ] Migração de banco de dados com Alembic (evitar reset manual do `app.db`)
- [ ] Server-Sent Events (SSE) para substituir o polling AJAX por push real-time
- [ ] Suporte a Docker Compose com LLM integrado

## 📄 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👥 Autores

Desenvolvido por [Armando Soares Sousa]

## 🙏 Agradecimentos

- LM Studio Team pela excelente ferramenta de LLM local
- Ollama Team pelo excelente trabalho com LLMs locais
- FastAPI e Flask communities
- Todos os contribuidores e usuários

## 📞 Suporte

Para suporte, por favor abra uma issue no repositório ou entre em contato em [armando@ufpi.edu.br].
