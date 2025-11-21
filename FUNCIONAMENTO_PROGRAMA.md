# Funcionamento do Sistema de Benchmark para Geração de Código ST

## Visão Geral

Este sistema realiza um benchmark automatizado para avaliar a capacidade de modelos de linguagem (LLMs) em gerar código Structured Text (ST) compatível com OpenPLC a partir de descrições em linguagem natural. O processo é dividido em fases automatizadas e uma fase final de avaliação manual.

## Arquitetura do Sistema

A arquitetura do sistema pode ser visualizada através do **Diagrama 1** (ver seção de Diagramas), que apresenta o fluxo completo desde a definição das tarefas até a avaliação manual dos resultados.

## Descrição Detalhada das Fases

### 1. Definição das Tarefas

As tarefas são definidas em arquivos JSON localizados no diretório `tasks/`. Cada arquivo contém:

- **Prompt**: Descrição em linguagem natural da funcionalidade desejada, especificando:
  - Uso de variáveis locais (sem entradas/saídas físicas)
  - Funcionalidade a ser implementada
  - Requisitos de compatibilidade com OpenPLC
  
- **Testes**: Casos de teste que definem os valores esperados (usados apenas como referência para o avaliador humano)

**Exemplo de Tarefa (task_01.json):**
```json
{
  "prompt": "Você deve gerar código Structured Text (ST) compatível com o OpenPLC. Use apenas variáveis locais (VAR ... END_VAR). Tarefa: implementar uma função que retorna TRUE quando duas variáveis booleanas locais (input1 e input2) forem ambas verdadeiras...",
  "tests": [
    { "inputs": {"input1":false, "input2":false}, "expected_outputs":{"output":false} },
    { "inputs": {"input1":true, "input2":false},  "expected_outputs":{"output":false} },
    { "inputs": {"input1":true, "input2":true},   "expected_outputs":{"output":true} }
  ]
}
```

**Tarefas Implementadas:**
1. **Task 01**: Lógica AND - Implementação de porta lógica AND com variáveis locais
2. **Task 02**: Latch/Selo - Implementação de circuito de selo (SET/RESET)
3. **Task 03**: Temporizador TON - Timer On Delay de 2 segundos
4. **Task 04**: Temporizador TOF - Timer Off Delay de 1 segundo
5. **Task 05**: Contador CTU - Contador crescente até 10

### 2. Escolha das IAs no OpenRouter

A seleção dos modelos de linguagem é realizada através do arquivo de configuração `config/models.yaml`. O OpenRouter é uma plataforma unificada que fornece acesso a múltiplos modelos de IA através de uma única API.

**Critérios de Seleção:**
- Modelos gratuitos disponíveis no OpenRouter
- Modelos testados e funcionais (verificados via `test_openrouter.py`)
- Diversidade de fornecedores (Kwaipilot, Google, NVIDIA, OpenAI, Z.AI)
- Capacidade de geração de código

**Modelos Selecionados:**
1. `kwaipilot/kat-coder-pro:free` - Especializado em geração de código
2. `google/gemma-3n-e4b-it:free` - Modelo Google otimizado para instruções
3. `nvidia/nemotron-nano-12b-v2-vl:free` - Modelo NVIDIA de 12B parâmetros
4. `openai/gpt-oss-20b:free` - Modelo open-source da OpenAI
5. `z-ai/glm-4.5-air:free` - Modelo Z.AI para tarefas gerais

**Processo de Validação:**
Antes da execução do benchmark, os modelos são testados através do script `test_openrouter.py`, que verifica:
- Disponibilidade do modelo na API
- Funcionamento da API key
- Capacidade de resposta do modelo

### 3. Execução da Tradução de Linguagem Natural em ST

O processo de tradução é executado pelo script principal `benchmark.py`, que orquestra as seguintes etapas:

#### 3.1. Inicialização
- Carrega configuração de modelos do `config/models.yaml`
- Valida API key do OpenRouter (variável de ambiente ou arquivo `.env`)
- Lê tarefas do diretório `tasks/`

#### 3.2. Geração de Códigos (Para cada tarefa × cada IA)

**3.2.1. Chamada à API OpenRouter**
```python
# Exemplo de requisição
POST https://openrouter.ai/api/v1/chat/completions
Headers:
  - Authorization: Bearer {API_KEY}
  - Content-Type: application/json
Body:
  {
    "model": "kwaipilot/kat-coder-pro:free",
    "messages": [{
      "role": "user",
      "content": "{prompt_da_tarefa}"
    }],
    "temperature": 0.0
  }
```

**3.2.2. Processamento da Resposta**
- A resposta da IA pode vir em diferentes formatos:
  - Código ST puro
  - Código dentro de blocos markdown (```st ... ```)
  - Texto explicativo + código
  
- O sistema extrai o código usando expressões regulares:
  ```python
  patterns = [
    r'```(?:st|structuredtext|structured_text|plc|openplc)\s*\n(.*?)```',
    r'```\s*\n(.*?)```',
    r'```(.*?)```'
  ]
  ```

**3.2.3. Validação e Armazenamento**
- Valida se o conteúdo não está vazio
- Remove espaços em branco desnecessários
- Sanitiza nome do arquivo (remove caracteres inválidos como `:`)
- Salva em: `results/raw_responses/{tarefa}/{modelo}.st`

**Exemplo de Código Gerado:**
```st
PROGRAM PLC_PRG
VAR
    input1 : BOOL;
    input2 : BOOL;
    output : BOOL;
END_VAR

IF (input1 AND input2) THEN
    output := TRUE;
ELSE
    output := FALSE;
END_IF;
END_PROGRAM
```

#### 3.3. Geração de Relatórios
Ao final do processamento, o sistema gera:
- `summary.json`: Resumo estatístico (quantos códigos gerados por tarefa/IA)
- `README_AVALIACAO.md`: Guia para o avaliador humano
- `evaluation_template.json`: Template para registro dos resultados

### 4. Organização dos Resultados

A estrutura de resultados é organizada hierarquicamente:

```
results/
├── raw_responses/              # Códigos ST gerados
│   ├── task_01/
│   │   ├── kwaipilot_kat-coder-pro_free.st
│   │   ├── google_gemma-3n-e4b-it_free.st
│   │   ├── nvidia_nemotron-nano-12b-v2-vl_free.st
│   │   ├── openai_gpt-oss-20b_free.st
│   │   └── z-ai_glm-4.5-air_free.st
│   ├── task_02/
│   │   └── ...
│   └── ...
├── summary.json                 # Estatísticas do benchmark
├── README_AVALIACAO.md         # Guia de avaliação
└── evaluation_template.json    # Template para resultados
```

**Total de Códigos Gerados:**
- 5 tarefas × 5 IAs = **25 códigos ST**

### 5. Avaliação Manual pelo Agente Humano

A fase final de avaliação é realizada manualmente por um agente humano especializado, seguindo os critérios estabelecidos.

#### 5.1. Processo de Avaliação

Para cada código ST gerado, o avaliador:

1. **Abre o arquivo** `.st` correspondente
2. **Compila no OpenPLC**:
   - Copia o código para o OpenPLC
   - Executa o compilador MatIEC
   - Verifica se há erros de sintaxe ou semântica
   - Registra: `compila: true/false`
3. **Executa no OpenPLC** (se compilou com sucesso):
   - Carrega o programa compilado no runtime
   - Testa com diferentes valores de entrada
   - Verifica se o comportamento corresponde ao esperado
   - Registra: `executa: true/false`
4. **Registra Observações**:
   - Erros encontrados
   - Comportamentos inesperados
   - Qualidade do código gerado

#### 5.2. Critérios de Avaliação

**Compila Corretamente:**
- ✅ O código compila sem erros no OpenPLC
- ❌ O código apresenta erros de compilação (sintaxe, tipos, etc.)

**Executa Corretamente:**
- ✅ O código executa e produz os resultados esperados
- ❌ O código não executa ou produz resultados incorretos

#### 5.3. Registro dos Resultados

Os resultados são registrados no arquivo `evaluation_results.json` (criado a partir do template), seguindo a estrutura:

```json
{
  "avaliacao": {
    "data": "2024-01-15",
    "avaliador": "Nome do Avaliador",
    "criteria": "Compila e Executa Corretamente"
  },
  "resultados": {
    "task_01": {
      "kwaipilot_kat-coder-pro_free": {
        "compila": true,
        "executa": true,
        "observacoes": "Código correto e bem estruturado"
      },
      ...
    },
    ...
  }
}
```

## Fluxo de Dados Completo

O fluxo completo de dados do sistema está representado no **Diagrama 2** (ver arquivo `DIAGRAMAS_TCC.md`), mostrando a interação entre os componentes do sistema, desde a entrada (tarefas e configuração) até a saída (resultados da avaliação).

## Vantagens da Abordagem

1. **Automatização**: Geração de 25 códigos de forma automatizada
2. **Reprodutibilidade**: Mesmas tarefas testadas em todas as IAs
3. **Avaliação Consistente**: Critérios claros e padronizados
4. **Escalabilidade**: Fácil adicionar novas tarefas ou IAs
5. **Rastreabilidade**: Todos os códigos gerados são armazenados para análise posterior

## Limitações e Considerações

1. **Avaliação Manual**: Requer tempo do avaliador humano
2. **Subjetividade**: Avaliação pode variar entre avaliadores
3. **Dependência de API**: Requer conexão com OpenRouter
4. **Custos**: Modelos gratuitos têm limitações de taxa e uso

## Conclusão

Este sistema fornece uma estrutura completa para avaliar a capacidade de modelos de linguagem em gerar código ST a partir de descrições em linguagem natural. A combinação de automação na geração e avaliação manual garante tanto eficiência quanto precisão na análise dos resultados.

