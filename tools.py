"""
Cross-Platform Tool Execution Engine:
Supports:
- Linux (Debian, Ubuntu, Kali, Fedora, Bazzite, Arch)
- macOS (Apple Silicon / Intel, Darwin)
- Windows (PowerShell / cmd)
"""

import os
import sys
import subprocess
import shutil
import platform

IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"

class SystemTools:
    @staticmethod
    def execute_command_with_code(command: str):
        """Executes shell command with cross-platform shell support."""
        try:
            # On Windows, use default shell or powershell
            use_shell = True
            res = subprocess.run(
                command,
                shell=use_shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=120
            )
            out = res.stdout if res.stdout else ""
            return out, res.returncode
        except subprocess.TimeoutExpired:
            return "[Error: Command timed out after 120 seconds]", 124
        except Exception as e:
            return f"[Execution error: {str(e)}]", 1

    @staticmethod
    def execute_command(command: str) -> str:
        out, _ = SystemTools.execute_command_with_code(command)
        return out if out else "[Command finished with no output]"

    @staticmethod
    def read_file(path: str) -> str:
        try:
            expanded_path = os.path.expanduser(os.path.expandvars(path))
            with open(expanded_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception as e:
            return f"[Error reading file: {str(e)}]"

    @staticmethod
    def write_file(path: str, content: str) -> str:
        try:
            expanded_path = os.path.expanduser(os.path.expandvars(path))
            os.makedirs(os.path.dirname(os.path.abspath(expanded_path)), exist_ok=True)
            with open(expanded_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"[File written successfully: {expanded_path}]"
        except Exception as e:
            return f"[Error writing file: {str(e)}]"

    @staticmethod
    def open_browser(target: str) -> str:
        """Cross-platform browser / file opening."""
        if IS_MACOS:
            cmd = f"open '{target}'"
        elif IS_WINDOWS:
            cmd = f"start {target}"
        else: # Linux (Flatpak Brave -> Native Brave -> Firefox -> xdg-open)
            if shutil.which("flatpak") and "com.brave.Browser" in subprocess.getoutput("flatpak list --app"):
                cmd = f"flatpak run com.brave.Browser '{target}'"
            elif shutil.which("xdg-open"):
                cmd = f"xdg-open '{target}'"
            elif shutil.which("brave"):
                cmd = f"brave '{target}'"
            elif shutil.which("firefox"):
                cmd = f"firefox '{target}'"
            else:
                cmd = f"python3 -m webbrowser -t '{target}'"

        out, code = SystemTools.execute_command_with_code(cmd)
        return f"[Opened via: {cmd}]" if code == 0 else f"[Failed to open: {out}]"

    @staticmethod
    def mouse_click(x: int = None, y: int = None, button: str = "left") -> str:
        """Cross-platform mouse control."""
        # 1. Linux Wayland / X11 via ydotool
        if shutil.which("ydotool"):
            try:
                if x is not None and y is not None:
                    subprocess.run(f"ydotool mousemove -a {x} {y}", shell=True, check=True)
                btn_code = "0xC0" if button == "left" else "0xC1"
                subprocess.run(f"ydotool click {btn_code}", shell=True, check=True)
                return f"[Mouse clicked at ({x}, {y}) via ydotool]"
            except Exception:
                pass
        
        # 2. Linux X11 via xdotool
        if shutil.which("xdotool"):
            try:
                if x is not None and y is not None:
                    subprocess.run(f"xdotool mousemove {x} {y}", shell=True, check=True)
                btn = 1 if button == "left" else 3
                subprocess.run(f"xdotool click {btn}", shell=True, check=True)
                return f"[Mouse clicked at ({x}, {y}) via xdotool]"
            except Exception as e:
                pass

        # 3. Python fallback (pyautogui if installed on Windows/macOS/Linux)
        try:
            import pyautogui
            if x is not None and y is not None:
                pyautogui.click(x=x, y=y, button=button)
            else:
                pyautogui.click(button=button)
            return f"[Mouse clicked at ({x}, {y}) via pyautogui]"
        except Exception:
            pass
        
        return "[Error: No supported mouse automation tool found (ydotool, xdotool, or pyautogui)]"

    @staticmethod
    def keyboard_type(text: str) -> str:
        """Cross-platform keyboard automation."""
        if shutil.which("ydotool"):
            try:
                subprocess.run(["ydotool", "type", text], check=True)
                return f"[Typed text via ydotool: {text}]"
            except Exception:
                pass

        if shutil.which("xdotool"):
            try:
                subprocess.run(["xdotool", "type", "--delay", "12", text], check=True)
                return f"[Typed text via xdotool: {text}]"
            except Exception:
                pass

        try:
            import pyautogui
            pyautogui.write(text, interval=0.02)
            return f"[Typed text via pyautogui: {text}]"
        except Exception:
            pass

        return "[Error: No supported keyboard automation tool found]"
