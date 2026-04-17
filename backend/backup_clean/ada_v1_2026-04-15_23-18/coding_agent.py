"""
Coding Agent — Autonomous code generation for ADA.
Uses Groq (or OpenAI/Anthropic) to generate and modify code.
"""
import json
import os
import re
import time
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()


class CodingAgent:
    """
    Autonomous coding agent that can read files, generate code, and propose modifications.
    Works as a sub-agent called by improve_code / self_modification_runner.
    """

    def __init__(self, model: str = "groq"):
        self.model = model
        self.api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.api_base = "https://api.groq.com/openai/v1"
        self.provider = "groq"

        if not self.api_key:
            print("[CODING AGENT] Warning: No API key found (GROQ_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY)")

    def _call_llm(self, messages: List[Dict], temperature: float = 0.3, max_tokens: int = 4000) -> str:
        """Make an LLM API call. Tries Groq first, falls back to OpenAI-compatible."""
        if not self.api_key:
            return json.dumps({"error": "No API key configured for coding agent"})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Groq
        if "groq" in self.api_base or self.provider == "groq":
            payload = {
                "model": "llama-3.3-70b-versatile",  # Good code performance on Groq
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            url = "https://api.groq.com/openai/v1/chat/completions"
        else:
            # OpenAI or compatible
            payload = {
                "model": "gpt-4o" if self.provider == "openai" else "claude-3-5-sonnet-20241022",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            url = "https://api.openai.com/v1/chat/completions"

        try:
            import urllib.request
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            return json.dumps({"error": str(e)})

    # ── CONTEXT GATHERING ────────────────────────────────────────

    def read_file_safe(self, path: str, lines: int = 200) -> str:
        """Read a file safely, returning content or error."""
        try:
            from pathlib import Path
            p = Path(path)
            if not p.exists():
                return f"[FILE NOT FOUND: {path}]"
            content = p.read_text(encoding="utf-8", errors="replace")
            if len(content) > lines * 200:
                content = content[: lines * 200] + f"\n... [TRUNCATED {len(content)} bytes total]"
            return content
        except Exception as e:
            return f"[READ ERROR {path}: {e}]"

    # ── CODE GENERATION ─────────────────────────────────────────

    def generate_code(self, goal: str, context_files: Dict[str, str] = None, language: str = "python") -> Dict[str, Any]:
        """
        Generate code based on a goal and optional context files.
        Returns dict with 'code', 'explanation', and 'files_modified'.
        """
        context_parts = []
        if context_files:
            for fname, content in list(context_files.items())[:5]:
                context_parts.append(f"\n### File: {fname}\n```\n{content[-3000:]}\n```")

        system_prompt = f"""You are an expert Python/Windows developer. Generate clean, working code.

Rules:
- Output valid {language} code that can be saved directly to a file
- For Python: follow PEP8, use type hints, handle exceptions
- For Windows/ADA: use proper Windows APIs (win32, ctypes, subprocess)
- Do NOT include markdown code blocks — output raw code
- Keep functions focused and small (<100 lines each)
- Include docstrings in English
- If modifying existing files, output ONLY the new/changed sections with file path markers

File marker format: ### FILE: path/to/file.py
--- code starts next line ---
def example():
    pass"""

        user_msg = f"Goal: {goal}"
        if context_parts:
            user_msg += "\n\nRelevant context:\n" + "\n".join(context_parts)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ]

        raw = self._call_llm(messages, temperature=0.2, max_tokens=4000)
        return self._parse_generation(raw, goal)

    def _parse_generation(self, raw: str, goal: str) -> Dict[str, Any]:
        """Parse LLM output into structured file edits."""
        files = {}
        explanation = ""

        # Try to extract file sections
        file_pattern = re.compile(r"### FILE:\s*(.+?)\n--- code starts next line ---\n(.*?)(?=\n### FILE:|$)", re.DOTALL)
        for match in file_pattern.finditer(raw):
            filepath = match.group(1).strip()
            code = match.group(2).rstrip()
            files[filepath] = code

        if not files:
            # No file markers — try to extract any code blocks
            code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", raw, re.DOTALL)
            if code_blocks:
                files[f"generated_{int(time.time())}.py"] = "\n".join(code_blocks).strip()

        # Extract explanation (everything before first FILE: marker)
        first_file = raw.find("### FILE:")
        explanation = raw[:first_file].strip() if first_file > 0 else raw.strip()[:500]

        return {
            "goal": goal,
            "files": files,
            "explanation": explanation[:500],
            "model_used": self.provider,
            "raw_preview": raw[:300]
        }

    # ── IMPROVEMENT LOOP ─────────────────────────────────────────

    def improve_file(self, file_path: str, goal: str, current_code: str = None) -> Dict[str, Any]:
        """
        Given a file and a goal, generate an improved version.
        """
        if current_code is None:
            current_code = self.read_file_safe(file_path)

        system_prompt = """You are an expert Python developer improving an existing file.
Read the current code carefully, then generate an improved version.

Rules:
- Output ONLY the NEW version of the file — no explanations, no comments about changes
- Use ### FILE: path marker (see below)
- Keep the same function signatures and public API
- Add type hints, docstrings, and error handling if missing
- Preserve all existing functionality
- Follow PEP8 strictly

Output format:
### FILE: path/to/file.py
--- code starts next line ---
[complete new file content]"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"File: {file_path}\n\nCurrent code:\n{current_code[-4000:]}\n\nImprovement goal: {goal}"}
        ]

        raw = self._call_llm(messages, temperature=0.2, max_tokens=4000)
        parsed = self._parse_generation(raw, goal)

        # Filter to only this file
        filtered = {file_path: code for f, code in parsed["files"].items() if file_path in f}
        if not filtered and parsed["files"]:
            # If no exact match, assume first result is for this file
            filtered = {file_path: list(parsed["files"].values())[0]}

        return {
            "goal": goal,
            "files": filtered,
            "explanation": parsed.get("explanation", ""),
            "model_used": self.provider
        }

    # ── FULL IMPROVE_CODE IMPLEMENTATION ────────────────────────

    def execute_improvement(self, goal: str, files: List[str] = None) -> Dict[str, Any]:
        """
        Complete improvement loop: analyze → read files → generate → apply.
        Returns structured result with all changes.
        """
        results = {
            "goal": goal,
            "files_requested": files or [],
            "generations": [],
            "errors": []
        }

        for fpath in (files or []):
            try:
                current = self.read_file_safe(fpath)
                improved = self.improve_file(fpath, goal, current)
                results["generations"].append({
                    "file": fpath,
                    "improved": fpath in improved["files"],
                    "explanation": improved.get("explanation", "")
                })
            except Exception as e:
                results["errors"].append({"file": fpath, "error": str(e)})

        return results
