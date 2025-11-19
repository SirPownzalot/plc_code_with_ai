# Benchmark-ST-OpenPLC

Benchmark automatizado para avaliação de modelos de linguagem (LLMs) na geração de código Structured Text (ST) compatível com **OpenPLC** utilizando o **OpenRouter API**.

Este projeto executa o pipeline completo:

1. Lê uma bateria de tarefas em NL (descrições de funções típicas de CLP).
2. Envia cada tarefa para múltiplos modelos configurados no OpenRouter.
3. Armazena localmente cada código ST retornado.
4. Compila e executa cada código no **OpenPLC Runtime**, controlando via **Modbus/TCP**.
5. Avalia automaticamente cada implementação com base nos testes definidos.
6. Gera relatórios de performance e correção para cada modelo.

---

## 📦 Requisitos

- Python 3.10+
- OpenPLC instalado localmente (Runtime + Compiler)
- Modbus/TCP ativo (porta 502)
- Conta no OpenRouter com API Key

### Dependências Python

```bash
pip install -r requirements.txt
```

---

## 🚀 Instalação

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd PLC_Ai_Code
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure a API Key do OpenRouter:

   **Opção 1: Arquivo .env (recomendado)**
   
   Crie um arquivo `.env` na raiz do projeto:
   ```env
   OPENROUTER_API_KEY=sua_chave_aqui
   OPENPLC_PATH=C:/OpenPLC  # Opcional, apenas se necessário
   ```
   
   Obtenha sua chave em: https://openrouter.ai/keys

   **Opção 2: Variável de ambiente**
   ```bash
   # Linux/Mac
   export OPENROUTER_API_KEY=sua_chave_aqui
   
   # Windows (PowerShell)
   $env:OPENROUTER_API_KEY="sua_chave_aqui"
   ```

4. Configure os modelos em `config/models.yaml`:
   - Por padrão, o projeto tenta usar modelos sem sufixo `:free`
   - Você pode adicionar qualquer modelo disponível no OpenRouter
   - Modelos gratuitos têm limitações (20 req/min, 50 chamadas/dia)

5. **Teste a conexão com OpenRouter** (recomendado):
   ```bash
   python test_openrouter.py
   ```
   Este script lista os modelos disponíveis e testa a conexão. Use-o para descobrir os nomes corretos dos modelos.

---

## 📝 Uso

### Execução Básica

Execute o benchmark com o comando:

```bash
python benchmark.py
```

### Opções de Linha de Comando

```bash
python benchmark.py --help
```

Opções disponíveis:
- `--openplc-path`: Caminho para instalação do OpenPLC (opcional, tenta detectar automaticamente)
- `--tasks-dir`: Diretório contendo as tarefas JSON (padrão: `tasks`)
- `--results-dir`: Diretório para salvar resultados (padrão: `results`)

### Exemplos

```bash
# Execução padrão
python benchmark.py

# Especificar caminho do OpenPLC
python benchmark.py --openplc-path "C:/OpenPLC"

# Usar diretório customizado de tarefas
python benchmark.py --tasks-dir "minhas_tarefas" --results-dir "meus_resultados"
```

---

## 📁 Estrutura do Projeto

```
PLC_Ai_Code/
├── ai/
│   └── openrouter_client.py    # Cliente para API OpenRouter
├── openplc/
│   └── runner.py                # Executor de programas OpenPLC
├── config/
│   └── models.yaml              # Configuração de modelos
├── tasks/                       # Tarefas de benchmark (JSON)
│   ├── task_01.json
│   ├── task_02.json
│   └── ...
├── results/                     # Resultados gerados
│   ├── raw_responses/          # Códigos ST brutos das IAs
│   └── evaluations/            # Resultados das avaliações
├── benchmark.py                 # Programa principal
├── evaluator.py                 # Módulo de avaliação
├── requirements.txt
└── README.md
```

---

## 📋 Formato das Tarefas

Cada tarefa é um arquivo JSON com a seguinte estrutura:

```json
{
  "prompt": "Descrição da tarefa em linguagem natural",
  "tests": [
    {
      "inputs": {"0": false, "1": false},
      "expected_outputs": {"0": false},
      "wait": 0.1
    }
  ]
}
```

- `prompt`: Descrição da tarefa que será enviada para as IAs
- `tests`: Array de casos de teste
  - `inputs`: Valores de entrada (endereços IEC como strings)
  - `expected_outputs`: Valores esperados nas saídas
  - `wait`: Tempo de espera em segundos antes de ler as saídas

---

## 📊 Resultados

Os resultados são salvos em `results/`:

- `raw_responses/`: Códigos ST gerados pelas IAs (um arquivo `.st` por modelo)
- `evaluations/`: Resultados das avaliações (arquivos JSON com scores e detalhes)

Cada arquivo de avaliação contém:
```json
{
  "score": 0.85,
  "results": [
    {
      "inputs": {...},
      "expected": {...},
      "got": {...},
      "correct": {...}
    }
  ]
}
```

---

## ⚙️ Configuração do OpenPLC

### Encontrando sua Instalação

Se você não sabe onde está instalado o OpenPLC, execute o script de busca:

```bash
python find_openplc.py
```

Este script irá:
- Procurar instalações do OpenPLC em locais comuns
- Listar os componentes encontrados (Runtime, Compilador, Editor)
- Mostrar quais instalações estão completas ou incompletas
- Fornecer recomendações específicas para sua situação

### Detecção Automática

O programa tenta detectar automaticamente o OpenPLC nos seguintes locais:

**Linux:**
- `/usr/local/openplc`
- `/opt/openplc`
- `$HOME/openplc`
- Variável de ambiente `OPENPLC_PATH`

**Windows:**
- `C:/OpenPLC_Runtime` (instalação comum do Runtime)
- `C:/OpenPLC`
- `C:/OpenPLC_v3`
- `C:/Program Files/OpenPLC`
- `C:/Program Files/OpenPLC_Runtime`
- `$HOME/OpenPLC`
- Variável de ambiente `OPENPLC_PATH`

### Estrutura do OpenPLC

O OpenPLC pode ter diferentes estruturas de instalação:

1. **OpenPLC_v3 completo** (recomendado)
   - Contém: Runtime + Compilador + Editor
   - Compilador pode estar em: `compiler/openplc` ou `webserver/core/matiec/iec2c`
   - Download: https://github.com/thiagoralves/OpenPLC_v3

2. **OpenPLC Runtime apenas**
   - Contém apenas o runtime (pode não ter compilador separado)
   - Pode precisar do compilador MatIEC instalado separadamente

3. **OpenPLC Editor**
   - Interface gráfica para edição
   - Compilador pode estar integrado no editor

### Configuração Manual

Se o OpenPLC não for detectado automaticamente:

1. **Definir variável de ambiente:**
   ```bash
   # Linux/Mac
   export OPENPLC_PATH=/caminho/para/openplc
   
   # Windows (PowerShell)
   $env:OPENPLC_PATH="C:\caminho\para\OpenPLC"
   
   # Windows (CMD)
   set OPENPLC_PATH=C:\caminho\para\OpenPLC
   ```

2. **Usar o parâmetro `--openplc-path`:**
   ```bash
   python benchmark.py --openplc-path "C:/caminho/para/OpenPLC"
   ```

3. **Usar componentes de instalações diferentes:**
   Se você tem o Runtime em um local e o Compilador em outro (comum no Windows):
   ```bash
   python benchmark.py \
     --openplc-path "C:/OpenPLC_Runtime" \
     --compiler-path "C:/OpenPLC_v3/webserver/iec2c.exe" \
     --runtime-path "C:/OpenPLC_Runtime/OpenPLC_Runtime.exe"
   ```
   
   Ou usando o compilador do Editor:
   ```bash
   python benchmark.py \
     --openplc-path "C:/OpenPLC_Runtime" \
     --compiler-path "C:/Users/Matheus/OpenPLC_Editor/matiec/iec2c.exe"
   ```

---

## 🔧 Solução de Problemas

### Erro 404: "Modelo não encontrado"

Se você receber erros 404 ao tentar usar os modelos, execute o script de teste para verificar:

```bash
python test_openrouter.py
```

Este script irá:
- Listar todos os modelos disponíveis no OpenRouter
- Testar diferentes formatos de nomes de modelos
- Mostrar quais modelos funcionam com sua API key

**Soluções comuns:**
- Os nomes dos modelos podem ter mudado - use o script de teste para descobrir os nomes corretos
- Alguns modelos podem não estar mais disponíveis
- Verifique se sua API key tem permissão para usar modelos gratuitos
- Tente remover o sufixo `:free` do nome do modelo
- Atualize o arquivo `config/models.yaml` com os nomes corretos

### Erro: "API Key do OpenRouter não configurada"
- Verifique se o arquivo `.env` existe e contém `OPENROUTER_API_KEY`
- Ou configure a variável de ambiente `OPENROUTER_API_KEY`
- Execute `python test_openrouter.py` para verificar se a chave está funcionando

### Erro: "OpenPLC não encontrado" ou "Compilador não encontrado"

**Se você tem apenas o Runtime instalado:**

O benchmark precisa do compilador para converter código ST em código executável. Você tem algumas opções:

1. **Verificar se o Editor tem o compilador:**
   ```bash
   python find_openplc.py
   ```
   O script verificará se o Editor (se instalado) tem o compilador integrado.

2. **Instalar o compilador MatIEC separadamente:**
   - Veja o guia completo em `INSTALL_COMPILER.md`
   - Baixe ou compile o MatIEC (compilador IEC 61131-3)
   - Coloque `iec2c.exe` no diretório do Runtime

3. **Corrigir instalação do OpenPLC_v3:**
   - Se você tentou instalar o OpenPLC_v3 completo mas teve erros, veja `INSTALL_COMPILER.md` para soluções
   - O erro comum do ambiente virtual pode ser resolvido criando o `.venv` manualmente

4. **Usar variável de ambiente ou parâmetro:**
   ```bash
   # Configure o caminho
   python benchmark.py --openplc-path "C:/OpenPLC_Runtime"
   ```

### Erro: "Não foi possível conectar ao OpenPLC via Modbus/TCP"
- Verifique se o OpenPLC Runtime está rodando
- Confirme que a porta 502 está disponível
- Verifique se não há firewall bloqueando a conexão

### Erro de compilação do código ST
- Verifique os logs de erro do compilador
- Os códigos gerados pelas IAs podem conter erros de sintaxe
- Revise os arquivos em `results/raw_responses/`

---

## 📝 Notas

- Modelos gratuitos no OpenRouter têm limitações de taxa e uso diário
- O programa continua executando mesmo se um modelo falhar
- Resultados de erro são salvos com score 0.0 para análise posterior
- O programa suporta Windows e Linux (caminhos detectados automaticamente)

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou pull requests.

---

## 📄 Licença

[Adicione informações de licença aqui]
