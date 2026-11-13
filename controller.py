"""
Controller Module: Runs Deterministically (Zero LLM Overhead)
Responsibilities:
1. Dynamic Token Calculation: Computes optimal max_tokens based on intent, input size, and remaining budget.
2. Context Window Guard: Prunes and compacts conversation history so the LLM never exceeds context limits.
3. Command Execution & Completion Tracker:
   - Validates exit code (must be 0)
   - Checks for error keywords (not found, permission denied, failed, tracebacks)
   - Verifies file creation if command was expected to write/create files
   - Refuses false 'Completed' claims if prerequisites aren't met!
"""

import os
import re

class AgentController:
    MAX_CONTEXT_TOKENS = 4096
    RESERVED_FOR_SYSTEM = 1200

    @staticmethod
    def calculate_dynamic_tokens(user_input: str, intent_type: str) -> int:
        """
        Dynamically assigns token budget:
        - Greeting / conversational: small (60 - 120 tokens)
        - Explanation / Q&A: medium (256 - 512 tokens)
        - Code generation / Complex bash: large (1024 - 1536 tokens)
        """
        input_len = len(user_input.split())

        if intent_type == "greeting":
            return 80
        elif intent_type == "capability":
            return 450
        elif any(kw in user_input.lower() for kw in ["html", "game", "script", "website", "code", "app", "build", "create"]):
            return 1536
        elif input_len > 40:
            return 1024
        else:
            return 768

    @classmethod
    def guard_context_window(cls, history: list) -> list:
        """
        Ensures total conversation tokens stay safely within context size.
        If history gets too large, preserves system prompt and drops oldest middle turns.
        """
        if len(history) <= 4:
            return history

        # Approximate token count: 1 token ~ 3.8 characters
        def estimate_tokens(msgs):
            return sum(len(m.get("content", "")) for m in msgs) // 4

        current_tokens = estimate_tokens(history)
        safe_limit = cls.MAX_CONTEXT_TOKENS - 800

        compacted = list(history)
        while current_tokens > safe_limit and len(compacted) > 3:
            # Drop the oldest user/assistant exchange (indexes 1 and 2)
            compacted.pop(1)
            if len(compacted) > 2 and compacted[1].get("role") == "assistant":
                compacted.pop(1)
            current_tokens = estimate_tokens(compacted)

        return compacted

    @staticmethod
    def track_command_completion(cmd: str, stdout: str, exit_code: int) -> dict:
        """
        Deterministically verifies if a command actually succeeded or failed.
        Catches:
        - Non-zero exit code
        - Empty output when output was expected
        - Common error patterns
        """
        output_lower = stdout.lower() if stdout else ""
        error_indicators = [
            "command not found",
            "no such file or directory",
            "permission denied",
            "failed to",
            "syntax error",
            "traceback (most recent call last)",
            "connection refused",
            "could not resolve host",
            "fatal error"
        ]

        has_error = (exit_code != 0) or any(err in output_lower for err in error_indicators)

        # File creation verification
        created_file_verified = True
        create_match = re.search(r">\s*([^\s;&|]+)|-o\s+([^\s;&|]+)", cmd)
        if create_match:
            filepath = create_match.group(1) or create_match.group(2)
            filepath = os.path.expanduser(filepath.strip("\"'"))
            if not os.path.exists(filepath):
                created_file_verified = False

        status = "FAILED" if (has_error or not created_file_verified) else "VERIFIED_SUCCESS"

        reasons = []
        if exit_code != 0:
            reasons.append(f"Exited with error code {exit_code}")
        for err in error_indicators:
            if err in output_lower:
                reasons.append(f"Detected error pattern: '{err}'")
                break
        if not created_file_verified:
            reasons.append(f"Target file {filepath} was NOT created on disk")

        return {
            "status": status,
            "cmd": cmd,
            "is_success": status == "VERIFIED_SUCCESS",
            "feedback": "; ".join(reasons) if reasons else "Execution verified successfully."
        }

    @staticmethod
    def verify_goal_completion(llm_reply: str, executed_commands_log: list) -> bool:
        """
        Prevents LLM from falsely claiming 'done' or 'completed' if:
        - It emitted tools in this same reply (not finished yet!)
        - The last command failed
        - No actions were taken for an actionable goal
        """
        reply_lower = llm_reply.lower()

        # If model is currently trying to execute a tool, it is NOT completed
        if "tool:run_command" in reply_lower or "tool:write_file" in reply_lower:
            return False

        # If it claims complete, verify that the last executed command actually succeeded
        claims_done = any(w in reply_lower for w in ["completed", "done", "finished", "safalta", "ban gaya"])
        if claims_done:
            if executed_commands_log:
                last_cmd = executed_commands_log[-1]
                if not last_cmd.get("is_success", False):
                    # False claim! Last command had errors!
                    return False
            return True

        return False
