# Local Claude Code (100% Offline, Unrestricted GGUF)

An autonomous local AI coding assistant and system controller running directly in your terminal, with zero online APIs, zero telemetry, and full tool execution.

---

## 🌟 Universal All-OS Support
This agent works out-of-the-box across all major operating systems and Linux distributions:
- **Kali Linux & Debian / Ubuntu** (Full penetration testing & development workflows)
- **Bazzite & Fedora / RedHat** (Atomic immutable OS, Flatpak, Homebrew)
- **Arch Linux & Manjaro**
- **macOS** (Apple Silicon M1/M2/M3/M4 with Metal acceleration & Intel)
- **Windows 10 / 11** (Direct cmd/PowerShell launch via `run.bat`)

---

## 🚀 Quick Start by Operating System

### 1. Kali Linux (or Debian / Ubuntu)
```bash
# 1. Install prerequisites (if not already installed)
sudo apt update
sudo apt install -y python3-pip python3-venv git

# 2. Clone or navigate to the directory (e.g. from mounted partition)
cd local-agent

# 3. Install Python dependencies
pip install llama-cpp-python huggingface_hub psutil
# Or with NVIDIA GPU CUDA acceleration:
CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python

# 4. Launch
./run.sh
```

### 2. Bazzite / Fedora Atomic
```bash
cd local-agent
./run.sh
```

### 3. macOS (Apple Silicon / Intel)
```bash
# With Metal GPU acceleration:
CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python huggingface_hub psutil
./run.sh
```

### 4. Windows 10 / 11
Double-click `run.bat` or run:
```cmd
run.bat
```

---

## 🧠 Smart Persistent Hardware Configuration
- **On First Run on Any New Device**:
  1. The agent detects your exact CPU cores, system RAM, and GPU VRAM.
  2. Automatically matches and downloads the optimal unrestricted GGUF model (e.g., Qwen2.5-Coder 7B Abliterated).
  3. Saves the hardware profile to `config.json`.
- **Subsequent Runs**:
  - Loads immediately from `config.json` with **zero re-checking or download delay**.

---

## 🛠️ Operational Modes & Slash Commands

| Command | Purpose |
|---|---|
| **`/aim <goal>`** | **Continuous Execution Loop**: No step limitation. Keeps running, coding, testing, and self-healing until 100% complete. |
| **`Ctrl+C` or `/listen`** | **Mid-Flight Interrupt**: Pause at any step to give guidance or course-correct without killing the agent. |
| **`/think <task>`** | **Deep Reasoning**: Analyzes edge cases and plans before emitting commands. |
| **`/chain <task>`** | **Step-by-Step Chain**: Executes 1 single action at a time and re-evaluates the system state after every step. |
| **`/planner <task>`** | **Structured Roadmap**: Generates a 4-6 step project plan and executes step-by-step. |
| **`/mcq <task>`** | **Interactive Interview**: Asks 3-5 multiple-choice questions to clarify requirements before building. |

---

## 🛡️ Self-Healing & Controller Safeguards
- **3x Fail-safe**: If any approach or command fails 3 times consecutively, automatically changes strategy or skips.
- **Real-Time Token Streaming**: Word-by-word instant output with zero freeze.
- **Deterministic Tracker**: Validates exit code 0 and verifies files actually exist on disk before declaring completion.
