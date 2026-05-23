# Relatório Técnico: Ferramenta de Geração de Documentação Técnica Automática para Repositórios GitHub

## Sumário Executivo

Este relatório técnico descreve a arquitetura, implementação e proposta de uma solução web inovadora para geração automática de documentação técnica de repositórios públicos do GitHub. A ferramenta utiliza inteligência artificial generativa local através do servidor Ollama com o modelo Qwen3 para analisar repositórios e produzir documentação técnica completa e estruturada.

## 1. Visão Geral do Produto

### 1.1 Objetivo Principal
Desenvolver uma plataforma web que permita aos usuários analisar repositórios públicos do GitHub e gerar automaticamente documentação técnica abrangente, incluindo requisitos funcionais e não-funcionais, arquitetura de software, stack tecnológica e resumo executivo.

### 1.2 Fluxo de Operação
1. **Usuário autenticado** acessa a plataforma
2. **Cadastra repositório** público do GitHub
3. **Inicia análise** do repositório
4. **Sistema baixa** e indexa o repositório
5. **IA Generativa** analisa e gera documentação
6. **Usuário visualiza** e **baixa** a documentação em Markdown ou PDF

## 2. Arquitetura Técnica

### 2.1 Componentes Principais

#### 2.1.1 Frontend (Flask)
- **Tecnologias**: HTML5, Bootstrap 5.2, JavaScript
- **Telas**: Login/Cadastro, Dashboard, Repositórios, Análises, Visualização
- **Responsabilidades**: Interface com usuário, consumo da API FastAPI

#### 2.1.2 Backend (FastAPI)
- **API REST**: Autenticação, gerenciamento de repositórios, jobs de análise, documentos
- **Segurança**: JWT, validação de inputs, rate limiting
- **Assincronicidade**: BackgroundTasks para processamento de análises

#### 2.1.3 Banco de Dados (SQLite + SQLAlchemy)
- **Modelos**: Users, Repositories, AnalysisJobs, Documents
- **Persistência**: SQLite para MVP, escalável para PostgreSQL
- **Relacionamentos**: ORM com SQLAlchemy

#### 2.1.4 Worker de Análise
- **MVP**: BackgroundTasks do FastAPI
- **Evolução**: Celery/RQ + Redis para escalabilidade
- **Responsabilidades**: Fetch, indexação, detecção de stack, chamada LLM

#### 2.1.5 Módulo IA Generativa (Ollama + Qwen3)
- **Endpoint**: `http://localhost:11434`
- **Modelo**: Qwen3 (ou alternativas compatíveis)
- **Processamento**: Análise de contexto, geração de documentação

### 2.2 Estrutura de Pastas Recomendada

```
project/
├── backend/
│   ├── app/
│   │   ├── routers/          # auth, repos, analyses, docs
│   │   ├── services/         # github_fetcher, repo_indexer, etc.
│   │   ├── models/           # SQLAlchemy models
│   │   └── main.py           # FastAPI app
│   └── requirements.txt
├── frontend/
│   ├── templates/            # HTML templates
│   ├── static/               # CSS, JS, images
│   └── app.py                # Flask app
├── storage/
│   ├── repos/                # Repositórios baixados
│   └── docs/                 # Documentos gerados
└── docker-compose.yml        # Containerização
```

## 3. Banco de Dados

### 3.1 Modelos Principais

#### 3.1.1 Users
```python
class User(Base):
    id: int
    name: str
    email: str (unique)
    password_hash: str
    created_at: datetime
```

#### 3.1.2 Repositories
```python
class Repository(Base):
    id: int
    user_id: int
    full_name: str  # "org/repo"
    html_url: str
    default_branch: str
    created_at: datetime
```

#### 3.1.3 AnalysisJobs
```python
class AnalysisJob(Base):
    id: int
    user_id: int
    repository_id: int
    status: Enum[PENDING, RUNNING, DONE, ERROR]
    started_at: datetime
    finished_at: datetime
    error_message: str
    evidence_json: JSON  # Estrutura + stack + trechos
    llm_model: str  # "qwen3:..."
    llm_params: JSON  # temperature, top_p, max_tokens
```

#### 3.1.4 Documents
```python
class Document(Base):
    id: int
    analysis_job_id: int
    format: Enum[md, pdf]
    path: str
    created_at: datetime
```

## 4. Autenticação e Segurança

### 4.1 Rotas de Autenticação
- `POST /auth/register` - Registro de novo usuário
- `POST /auth/login` - Login com retorno de access_token
- `GET /auth/me` - Informações do usuário autenticado

### 4.2 Boas Práticas de Segurança
- **Hash de senhas**: bcrypt ou argon2
- **JWT**: Tempo de expiração curto (30-60 min)
- **Validação**: Repositórios devem ser públicos do github.com
- **Limites**: Tamanho de repositórios, número de arquivos, timeout
- **Extração segura**: Proteção contra path traversal
- **Ignorar diretórios**: node_modules, dist, .venv, etc.

## 5. Pipeline de Análise do GitHub

### 5.1 Fetch do Repositório
**Método**: Download ZIP do branch padrão
**Localização**: `storage/repos/<job_id>/`
**Validação**: Verificar se é repositório público válido

### 5.2 Indexação Controlada
- **Árvore de pastas/arquivos**: Limitar profundidade (3-5 níveis)
- **Contagem de extensões**: Identificar linguagens predominantes
- **Arquivos-chave**: README, manifests, Dockerfile, config files
- **Limites**: Tamanho máximo de arquivos, número total

### 5.3 Interpretação do README
**Extração de seções**:
- Sobre/Descrição
- Instalação e Configuração
- Uso e Exemplos
- Variáveis de Ambiente
- Dependências e Requisitos

**Saída**: Estrutura organizada de informações relevantes

### 5.4 Detecção de Stack Tecnológica
**Sinais fortes**:
- **Python**: pyproject.toml, requirements.txt, setup.py
- **JavaScript/TypeScript**: package.json, tsconfig.json
- **Java**: pom.xml, build.gradle
- **C/C++**: CMakeLists.txt, Makefile
- **Web**: .html, .css, .js em grande quantidade

**Saída**: primary_language, frameworks, build_tools, run_commands

## 6. Proposta de Ferramenta de Geração de Documentação Técnica Usando Modelos LLM

### 6.1 Fundamentação Conceitual

A utilização de modelos de linguagem de grande porte (LLMs) para geração de documentação técnica representa uma abordagem inovadora que combina capacidades de processamento de linguagem natural com conhecimento técnico especializado. A proposta central é transformar código-fonte e estruturas de projetos em documentação técnica estruturada e compreensível.

### 6.2 Arquitetura do Módulo LLM

#### 6.2.1 Context Builder (Montagem de Evidências)

O componente mais crítico é a construção de um **pacote de evidências compacto e bem estruturado** que serve como contexto para o LLM:

**Estrutura do Pacote de Evidências**:
```json
{
  "repository_info": {
    "name": "org/repo",
    "description": "...",
    "topics": ["..."]
  },
  "project_structure": {
    "tree": "...",
    "key_files": ["README.md", "package.json", ...]
  },
  "content_snippets": {
    "readme_sections": {
      "installation": "...",
      "usage": "...",
      "configuration": "..."
    },
    "dependencies": {
      "package.json": "...",
      "requirements.txt": "..."
    },
    "architecture_hints": {
      "folder_structure": "...",
      "file_patterns": "..."
    }
  },
  "detected_stack": {
    "primary_language": "...",
    "frameworks": ["..."],
    "build_tools": ["..."]
  },
  "uncertainties": [
    "No test files found",
    "Deployment configuration unclear"
  ]
}
```

#### 6.2.2 Prompt Engineering

**Prompt do Sistema** (instruções gerais):
```
Você é um especialista em engenharia de software e documentação técnica.
Sua tarefa é analisar o contexto fornecido e gerar documentação técnica completa.

REGRAS:
1. Baseie-se EXCLUSIVAMENTE nas evidências fornecidas
2. Quando inferir algo, marque explicitamente como "Inferido"
3. Cite as fontes das informações ("Baseado no README...", "No package.json...")
4. Mantenha tom técnico e objetivo
5. Estruture a saída conforme o formato Markdown exigido
6. Não invente informações não presentes no contexto
```

**Prompt do Usuário** (contexto + instruções específicas):
```
Analise o seguinte repositório e gere documentação técnica completa:

[CONTEXTO COMPLETO INSERIDO AQUI]

FORMATO DE SAÍDA EXIGIDO (Markdown):
1. Documento de Requisitos
   1.1 Requisitos Funcionais
   1.2 Requisitos Não-Funcionais
2. Documento de Arquitetura
   2.1 Diagrama C4 (Context, Container, Component) em Mermaid
   2.2 Arquitetura MVC/Camadas
   2.3 Diagrama de Pacotes/Módulos
3. Documentação Técnica da Stack
   3.1 Linguagens e Frameworks
   3.2 Build/Run/Test Commands
   3.3 Estrutura do Projeto
4. Resumo Executivo
```

#### 6.2.3 Chamada ao Ollama

**Configuração da Chamada**:
```python
import httpx

async def call_ollama(context: str, prompt: str):
    payload = {
        "model": "qwen3",
        "prompt": f"{system_prompt}\n\n{user_prompt_with_context}",
        "stream": False,
        "options": {
            "temperature": 0.3,  # Baixa para consistência
            "top_p": 0.9,
            "num_predict": 2000  # Limite para evitar "romances"
        }
    }
    
    response = await httpx.post(
        "http://localhost:11434/api/generate",
        json=payload,
        timeout=300
    )
    
    return response.json()["response"]
```

#### 6.2.4 Pós-Processamento e Validação

**Validação da Saída**:
1. Verificar presença de seções obrigatórias
2. Validar sintaxe Markdown
3. Sanitizar conteúdo potencialmente malicioso
4. Verificar referências a evidências

**Fallback Strategy**:
- Se seções faltantes: regenerar com prompt mais específico
- Se alucinações detectadas: reduzir temperatura e regenerar
- Se timeout: implementar retry com backoff exponencial

### 6.3 Vantagens da Abordagem LLM

#### 6.3.1 Benefícios Técnicos
- **Adaptação automática**: Ajusta-se a diferentes stacks tecnológicas
- **Compreensão contextual**: Entende relações entre componentes
- **Geração natural**: Produz texto fluido e compreensível
- **Escalabilidade**: Processa múltiplos repositórios simultaneamente

#### 6.3.2 Benefícios de Negócio
- **Redução de tempo**: Documentação em minutos vs. dias/semanas
- **Consistência**: Padrão uniforme para todos os projetos
- **Atualização fácil**: Reanálise rápida para novas versões
- **Acessibilidade**: Documentação técnica para não-especialistas

### 6.4 Considerações e Limitações

#### 6.4.1 Desafios Técnicos
- **Context window**: Limitação de tokens do modelo
- **Alucinações**: Possibilidade de informações incorretas
- **Performance**: Tempo de resposta dependente do hardware
- **Custo computacional**: Requer recursos significativos

#### 6.4.2 Mitigações Propostas
- **Context compression**: Técnicas de resumo e seleção de evidências
- **Validation layers**: Verificação cruzada de informações
- **Caching strategy**: Cache por commit hash para evitar reprocessamento
- **Progressive enhancement**: Começar com MVP e evoluir gradualmente

## 7. Jobs Assíncronos e Processamento

### 7.1 MVP (BackgroundTasks)
```python
@router.post("/analyses")
async def create_analysis(
    repo_id: int,
    background_tasks: BackgroundTasks
):
    job = create_job(repo_id)
    background_tasks.add_task(process_analysis, job.id)
    return job
```

### 7.2 Evolução (Celery/RQ)
```python
@celery.task(bind=True)
def process_analysis_task(self, job_id):
    job = get_job(job_id)
    
    # Etapa 1: Fetch
    self.update_state(state='PROGRESS', meta={'step': 'fetch'})
    fetch_repo(job.repository)
    
    # Etapa 2: Index
    self.update_state(state='PROGRESS', meta={'step': 'index'})
    index_repo(job.repository)
    
    # Etapa 3: LLM Analysis
    self.update_state(state='PROGRESS', meta={'step': 'llm'})
    generate_documentation(job)
    
    # Etapa 4: Save
    self.update_state(state='SUCCESS')
```

## 8. Rotas da API FastAPI

### 8.1 Autenticação
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `POST /auth/refresh`

### 8.2 Repositórios
- `GET /repos` - Listar repositórios do usuário
- `POST /repos` - Criar novo repositório
- `GET /repos/{id}` - Detalhes do repositório
- `DELETE /repos/{id}` - Remover repositório

### 8.3 Análises
- `POST /analyses` - Criar nova análise
- `GET /analyses` - Listar análises
- `GET /analyses/{id}` - Detalhes da análise
- `GET /analyses/{id}/status` - Status da análise
- `DELETE /analyses/{id}` - Cancelar/remover análise

### 8.4 Documentos
- `GET /documents/{id}` - Visualizar documento
- `GET /documents/{id}/download` - Download do documento
- `GET /documents/{id}/preview` - Preview HTML

## 9. Plano de Implementação

### Sprint 1: Base Web + Autenticação (2 semanas)
1. Configurar ambiente de desenvolvimento
2. Implementar FastAPI com autenticação JWT
3. Criar banco de dados com SQLAlchemy
4. Desenvolver frontend Flask básico
5. Implementar CRUD de repositórios

### Sprint 2: Pipeline GitHub (3 semanas)
6. Implementar fetch de repositórios via ZIP
7. Criar indexador de arquivos com limites
8. Desenvolver parser de README
9. Implementar detector de stack tecnológica
10. Testar pipeline completo sem IA

### Sprint 3: IA Generativa com Ollama (3 semanas)
11. Configurar ambiente Ollama local
12. Implementar cliente Ollama
13. Desenvolver context builder
14. Criar sistema de prompting
15. Implementar geração de documentação
16. Testar integração completa

### Sprint 4: Diagramas e PDF (2 semanas)
17. Implementar geração de diagramas Mermaid
18. Adicionar conversão MD → PDF
19. Melhorar validação de saída
20. Implementar sistema de cache
21. Testes finais e otimização

## 10. Considerações Finais e Próximos Passos

### 10.1 Fatores de Sucesso
- **Contexto compacto**: Evitar estouro de tokens
- **Output determinístico**: Parâmetros controlados
- **Validação rigorosa**: Prevenir alucinações
- **Logs completos**: Auditoria de processos

### 10.2 Possíveis Evoluções
- **Suporte a repositórios privados**: Com autenticação OAuth
- **Análise incremental**: Detectar mudanças desde última análise
- **Comparação de versões**: Diferenças entre commits
- **Integração CI/CD**: Geração automática em pipelines
- **Multi-model support**: Testar diferentes LLMs
- **Cloud deployment**: Escalonamento horizontal

### 10.3 Métricas de Sucesso
- Tempo médio de análise por repositório
- Precisão da documentação gerada (avaliação humana)
- Taxa de sucesso de geração
- Satisfação do usuário (pesquisas)
- Redução de tempo manual de documentação

## Conclusão

Esta proposta apresenta uma solução robusta e escalável para automação de documentação técnica usando IA generativa. A combinação de técnicas tradicionais de análise de código com capacidades avançadas de LLMs permite criar documentação técnica de alta qualidade de forma rápida e consistente.

A arquitetura modular permite evolução gradual, começando com um MVP funcional e expandindo para funcionalidades mais avançadas conforme a necessidade. A abordagem de "contexto compacto" garante eficiência e precisão, enquanto as camadas de validação e fallback asseguram confiabilidade do sistema.

A implementação desta ferramenta representa um avanço significativo na automação de processos de engenharia de software, potencialmente revolucionando a forma como equipes mantêm e documentam seus projetos de código aberto e proprietários.
