# Como o Programa Interage com I/Os do PLC

## 📋 Visão Geral

O programa usa **Modbus/TCP** para interagir com as I/Os do OpenPLC. A comunicação acontece através de **coils Modbus**, que são mapeados para os endereços IEC do código ST.

---

## 🔄 Fluxo Completo

### 1. **Preparação do Programa ST**

O código ST gerado pelas IAs usa endereços IEC padrão:
- **Entradas:** `%IX0.0`, `%IX0.1`, `%IX1.0`, etc.
- **Saídas:** `%QX0.0`, `%QX0.1`, `%QX1.0`, etc.

**Exemplo de código ST:**
```st
%QX0.0 := %IX0.0 AND %IX0.1;
```

### 2. **Compilação**

O compilador MatIEC converte o código ST em código C executável, mantendo o mapeamento dos endereços IEC.

### 3. **Execução no Runtime**

O OpenPLC Runtime executa o programa compilado e expõe as I/Os via **Modbus/TCP na porta 502**.

### 4. **Mapeamento IEC → Modbus**

O OpenPLC mapeia os endereços IEC para coils Modbus:

| Endereço IEC | Tipo | Coil Modbus | Descrição |
|--------------|------|-------------|-----------|
| `%IX0.0` | Entrada Digital | Coil 0 | Primeira entrada digital |
| `%IX0.1` | Entrada Digital | Coil 1 | Segunda entrada digital |
| `%IX1.0` | Entrada Digital | Coil 8 | Entrada do byte 1 |
| `%QX0.0` | Saída Digital | Coil 0 | Primeira saída digital |
| `%QX0.1` | Saída Digital | Coil 1 | Segunda saída digital |

**Nota:** O mapeamento pode variar dependendo da configuração do OpenPLC. O padrão é:
- **Entradas:** `%IX<byte>.<bit>` → Coil `(byte * 8) + bit`
- **Saídas:** `%QX<byte>.<bit>` → Coil `(byte * 8) + bit`

---

## 💻 Implementação no Código

### Arquivo: `openplc/runner.py`

#### **Conexão Modbus/TCP**

```python
# Conecta ao OpenPLC via Modbus/TCP (porta 502)
client = ModbusTcpClient("127.0.0.1", port=502)
client.connect()
```

#### **Escrevendo Entradas (Inputs)**

```python
for i, val in inputs.items():
    addr = int(i)  # Converte string "0" para inteiro 0
    result = client.write_coil(addr, val)  # Escreve TRUE ou FALSE
```

**Exemplo:**
- `inputs = {"0": true, "1": false}`
- Escreve `TRUE` no coil 0 (equivale a `%IX0.0 = TRUE`)
- Escreve `FALSE` no coil 1 (equivale a `%IX0.1 = FALSE`)

#### **Lendo Saídas (Outputs)**

```python
for o in expected.keys():
    addr = int(o)  # Converte string "0" para inteiro 0
    result = client.read_coils(addr, 1)  # Lê 1 coil
    out_states[o] = result.bits[0]  # Extrai o valor (True/False)
```

**Exemplo:**
- `expected_outputs = {"0": true}`
- Lê o coil 0 (equivale a `%QX0.0`)
- Compara com o valor esperado

---

## 📝 Formato das Tarefas (JSON)

### Estrutura do Arquivo de Tarefa

```json
{
  "prompt": "Descrição da tarefa...",
  "tests": [
    {
      "inputs": {"0": false, "1": false},
      "expected_outputs": {"0": false},
      "wait": 0.1
    }
  ]
}
```

### Mapeamento de Endereços

**No JSON:**
- `"0"` = Coil 0 = `%IX0.0` (entrada) ou `%QX0.0` (saída)
- `"1"` = Coil 1 = `%IX0.1` (entrada) ou `%QX0.1` (saída)
- `"8"` = Coil 8 = `%IX1.0` (entrada) ou `%QX1.0` (saída)

**Fórmula:**
```
Coil = (byte * 8) + bit
```

**Exemplos:**
- `%IX0.0` → Coil 0 = (0 * 8) + 0 = 0
- `%IX0.1` → Coil 1 = (0 * 8) + 1 = 1
- `%IX1.0` → Coil 8 = (1 * 8) + 0 = 8
- `%QX2.3` → Coil 19 = (2 * 8) + 3 = 19

---

## 🔍 Exemplo Completo

### Tarefa: `task_01.json`

```json
{
  "prompt": "Acender %QX0.0 quando %IX0.0 e %IX0.1 forem verdadeiros",
  "tests": [
    { "inputs": {"0": false, "1": false}, "expected_outputs": {"0": false}, "wait": 0.1 },
    { "inputs": {"0": true, "1": false},  "expected_outputs": {"0": false}, "wait": 0.1 },
    { "inputs": {"0": true, "1": true},   "expected_outputs": {"0": true},  "wait": 0.1 }
  ]
}
```

### Execução Passo a Passo

**Teste 1:**
1. ✅ Escreve `%IX0.0 = FALSE` (coil 0 = false)
2. ✅ Escreve `%IX0.1 = FALSE` (coil 1 = false)
3. ⏱️ Aguarda 0.1 segundos (permite o PLC processar)
4. ✅ Lê `%QX0.0` (coil 0)
5. ✅ Compara: esperado `FALSE`, obtido `FALSE` → ✅ Correto

**Teste 2:**
1. ✅ Escreve `%IX0.0 = TRUE` (coil 0 = true)
2. ✅ Escreve `%IX0.1 = FALSE` (coil 1 = false)
3. ⏱️ Aguarda 0.1 segundos
4. ✅ Lê `%QX0.0` (coil 0)
5. ✅ Compara: esperado `FALSE`, obtido `FALSE` → ✅ Correto

**Teste 3:**
1. ✅ Escreve `%IX0.0 = TRUE` (coil 0 = true)
2. ✅ Escreve `%IX0.1 = TRUE` (coil 1 = true)
3. ⏱️ Aguarda 0.1 segundos
4. ✅ Lê `%QX0.0` (coil 0)
5. ✅ Compara: esperado `TRUE`, obtido `TRUE` → ✅ Correto

---

## ⚙️ Detalhes Técnicos

### Protocolo Modbus

- **Função 05 (Write Single Coil):** Usada para escrever entradas
  ```python
  client.write_coil(address, value)  # value = True ou False
  ```

- **Função 01 (Read Coils):** Usada para ler saídas
  ```python
  result = client.read_coils(address, count)  # count = número de coils
  value = result.bits[0]  # Extrai o primeiro bit
  ```

### Timing e Sincronização

```python
time.sleep(step.get("wait", 0.1))  # Aguarda antes de ler
```

**Por que esperar?**
- O PLC precisa processar o ciclo de varredura
- Garante que as saídas foram atualizadas
- Evita leituras prematuras

### Tratamento de Erros

```python
if hasattr(result, 'isError') and result.isError():
    raise RuntimeError(f"Erro ao escrever coil {addr}: {result}")
```

O código verifica erros em cada operação Modbus para garantir que:
- As escritas foram bem-sucedidas
- As leituras retornaram dados válidos
- A conexão está estável

---

## 📊 Avaliação dos Resultados

### Arquivo: `evaluator.py`

```python
def score_results(results):
    total = 0
    ok = 0
    
    for r in results:
        for bit, right in r["correct"].items():
            total += 1
            if right:
                ok += 1
    
    return ok / total if total > 0 else 0.0
```

**Exemplo de resultado:**
```json
{
  "score": 0.85,
  "results": [
    {
      "inputs": {"0": false, "1": false},
      "expected": {"0": false},
      "got": {"0": false},
      "correct": {"0": true}  // ✅ Correto!
    },
    {
      "inputs": {"0": true, "1": true},
      "expected": {"0": true},
      "got": {"0": false},  // ❌ Errado!
      "correct": {"0": false}
    }
  ]
}
```

**Score:** 1/2 = 0.5 (50% de acerto)

---

## ⚠️ Limitações e Considerações

### 1. **Apenas I/Os Digitais**

Atualmente, o código suporta apenas:
- ✅ Entradas digitais (`%IX`)
- ✅ Saídas digitais (`%QX`)

**Não suporta (ainda):**
- ❌ Entradas analógicas (`%IW`, `%ID`)
- ❌ Saídas analógicas (`%QW`, `%QD`)
- ❌ Memórias internas (`%M`, `%MW`)

### 2. **Mapeamento Fixo**

O mapeamento assume que:
- Coil 0 = `%IX0.0` ou `%QX0.0`
- Coil 1 = `%IX0.1` ou `%QX0.1`
- etc.

**Se o OpenPLC estiver configurado diferente, pode precisar ajustar.**

### 3. **Timing**

O tempo de espera (`wait`) é fixo por teste. Para lógicas com timers:
- Pode precisar aumentar o `wait`
- Ou adicionar múltiplas leituras ao longo do tempo

### 4. **Endereçamento**

Os endereços no JSON são strings que representam o número do coil:
- `"0"` = Coil 0
- `"1"` = Coil 1
- `"8"` = Coil 8

**Para endereços mais complexos, pode precisar ajustar a conversão.**

---

## 🔧 Possíveis Melhorias

### 1. **Suporte a I/Os Analógicos**

```python
# Ler entrada analógica
result = client.read_holding_registers(0, 1)  # Lê 1 registro (16 bits)
value = result.registers[0]  # Valor analógico
```

### 2. **Mapeamento Configurável**

Criar arquivo de configuração para mapear endereços IEC → Coils Modbus:
```yaml
mapping:
  inputs:
    "%IX0.0": 0
    "%IX0.1": 1
  outputs:
    "%QX0.0": 0
    "%QX0.1": 1
```

### 3. **Leitura Contínua**

Para timers e contadores, ler múltiplas vezes:
```python
for t in range(0, 3, 0.1):  # A cada 0.1s por 3s
    time.sleep(0.1)
    value = client.read_coils(addr, 1)
    # Armazena histórico
```

### 4. **Validação de Endereços**

Verificar se os endereços no JSON são válidos antes de executar.

---

## 📚 Referências

- **Modbus Protocol:** https://modbus.org/docs/Modbus_Application_Protocol_V1_1b3.pdf
- **IEC 61131-3:** Padrão para linguagens de programação de CLPs
- **OpenPLC Documentation:** https://openplcproject.com/
- **pymodbus Library:** https://pymodbus.readthedocs.io/

---

## 🎯 Resumo

1. **Código ST** usa endereços IEC (`%IX`, `%QX`)
2. **Compilador** converte para código executável
3. **Runtime** expõe I/Os via **Modbus/TCP (porta 502)**
4. **Python** escreve entradas e lê saídas usando **pymodbus**
5. **Avaliação** compara resultados esperados vs obtidos
6. **Score** calcula porcentagem de acerto

O sistema é **automatizado** e **repetível**, permitindo testar múltiplos modelos de IA na mesma bateria de testes.

