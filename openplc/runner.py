import time
import subprocess
import json
import os
import platform
from pathlib import Path

try:
    from pymodbus.client import ModbusTcpClient
except ImportError:
    # Fallback para versão antiga do pymodbus
    from pymodbus.client.sync import ModbusTcpClient

class OpenPLCRunner:
    def __init__(self, openplc_path=None, compiler_path=None, runtime_path=None):
        """
        Inicializa o runner do OpenPLC.
        
        Args:
            openplc_path: Caminho base para instalação do OpenPLC. 
                         Se None, tenta detectar automaticamente.
            compiler_path: Caminho direto para o compilador (opcional, sobrescreve detecção)
            runtime_path: Caminho direto para o runtime (opcional, sobrescreve detecção)
        """
        self.compiler_path_override = Path(compiler_path) if compiler_path else None
        self.runtime_path_override = Path(runtime_path) if runtime_path else None
        
        if openplc_path:
            self.openplc_path = Path(openplc_path)
            if not self.openplc_path.exists():
                raise FileNotFoundError(
                    f"Caminho do OpenPLC não existe: {self.openplc_path}\n"
                    f"Verifique se o caminho está correto."
                )
        else:
            # Detecção automática baseada no OS
            if platform.system() == "Windows":
                # Caminhos comuns no Windows
                possible_paths = [
                    Path(os.environ.get("OPENPLC_PATH", "")),
                    Path("C:/OpenPLC_Runtime"),  # Instalação comum do Runtime
                    Path("C:/OpenPLC"),
                    Path("C:/OpenPLC_v3"),
                    Path("C:/Program Files/OpenPLC"),
                    Path("C:/Program Files/OpenPLC_Runtime"),
                    Path("C:/Program Files (x86)/OpenPLC"),
                    Path("C:/Program Files (x86)/OpenPLC_Runtime"),
                    Path.home() / "OpenPLC",
                    Path.home() / "OpenPLC_Runtime",
                    Path.home() / "Documents" / "OpenPLC",
                    Path(".") / "OpenPLC",  # Pasta atual
                ]
            else:
                # Caminhos comuns no Linux
                possible_paths = [
                    Path(os.environ.get("OPENPLC_PATH", "")),
                    Path("/usr/local/openplc"),
                    Path("/opt/openplc"),
                    Path("/usr/openplc"),
                    Path.home() / "openplc",
                    Path.home() / "OpenPLC",
                    Path(".") / "openplc",  # Pasta atual
                ]
            
            self.openplc_path = None
            for path in possible_paths:
                if path and path.exists() and path.is_dir():
                    # Verifica se tem runtime (prioridade) ou compilador
                    runtime_names = [
                        "OpenPLC_Runtime.exe" if platform.system() == "Windows" else "OpenPLC_Runtime",
                        "openplc_runtime.exe" if platform.system() == "Windows" else "openplc_runtime",
                        "runtime.exe" if platform.system() == "Windows" else "runtime",
                    ]
                    
                    has_runtime = False
                    for name in runtime_names:
                        if (path / name).exists() or (path / "runtime" / name).exists():
                            has_runtime = True
                            break
                    
                    compiler = path / "compiler" / ("openplc.exe" if platform.system() == "Windows" else "openplc")
                    matiec = path / "webserver" / "iec2c.exe" if platform.system() == "Windows" else path / "webserver" / "iec2c"
                    
                    if has_runtime or compiler.exists() or matiec.exists():
                        self.openplc_path = path
                        break
            
            if not self.openplc_path:
                error_msg = (
                    "OpenPLC não encontrado automaticamente.\n\n"
                    "Soluções:\n"
                    "1. Configure a variável de ambiente OPENPLC_PATH:\n"
                    f"   Windows: set OPENPLC_PATH=C:\\caminho\\para\\OpenPLC\n"
                    f"   Linux: export OPENPLC_PATH=/caminho/para/openplc\n"
                    "2. Use o parâmetro --openplc-path ao executar:\n"
                    "   python benchmark.py --openplc-path \"C:\\caminho\\para\\OpenPLC\"\n\n"
                    "Caminhos testados:\n"
                )
                for path in possible_paths:
                    if path:
                        error_msg += f"  - {path}\n"
                
                raise FileNotFoundError(error_msg)
        
        # Valida componentes essenciais
        self._validate_openplc_installation()
    
    def _find_compiler(self):
        """Procura o compilador em vários locais possíveis"""
        # Se temos override, usa ele
        if self.compiler_path_override and self.compiler_path_override.exists():
            return self.compiler_path_override
        
        compiler_name = "openplc.exe" if platform.system() == "Windows" else "openplc"
        matiec_name = "iec2c.exe" if platform.system() == "Windows" else "iec2c"
        
        # Possíveis locais do compilador (no diretório base)
        possible_compiler_paths = [
            # Estrutura padrão OpenPLC_v3
            self.openplc_path / "compiler" / compiler_name,
            self.openplc_path / "webserver" / "core" / "matiec" / matiec_name,
            self.openplc_path / "webserver" / matiec_name,
            self.openplc_path / "matiec" / matiec_name,
            # Compilador na raiz
            self.openplc_path / compiler_name,
            self.openplc_path / matiec_name,
            # Editor pode ter o compilador
            self.openplc_path / "editor" / "compiler" / compiler_name,
            self.openplc_path / "editor" / compiler_name,
            self.openplc_path / "editor" / "bin" / compiler_name,
            self.openplc_path / "editor" / "bin" / matiec_name,
            self.openplc_path / "editor" / "tools" / compiler_name,
            self.openplc_path / "editor" / "tools" / matiec_name,
        ]
        
        # Procurar em diretórios adjacentes e locais comuns do Windows
        if platform.system() == "Windows":
            common_paths = [
                Path("C:/OpenPLC_v3/webserver/iec2c.exe"),
                Path("C:/OpenPLC_v3/webserver/core/matiec/iec2c.exe"),
                Path.home() / "OpenPLC_Editor" / "matiec" / "iec2c.exe",
                Path("C:/OpenPLC_Editor/matiec/iec2c.exe"),
                Path("C:/Program Files/OpenPLC_v3/webserver/iec2c.exe"),
            ]
            possible_compiler_paths.extend(common_paths)
        
        # Procurar em diretórios adjacentes (Editor pode estar em pasta separada)
        possible_compiler_paths.extend([
            self.openplc_path.parent / "OpenPLC_Editor" / "compiler" / compiler_name,
            self.openplc_path.parent / "OpenPLC_Editor" / compiler_name,
            self.openplc_path.parent / "OpenPLC_Editor" / "matiec" / matiec_name,
            self.openplc_path.parent / "OpenPLC_v3" / "webserver" / matiec_name,
            self.openplc_path.parent / "OpenPLC_v3" / "webserver" / "core" / "matiec" / matiec_name,
        ])
        
        for path in possible_compiler_paths:
            if path.exists():
                return path
        
        return None
    
    def _validate_openplc_installation(self):
        """Valida se a instalação do OpenPLC tem os componentes necessários"""
        # Se temos override, usa ele
        if self.runtime_path_override and self.runtime_path_override.exists():
            runtime_path = self.runtime_path_override
        else:
            runtime_name = "openplc_runtime.exe" if platform.system() == "Windows" else "openplc_runtime"
            
            # Procura runtime em vários locais
            runtime_names_variants = [
                runtime_name,
                "OpenPLC_Runtime.exe" if platform.system() == "Windows" else "OpenPLC_Runtime",
                "runtime.exe" if platform.system() == "Windows" else "runtime",
            ]
            
            possible_runtime_paths = []
            for name in runtime_names_variants:
                possible_runtime_paths.extend([
                    self.openplc_path / "runtime" / name,
                    self.openplc_path / name,  # Pode estar diretamente na raiz
                    self.openplc_path / "webserver" / name,
                    self.openplc_path / "bin" / name,  # Algumas instalações têm bin/
                ])
            
            # Procurar em locais comuns do Windows
            if platform.system() == "Windows":
                common_runtime_paths = [
                    Path("C:/OpenPLC_Runtime/OpenPLC_Runtime.exe"),
                    Path("C:/OpenPLC_Runtime/openplc_runtime.exe"),
                    Path("C:/OpenPLC_Runtime/runtime.exe"),
                    Path("C:/OpenPLC_Runtime/runtime/OpenPLC_Runtime.exe"),
                    Path("C:/Program Files/OpenPLC_Runtime/OpenPLC_Runtime.exe"),
                ]
                possible_runtime_paths.extend(common_runtime_paths)
            
            runtime_path = None
            for path in possible_runtime_paths:
                if path.exists():
                    runtime_path = path
                    break
        
        # Procura compilador
        compiler_path = self._find_compiler()
        
        missing = []
        if not compiler_path:
            missing.append(f"Compilador (procurado em vários locais)")
        if not runtime_path:
            missing.append(f"Runtime (procurado em vários locais)")
        
        if missing:
            # Lista os caminhos que foram procurados
            compiler_name = "openplc.exe" if platform.system() == "Windows" else "openplc"
            matiec_name = "iec2c.exe" if platform.system() == "Windows" else "iec2c"
            
            searched_compiler_paths = [
                self.openplc_path / "compiler" / compiler_name,
                self.openplc_path / "webserver" / "core" / "matiec" / matiec_name,
                self.openplc_path / "webserver" / matiec_name,
                self.openplc_path / "matiec" / matiec_name,
                self.openplc_path / compiler_name,
                self.openplc_path / matiec_name,
                self.openplc_path / "editor" / "compiler" / compiler_name,
                self.openplc_path / "editor" / compiler_name,
            ]
            
            searched_runtime_paths = [
                self.openplc_path / "runtime" / runtime_name,
                self.openplc_path / runtime_name,
                self.openplc_path / "webserver" / runtime_name,
            ]
            
            error_msg = (
                f"Componentes do OpenPLC não encontrados em {self.openplc_path}:\n"
                + "\n".join(f"  - {m}" for m in missing) + "\n\n"
            )
            
            if not compiler_path:
                error_msg += "Locais onde o COMPILADOR foi procurado:\n"
                for path in searched_compiler_paths:
                    error_msg += f"  - {path}\n"
                error_msg += "\n"
            
            if not runtime_path:
                error_msg += "Locais onde o RUNTIME foi procurado:\n"
                for path in searched_runtime_paths:
                    error_msg += f"  - {path}\n"
                error_msg += "\n"
            
            error_msg += (
                "O OpenPLC pode ter diferentes estruturas de instalação:\n"
                "1. OpenPLC_v3 completo (com compilador em compiler/ ou webserver/core/matiec/)\n"
                "2. OpenPLC Runtime apenas (pode não ter compilador separado)\n"
                "3. OpenPLC Editor (compilador pode estar integrado)\n\n"
                "Soluções:\n"
                "1. Execute 'python find_openplc.py' para encontrar sua instalação\n"
                "2. Instale o OpenPLC_v3 completo de: https://github.com/thiagoralves/OpenPLC_v3\n"
                "3. Ou indique o caminho correto usando --openplc-path\n"
                "4. Verifique se o compilador MatIEC está instalado separadamente"
            )
            
            raise FileNotFoundError(error_msg)
        
        # Armazena os caminhos encontrados
        self.compiler_path = compiler_path
        self.runtime_path = runtime_path

    def run_program(self, st_code_path, test_cases):
        """Executa um código ST dentro do OpenPLC e avalia"""
        runtime = None
        client = None
        
        try:
            # 1. Copiar arquivo ST para pasta de compilação
            tmp_program = self.openplc_path / "program.st"
            tmp_program.write_text(Path(st_code_path).read_text(), encoding='utf-8')

            # 2. Compilar usando o compilador encontrado
            if not hasattr(self, 'compiler_path') or not self.compiler_path:
                raise FileNotFoundError("Compilador OpenPLC não foi encontrado durante a inicialização")
            
            print(f"[DEBUG] Usando compilador: {self.compiler_path}")
            
            # Diferentes compiladores podem ter diferentes sintaxes
            # MatIEC (iec2c) precisa do arquivo como argumento
            compiler_name = self.compiler_path.name.lower()
            if "iec2c" in compiler_name or "matiec" in compiler_name:
                # MatIEC compiler
                compile_result = subprocess.run(
                    [str(self.compiler_path), str(tmp_program)],
                    cwd=str(self.openplc_path),
                    capture_output=True,
                    text=True,
                    check=False
                )
            else:
                # Compilador padrão (openplc) - lê program.st do diretório atual
                compile_result = subprocess.run(
                    [str(self.compiler_path)],
                    cwd=str(self.openplc_path),
                    capture_output=True,
                    text=True,
                    check=False
                )
            
            if compile_result.returncode != 0:
                error_output = compile_result.stderr or compile_result.stdout
                raise RuntimeError(
                    f"Erro na compilação (código {compile_result.returncode}):\n"
                    f"STDERR: {compile_result.stderr}\n"
                    f"STDOUT: {compile_result.stdout}"
                )

            # 3. Start runtime usando o runtime encontrado
            if not hasattr(self, 'runtime_path') or not self.runtime_path:
                raise FileNotFoundError("Runtime OpenPLC não foi encontrado durante a inicialização")
            
            print(f"[DEBUG] Usando runtime: {self.runtime_path}")
            
            runtime = subprocess.Popen(
                [str(self.runtime_path)],
                cwd=str(self.openplc_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(2)

            # 4. Conectar via Modbus/TCP
            client = ModbusTcpClient("127.0.0.1", port=502)
            
            # Compatibilidade com versões antigas e novas do pymodbus
            try:
                connect_result = client.connect()
                if connect_result is False:
                    raise ConnectionError("Não foi possível conectar ao OpenPLC via Modbus/TCP")
            except (AttributeError, TypeError):
                # Versão nova do pymodbus pode não ter connect() ou retornar diferente
                pass
            
            time.sleep(0.5)

            results = []

            for step in test_cases:
                inputs = step["inputs"]
                expected = step["expected_outputs"]

                # Escreve entradas digitais
                for i, val in inputs.items():
                    addr = int(i)
                    result = client.write_coil(addr, val)
                    
                    # Verifica erro (compatível com versões antigas e novas)
                    if hasattr(result, 'isError') and result.isError():
                        raise RuntimeError(f"Erro ao escrever coil {addr}: {result}")
                    elif hasattr(result, 'is_error') and result.is_error():
                        raise RuntimeError(f"Erro ao escrever coil {addr}: {result}")

                time.sleep(step.get("wait", 0.1))  # tempo em segundos

                # Ler saídas
                out_states = {}
                for o in expected.keys():
                    addr = int(o)
                    result = client.read_coils(addr, 1)
                    
                    # Verifica erro (compatível com versões antigas e novas)
                    if hasattr(result, 'isError') and result.isError():
                        raise RuntimeError(f"Erro ao ler coil {addr}: {result}")
                    elif hasattr(result, 'is_error') and result.is_error():
                        raise RuntimeError(f"Erro ao ler coil {addr}: {result}")
                    
                    # Extrai o valor do bit (compatível com versões antigas e novas)
                    if hasattr(result, 'bits') and len(result.bits) > 0:
                        out_states[o] = result.bits[0]
                    elif hasattr(result, 'getBit'):
                        out_states[o] = result.getBit(0)
                    else:
                        raise RuntimeError(f"Não foi possível extrair o valor do coil {addr}")

                # Comparação
                correct = {k: (out_states[k] == expected[k]) for k in expected}

                results.append({
                    "inputs": inputs,
                    "expected": expected,
                    "got": out_states,
                    "correct": correct
                })

            return results
            
        except Exception as e:
            raise RuntimeError(f"Erro ao executar programa OpenPLC: {e}") from e
            
        finally:
            # Limpeza
            if client:
                try:
                    client.close()
                except:
                    pass
            
            if runtime:
                try:
                    runtime.terminate()
                    runtime.wait(timeout=5)
                except:
                    try:
                        runtime.kill()
                    except:
                        pass
