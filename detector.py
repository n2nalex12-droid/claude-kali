"""
Hardware and Performance Detector module.
Detects CPU, RAM, GPU (NVIDIA CUDA VRAM), and calculates optimal LLM parameters
(quantization size, context window, gpu layer offloading).
"""

import os
import psutil
import subprocess
import shutil

def get_hardware_profile():
    cpu_count = psutil.cpu_count(logical=True)
    physical_cpus = psutil.cpu_count(logical=False) or cpu_count
    
    # RAM in GB
    virtual_mem = psutil.virtual_memory()
    total_ram_gb = round(virtual_mem.total / (1024 ** 3), 2)
    available_ram_gb = round(virtual_mem.available / (1024 ** 3), 2)
    
    # GPU detection (NVIDIA)
    gpu_info = None
    if shutil.which("nvidia-smi"):
        try:
            cmd = "nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader,nounits"
            res = subprocess.check_output(cmd, shell=True, text=True).strip()
            if res:
                lines = res.split("\n")
                gpus = []
                for line in lines:
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 3:
                        gpus.append({
                            "name": parts[0],
                            "total_vram_mb": float(parts[1]),
                            "free_vram_mb": float(parts[2])
                        })
                if gpus:
                    gpu_info = gpus
        except Exception:
            pass

    # Recommend model specs based on resources
    recommendation = {}
    total_vram_mb = sum(g["total_vram_mb"] for g in gpu_info) if gpu_info else 0

    if total_vram_mb >= 12000 or (gpu_info is None and available_ram_gb >= 24):
        recommendation["model_size"] = "14B"
        recommendation["quant"] = "Q4_K_M"
        recommendation["n_gpu_layers"] = -1 if gpu_info else 0
        recommendation["context_size"] = 8192
    elif total_vram_mb >= 3500 or available_ram_gb >= 12:
        recommendation["model_size"] = "7B - 8B"
        recommendation["quant"] = "Q4_K_M"
        # RTX 3050 has ~4GB VRAM -> offload 20-28 layers
        recommendation["n_gpu_layers"] = 24 if gpu_info else 0
        recommendation["context_size"] = 4096
    elif available_ram_gb >= 6:
        recommendation["model_size"] = "3B - 4B"
        recommendation["quant"] = "Q4_K_M"
        recommendation["n_gpu_layers"] = -1 if gpu_info else 0
        recommendation["context_size"] = 4096
    else:
        recommendation["model_size"] = "1.5B"
        recommendation["quant"] = "Q4_K_M"
        recommendation["n_gpu_layers"] = 0
        recommendation["context_size"] = 2048

    return {
        "cpu_threads": cpu_count,
        "physical_cpus": physical_cpus,
        "total_ram_gb": total_ram_gb,
        "available_ram_gb": available_ram_gb,
        "gpu": gpu_info,
        "recommendation": recommendation
    }

if __name__ == "__main__":
    import json
    print(json.dumps(get_hardware_profile(), indent=2))
