"""
Tool Execution Engine:
Allows the local agent to:
1. Run bash commands with exit code & output tracking
2. Read, write, and edit files
3. Take over screen/mouse/keyboard (Wayland and X11 via ydotool / xdotool)
"""

import os
import subprocess
import shutil

class SystemTools:
    @staticmethod
    def execute_command_with_code(command: str):
        """Executes shell command and returns (stdout, exit_code)."""
        try:
            res = subprocess.run(
                command,
                shell=True,
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
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception as e:
            return f"[Error reading file: {str(e)}]"

    @staticmethod
    def write_file(path: str, content: str) -> str:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"[File written successfully: {path}]"
        except Exception as e:
            return f"[Error writing file: {str(e)}]"

    @staticmethod
    def mouse_click(x: int = None, y: int = None, button: str = "left") -> str:
        """Controls mouse cursor and clicks."""
        if shutil.which("ydotool"):
            try:
                if x is not None and y is not None:
                    subprocess.run(f"ydotool mousemove -a {x} {y}", shell=True, check=True)
                btn_code = "0xC0" if button == "left" else "0xC1"
                subprocess.run(f"ydotool click {btn_code}", shell=True, check=True)
                return f"[Mouse clicked at ({x}, {y}) via ydotool]"
            except Exception:
                pass
        
        if shutil.which("xdotool"):
            try:
                if x is not None and y is not None:
                    subprocess.run(f"xdotool mousemove {x} {y}", shell=True, check=True)
                btn = 1 if button == "left" else 3
                subprocess.run(f"xdotool click {btn}", shell=True, check=True)
                return f"[Mouse clicked at ({x}, {y}) via xdotool]"
            except Exception as e:
                return f"[Error using xdotool: {str(e)}]"
        
        return "[Error: Neither ydotool nor xdotool is available for mouse control]"

    @staticmethod
    def keyboard_type(text: str) -> str:
        """Types string into active window."""
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
            except Exception as e:
                return f"[Error using xdotool: {str(e)}]"

        return "[Error: Neither ydotool nor xdotool is available for keyboard control]"
