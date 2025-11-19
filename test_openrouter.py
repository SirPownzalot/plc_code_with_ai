"""
Script de teste para verificar conexão com OpenRouter e listar modelos disponíveis
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    print("[ERRO] OPENROUTER_API_KEY não configurada no arquivo .env")
    exit(1)

print(f"[INFO] Testando conexão com OpenRouter...")
print(f"[INFO] API Key: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else '****'}")

# Teste 1: Listar modelos disponíveis
print("\n[TESTE 1] Listando modelos disponíveis...")
try:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/PLC_Ai_Code",
        "X-Title": "PLC Benchmark"
    }
    
    response = requests.get("https://openrouter.ai/api/v1/models", headers=headers, timeout=30)
    
    if response.status_code == 200:
        models_data = response.json()
        models = models_data.get("data", [])
        
        print(f"[OK] Encontrados {len(models)} modelos")
        print("\nModelos gratuitos disponíveis:")
        print("-" * 80)
        
        free_models = [m for m in models if m.get("pricing", {}).get("prompt") == "0" or ":free" in m.get("id", "")]
        
        for model in free_models[:20]:  # Mostra os primeiros 20
            model_id = model.get("id", "N/A")
            name = model.get("name", "N/A")
            print(f"  {model_id}")
            if name != model_id:
                print(f"    Nome: {name}")
        
        if len(free_models) > 20:
            print(f"\n  ... e mais {len(free_models) - 20} modelos gratuitos")
            
    else:
        print(f"[ERRO] Falha ao listar modelos: {response.status_code}")
        print(f"Resposta: {response.text}")
        
except Exception as e:
    print(f"[ERRO] Erro ao listar modelos: {e}")

# Teste 2: Testar um modelo específico
print("\n[TESTE 2] Testando chamada de API com modelo de exemplo...")

test_models = [
    "meta-llama/llama-3.1-8b-instruct:free",
    "google/gemini-flash-1.5:free",
    "meta-llama/llama-3.1-8b-instruct",
    "google/gemini-flash-1.5",
    "openrouter/auto"  # Modelo automático
]

for model_name in test_models:
    print(f"\n  Testando: {model_name}")
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/PLC_Ai_Code",
            "X-Title": "PLC Benchmark"
        }
        
        body = {
            "model": model_name,
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=body,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"    [OK] Modelo '{model_name}' funciona!")
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]
                print(f"    Resposta: {content[:50]}...")
        else:
            error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            error_msg = error_data.get("error", {}).get("message", response.text)
            print(f"    [ERRO] {response.status_code}: {error_msg}")
            
    except Exception as e:
        print(f"    [ERRO] {e}")

print("\n[INFO] Teste concluído!")

