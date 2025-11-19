import requests
import yaml
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

class OpenRouterClient:
    def __init__(self, config_path="config/models.yaml"):
        with open(config_path, "r", encoding='utf-8') as f:
            cfg = yaml.safe_load(f)

        self.models = cfg["models"]
        
        # Prioriza variável de ambiente, depois arquivo de configuração
        self.api_key = os.getenv("OPENROUTER_API_KEY") or cfg.get("openrouter_api_key")
        
        if not self.api_key or self.api_key == "COLOQUE_SUA_CHAVE_AQUI":
            raise ValueError(
                "API Key do OpenRouter não configurada. "
                "Configure OPENROUTER_API_KEY no arquivo .env ou em config/models.yaml"
            )
        
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def call_model(self, model_name, prompt, max_retries=3):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/PLC_Ai_Code",  # OpenRouter pode exigir este header
            "X-Title": "PLC Benchmark"  # Identificação opcional
        }

        body = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0
        }

        for attempt in range(max_retries):
            try:
                r = requests.post(self.base_url, json=body, headers=headers, timeout=60)
                
                # Tenta obter detalhes do erro antes de fazer raise_for_status
                if r.status_code != 200:
                    try:
                        error_data = r.json()
                        error_msg = error_data.get("error", {}).get("message", r.text)
                    except:
                        error_msg = r.text
                    
                    if r.status_code == 404:
                        raise ValueError(
                            f"Modelo '{model_name}' não encontrado (404). "
                            f"Verifique se o nome do modelo está correto. "
                            f"Detalhes: {error_msg}"
                        )
                    elif r.status_code == 401:
                        raise ValueError(
                            f"API Key inválida ou não autorizada (401). "
                            f"Verifique sua chave do OpenRouter. "
                            f"Detalhes: {error_msg}"
                        )
                    else:
                        raise RuntimeError(
                            f"Erro HTTP {r.status_code}: {error_msg}"
                        )
                
                r.raise_for_status()
                response_data = r.json()
                
                if "choices" not in response_data or len(response_data["choices"]) == 0:
                    raise ValueError("Resposta da API não contém choices válidas")
                
                content = response_data["choices"][0]["message"]["content"]
                
                # Tenta extrair código de blocos markdown se presente
                # Muitas IAs retornam código dentro de ```st ou ```structuredtext
                import re
                code_patterns = [
                    r'```(?:st|structuredtext|structured_text|plc|openplc)\s*\n(.*?)```',
                    r'```\s*\n(.*?)```',  # Qualquer bloco de código
                    r'```(.*?)```',  # Bloco sem quebra de linha
                ]
                
                for pattern in code_patterns:
                    matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                    if matches:
                        # Pega o primeiro match e remove espaços em branco
                        extracted = matches[0].strip()
                        if extracted:
                            print(f"[DEBUG] Código extraído de bloco markdown ({len(extracted)} caracteres)")
                            return extracted
                
                # Se não encontrou blocos markdown, retorna o conteúdo original
                return content
                
            except (ValueError, RuntimeError) as e:
                # Erros de validação ou HTTP não devem ser retentados
                raise
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Erro ao chamar modelo {model_name} após {max_retries} tentativas: {e}") from e
                print(f"[WARN] Tentativa {attempt + 1} falhou, tentando novamente...")
                import time
                time.sleep(2 ** attempt)  # Backoff exponencial

    def run_all_models(self, task_prompt, save_dir):
        Path(save_dir).mkdir(parents=True, exist_ok=True)

        outputs = {}

        for model in self.models:
            name = model["name"]
            print(f"[INFO] Rodando modelo: {name}")

            try:
                result = self.call_model(name, task_prompt)
                
                # Debug: mostra tamanho da resposta
                print(f"[DEBUG] Resposta recebida: {len(result) if result else 0} caracteres")
                
                # Validação do resultado
                if not result:
                    print(f"[AVISO] Modelo {name} retornou resposta vazia (None ou string vazia)")
                    continue
                
                if not isinstance(result, str):
                    print(f"[AVISO] Modelo {name} retornou tipo inválido: {type(result)}, convertendo para string")
                    result = str(result)
                
                # Remove espaços em branco no início/fim
                result_original = result
                result = result.strip()
                
                if not result:
                    print(f"[AVISO] Modelo {name} retornou apenas espaços em branco")
                    print(f"[DEBUG] Conteúdo original (primeiros 100 chars): {repr(result_original[:100])}")
                    continue
                
                outputs[name] = result

                out_path = Path(save_dir) / f"{name.replace('/', '_')}.st"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Debug: mostra caminho do arquivo
                print(f"[DEBUG] Salvando em: {out_path}")
                
                try:
                    with open(out_path, "w", encoding='utf-8') as f:
                        bytes_written = f.write(result)
                        f.flush()  # Força escrita imediata
                        os.fsync(f.fileno())  # Garante que foi escrito no disco
                    
                    print(f"[DEBUG] {bytes_written} bytes escritos no arquivo")
                    
                except Exception as write_error:
                    print(f"[ERRO] Falha ao escrever arquivo: {write_error}")
                    raise
                
                # Verifica se o arquivo foi escrito corretamente
                if not out_path.exists():
                    print(f"[ERRO] Arquivo não foi criado: {out_path}")
                    continue
                
                file_size = out_path.stat().st_size
                if file_size > 0:
                    print(f"[OK] Modelo {name} concluído ({file_size} bytes salvos em {out_path.name})")
                else:
                    print(f"[ERRO] Arquivo criado mas está vazio: {out_path}")
                    print(f"[DEBUG] Tentando ler arquivo: {out_path.read_text(encoding='utf-8')[:200]}")
                    
            except Exception as e:
                print(f"[ERRO] Falha ao processar modelo {name}: {e}")
                import traceback
                print(f"[DEBUG] Traceback completo:")
                traceback.print_exc()
                # Continua com os outros modelos mesmo se um falhar
                continue

        return outputs