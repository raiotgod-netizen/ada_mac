"""
Memory 2.0 for ADA v1.
Automatically generates daily summaries and stores them in long-term memory.
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path


class MemoryEngine:
    """
    Manages ADA's long-term memory via periodic summarization.
    Optionally integrates with LongTermMemory for passive learning.
    """

    def __init__(self, project_manager, log_dir=None, long_term_memory=None):
        self.project_manager = project_manager
        self.long_term_memory = long_term_memory  # Optional: LongTermMemory instance for passive learning
        self.log_dir = log_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "memory"
        )
        os.makedirs(self.log_dir, exist_ok=True)

        # Daily log file
        self.today_file = self._get_daily_file()

        # Session buffer
        self._session_events = []
        self._session_start = datetime.now()

    def _get_daily_file(self):
        """Get the daily memory file path for today."""
        today = datetime.now().strftime("%Y-%m-%d")
        return Path(self.log_dir) / f"daily_{today}.md"

    def log_event(self, event_type, content, metadata=None):
        """
        Log an event to the daily memory.
        event_type: 'tool_use', 'error', 'conversation', 'system', 'project'
        content: str description
        metadata: optional dict
        """
        timestamp = datetime.now().strftime("%H:%M")
        entry = {
            "time": timestamp,
            "type": event_type,
            "content": content,
            "metadata": metadata or {}
        }
        self._session_events.append(entry)

        # Also write to daily file immediately
        meta_str = f" | {json.dumps(metadata)}" if metadata else ""
        line = f"[{timestamp}] [{event_type.upper()}] {content}{meta_str}\n"

        try:
            with open(self.today_file, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as e:
            print(f"[MEMORY] Failed to write to daily file: {e}")

    def generate_daily_summary(self):
        """
        Generate a summary of today's events.
        Returns a string summary suitable for injecting into ADA's context.
        """
        if not self.today_file.exists():
            return "No hay registro de actividad para hoy."

        try:
            with open(self.today_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if not lines:
                return "Sin actividad registrada hoy."

            # Group by type
            by_type = {"TOOL_USE": [], "ERROR": [], "CONVERSATION": [], "SYSTEM": [], "PROJECT": []}
            for line in lines:
                for event_type in by_type:
                    if f"[{event_type}]" in line:
                        by_type[event_type].append(line.strip())
                        break

            summary_parts = []
            for event_type, entries in by_type.items():
                if entries:
                    count = len(entries)
                    summary_parts.append(f"{count} {event_type.replace('_', ' ').lower()}(s)")

            summary = f"Resumen del {datetime.now().strftime('%d/%m/%Y')}: "
            summary += ", ".join(summary_parts) if summary_parts else "Sin actividad registrada."

            return summary

        except Exception as e:
            return f"Error generando resumen: {e}"

    def get_recent_context(self, hours=24):
        """
        Get recent memory context for injecting into ADA's startup.
        Returns recent events from the last N hours.
        """
        try:
            if not self.today_file.exists():
                return ""

            with open(self.today_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Filter to last N hours
            cutoff = (datetime.now() - timedelta(hours=hours)).strftime("%H:%M")
            today_date = datetime.now().strftime("%Y-%m-%d")

            recent = [
                line.strip() for line in lines
                if line.startswith(f"[{today_date}]") or line.startswith("[")
            ]

            if not recent:
                return ""

            # Return as formatted string
            return "\n".join(recent[-50:])  # Last 50 events max

        except Exception as e:
            print(f"[MEMORY] get_recent_context error: {e}")
            return ""

    def inject_context(self):
        """
        Returns the memory context string to inject into ADA's system instruction.
        Call this at startup.
        """
        recent = self.get_recent_context(hours=24)
        if not recent:
            return ""
        return f"\n\n## CONTEXTO RECIENTE (últimas 24h)\n{recent}\n"

    # ---- LIGHTWEIGHT LOGGING (called from ADA directly) ----

    def log_tool_use(self, tool_name, args=None, result_preview=None):
        """Log a tool usage event."""
        preview = result_preview[:80] if result_preview else ""
        self.log_event("tool_use", f"{tool_name} | args={args} | result={preview}",
                      metadata={"tool": tool_name})

    def log_error(self, error_msg, context=None):
        """Log an error."""
        self.log_event("error", error_msg, metadata={"context": context})

    def log_conversation(self, user_message, ada_response_preview):
        """Log a conversation turn and optionally extract facts for long-term memory."""
        self.log_event(
            "conversation",
            f"User: {user_message[:100]} | ADA: {ada_response_preview[:100]}",
            metadata={"user_len": len(user_message)}
        )
        # Passive learning: extract facts from user message
        if self.long_term_memory and user_message:
            try:
                learned = self.long_term_memory.learn_from_text(user_message)
                if learned:
                    print(f"[MEMORY] Learned from conversation: {learned.content[:80]}")
            except Exception as e:
                print(f"[MEMORY] learn_from_text error: {e}")
