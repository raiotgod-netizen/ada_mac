"""
claude_code_tool.py — Claude Code as a tool for ADA

Provides a way for ADA to invoke Claude Code CLI for complex coding tasks.
Uses subprocess to spawn claude-code with --print for non-interactive output.

Usage:
    from claude_code_tool import ClaudeCodeTool
    tool = ClaudeCodeTool()
    result = tool.run("Write a Python script that does X")
"""

import asyncio
import json
import os
import subprocess
import tempfile
from typing import Any, Dict, Optional


class ClaudeCodeTool:
    """
    Wrapper around Claude Code CLI for use as an ADA tool.
    """

    def __init__(self, model: str = "sonnet", working_dir: str = None):
        self.model = model
        self.working_dir = working_dir or os.path.expanduser("~/ada_mac")
        self.timeout = 120  # seconds per task

    def is_available(self) -> Dict[str, Any]:
        """Check if Claude Code CLI is installed."""
        try:
            result = subprocess.run(
                ["claude-code", "--version"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return {"available": True, "version": result.stdout.strip()}
            return {"available": False, "error": result.stderr.strip()}
        except FileNotFoundError:
            return {"available": False, "error": "claude-code not found in PATH"}
        except Exception as e:
            return {"available": False, "error": str(e)}

    def run(self, prompt: str, model: str = None, extra_args: list = None) -> Dict[str, Any]:
        """
        Run a single Claude Code task synchronously.
        Uses --print for non-interactive mode.
        """
        cmd = [
            "claude-code", "--print",
            "--model", model or self.model,
            "--no-input",
        ]

        if extra_args:
            cmd.extend(extra_args)

        # Add the task prompt
        cmd.append("--")
        cmd.append(prompt)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=self.working_dir,
                env={**os.environ, "CLAUDE_SKIP_PERMISSIONS": "1"}
            )

            output = result.stdout.strip()
            error = result.stderr.strip()

            if result.returncode == 0:
                return {
                    "ok": True,
                    "result": output,
                    "model": model or self.model
                }
            else:
                return {
                    "ok": False,
                    "error": error or f"Exit code {result.returncode}",
                    "output": output[:500] if output else ""
                }

        except subprocess.TimeoutExpired:
            return {"ok": False, "error": f"Timeout after {self.timeout}s"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def run_async(self, prompt: str, model: str = None) -> Dict[str, Any]:
        """
        Run a single Claude Code task asynchronously.
        """
        cmd = [
            "claude-code", "--print",
            "--model", model or self.model,
            "--no-input",
            "--",
            prompt
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.working_dir,
                env={**os.environ, "CLAUDE_SKIP_PERMISSIONS": "1"}
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=self.timeout
                )
            except asyncio.TimeoutExpired:
                proc.kill()
                return {"ok": False, "error": f"Timeout after {self.timeout}s"}

            output = stdout.decode().strip()
            error = stderr.decode().strip()

            if proc.returncode == 0:
                return {"ok": True, "result": output, "model": model or self.model}
            else:
                return {
                    "ok": False,
                    "error": error or f"Exit code {proc.returncode}",
                    "output": output[:500] if output else ""
                }

        except Exception as e:
            return {"ok": False, "error": str(e)}

    def check_status(self) -> Dict[str, Any]:
        """Get Claude Code availability and status."""
        avail = self.is_available()
        if not avail.get("available"):
            return {
                "claude_code_ready": False,
                "issue": avail.get("error", "unknown"),
                "install_hint": "npm install -g @anthropic-ai/claude-code"
            }

        # Check if logged in
        try:
            result = subprocess.run(
                ["claude-code", "--print", "--model", "sonnet", "--no-input", "--", "hi"],
                capture_output=True, text=True, timeout=10,
                env={**os.environ, "CLAUDE_SKIP_PERMISSIONS": "1"}
            )
            # If it needs login, it'll fail
            if "not authenticated" in result.stderr.lower() or result.returncode != 0:
                return {
                    "claude_code_ready": False,
                    "issue": "Not logged in. Run: claude-code login",
                    "version": avail.get("version")
                }
        except Exception:
            pass

        return {
            "claude_code_ready": True,
            "version": avail.get("version"),
            "model": self.model,
            "working_dir": self.working_dir
        }
