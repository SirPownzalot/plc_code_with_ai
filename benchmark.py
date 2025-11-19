import json
import sys
import argparse
from pathlib import Path

from ai.openrouter_client import OpenRouterClient
from openplc.runner import OpenPLCRunner
from evaluator import score_results


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark automatizado para avaliação de LLMs na geração de código ST"
    )
    parser.add_argument(
        "--openplc-path",
        type=str,
        default=None,
        help="Caminho base para instalação do OpenPLC (opcional, tenta detectar automaticamente)"
    )
    parser.add_argument(
        "--compiler-path",
        type=str,
        default=None,
        help="Caminho direto para o compilador (opcional, ex: C:/OpenPLC_v3/webserver/iec2c.exe)"
    )
    parser.add_argument(
        "--runtime-path",
        type=str,
        default=None,
        help="Caminho direto para o runtime (opcional, ex: C:/OpenPLC_Runtime/OpenPLC_Runtime.exe)"
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
    except Exception as e:
        print(f"[ERRO] Falha ao inicializar OpenRouter: {e}")
        sys.exit(1)

    try:
        print("[INFO] Inicializando runner OpenPLC...")
        plc = OpenPLCRunner(
            openplc_path=args.openplc_path,
            compiler_path=args.compiler_path,
            runtime_path=args.runtime_path
        )
        print(f"[OK] OpenPLC encontrado:")
        print(f"  - Caminho base: {plc.openplc_path}")
        if hasattr(plc, 'compiler_path') and plc.compiler_path:
            print(f"  - Compilador: {plc.compiler_path}")
        if hasattr(plc, 'runtime_path') and plc.runtime_path:
            print(f"  - Runtime: {plc.runtime_path}")
    except Exception as e:
        print(f"[ERRO] Falha ao inicializar OpenPLC: {e}")
        print(f"\nDica: Você pode especificar caminhos separados:")
        print(f"  --openplc-path \"C:/OpenPLC_Runtime\"")
        print(f"  --compiler-path \"C:/OpenPLC_v3/webserver/iec2c.exe\"")
        print(f"  --runtime-path \"C:/OpenPLC_Runtime/OpenPLC_Runtime.exe\"")
        sys.exit(1)

    task_files = list(tasks_path.glob("*.json"))
    if not task_files:
        print(f"[ERRO] Nenhuma tarefa encontrada em: {tasks_path}")
        sys.exit(1)

    print(f"[INFO] Encontradas {len(task_files)} tarefa(s)")

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

            # 2. Executar cada programa gerado no OpenPLC
            print(f"\n[FASE 2] Executando programas no OpenPLC...")
            eval_dir = results_dir / "evaluations" / task_file.stem
            eval_dir.mkdir(parents=True, exist_ok=True)

            for model_name in st_outputs:
                st_path = results_dir / "raw_responses" / task_file.stem / f"{model_name.replace('/', '_')}.st"
                print(f"\n  [RUN] Executando: {model_name}")

                try:
                    res = plc.run_program(str(st_path), cases)
                    score = score_results(res)

                    result_file = eval_dir / f"{model_name.replace('/', '_')}.json"
                    with open(result_file, "w", encoding='utf-8') as f:
                        json.dump({"score": score, "results": res}, f, indent=2, ensure_ascii=False)

                    print(f"   -> Score: {score:.2%} ({score:.2f})")
                    
                except Exception as e:
                    print(f"   -> [ERRO] Falha ao executar: {e}")
                    # Salva resultado de erro
                    result_file = eval_dir / f"{model_name.replace('/', '_')}.json"
                    with open(result_file, "w", encoding='utf-8') as f:
                        json.dump({
                            "score": 0.0,
                            "error": str(e),
                            "results": []
                        }, f, indent=2, ensure_ascii=False)

        except json.JSONDecodeError as e:
            print(f"[ERRO] Erro ao ler JSON da tarefa {task_file.name}: {e}")
            continue
        except KeyError as e:
            print(f"[ERRO] Campo obrigatório ausente em {task_file.name}: {e}")
            continue
        except Exception as e:
            print(f"[ERRO] Erro inesperado ao processar {task_file.name}: {e}")
            continue

    print(f"\n{'='*60}")
    print("[INFO] Benchmark concluído!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()