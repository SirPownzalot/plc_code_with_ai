# Guia de Instalação do OpenPLC no Windows

## 🎯 Objetivo

Instalar o OpenPLC completo (Runtime + Compilador) no Windows para usar com o benchmark.

---

## 📋 Opções de Instalação

### Opção 1: OpenPLC_v3 Completo (Recomendado)

**Vantagens:**
- Inclui Runtime + Compilador + Editor
- Tudo em um só lugar
- Mais fácil de gerenciar

**Desvantagens:**
- Instalação mais complexa
- Pode ter problemas com ambiente virtual Python

### Opção 2: Componentes Separados

**Vantagens:**
- Instalação mais simples
- Menos problemas de dependências

**Desvantagens:**
- Precisa instalar Runtime e Compilador separadamente
- Pode estar em locais diferentes

---

## 🚀 Instalação: Opção 1 - OpenPLC_v3 Completo

### Passo 1: Pré-requisitos

1. **Python 3.8+ instalado:**
   ```powershell
   python --version
   ```
   Se não tiver, baixe em: https://www.python.org/downloads/
   ⚠️ **IMPORTANTE:** Marque "Add Python to PATH" durante a instalação

2. **Git instalado:**
   ```powershell
   git --version
   ```
   Se não tiver, baixe em: https://git-scm.com/download/win

3. **Visual Studio Build Tools (opcional, para compilar):**
   - Baixe: https://visualstudio.microsoft.com/downloads/
   - Instale "Desktop development with C++"

### Passo 2: Clonar Repositório

```powershell
cd C:\
git clone https://github.com/thiagoralves/OpenPLC_v3.git
cd OpenPLC_v3
```

### Passo 3: Corrigir Problema do Ambiente Virtual

O erro que você teve (`/c/OpenPLC_v3/.venv/bin/python3: No such file or directory`) acontece porque o script tenta criar o ambiente virtual mas falha.

**Solução:**

1. **Criar ambiente virtual manualmente:**
   ```powershell
   cd C:\OpenPLC_v3
   python -m venv .venv --copies
   ```

2. **Ativar ambiente virtual:**
   ```powershell
   # PowerShell
   .\.venv\Scripts\Activate.ps1
   
   # Se der erro de política de execução, execute primeiro:
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   
   # Ou use CMD:
   .\.venv\Scripts\activate.bat
   ```

3. **Verificar se está ativo:**
   ```powershell
   python --version
   # Deve mostrar o Python do ambiente virtual
   ```

### Passo 4: Executar Instalação

**No Windows, use o script PowerShell:**

```powershell
# Com ambiente virtual ativado
.\install_windows.ps1
```

**Ou se não tiver script PowerShell, use o script bash (requer Git Bash ou WSL):**

```bash
# No Git Bash
./install.sh windows
```

**Se der erro, tente executar o background_installer.sh manualmente:**

```bash
# No Git Bash
bash background_installer.sh
```

### Passo 5: Verificar Instalação

Após a instalação, verifique:

```powershell
# Verificar se os componentes existem
Test-Path C:\OpenPLC_v3\webserver\iec2c.exe
Test-Path C:\OpenPLC_v3\runtime\openplc_runtime.exe
```

---

## 🚀 Instalação: Opção 2 - Componentes Separados

### Parte A: Instalar Runtime

1. **Baixar OpenPLC Runtime:**
   - Acesse: https://github.com/thiagoralves/OpenPLC_Runtime/releases
   - Baixe a versão mais recente para Windows
   - Extraia para `C:\OpenPLC_Runtime`

2. **Verificar instalação:**
   ```powershell
   Test-Path C:\OpenPLC_Runtime\OpenPLC_Runtime.exe
   ```

### Parte B: Instalar Compilador (MatIEC)

Você tem duas opções:

#### Opção B1: Usar Compilador do OpenPLC_v3

Se você já tem o OpenPLC_v3 instalado (mesmo que parcialmente):

```powershell
# O compilador deve estar em:
C:\OpenPLC_v3\webserver\iec2c.exe
```

#### Opção B2: Compilar MatIEC Separadamente

1. **Instalar MinGW ou MSYS2:**
   - MinGW: https://sourceforge.net/projects/mingw-w64/
   - MSYS2: https://www.msys2.org/

2. **Clonar e compilar MatIEC:**
   ```bash
   git clone https://github.com/beremiz/matiec.git
   cd matiec
   # Siga as instruções de compilação para Windows
   ```

3. **Copiar executável:**
   ```powershell
   # Copiar iec2c.exe para C:\OpenPLC_Runtime\
   copy matiec\iec2c.exe C:\OpenPLC_Runtime\iec2c.exe
   ```

#### Opção B3: Usar Compilador do Editor

Se você tem o OpenPLC Editor instalado:

```powershell
# O compilador deve estar em:
C:\Users\Matheus\OpenPLC_Editor\matiec\iec2c.exe
```

Você pode copiar para o Runtime:
```powershell
copy "C:\Users\Matheus\OpenPLC_Editor\matiec\iec2c.exe" "C:\OpenPLC_Runtime\iec2c.exe"
```

---

## ✅ Verificação Final

Execute o script de busca para verificar:

```powershell
python find_openplc.py
```

Deve mostrar:
- ✓ Runtime encontrado
- ✓ Compilador encontrado

---

## 🔧 Solução de Problemas Comuns

### Problema 1: Erro do Ambiente Virtual

**Erro:** `./background_installer.sh: line 281: /c/OpenPLC_v3/.venv/bin/python3: No such file or directory`

**Solução:**
```powershell
cd C:\OpenPLC_v3
python -m venv .venv --copies
.\.venv\Scripts\activate
# Depois execute o script novamente
```

### Problema 2: Script Não Encontrado

**Erro:** `install.sh: command not found`

**Solução:**
- Use Git Bash ou WSL
- Ou execute o script PowerShell: `.\install_windows.ps1`

### Problema 3: Permissões Negadas

**Erro:** `Permission denied`

**Solução:**
- Execute PowerShell como Administrador
- Ou ajuste permissões da pasta

### Problema 4: Python Não Encontrado

**Erro:** `python: command not found`

**Solução:**
1. Verifique se Python está no PATH:
   ```powershell
   $env:Path -split ';' | Select-String python
   ```

2. Adicione Python ao PATH manualmente se necessário

3. Reinicie o terminal após adicionar ao PATH

### Problema 5: Compilação Falha

**Erro:** Erros de compilação do MatIEC

**Solução:**
- Use o compilador pré-compilado do OpenPLC_v3
- Ou use o compilador do Editor (já compilado)

---

## 🎯 Configuração Rápida (Recomendada)

**Para seu caso específico, recomendo:**

1. **Manter Runtime em:** `C:\OpenPLC_Runtime`
2. **Usar compilador de:** `C:\OpenPLC_v3\webserver\iec2c.exe` (se disponível)
   - Ou: `C:\Users\Matheus\OpenPLC_Editor\matiec\iec2c.exe`

3. **Executar benchmark com:**
   ```powershell
   python benchmark.py `
     --openplc-path "C:/OpenPLC_Runtime" `
     --compiler-path "C:/OpenPLC_v3/webserver/iec2c.exe"
   ```

---

## 📝 Checklist de Instalação

- [ ] Python 3.8+ instalado e no PATH
- [ ] Git instalado
- [ ] OpenPLC Runtime instalado em `C:\OpenPLC_Runtime`
- [ ] Compilador disponível (OpenPLC_v3, Editor, ou MatIEC)
- [ ] `find_openplc.py` encontra ambos os componentes
- [ ] Benchmark executa sem erros

---

## 🆘 Ajuda Adicional

Se ainda tiver problemas:

1. **Execute diagnóstico:**
   ```powershell
   python find_openplc.py
   ```

2. **Verifique logs de instalação:**
   - Procure por arquivos `.log` na pasta do OpenPLC_v3

3. **Consulte documentação oficial:**
   - https://github.com/thiagoralves/OpenPLC_v3
   - https://openplcproject.com/

4. **Fóruns:**
   - https://openplc.discussion.community/

---

## 💡 Dica Final

Se a instalação completa do OpenPLC_v3 continuar dando problemas, a **abordagem mais simples** é:

1. ✅ Manter o Runtime que você já tem (`C:\OpenPLC_Runtime`)
2. ✅ Usar o compilador do Editor que já está funcionando
3. ✅ Especificar os caminhos manualmente no benchmark

Isso evita ter que lidar com problemas de instalação complexa!

