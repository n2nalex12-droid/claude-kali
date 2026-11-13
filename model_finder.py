"""
Model Finder & Downloader module.
Scans for existing GGUF models. If none found, downloads unrestricted abliterated models.
"""

import os

COMMON_SCAN_PATHS = [
    os.path.expanduser("~/models"),
    os.path.expanduser("~/.cache/huggingface/hub"),
    os.path.expanduser("~/.ollama/models"),
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/Projects"),
    os.path.expanduser("~/.local/share/models"),
    "./models",
    "."
]

RECOMMENDED_MODELS = {
    "qwen_coder_abliterated_7b": {
        "name": "Qwen2.5-Coder 7B Instruct Abliterated (Q4_K_M)",
        "repo_id": "bartowski/Qwen2.5-Coder-7B-Instruct-abliterated-GGUF",
        "filename": "Qwen2.5-Coder-7B-Instruct-abliterated-Q4_K_M.gguf",
        "size_gb": 4.36,
        "description": "Unrestricted 7B coding model with safety refusals removed. Best for autonomous agentic execution."
    },
    "hermes_llama3": {
        "name": "Nous Hermes 3 Llama-3.1 8B (Q4_K_M)",
        "repo_id": "bartowski/Hermes-3-Llama-3.1-8B-GGUF",
        "filename": "Hermes-3-Llama-3.1-8B-Q4_K_M.gguf",
        "size_gb": 4.92,
        "description": "Nous Research neutral steered open model designed for tool use and autonomous agentic workflows."
    }
}

def scan_for_gguf_models():
    found_models = []
    seen = set()
    for base in COMMON_SCAN_PATHS:
        expanded = os.path.abspath(os.path.expanduser(base))
        if not os.path.exists(expanded):
            continue
        for root, dirs, files in os.walk(expanded):
            for file in files:
                if file.lower().endswith(".gguf"):
                    full_path = os.path.join(root, file)
                    real_path = os.path.realpath(full_path)
                    if real_path not in seen:
                        seen.add(real_path)
                        size_mb = round(os.path.getsize(full_path) / (1024 * 1024), 2)
                        found_models.append({
                            "path": full_path,
                            "filename": file,
                            "size_mb": size_mb
                        })
    return found_models

def download_model(repo_id: str, filename: str, destination_dir: str = "./models"):
    os.makedirs(destination_dir, exist_ok=True)
    from huggingface_hub import hf_hub_download
    print(f"[*] Downloading {filename} from '{repo_id}'...")
    local_file = hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        local_dir=destination_dir,
        local_dir_use_symlinks=False
    )
    print(f"[+] Download complete: {local_file}")
    return local_file

if __name__ == "__main__":
    print("[*] Scanning for local GGUF models...")
    models = scan_for_gguf_models()
    if models:
        print(f"[+] Found {len(models)} model(s):")
        for m in models:
            print(f"  - {m['filename']} ({m['size_mb']} MB) at {m['path']}")
    else:
        print("[!] No GGUF model detected.")
