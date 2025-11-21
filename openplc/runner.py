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
            runtime_path: Caminho direto para o webserver.py (opcional, sobrescreve detecção)
                         NOTA: O OpenPLC moderno usa webserver.py como runtime, não executável
        """
        self.compiler_path_override = Path(compiler_path) if compiler_path else None
        self.webserver_script_override = Path(runtime_path) if runtime_path else None
        
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
                    Path("C:/OpenPLC_Runtime/home") / os.environ.get("USERNAME", "Matheus") / "OpenPLC_v3",  # Webserver rodando
                    Path("C:/OpenPLC_Runtime/home/Matheus/OpenPLC_v3"),  # Caminho específico mencionado
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
            username = os.environ.get("USERNAME", "Matheus")
            common_paths = [
                # Caminho do webserver rodando
                Path(f"C:/OpenPLC_Runtime/home/{username}/OpenPLC_v3/webserver/iec2c.exe"),
                Path(f"C:/OpenPLC_Runtime/home/{username}/OpenPLC_v3/webserver/core/matiec/iec2c.exe"),
                Path("C:/OpenPLC_Runtime/home/Matheus/OpenPLC_v3/webserver/iec2c.exe"),
                Path("C:/OpenPLC_Runtime/home/Matheus/OpenPLC_v3/webserver/core/matiec/iec2c.exe"),
                # Outros caminhos comuns
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
    
    def _check_webserver_running(self, port=8080):
        """Verifica se o webserver do OpenPLC está rodando"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return result == 0
        except:
            return False
    
    def _check_modbus_running(self, port=502):
        """Verifica se o Modbus/TCP está respondendo (runtime ativo)"""
        try:
            test_client = ModbusTcpClient("127.0.0.1", port=port)
            connect_result = test_client.connect()
            test_client.close()
            return connect_result is not False
        except:
            return False
    
    def _find_webserver_script(self):
        """Procura o script webserver.py do OpenPLC"""
        # Se temos override, usa ele
        if self.webserver_script_override and self.webserver_script_override.exists():
            return self.webserver_script_override
        
        possible_paths = [
            self.openplc_path / "webserver" / "webserver.py",
            self.openplc_path / "webserver.py",
            self.openplc_path / "webserver" / "main.py",
            self.openplc_path / "main.py",
        ]
        
        # Procurar em locais comuns do Windows
        if platform.system() == "Windows":
            username = os.environ.get("USERNAME", "Matheus")
            possible_paths.extend([
                Path(f"C:/OpenPLC_Runtime/home/{username}/OpenPLC_v3/webserver/webserver.py"),
                Path("C:/OpenPLC_Runtime/home/Matheus/OpenPLC_v3/webserver/webserver.py"),
            ])
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def _validate_openplc_installation(self):
        """Valida se a instalação do OpenPLC tem os componentes necessários"""
        # Verifica se webserver está rodando (OpenPLC moderno)
        webserver_running = self._check_webserver_running(8080)
        modbus_running = self._check_modbus_running(502)
        
        # Procura o script webserver.py
        webserver_script = self._find_webserver_script()
        
        # Se webserver está rodando, não precisa iniciar
        if webserver_running or modbus_running:
            print(f"[INFO] OpenPLC webserver detectado (porta 8080: {webserver_running}, Modbus 502: {modbus_running})")
            webserver_path = webserver_script if webserver_script else "webserver_running"
        else:
            # Webserver não está rodando, precisa encontrar o script para iniciar
            if webserver_script:
                print(f"[INFO] Webserver não está rodando, mas script encontrado: {webserver_script}")
                webserver_path = webserver_script
            else:
                webserver_path = None
        
        # Procura compilador
        compiler_path = self._find_compiler()
        
        missing = []
        if not compiler_path:
            missing.append(f"Compilador (procurado em vários locais)")
        if not webserver_path and not (webserver_running or modbus_running):
            missing.append(f"Webserver (webserver.py não encontrado e webserver não está rodando)")
        
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
            
            if not webserver_path:
                error_msg += "Locais onde o WEBSERVER foi procurado:\n"
                searched_webserver_paths = [
                    self.openplc_path / "webserver" / "webserver.py",
                    self.openplc_path / "webserver.py",
                    self.openplc_path / "webserver" / "main.py",
                ]
                for path in searched_webserver_paths:
                    error_msg += f"  - {path}\n"
                error_msg += "\n"
            
            error_msg += (
                "O OpenPLC moderno roda como webserver (webserver.py), não como executável.\n"
                "Estruturas de instalação:\n"
                "1. OpenPLC_v3 completo (webserver.py em webserver/webserver.py)\n"
                "2. OpenPLC Runtime (webserver.py pode estar em local diferente)\n\n"
                "Soluções:\n"
                "1. Certifique-se de que o OpenPLC webserver está instalado\n"
                "2. Execute 'python find_openplc.py' para encontrar sua instalação\n"
                "3. Instale o OpenPLC_v3 completo de: https://github.com/thiagoralves/OpenPLC_v3\n"
                "4. Ou indique o caminho correto usando --openplc-path\n"
                "5. O webserver será iniciado automaticamente se não estiver rodando\n\n"
                "NOTA: O webserver.py é a runtime do OpenPLC. Ele será iniciado automaticamente se necessário."
            )
            
            raise FileNotFoundError(error_msg)
        
        # Armazena os caminhos encontrados
        self.compiler_path = compiler_path
        self.webserver_script = webserver_path
        self.webserver_running = webserver_running or modbus_running
        self.webserver_port = 8080
        self.webserver_url = f"http://127.0.0.1:{self.webserver_port}"
    
    def _upload_program_via_api(self, st_code_path):
        """Tenta fazer upload do programa via API REST do webserver (opcional)"""
        try:
            import requests
            st_content = Path(st_code_path).read_text(encoding='utf-8')
            
            # Tenta fazer upload via API (endpoint pode variar)
            # OpenPLC webserver pode ter endpoint /upload ou similar
            endpoints = [
                f"{self.webserver_url}/upload_program",
                f"{self.webserver_url}/api/upload",
                f"{self.webserver_url}/program/upload",
            ]
            
            for endpoint in endpoints:
                try:
                    response = requests.post(
                        endpoint,
                        files={"file": ("program.st", st_content, "text/plain")},
                        timeout=5
                    )
                    if response.status_code == 200:
                        print(f"[DEBUG] Programa enviado via API para: {endpoint}")
                        return
                except:
                    continue
            
            # Se não conseguiu via API, continua com método local
            print(f"[DEBUG] API de upload não disponível, usando método local")
        except ImportError:
            # requests não disponível, continua com método local
            pass
        except Exception as e:
            # Qualquer erro, continua com método local
            print(f"[DEBUG] Upload via API falhou: {e}, usando método local")

    def run_program(self, st_code_path, test_cases):
        """Executa um código ST dentro do OpenPLC e avalia"""
        webserver_process = None
        client = None
        
        try:
            # 1. Copiar arquivo ST para pasta de compilação
            # Se for webserver, pode estar em local diferente
            if "webserver" in str(self.openplc_path).lower() or "home" in str(self.openplc_path).lower():
                # Estrutura de webserver: tenta vários locais possíveis
                possible_locations = [
                    self.openplc_path / "webserver" / "program.st",
                    self.openplc_path / "program.st",
                    self.openplc_path / "st_files" / "program.st",
                ]
                tmp_program = None
                for loc in possible_locations:
                    if loc.parent.exists():
                        tmp_program = loc
                        break
                if not tmp_program:
                    # Cria no primeiro local possível
                    tmp_program = possible_locations[0]
            else:
                tmp_program = self.openplc_path / "program.st"
            
            tmp_program.parent.mkdir(parents=True, exist_ok=True)
            tmp_program.write_text(Path(st_code_path).read_text(), encoding='utf-8')
            print(f"[DEBUG] Arquivo ST copiado para: {tmp_program}")
            
            # Se webserver está rodando, tenta fazer upload via API (opcional)
            if hasattr(self, 'webserver_running') and self.webserver_running:
                try:
                    self._upload_program_via_api(st_code_path)
                except Exception as e:
                    print(f"[AVISO] Falha ao fazer upload via API, usando método local: {e}")

            # 2. Compilar usando o compilador encontrado
            if not hasattr(self, 'compiler_path') or not self.compiler_path:
                raise FileNotFoundError("Compilador OpenPLC não foi encontrado durante a inicialização")
            
            print(f"[DEBUG] Usando compilador: {self.compiler_path}")
            
            # Tenta encontrar script de compilação primeiro
            compile_script = None
            possible_scripts = [
                self.openplc_path / "scripts" / "compile_program.sh",
                self.openplc_path / "webserver" / "scripts" / "compile_program.sh",
                self.openplc_path / "scripts" / "compile_program.bat",
                self.openplc_path / "webserver" / "scripts" / "compile_program.bat",
            ]
            
            for script_path in possible_scripts:
                if script_path.exists():
                    compile_script = script_path
                    print(f"[DEBUG] Script de compilação encontrado: {compile_script}")
                    break
            
            # Diferentes compiladores podem ter diferentes sintaxes
            compiler_name = self.compiler_path.name.lower()
            
            if compile_script:
                # Usa script de compilação se disponível
                if compile_script.suffix == ".sh":
                    # Script bash (pode precisar de WSL no Windows)
                    compile_result = subprocess.run(
                        ["bash", str(compile_script), str(tmp_program)],
                        cwd=str(compile_script.parent),
                        capture_output=True,
                        text=True,
                        check=False
                    )
                else:
                    # Script batch (.bat)
                    compile_result = subprocess.run(
                        [str(compile_script), str(tmp_program)],
                        cwd=str(compile_script.parent),
                        capture_output=True,
                        text=True,
                        check=False,
                        shell=True
                    )
            elif "iec2c" in compiler_name or "matiec" in compiler_name:
                # MatIEC compiler - precisa executar no diretório onde está lib/ieclib.txt
                compiler_dir = self.compiler_path.parent
                
                # Procura lib/ieclib.txt em vários locais possíveis
                lib_path = None
                possible_lib_paths = [
                    compiler_dir / "lib",
                    compiler_dir.parent / "lib",
                    compiler_dir.parent.parent / "lib",
                    self.openplc_path / "webserver" / "core" / "matiec" / "lib",
                    self.openplc_path / "webserver" / "lib",
                    self.openplc_path / "lib",
                ]
                
                for path in possible_lib_paths:
                    if path.exists() and (path / "ieclib.txt").exists():
                        lib_path = path
                        print(f"[DEBUG] Biblioteca encontrada em: {lib_path}")
                        break
                
                # Determina o diretório de trabalho para o compilador
                # O MatIEC precisa que lib/ esteja relativo ao diretório de execução
                if lib_path:
                    compile_cwd = lib_path.parent
                    print(f"[DEBUG] Compilando a partir de: {compile_cwd} (lib em: {lib_path})")
                else:
                    # Se não encontrou lib/, tenta usar o diretório do compilador
                    compile_cwd = compiler_dir
                    print(f"[AVISO] Biblioteca lib/ieclib.txt não encontrada, compilando a partir de: {compile_cwd}")
                    print(f"[DEBUG] Locais procurados: {[str(p) for p in possible_lib_paths]}")
                
                # Converte o caminho do arquivo ST para relativo ao diretório de trabalho
                try:
                    st_file_for_compiler = tmp_program.relative_to(compile_cwd)
                except ValueError:
                    # Se não é relativo, usa caminho absoluto
                    st_file_for_compiler = tmp_program
                
                print(f"[DEBUG] Executando: {self.compiler_path} {st_file_for_compiler}")
                print(f"[DEBUG] Diretório de trabalho: {compile_cwd}")
                
                compile_result = subprocess.run(
                    [str(self.compiler_path), str(st_file_for_compiler)],
                    cwd=str(compile_cwd),
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

            # 3. Verificar se webserver já está rodando e iniciar se necessário
            webserver_process = None
            
            # Verifica se webserver já está rodando
            webserver_running = self._check_webserver_running(8080)
            modbus_running = self._check_modbus_running(502)
            
            if webserver_running or modbus_running:
                print(f"[INFO] OpenPLC webserver já está rodando (porta 8080: {webserver_running}, Modbus 502: {modbus_running})")
            else:
                # Webserver não está rodando, precisa iniciar
                if hasattr(self, 'webserver_script') and self.webserver_script:
                    if isinstance(self.webserver_script, Path) and self.webserver_script.exists():
                        print(f"[INFO] Iniciando OpenPLC webserver: {self.webserver_script}")
                        
                        # Determina o diretório de trabalho (onde está o webserver.py)
                        webserver_dir = self.webserver_script.parent
                        
                        # Inicia o webserver.py
                        webserver_process = subprocess.Popen(
                            ["python", str(self.webserver_script)],
                            cwd=str(webserver_dir),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE
                        )
                        
                        # Aguarda o webserver iniciar
                        print(f"[INFO] Aguardando webserver iniciar...")
                        max_wait = 10  # máximo 10 segundos
                        waited = 0
                        while waited < max_wait:
                            time.sleep(1)
                            waited += 1
                            if self._check_webserver_running(8080) or self._check_modbus_running(502):
                                print(f"[OK] Webserver iniciado com sucesso!")
                                break
                        
                        if not (self._check_webserver_running(8080) or self._check_modbus_running(502)):
                            # Verifica se o processo ainda está rodando
                            if webserver_process.poll() is not None:
                                stderr_output = webserver_process.stderr.read().decode('utf-8', errors='ignore')
                                raise RuntimeError(
                                    f"Falha ao iniciar webserver (processo terminou com código {webserver_process.returncode}):\n"
                                    f"{stderr_output}"
                                )
                            else:
                                print(f"[AVISO] Webserver iniciado, mas ainda não responde nas portas 8080/502. Continuando...")
                    else:
                        raise FileNotFoundError(f"Script webserver.py não encontrado: {self.webserver_script}")
                else:
                    raise FileNotFoundError(
                        "Webserver não está rodando e webserver.py não foi encontrado. "
                        "Certifique-se de que o OpenPLC está instalado corretamente."
                    )

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
            
            # Só termina o webserver se nós o iniciamos (não estava rodando antes)
            if webserver_process and not (webserver_running or modbus_running):
                try:
                    print(f"[INFO] Encerrando processo de webserver...")
                    webserver_process.terminate()
                    webserver_process.wait(timeout=5)
                except:
                    try:
                        webserver_process.kill()
                    except:
                        pass
