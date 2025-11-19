# Script PowerShell para ajudar na instalação do OpenPLC no Windows
# Execute: .\fix_openplc_install.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Assistente de Instalação OpenPLC" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar Python
Write-Host "[1/5] Verificando Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python não encontrado!" -ForegroundColor Red
    Write-Host "  Baixe em: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Verificar Git
Write-Host "[2/5] Verificando Git..." -ForegroundColor Yellow
try {
    $gitVersion = git --version 2>&1
    Write-Host "  ✓ Git encontrado: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Git não encontrado!" -ForegroundColor Red
    Write-Host "  Baixe em: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# Verificar se OpenPLC_v3 existe
Write-Host "[3/5] Verificando OpenPLC_v3..." -ForegroundColor Yellow
$openplcPath = "C:\OpenPLC_v3"
if (Test-Path $openplcPath) {
    Write-Host "  ✓ OpenPLC_v3 encontrado em: $openplcPath" -ForegroundColor Green
    
    # Verificar ambiente virtual
    $venvPath = Join-Path $openplcPath ".venv"
    if (-not (Test-Path $venvPath)) {
        Write-Host "  ⚠ Ambiente virtual não encontrado. Criando..." -ForegroundColor Yellow
        Set-Location $openplcPath
        python -m venv .venv --copies
        Write-Host "  ✓ Ambiente virtual criado" -ForegroundColor Green
    } else {
        Write-Host "  ✓ Ambiente virtual já existe" -ForegroundColor Green
    }
    
    # Verificar componentes
    $compiler = Join-Path $openplcPath "webserver\iec2c.exe"
    $runtime = Join-Path $openplcPath "runtime\openplc_runtime.exe"
    
    if (Test-Path $compiler) {
        Write-Host "  ✓ Compilador encontrado: $compiler" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Compilador não encontrado" -ForegroundColor Red
    }
    
    if (Test-Path $runtime) {
        Write-Host "  ✓ Runtime encontrado: $runtime" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Runtime não encontrado" -ForegroundColor Red
    }
} else {
    Write-Host "  ✗ OpenPLC_v3 não encontrado em: $openplcPath" -ForegroundColor Red
    Write-Host "  Deseja clonar? (S/N)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq "S" -or $response -eq "s") {
        Write-Host "  Clonando repositório..." -ForegroundColor Yellow
        git clone https://github.com/thiagoralves/OpenPLC_v3.git $openplcPath
        Write-Host "  ✓ Repositório clonado" -ForegroundColor Green
    }
}

# Verificar Runtime separado
Write-Host "[4/5] Verificando OpenPLC Runtime..." -ForegroundColor Yellow
$runtimePath = "C:\OpenPLC_Runtime"
if (Test-Path $runtimePath) {
    Write-Host "  ✓ Runtime encontrado em: $runtimePath" -ForegroundColor Green
    
    # Procurar executável do runtime
    $runtimeExe = Get-ChildItem -Path $runtimePath -Filter "*runtime*.exe" -ErrorAction SilentlyContinue
    if ($runtimeExe) {
        Write-Host "  ✓ Executável encontrado: $($runtimeExe.Name)" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Executável do runtime não encontrado" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✗ Runtime não encontrado em: $runtimePath" -ForegroundColor Red
}

# Verificar Editor
Write-Host "[5/5] Verificando OpenPLC Editor..." -ForegroundColor Yellow
$editorPath = "$env:USERPROFILE\OpenPLC_Editor"
if (Test-Path $editorPath) {
    Write-Host "  ✓ Editor encontrado em: $editorPath" -ForegroundColor Green
    
    $editorCompiler = Join-Path $editorPath "matiec\iec2c.exe"
    if (Test-Path $editorCompiler) {
        Write-Host "  ✓ Compilador do Editor encontrado: $editorCompiler" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Compilador do Editor não encontrado" -ForegroundColor Red
    }
} else {
    Write-Host "  ✗ Editor não encontrado" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Resumo" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para usar o benchmark, execute:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  python benchmark.py --openplc-path `"C:/OpenPLC_Runtime`"" -ForegroundColor White

if (Test-Path "C:\OpenPLC_v3\webserver\iec2c.exe") {
    Write-Host "    --compiler-path `"C:/OpenPLC_v3/webserver/iec2c.exe`"" -ForegroundColor White
} elseif (Test-Path "$env:USERPROFILE\OpenPLC_Editor\matiec\iec2c.exe") {
    Write-Host "    --compiler-path `"$env:USERPROFILE/OpenPLC_Editor/matiec/iec2c.exe`"" -ForegroundColor White
}

Write-Host ""
Write-Host "Ou execute o script de busca:" -ForegroundColor Yellow
Write-Host "  python find_openplc.py" -ForegroundColor White
Write-Host ""

