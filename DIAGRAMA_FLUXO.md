# Diagrama de Fluxo do Sistema - Formato Mermaid

Este arquivo contém diagramas em formato Mermaid que podem ser renderizados em ferramentas como:
- GitHub (renderização automática)
- VS Code (extensão Mermaid Preview)
- https://mermaid.live/
- Documentos LaTeX/Overleaf (com pacote mermaid)

## Diagrama de Fluxo Principal

```mermaid
flowchart TD
    A[Início: benchmark.py] --> B[Carregar Configuração]
    B --> C[Ler Tarefas tasks/*.json]
    B --> D[Ler Modelos config/models.yaml]
    
    C --> E[Para cada Tarefa task_01 a task_05]
    D --> E
    
    E --> F[Para cada IA 1 a 5]
    
    F --> G[Construir Prompt<br/>Linguagem Natural]
    G --> H[Chamar OpenRouter API]
    
    H --> I{Resposta<br/>Recebida?}
    I -->|Erro| J[Registrar Erro]
    I -->|Sucesso| K[Extrair Código ST<br/>de Blocos Markdown]
    
    K --> L[Validar Conteúdo]
    L --> M{Conteúdo<br/>Válido?}
    M -->|Não| J
    M -->|Sim| N[Salvar Arquivo .st<br/>results/raw_responses/]
    
    N --> O{Última IA?}
    O -->|Não| F
    O -->|Sim| P{Última Tarefa?}
    
    P -->|Não| E
    P -->|Sim| Q[Gerar Relatórios]
    
    Q --> R[summary.json]
    Q --> S[README_AVALIACAO.md]
    Q --> T[evaluation_template.json]
    
    R --> U[Fim: Códigos Prontos]
    S --> U
    T --> U
    
    U --> V[Avaliador Humano]
    V --> W[Para cada Código ST]
    W --> X[Compilar no OpenPLC]
    X --> Y{Compila?}
    Y -->|Não| Z[Registrar: compila=false]
    Y -->|Sim| AA[Executar no OpenPLC]
    AA --> BB{Executa<br/>Corretamente?}
    BB -->|Não| CC[Registrar: executa=false]
    BB -->|Sim| DD[Registrar: compila=true<br/>executa=true]
    
    Z --> EE{Último Código?}
    CC --> EE
    DD --> EE
    
    EE -->|Não| W
    EE -->|Sim| FF[Salvar evaluation_results.json]
    FF --> GG[Fim: Avaliação Completa]
```

## Diagrama de Arquitetura do Sistema

```mermaid
graph TB
    subgraph "Entrada"
        A[Tarefas JSON<br/>tasks/task_*.json]
        B[Configuração Modelos<br/>config/models.yaml]
        C[API Key OpenRouter<br/>.env]
    end
    
    subgraph "Processamento"
        D[benchmark.py<br/>Orquestrador Principal]
        E[OpenRouterClient<br/>ai/openrouter_client.py]
        F[OpenRouter API<br/>https://openrouter.ai]
    end
    
    subgraph "Armazenamento"
        G[Códigos ST Gerados<br/>results/raw_responses/]
        H[Relatórios<br/>results/summary.json]
        I[Template Avaliação<br/>results/evaluation_template.json]
    end
    
    subgraph "Avaliação Manual"
        J[Avaliador Humano]
        K[OpenPLC<br/>Compilador + Runtime]
        L[Resultados<br/>evaluation_results.json]
    end
    
    A --> D
    B --> D
    C --> E
    D --> E
    E --> F
    F -->|Código ST| E
    E -->|Salva| G
    D --> H
    D --> I
    G --> J
    I --> J
    J --> K
    K --> L
```

## Diagrama de Sequência: Geração de um Código

```mermaid
sequenceDiagram
    participant B as benchmark.py
    participant OC as OpenRouterClient
    participant OR as OpenRouter API
    participant FS as FileSystem
    participant AH as Avaliador Humano
    participant OP as OpenPLC
    
    B->>OC: run_all_models(task_prompt)
    loop Para cada IA
        OC->>OR: POST /chat/completions<br/>(model, prompt)
        OR-->>OC: Resposta JSON<br/>(código ST)
        OC->>OC: Extrair código de<br/>blocos markdown
        OC->>OC: Validar conteúdo
        OC->>FS: Salvar arquivo .st<br/>results/raw_responses/
    end
    OC-->>B: Retorna dict com códigos
    B->>FS: Gerar relatórios
    
    Note over AH,OP: Fase de Avaliação Manual
    AH->>FS: Ler arquivo .st
    AH->>OP: Compilar código
    OP-->>AH: Resultado compilação
    alt Compilou com sucesso
        AH->>OP: Executar programa
        OP-->>AH: Resultado execução
        AH->>FS: Registrar resultados<br/>evaluation_results.json
    else Erro de compilação
        AH->>FS: Registrar: compila=false
    end
```

## Diagrama de Estrutura de Dados

```mermaid
classDiagram
    class Tarefa {
        +string prompt
        +array tests
    }
    
    class Modelo {
        +string name
        +int max_tokens
    }
    
    class OpenRouterClient {
        +string api_key
        +array models
        +call_model()
        +run_all_models()
    }
    
    class Resultado {
        +string task_name
        +string model_name
        +string st_code
        +string file_path
    }
    
    class Avaliacao {
        +string data
        +string avaliador
        +bool compila
        +bool executa
        +string observacoes
    }
    
    Tarefa --> OpenRouterClient : usado como prompt
    Modelo --> OpenRouterClient : configuração
    OpenRouterClient --> Resultado : gera
    Resultado --> Avaliacao : avaliado por
```

## Diagrama de Estados: Processo de Avaliação

```mermaid
stateDiagram-v2
    [*] --> CodigoGerado: IA gera código ST
    
    CodigoGerado --> Compilando: Avaliador inicia
    
    Compilando --> ErroCompilacao: Erro sintático
    Compilando --> Compilado: Sucesso
    
    ErroCompilacao --> Registrado: compila=false
    Compilado --> Executando: Inicia execução
    
    Executando --> ErroExecucao: Comportamento incorreto
    Executando --> Executado: Resultado correto
    
    ErroExecucao --> Registrado: executa=false
    Executado --> Registrado: compila=true<br/>executa=true
    
    Registrado --> [*]: Avaliação completa
```

## Estatísticas do Benchmark

```mermaid
pie title Distribuição de Códigos Gerados
    "Task 01" : 5
    "Task 02" : 5
    "Task 03" : 5
    "Task 04" : 5
    "Task 05" : 5
```

```mermaid
pie title Distribuição por IA
    "kwaipilot/kat-coder-pro:free" : 5
    "google/gemma-3n-e4b-it:free" : 5
    "nvidia/nemotron-nano-12b-v2-vl:free" : 5
    "openai/gpt-oss-20b:free" : 5
    "z-ai/glm-4.5-air:free" : 5
```

## Como Usar Estes Diagramas

1. **Para GitHub**: Os diagramas Mermaid são renderizados automaticamente em arquivos `.md`
2. **Para LaTeX/Overleaf**: Use o pacote `mermaid` ou converta para imagem
3. **Para Apresentações**: Use https://mermaid.live/ para exportar como PNG/SVG
4. **Para Word**: Converta via https://mermaid.live/ e insira como imagem

