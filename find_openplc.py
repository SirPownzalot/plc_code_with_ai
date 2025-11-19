"""
Script para ajudar a encontrar a instalação do OpenPLC e seus componentes
"""
import os
import platform
from pathlib import Path

def find_openplc_components():
    """Procura instalações do OpenPLC e lista os componentes encontrados"""
    
    print("=" * 70)
    print("Buscando instalação do OpenPLC...")
    print("=" * 70)
    
    # Caminhos possíveis
    if platform.system() == "Windows":
        search_paths = [
            Path("C:/OpenPLC_Runtime"),  # Instalação comum do Runtime
            Path("C:/OpenPLC_Editor"),  # Instalação comum do Editor
            Path("C:/OpenPLC"),
            Path("C:/OpenPLC_v3"),
            Path("C:/Program Files/OpenPLC"),
            Path("C:/Program Files/OpenPLC_Runtime"),
            Path("C:/Program Files/OpenPLC_Editor"),
            Path("C:/Program Files (x86)/OpenPLC"),
            Path("C:/Program Files (x86)/OpenPLC_Runtime"),
            Path("C:/Program Files (x86)/OpenPLC_Editor"),
            Path(os.environ.get("OPENPLC_PATH", "")),
            Path.home() / "OpenPLC",
            Path.home() / "OpenPLC_Runtime",
            Path.home() / "OpenPLC_Editor",
            Path.home() / "Documents" / "OpenPLC",
            Path(".") / "OpenPLC",
        ]
    else:
        search_paths = [
            Path("/usr/local/openplc"),
            Path("/opt/openplc"),
            Path("/usr/openplc"),
            Path(os.environ.get("OPENPLC_PATH", "")),
            Path.home() / "openplc",
            Path.home() / "OpenPLC",
            Path(".") / "openplc",
        ]
    
    found_installations = []
    
    for base_path in search_paths:
        if not base_path or not base_path.exists():
            continue
        
        print(f"\nVerificando: {base_path}")
        
        # Procura componentes
        components = {
            "Runtime": [],
            "Compiler": [],
            "Editor": [],
            "MatIEC": [],
        }
        
        # Runtime
        runtime_names = ["openplc_runtime.exe", "openplc_runtime", "runtime.exe", "runtime", "OpenPLC_Runtime.exe"]
        for name in runtime_names:
            for path in [
                base_path / "runtime" / name,
                base_path / name,  # Pode estar diretamente na raiz
                base_path / "webserver" / name,
                base_path / "bin" / name,  # Algumas instalações têm bin/
            ]:
                if path.exists():
                    components["Runtime"].append(path)
        
        # Compilador
        compiler_names = ["openplc.exe", "openplc", "compiler.exe", "compiler"]
        for name in compiler_names:
            for path in [
                base_path / "compiler" / name,
                base_path / name,
                base_path / "editor" / "compiler" / name,
                base_path / "editor" / name,
            ]:
                if path.exists():
                    components["Compiler"].append(path)
        
        # MatIEC
        matiec_names = ["iec2c.exe", "iec2c", "matiec.exe", "matiec"]
        for name in matiec_names:
            for path in [
                base_path / "webserver" / "core" / "matiec" / name,
                base_path / "webserver" / name,
                base_path / "matiec" / name,
                base_path / name,
            ]:
                if path.exists():
                    components["MatIEC"].append(path)
        
        # Editor (pasta ou executável)
        editor_paths = [
            base_path / "editor",
            base_path / "OpenPLC_Editor.exe",
            base_path / "editor.exe",
        ]
        for path in editor_paths:
            if path.exists():
                components["Editor"].append(path)
                # Se o Editor existe, procura compilador dentro dele
                if path.is_dir():
                    # Procura compilador dentro do editor
                    for comp_name in compiler_names + matiec_names:
                        editor_compiler_paths = [
                            path / "compiler" / comp_name,
                            path / comp_name,
                            path / "bin" / comp_name,
                            path / "tools" / comp_name,
                        ]
                        for comp_path in editor_compiler_paths:
                            if comp_path.exists():
                                if "iec2c" in comp_name.lower() or "matiec" in comp_name.lower():
                                    components["MatIEC"].append(comp_path)
                                else:
                                    components["Compiler"].append(comp_path)
        
        # Se encontrou algum componente, adiciona à lista
        has_components = any(components.values())
        if has_components:
            found_installations.append((base_path, components))
            print(f"  ✓ Instalação encontrada!")
            for comp_type, paths in components.items():
                if paths:
                    print(f"    {comp_type}: {len(paths)} encontrado(s)")
                    for p in paths:
                        print(f"      - {p}")
    
    print("\n" + "=" * 70)
    if found_installations:
        print(f"Total de instalações encontradas: {len(found_installations)}")
        print("\nRecomendações:")
        for base_path, components in found_installations:
            has_runtime = bool(components["Runtime"])
            has_compiler = bool(components["Compiler"] or components["MatIEC"])
            
            if has_runtime and has_compiler:
                print(f"\n✓ {base_path} - COMPLETO (Runtime + Compilador)")
                print(f"  Use: python benchmark.py --openplc-path \"{base_path}\"")
            elif has_runtime:
                print(f"\n⚠ {base_path} - APENAS RUNTIME (falta compilador)")
                print(f"  Você precisa instalar o compilador MatIEC ou OpenPLC completo")
            elif has_compiler:
                print(f"\n⚠ {base_path} - APENAS COMPILADOR (falta runtime)")
                print(f"  Você precisa instalar o OpenPLC Runtime")
    else:
        print("Nenhuma instalação do OpenPLC encontrada nos caminhos padrão.")
        print("\nSoluções:")
        print("1. Instale o OpenPLC_v3 completo:")
        print("   https://github.com/thiagoralves/OpenPLC_v3")
        print("2. Ou configure OPENPLC_PATH apontando para sua instalação:")
        if platform.system() == "Windows":
            print("   set OPENPLC_PATH=C:\\caminho\\para\\OpenPLC")
        else:
            print("   export OPENPLC_PATH=/caminho/para/openplc")
    
    print("=" * 70)

if __name__ == "__main__":
    find_openplc_components()

