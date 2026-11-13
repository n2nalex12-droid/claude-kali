# Local Claude Code (100% Offline, Unrestricted GGUF)

An autonomous local AI coding assistant running directly inside your terminal, identical in capability to Claude Code / Google Antigravity.

## Features
- **100% Offline & Private**: Zero cloud APIs, runs on local GGUF models.
- **Hardware-Aware Auto-Setup**: Detects CPU, RAM, and GPU VRAM. Automatically downloads matching unrestricted models (e.g. Qwen2.5-Coder-7B Abliterated) on any new device.
- **Persistent Caching**: Saves configuration to `config.json` — never checks or re-downloads repeatedly on a configured device.
- **Universal Dual-Boot Support**: Seamlessly portable between Bazzite (Fedora) and Kali Linux (Debian) when mounting the partition.
- **Modes**:
  - `/aim`: Unlimited execution loop that never stops until the project is 100% created and verified.
  - `/listen`: Mid-flight interrupt to redirect or give new instructions.
  - `/think`: Deep reasoning before taking action.
  - `/chain`: Single-action re-evaluation loop.
  - `/planner`: Structured roadmap generation and execution.
  - `/mcq`: Interactive multiple-choice requirements interview.
- **3x Fail-safe**: If any tool or command fails 3 times consecutively, automatically changes strategy or skips.
- **Real-Time Token Streaming**: Word-by-word instant output with zero freeze.

---

## Setup & Running

### On Bazzite / Fedora:
```bash
cd local-agent
./run.sh
```

### On Kali Linux (Dual Boot / Mounted Partition):
1. Mount your Bazzite partition:
   ```bash
   sudo mount /dev/nvme0n1p... /mnt/bazzite
   cd /mnt/bazzite/home/naitik/Projects/local-agent
   ```
2. Install requirements (first time on Kali):
   ```bash
   sudo apt update
   sudo apt install -y python3-pip python3-venv
   pip install llama-cpp-python huggingface_hub psutil
   # Or with CUDA acceleration on Kali:
   CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python
   ```
3. Run directly:
   ```bash
   ./run.sh
   ```
