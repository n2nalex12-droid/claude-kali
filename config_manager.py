"""
Persistent Hardware & Model Configuration Manager.
Maintains a local config.json.
- Checks if model already configured on this system -> loads instantly (zero check delay).
- On a new device or if model missing:
  * Probes hardware (CPU/RAM/GPU VRAM)
  * Auto-downloads matching unrestricted GGUF model
  * Saves path into config.json
"""

import os
import json
from detector import get_hardware_profile
from model_finder import scan_for_gguf_models, download_model, RECOMMENDED_MODELS

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

def load_or_init_model_config():
    """
    Returns (model_path, n_gpu_layers, n_ctx).
    If valid in config.json and file exists, returns immediately without re-checking or downloading.
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                cfg = json.load(f)
            model_path = cfg.get("model_path")
            if model_path and os.path.exists(os.path.expanduser(model_path)):
                print(f"\033[1;32m[Config Loaded]\033[0m Model cached: {model_path}")
                return model_path, cfg.get("n_gpu_layers", 24), cfg.get("n_ctx", 4096)
        except Exception:
            pass

    print("[*] No configured model found in config.json. Detecting device hardware...")
    hw = get_hardware_profile()
    rec = hw["recommendation"]
    print(f"  * Device: {hw['physical_cpus']} cores, {hw['available_ram_gb']} GB RAM, GPU: {hw['gpu']}")
    print(f"  * Hardware Target: {rec['model_size']} ({rec['quant']})")

    # 1. Scan if model already exists locally
    found = scan_for_gguf_models()
    selected_path = None
    if found:
        # Prefer 7B/8B or largest valid model
        selected_path = found[0]["path"]
        print(f"[+] Found existing local model: {selected_path}")
    else:
        # 2. Automatically select matching model based on hardware
        print("\033[1;33m[!] No GGUF model found on this device. Auto-downloading recommended unrestricted model...\033[0m")
        total_vram = sum(g.get("total_vram_mb", 0) for g in hw["gpu"]) if hw["gpu"] else 0
        
        # 7B abliterated is standard for >=4GB VRAM or >=8GB RAM
        target_key = "qwen_coder_abliterated_7b"
        target = RECOMMENDED_MODELS.get(target_key, list(RECOMMENDED_MODELS.values())[0])
        
        models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
        selected_path = download_model(target["repo_id"], target["filename"], destination_dir=models_dir)

    # 3. Save to config.json so device never checks again
    new_cfg = {
        "model_path": selected_path,
        "n_gpu_layers": rec.get("n_gpu_layers", 24),
        "n_ctx": rec.get("context_size", 4096),
        "device_profile": hw
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(new_cfg, f, indent=2)
    print(f"\033[1;32m[+] Device configured! Saved to {CONFIG_FILE}\033[0m")

    return selected_path, new_cfg["n_gpu_layers"], new_cfg["n_ctx"]

if __name__ == "__main__":
    p, layers, ctx = load_or_init_model_config()
    print("Active Model:", p, "Layers:", layers, "Ctx:", ctx)
