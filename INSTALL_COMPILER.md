# Guia de Instalação do Compilador OpenPLC

Se você já tem o OpenPLC Runtime instalado mas está faltando o compilador, aqui estão as opções:

## Opção 1: Usar o Compilador do Editor (se disponível)

Se você tem o OpenPLC Editor instalado, ele pode ter o compilador integrado. Execute:

```bash
python find_openplc.py
```

O script irá verificar se o Editor tem o compilador disponível.

## Opção 2: Instalar MatIEC Separadamente (Recomendado)

O MatIEC é o compilador usado pelo OpenPLC. Você pode instalá-lo separadamente:

### Windows:

1. **Baixar MatIEC pré-compilado:**
   - Procure por "MatIEC Windows binary" ou "MatIEC precompiled Windows"
   - Ou compile a partir do código-fonte

2. **Compilar MatIEC a partir do código-fonte:**
   ```bash
   # Requer: MinGW ou MSYS2
   git clone https://github.com/beremiz/matiec.git
   cd matiec
   # Siga as instruções de compilação para Windows
   ```

3. **Colocar o compilador em um local acessível:**
   - Coloque o executável `iec2c.exe` em `C:\OpenPLC_Runtime\` ou
   - Configure o caminho no código

## Opção 3: Corrigir Instalação do OpenPLC_v3

Se você quer instalar o OpenPLC_v3 completo mas está tendo problemas:

### Solução para o erro do ambiente virtual:

1. **Navegue até o diretório do OpenPLC_v3:**
   ```bash
   cd C:\OpenPLC_v3
   ```

2. **Crie o ambiente virtual manualmente:**
   ```bash
   python -m venv .venv --copies
   ```

3. **Ative o ambiente virtual:**
   ```bash
   # PowerShell
   .\.venv\Scripts\Activate.ps1
   
   # CMD
   .\.venv\Scripts\activate.bat
   ```

4. **Execute o script de instalação novamente:**
   ```bash
   ./background_installer.sh
   ```

### Alternativa: Usar WSL (Windows Subsystem for Linux)

Se você tem WSL instalado, pode ser mais fácil instalar o OpenPLC no ambiente Linux:

```bash
# No WSL
git clone https://github.com/thiagoralves/OpenPLC_v3.git
cd OpenPLC_v3
./install.sh linux
```

Depois, configure o caminho no Windows apontando para o WSL.

## Opção 4: Usar Docker (Avançado)

Se você tem Docker instalado, pode usar uma imagem do OpenPLC:

```bash
docker pull thiagoralves/openplc
```

## Verificação

Após instalar o compilador, execute:

```bash
python find_openplc.py
```

O script deve encontrar tanto o Runtime quanto o Compilador.

## Configuração Manual do Caminho do Compilador

Se você instalou o compilador em um local diferente, você pode:

1. **Criar um link simbólico ou copiar o compilador para o diretório do Runtime:**
   ```bash
   # Copiar iec2c.exe para C:\OpenPLC_Runtime\
   copy C:\caminho\para\iec2c.exe C:\OpenPLC_Runtime\iec2c.exe
   ```

2. **Ou modificar o código para procurar em locais adicionais**

## Ajuda Adicional

Se nenhuma dessas opções funcionar, você pode:
- Verificar os fóruns do OpenPLC: https://openplc.discussion.community/
- Abrir uma issue no repositório do OpenPLC
- Verificar a documentação oficial: https://openplcproject.com/

