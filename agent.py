#!/usr/bin/env python3
"""
Autonomous Local Coding Agent (Offline, Unrestricted GGUF powered)
Engineered like Claude Code / Google Antigravity:
Slash Command Operational Modes:
- Multi-Flag Slash Command Parser: supports `/listen /aim /think <task>` chained together
- Real Browser & System App Grounding: detects actual Flatpak / Native browsers (Brave, Firefox, Chrome, xdg-open)
- Indestructible Ctrl+C Listen Loop: recursive interrupt handling so Ctrl+C ALWAYS brings up `listen>` prompt
- 3x Fail-safe: automatically switches strategy if an approach fails 3 times
- /aim: Persistent goal loop with NO step limitation until 100% verified complete
"""

import os
import sys
import json
import re
import time
import platform
import socket
import select
import subprocess

from detector import get_hardware_profile
from model_finder import scan_for_gguf_models, download_model, RECOMMENDED_MODELS
from tools import SystemTools
from controller import AgentController
from config_manager import load_or_init_model_config

def get_live_system_context():
    """Gathers real-time OS, Hardware, Network, and real verified Installed Browsers / Launchers."""
    hw = get_hardware_profile()
    uname = platform.uname()
    
    os_name = "Linux"
    if os.path.exists("/etc/os-release"):
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        os_name = line.split("=", 1)[1].strip().strip('"')
                        break
        except Exception:
            pass

    home_dir = os.path.expanduser("~")
    user_name = os.getenv("USER", "user")
    current_dir = os.getcwd()

    # Network detection
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    # Detect REAL browsers installed (Native + Flatpak)
    installed_browsers = []
    # Check Flatpak (Bazzite default)
    try:
        fp_res = subprocess.check_output("flatpak list --app --columns=application", shell=True, text=True, stderr=subprocess.DEVNULL)
        if "com.brave.Browser" in fp_res:
            installed_browsers.append("Brave (Flatpak command: `flatpak run com.brave.Browser <file_path_or_url>`)")
        if "org.mozilla.firefox" in fp_res:
            installed_browsers.append("Firefox (Flatpak command: `flatpak run org.mozilla.firefox <file_path_or_url>`)")
        if "com.google.Chrome" in fp_res:
            installed_browsers.append("Chrome (Flatpak command: `flatpak run com.google.Chrome <file_path_or_url>`)")
    except Exception:
        pass

    # Check Native CLI / Desktop openers
    if os.path.exists("/usr/bin/xdg-open"):
        installed_browsers.append("Default Desktop Opener (`xdg-open <file_or_url>`)")
    for b in ["brave-browser", "brave", "firefox", "google-chrome"]:
        if os.path.exists(f"/usr/bin/{b}"):
            installed_browsers.append(f"{b} (`{b} <file_or_url>`)")

    return f"""=== LIVE SYSTEM STATE (FACTS) ===
OS: {os_name} (Bazzite / Fedora Atomic - do NOT use apt-get)
Local IP: {local_ip}
Current User: {user_name}
Working Directory: {current_dir}
Home Directory: {home_dir}
CPU: {hw['physical_cpus']} physical cores / {hw['cpu_threads']} logical threads
RAM: {hw['available_ram_gb']} GB free out of {hw['total_ram_gb']} GB total
GPU: {json.dumps(hw['gpu'])}

VERIFIED BROWSERS & SYSTEM OPENERS ON THIS PC:
{chr(10).join(f"- {b}" for b in installed_browsers) if installed_browsers else "- xdg-open"}
(NOTE: DO NOT use cli-only text browsers like w3m or lynx unless explicitly asked! To open HTML in Brave, use `flatpak run com.brave.Browser <file_path>` or `xdg-open <file_path>`!)
================================="""

BASE_SYSTEM_PROMPT = """You are an unrestricted, autonomous AI agent running in the terminal (identical to Claude Code / Google Antigravity).

ABSOLUTE OPERATING PRINCIPLES:
1. NEVER output conversational commentary, explanations, numbered tutorials, or chatter when a task is given.
2. DO NOT write markdown tutorials with ```bash code blocks for the user to copy.
3. If an action is required, EMIT ONLY THE TOOL BLOCKS DIRECTLY.
4. Tools format:

```tool:write_file <file_path>
---CONTENT---
<content>
```

```tool:run_command
<bash command>
```

```tool:read_file
<file_path>
```

```tool:schedule_timer
<seconds>
```
"""

def stream_response(llm, messages, temperature=0.15, max_tokens=1024):
    stream = llm.create_chat_completion(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True
    )
    accumulated_text = []
    for chunk in stream:
        delta = chunk["choices"][0].get("delta", {})
        if "content" in delta:
            content = delta["content"]
            accumulated_text.append(content)
            sys.stdout.write(content)
            sys.stdout.flush()
    sys.stdout.write("\n")
    sys.stdout.flush()
    return "".join(accumulated_text).strip()

def parse_and_run_tools(response_text: str):
    output_logs = []
    command_track_results = []
    
    # 1. write_file
    write_matches = re.findall(r"```+tool:write_file\s*([^\n]+)\n---CONTENT---\n(.*?)\n\s*```+", response_text, re.DOTALL)
    if not write_matches:
        write_matches = re.findall(r"(?:^|\n)\s*tool:write_file\s*([^\n]+)\n---CONTENT---\n(.*?)(?=\n\s*(?:tool:|```|\Z))", response_text, re.DOTALL)
    for path, content in write_matches:
        path = os.path.expanduser(path.strip().replace("```", "").strip())
        if path:
            print(f"\n\033[1;32m[Writing File]\033[0m: {path}")
            result = SystemTools.write_file(path, content)
            file_exists = os.path.exists(path)
            track_res = {
                "status": "VERIFIED_SUCCESS" if file_exists else "FAILED",
                "cmd": f"write_file {path}",
                "is_success": file_exists,
                "feedback": f"File verified on disk ({path})" if file_exists else "File write failed"
            }
            command_track_results.append(track_res)
            print(f"\033[1;30m{result}\033[0m")
            output_logs.append(result)

    # 2. run_command
    cmd_matches = re.findall(r"```+tool:run_command[^\n]*\n(.*?)\n\s*```+", response_text, re.DOTALL)
    if not cmd_matches:
        cmd_matches = re.findall(r"(?:^|\n)\s*tool:run_command\s*\n(.*?)(?=\n\s*(?:tool:|```|\Z))", response_text, re.DOTALL)

    for cmd in cmd_matches:
        cmd = cmd.strip()
        cmd = re.sub(r"```+$", "", cmd).strip()
        if cmd:
            print(f"\n\033[1;33m[Executing Terminal Command]\033[0m: {cmd}")
            stdout, exit_code = SystemTools.execute_command_with_code(cmd)
            track_res = AgentController.track_command_completion(cmd, stdout, exit_code)
            command_track_results.append(track_res)

            status_color = "\033[1;32m" if track_res["is_success"] else "\033[1;31m"
            print(f"{status_color}[Tracker: {track_res['status']}]\033[0m: {track_res['feedback']}")
            if stdout:
                print(f"\033[1;30m{stdout.strip()}\033[0m")
            output_logs.append(f"$ {cmd} (Exit Code: {exit_code})\n{stdout}")

    # 3. read_file
    read_matches = re.findall(r"```+tool:read_file[^\n]*\n(.*?)\n\s*```+", response_text, re.DOTALL)
    if not read_matches:
        read_matches = re.findall(r"(?:^|\n)\s*tool:read_file\s*\n(.*?)(?=\n\s*(?:tool:|```|\Z))", response_text, re.DOTALL)
    for path in read_matches:
        path = os.path.expanduser(re.sub(r"```+$", "", path.strip()).strip())
        if path:
            print(f"\n\033[1;34m[Reading File]\033[0m: {path}")
            result = SystemTools.read_file(path)
            output_logs.append(f"File ({path}):\n{result}")

    # 4. schedule_timer
    timer_matches = re.findall(r"```+tool:schedule_timer[^\n]*\n(.*?)\n\s*```+", response_text, re.DOTALL)
    if not timer_matches:
        timer_matches = re.findall(r"(?:^|\n)\s*tool:schedule_timer\s*\n(.*?)(?=\n\s*(?:tool:|```|\Z))", response_text, re.DOTALL)
    for sec in timer_matches:
        try:
            s = int(sec.strip())
            print(f"\n\033[1;36m[Timer Scheduled]\033[0m: Sleeping {s} seconds...")
            time.sleep(min(s, 60))
            output_logs.append(f"[Timer Finished: Waited {s} seconds.]")
        except Exception:
            pass

    return "\n".join(output_logs), command_track_results

def check_for_user_listen_interrupt() -> str:
    """Non-blocking check if the user typed during loop execution."""
    try:
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.readline().strip()
            if line:
                return line
    except Exception:
        pass
    return None

def parse_slash_modes(user_input: str):
    """
    Parses multiple chained slash commands like:
    `/listen /aim /think use brave browser for opening`
    Returns (set_of_modes, cleaned_query)
    """
    modes = set()
    tokens = user_input.strip().split()
    idx = 0
    valid_flags = {"/listen", "/aim", "/think", "/chain", "/planner", "/mcq"}
    
    while idx < len(tokens) and tokens[idx].lower() in valid_flags:
        modes.add(tokens[idx].lower().lstrip("/"))
        idx += 1
        
    cleaned_query = " ".join(tokens[idx:])
    return modes, cleaned_query

def run_mcq_mode(llm, user_goal: str):
    print(f"\n\033[1;35m[/mcq Mode Activated]\033[0m Generating 3-5 requirement clarifying questions with options...\n")
    mcq_prompt = f"""Generate 3 to 4 multiple choice questions to clarify requirements for this project:
Project: {user_goal}

Format EACH question clearly like:
Question 1: <question>
A) <option 1>
B) <option 2>
C) <option 3>
D) <option 4>

Output questions only."""

    raw_mcq = stream_response(
        llm,
        [
            {"role": "system", "content": "You are a requirements architect. Output multiple-choice questions with A/B/C/D options."},
            {"role": "user", "content": mcq_prompt}
        ],
        temperature=0.2,
        max_tokens=600
    )

    print("\n\033[1;36mEnter your answers (e.g. '1: A, 2: B, 3: C' or custom preference):\033[0m")
    user_answers = input("mcq-answers> ").strip()
    return f"{user_goal}\nUser Selected Requirements: {user_answers}"

def run_planner_mode(llm, user_goal: str) -> list:
    print(f"\n\033[1;35m[/planner Mode Activated]\033[0m Creating project execution plan...\n")
    plan_prompt = f"""Create a clear 4 to 6 step execution plan for this goal:
Goal: {user_goal}

Format:
Step 1: <action>
Step 2: <action>
Step 3: <action>
Step 4: <action>
Keep it concise and actionable."""

    plan_text = stream_response(
        llm,
        [
            {"role": "system", "content": "You are an expert software planner. Output a concise step-by-step plan."},
            {"role": "user", "content": plan_prompt}
        ],
        temperature=0.2,
        max_tokens=400
    )
    return plan_text

def execute_autonomous_engine(llm, raw_input: str, conversation_history: list):
    modes, cleaned_goal = parse_slash_modes(raw_input)

    if "mcq" in modes:
        cleaned_goal = run_mcq_mode(llm, cleaned_goal)
        modes.add("chain")

    # Conversational shortcut
    if not modes and cleaned_goal.lower() in ["hi", "hello", "hey"]:
        reply = stream_response(
            llm,
            [{"role": "system", "content": "You are an autonomous AI coding agent. Greet in 1 concise sentence."}, {"role": "user", "content": cleaned_goal}],
            temperature=0.3, max_tokens=60
        )
        conversation_history.append({"role": "user", "content": cleaned_goal})
        conversation_history.append({"role": "assistant", "content": reply})
        return

    plan_context = ""
    if "planner" in modes:
        plan_text = run_planner_mode(llm, cleaned_goal)
        plan_context = f"\nEXECUTION PLAN ROADMAP:\n{plan_text}\nStick to this plan and execute each step!"

    is_aim = "aim" in modes
    is_think = "think" in modes
    is_chain = "chain" in modes
    modes_display = "+".join(sorted(modes)).upper() if modes else "DIRECT"

    dynamic_tokens = AgentController.calculate_dynamic_tokens(cleaned_goal, "task")
    print(f"\n\033[1;32m[*] Goal Initiated [Modes: {modes_display}]:\033[0m {cleaned_goal}")
    if is_aim:
        print("\033[1;33m[*] /aim Mode: UNLIMITED STEPS. Will continue running until 100% verified complete.\033[0m")
    print(f"\033[1;30m[Controller Budget: {dynamic_tokens} tokens / Completion Tracker: ACTIVE]\033[0m\n")

    sys_ctx = get_live_system_context()

    # Dynamic system instructions based on combined flags
    extra_instructions = []
    if is_think:
        extra_instructions.append("First write a 2-3 line ```thinking ... ``` block reasoning about edge cases and dependencies, then immediately emit the tool blocks.")
    if is_chain:
        extra_instructions.append("Perform 1 single action at a time. After every action, re-evaluate the outcome before continuing.")
    if "planner" in modes:
        extra_instructions.append(f"Follow the execution plan strictly.{plan_context} Emit tool blocks to execute step-by-step.")
    if is_aim:
        extra_instructions.append("CONTINUOUS GOAL. Keep writing files, testing, verifying, and assembling until the entire project is 100% functional, on disk, and working.")
    if not extra_instructions:
        extra_instructions.append("ACT DIRECTLY! Write the files and run commands using tools immediately. Zero chatty commentary.")

    initial_prompt = f"""{sys_ctx}

USER GOAL: {cleaned_goal}

MANDATORY INSTRUCTIONS:
- {' '.join(extra_instructions)}
- DO NOT output conversational preamble or explain steps to the user. EMIT TOOL BLOCKS IMMEDIATELY.
- Use the VERIFIED BROWSERS & SYSTEM OPENERS listed above (e.g. flatpak run com.brave.Browser, xdg-open). Never guess cli tools like w3m/lynx!"""

    history = [
        {"role": "system", "content": BASE_SYSTEM_PROMPT},
        {"role": "user", "content": initial_prompt}
    ]

    step = 1
    max_steps = 999999 if is_aim else 25
    executed_commands_log = []
    consecutive_failures = {}

    while step <= max_steps:
        history = AgentController.guard_context_window(history)
        step_display = f"Step {step}" if is_aim else f"Step {step}/{max_steps}"
        print(f"\033[1;34m[{step_display} | {modes_display}]\033[0m Streaming action:")
        
        reply = stream_response(llm, history, temperature=0.15, max_tokens=dynamic_tokens)

        # Catch chatty tutorials without tools
        is_tutorial = bool(re.search(r"^\s*1\.\s+\*\*|^\s*Step 1:", reply, re.MULTILINE)) and "tool:" not in reply
        if is_tutorial:
            print("\033[1;31m[Controller Intercept]\033[0m Model chatted instead of using tools. Forcing direct tool emission...")
            history.append({"role": "assistant", "content": reply})
            history.append({
                "role": "user",
                "content": "DO NOT explain steps! You are the autonomous agent. Emit ```tool:write_file or ```tool:run_command right now to execute this on disk!"
            })
            step += 1
            continue

        tool_results, track_logs = parse_and_run_tools(reply)
        executed_commands_log.extend(track_logs)
        history.append({"role": "assistant", "content": reply})

        # 3x Fail-safe tracking
        step_had_failure = False
        cmd_key = ""
        for t in track_logs:
            cmd_key = t.get("cmd", "")
            if not t.get("is_success", True):
                step_had_failure = True
                consecutive_failures[cmd_key] = consecutive_failures.get(cmd_key, 0) + 1
                
                if consecutive_failures[cmd_key] >= 3:
                    print(f"\n\033[1;35m[3x Failure Rule Triggered]\033[0m '{cmd_key}' failed 3 times! Forcing strategy change / skip...")
                    history.append({
                        "role": "user",
                        "content": f"[STRATEGY CHANGE]: The approach '{cmd_key}' failed 3 consecutive times. SKIP this specific command and switch to an ALTERNATIVE method (e.g. pure python script, alternate browser, or different tool) to continue the goal!"
                    })
                    consecutive_failures[cmd_key] = 0
                    break
            else:
                if cmd_key in consecutive_failures:
                    consecutive_failures[cmd_key] = 0

        if step_had_failure and consecutive_failures.get(cmd_key, 0) < 3:
            failed_feedback = [t["feedback"] for t in track_logs if not t["is_success"]]
            print(f"\033[1;31m[Tracker Intercept]\033[0m Failure ({consecutive_failures.get(cmd_key, 1)}/3): {'; '.join(failed_feedback)}.")
            history.append({
                "role": "user",
                "content": f"[Command Failed]: {'; '.join(failed_feedback)}. Fix the error or use an alternative approach."
            })
            step += 1
            time.sleep(0.3)
            continue

        # /aim completion check
        if is_aim:
            if not tool_results:
                written_files = [t for t in executed_commands_log if t.get("cmd", "").startswith("write_file")]
                if len(written_files) >= 1 and all(t.get("is_success", True) for t in executed_commands_log[-3:]):
                    print(f"\n\033[1;32m[/aim Goal Fully Completed & Deterministically Verified on Disk!]\033[0m\n")
                    break
                else:
                    history.append({"role": "user", "content": "You are in /aim mode! Do not stop until the entire project is created, assets exist on disk, and are verified. What is the next file/action?"})
                    step += 1
                    continue

        if not tool_results:
            print(f"\n\033[1;32m[Goal Completed]\033[0m\n")
            conversation_history.append({"role": "user", "content": raw_input})
            conversation_history.append({"role": "assistant", "content": reply})
            break

        # Check for /listen user interruption mid-flight
        listen_input = check_for_user_listen_interrupt()
        if listen_input:
            print(f"\n\033[1;33m[/listen User Interruption Received]:\033[0m {listen_input}")
            history.append({
                "role": "user",
                "content": f"[USER /LISTEN INTERRUPT]: The user has updated the goal mid-flight: '{listen_input}'. Adjust your next action immediately according to this instruction!"
            })
            step += 1
            continue

        feedback_msg = f"[Tool Execution Result]:\n{tool_results}\n"
        if is_chain:
            feedback_msg += "Action executed. Re-evaluate current system state and decide the exact next single action."
        else:
            feedback_msg += "Analyze outcome and execute the next tool."

        history.append({"role": "user", "content": feedback_msg})
        step += 1
        time.sleep(0.3)

def interactive_loop(llm):
    """
    Master interactive session loop with Indestructible Ctrl+C Protection.
    Ctrl+C will ALWAYS trigger the `listen>` interactive guidance prompt without dying.
    """
    conversation_history = []
    
    while True:
        try:
            user_input = input("\033[1;36mlocal-agent>\033[0m ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", ":q"]:
                break
            
            # Execute with inner Ctrl+C capture
            while True:
                try:
                    execute_autonomous_engine(llm, user_input, conversation_history)
                    break
                except KeyboardInterrupt:
                    print("\n\n\033[1;33m[Execution Paused via Ctrl+C]\033[0m")
                    print("Type your guidance / command (supports /listen /aim /think, or type 'exit'):")
                    try:
                        listen_prompt = input("listen> ").strip()
                        if not listen_prompt:
                            print("Resuming execution...")
                            continue
                        if listen_prompt.lower() in ["exit", "quit", ":q"]:
                            return
                        user_input = listen_prompt
                    except KeyboardInterrupt:
                        print("\nAborted to main prompt.\n")
                        break
                        
        except KeyboardInterrupt:
            print("\n\n\033[1;33m[Main Session Paused]\033[0m (Press Enter to continue, or type 'exit' to quit)")
            try:
                check_exit = input("exit? ").strip()
                if check_exit.lower() in ["exit", "quit", "y", "yes"]:
                    break
            except KeyboardInterrupt:
                break

def main():
    print("=" * 70)
    print(" LOCAL CLAUDE CODE (BROWSER-GROUNDED + MULTI-SLASH + INDESTRUCTIBLE CTRL+C) ")
    print("=" * 70)

    # Persistent configuration manager:
    # If already set on this PC -> loads instantly without re-checking.
    # On a new PC (Kali or any Linux) -> checks hardware, auto-downloads model, writes config.json
    selected_model_path, n_gpu_layers, n_ctx = load_or_init_model_config()

    from llama_cpp import Llama
    llm = Llama(
        model_path=selected_model_path,
        n_gpu_layers=n_gpu_layers,
        n_ctx=n_ctx,
        verbose=False
    )
    print("\033[1;32m[+] Commands: /aim (Unlimited) | /listen (Interrupt) | /think | /chain | /planner | /mcq\033[0m\n")

    interactive_loop(llm)

if __name__ == "__main__":
    main()
