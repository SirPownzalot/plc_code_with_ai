import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

from ai.openrouter_client import OpenRouterClient


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark automatizado para avaliação de LLMs na geração de código ST"
    )
    parser.add_argument(
        "--tasks-dir",
        type=str,
        default="tasks",
        help="Diretório contendo as tarefas JSON (padrão: tasks)"
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default="results",
        help="Diretório para salvar resultados (padrão: results)"
    )
    
    args = parser.parse_args()
    
    tasks_path = Path(args.tasks_dir)
    results_dir = Path(args.results_dir)

    if not tasks_path.exists():
        print(f"[ERRO] Diretório de tarefas não encontrado: {tasks_path}")
        sys.exit(1)

    # Validação de pré-requisitos
    try:
        print("[INFO] Inicializando cliente OpenRouter...")
        ai = OpenRouterClient()
        print(f"[OK] {len(ai.models)} IAs configuradas")
    except Exception as e:
        print(f"[ERRO] Falha ao inicializar OpenRouter: {e}")
        sys.exit(1)

    task_files = sorted(list(tasks_path.glob("task_*.json")))
    if not task_files:
        print(f"[ERRO] Nenhuma tarefa encontrada em: {tasks_path}")
        sys.exit(1)

    # Processar apenas as primeiras 5 tarefas
    task_files = task_files[:5]
    
    if len(task_files) < 5:
        print(f"[AVISO] Apenas {len(task_files)} tarefas encontradas (esperado: 5)")

    print(f"[INFO] Processando {len(task_files)} tarefas:")
    for task_file in task_files:
        print(f"  - {task_file.name}")
    print(f"[INFO] Total de tarefas disponíveis: {len(list(tasks_path.glob('task_*.json')))}")

    for task_file in task_files:
        print(f"\n{'='*60}")
        print(f"[INFO] Executando tarefa: {task_file.name}")
        print(f"{'='*60}")

        try:
            task = json.loads(task_file.read_text(encoding='utf-8'))
            prompt = task["prompt"]
            cases = task["tests"]

            # 1. gerar códigos ST das IAs
            print("\n[FASE 1] Gerando códigos ST com IAs...")
            st_outputs = ai.run_all_models(
                task_prompt=prompt,
                save_dir=results_dir / "raw_responses" / task_file.stem
            )

            if not st_outputs:
                print(f"[AVISO] Nenhum código ST gerado para {task_file.name}, pulando...")
                continue

            print(f"[OK] {len(st_outputs)} códigos ST gerados para {task_file.name}")

        except json.JSONDecodeError as e:
            print(f"[ERRO] Erro ao ler JSON da tarefa {task_file.name}: {e}")
            continue
        except KeyError as e:
            print(f"[ERRO] Campo obrigatório ausente em {task_file.name}: {e}")
            continue
        except Exception as e:
            print(f"[ERRO] Erro inesperado ao processar {task_file.name}: {e}")
            continue

    # Gerar relatório resumo para avaliação manual
    print(f"\n{'='*60}")
    print("[INFO] Gerando relatório resumo...")
    print(f"{'='*60}")
    
    summary = {
        "timestamp": datetime.now().isoformat(),
        "config": {
            "num_models": len(ai.models),
            "num_tasks": len(task_files),
            "models": [m["name"] for m in ai.models],
            "tasks": [f.name for f in task_files]
        },
        "results": {}
    }
    
    # Contar códigos gerados por tarefa
    for task_file in task_files:
        task_stem = task_file.stem
        task_dir = results_dir / "raw_responses" / task_stem
        if task_dir.exists():
            st_files = list(task_dir.glob("*.st"))
            summary["results"][task_stem] = {
                "codes_generated": len(st_files),
                "files": [f.name for f in st_files]
            }
    
    # Salvar resumo
    summary_file = results_dir / "summary.json"
    with open(summary_file, "w", encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Relatório salvo em: {summary_file}")
    
    # Criar arquivo README para avaliação manual
    readme_content = f"""# Resultados do Benchmark - Avaliação Manual

## Configuração

- **Data/Hora**: {summary['timestamp']}
- **IAs Testadas**: {len(ai.models)}
- **Tarefas Processadas**: {len(task_files)}

## IAs Configuradas

"""
    for i, model in enumerate(ai.models, 1):
        readme_content += f"{i}. {model['name']}\n"
    
    readme_content += f"""
## Tarefas Processadas

"""
    for i, task_file in enumerate(task_files, 1):
        readme_content += f"{i}. {task_file.name}\n"
    
    readme_content += f"""
## Estrutura de Resultados

Os códigos ST gerados estão organizados em:

```
results/
└── raw_responses/
    ├── task_01/
    │   ├── [modelo1].st
    │   ├── [modelo2].st
    │   └── ...
    ├── task_02/
    └── ...
```

## Critérios de Avaliação Manual

Para cada código ST gerado, avalie:

1. **Compila Corretamente**: O código compila sem erros no OpenPLC?
   - ✅ Sim
   - ❌ Não (especificar erro)

2. **Executa Corretamente**: O código executa e produz os resultados esperados?
   - ✅ Sim
   - ❌ Não (especificar problema)

## Como Avaliar

1. Para cada tarefa, abra os arquivos `.st` na pasta correspondente
2. Tente compilar cada código no OpenPLC
3. Se compilar, execute e verifique se produz os resultados esperados
4. Registre os resultados usando o template: `evaluation_template.json`
   - Copie o template para `evaluation_results.json`
   - Preencha `compila: true/false` e `executa: true/false` para cada código
   - Adicione observações quando necessário

## Template de Avaliação

Um template está disponível em: `results/evaluation_template.json`

Copie este arquivo para `results/evaluation_results.json` e preencha conforme avalia cada código.

## Próximos Passos

Após a avaliação manual, os resultados podem ser consolidados em um relatório final usando o arquivo `evaluation_results.json`.
"""
    
    readme_file = results_dir / "README_AVALIACAO.md"
    with open(readme_file, "w", encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"[OK] Guia de avaliação salvo em: {readme_file}")
    
    print(f"\n{'='*60}")
    print("[INFO] Benchmark concluído!")
    print(f"[INFO] Códigos ST gerados e prontos para avaliação manual")
    print(f"[INFO] Verifique a pasta: {results_dir / 'raw_responses'}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()