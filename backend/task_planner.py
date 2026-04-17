"""
Task Planner for ADA v1.
Takes high-level goals, decomposes into steps, executes in background,
and notifies the user when done or on milestones.
"""
import asyncio
import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
SHARED_DIR = ROOT_DIR / "shared_state"
SHARED_DIR.mkdir(parents=True, exist_ok=True)
TASKS_PATH = SHARED_DIR / "planner_tasks.json"


def _now():
    return datetime.now(timezone.utc).isoformat()


def _load_tasks() -> list[dict]:
    try:
        if TASKS_PATH.exists():
            return json.loads(TASKS_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return []


def _save_tasks(tasks: list):
    TASKS_PATH.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")


class Step:
    """A single execution step within a task."""
    def __init__(self, id: str, description: str, tool_name: str | None = None,
                 tool_args: dict | None = None, status: str = "pending", result: Any = None, error: str = None):
        self.id = id
        self.description = description
        self.tool_name = tool_name
        self.tool_args = tool_args or {}
        self.status = status  # pending | running | done | failed | skipped
        self.result = result
        self.error = error

    def to_dict(self) -> dict:
        return {
            "id": self.id, "description": self.description,
            "tool_name": self.tool_name, "tool_args": self.tool_args,
            "status": self.status, "result": self.result, "error": self.error
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Step":
        return cls(
            id=d["id"], description=d["description"],
            tool_name=d.get("tool_name"), tool_args=d.get("tool_args", {}),
            status=d.get("status", "pending"), result=d.get("result"),
            error=d.get("error")
        )


class Task:
    """A decomposed task with execution steps."""
    def __init__(self, task_id: str, goal: str, steps: list[Step] | None = None,
                 status: str = "planning", created_at: str | None = None):
        self.id = task_id
        self.goal = goal
        self.steps: list[Step] = steps or []
        self.status = status  # planning | ready | running | completed | failed | cancelled
        self.created_at = created_at or _now()
        self.updated_at = self.created_at
        self.current_step: int = 0
        self.result_summary: str = ""
        self.error: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id, "goal": self.goal, "status": self.status,
            "steps": [s.to_dict() for s in self.steps],
            "current_step": self.current_step, "created_at": self.created_at,
            "updated_at": self.updated_at, "result_summary": self.result_summary,
            "error": self.error
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Task":
        t = cls(
            task_id=d["id"], goal=d["goal"], status=d.get("status", "planning"),
            created_at=d.get("created_at")
        )
        t.steps = [Step.from_dict(s) for s in d.get("steps", [])]
        t.current_step = d.get("current_step", 0)
        t.result_summary = d.get("result_summary", "")
        t.error = d.get("error")
        t.updated_at = d.get("updated_at", t.created_at)
        return t

    def progress_pct(self) -> int:
        if not self.steps:
            return 0
        done = sum(1 for s in self.steps if s.status in ("done", "skipped"))
        return round(done / len(self.steps) * 100)

    def pending_steps(self) -> list[Step]:
        return [s for s in self.steps if s.status == "pending"]

    def done_steps(self) -> list[Step]:
        return [s for s in self.steps if s.status == "done"]


class TaskPlanner:
    """
    Background task planner. Decomposes goals into steps using Gemini,
    executes them using available tools, and notifies on completion.
    """

    # Available tool definitions for step execution
    TOOL_MAP: dict[str, callable] = {}

    def __init__(self, ada_loop=None, on_notification=None):
        self.ada = ada_loop
        self.on_notification = on_notification
        self._tasks: dict[str, Task] = {}
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._load()

    # ------------------------------------------------------------------
    # Tool registration
    # ------------------------------------------------------------------
    @staticmethod
    def register_tool(name: str, fn: callable):
        TaskPlanner.TOOL_MAP[name] = fn

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _load(self):
        tasks_data = _load_tasks()
        for td in tasks_data:
            try:
                task = Task.from_dict(td)
                self._tasks[task.id] = task
            except Exception:
                pass

    def _save(self):
        tasks_data = [t.to_dict() for t in self._tasks.values()][:50]
        _save_tasks(tasks_data)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print("[PLANNER] Task planner started.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("[PLANNER] Task planner stopped.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def create_task(self, goal: str) -> dict:
        """Start a new task by decomposing a goal into steps."""
        import uuid
        task_id = f"plan-{uuid.uuid4().hex[:8]}"
        task = Task(task_id=task_id, goal=goal, status="planning")
        with self._lock:
            self._tasks[task_id] = task
        self._save()
        # Kick off async decomposition
        threading.Thread(target=self._decompose, args=(task_id,), daemon=True).start()
        return {"task_id": task_id, "goal": goal, "status": "planning"}

    def get_task(self, task_id: str) -> dict | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None
            return {
                "id": task.id,
                "goal": task.goal,
                "status": task.status,
                "progress_pct": task.progress_pct(),
                "current_step": task.current_step,
                "total_steps": len(task.steps),
                "steps": [s.to_dict() for s in task.steps],
                "result_summary": task.result_summary,
                "error": task.error,
            }

    def list_tasks(self, status: str | None = None) -> list[dict]:
        with self._lock:
            tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return [
            {"id": t.id, "goal": t.goal, "status": t.status,
             "progress_pct": t.progress_pct(), "total_steps": len(t.steps)}
            for t in tasks[:20]
        ]

    def cancel_task(self, task_id: str) -> dict:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return {"ok": False, "error": "Task not found"}
            if task.status == "running":
                task.status = "cancelled"
                task.updated_at = _now()
                self._save()
                return {"ok": True, "result": "Task cancelled"}
            elif task.status == "planning":
                task.status = "cancelled"
                self._save()
                return {"ok": True, "result": "Task cancelled during planning"}
            return {"ok": False, "error": f"Cannot cancel task in status '{task.status}'"}

    # ------------------------------------------------------------------
    # Step decomposition (offloaded to thread)
    # ------------------------------------------------------------------
    def _decompose(self, task_id: str):
        """Use Gemini to decompose goal into steps, then save and start execution."""
        time.sleep(0.5)  # Brief pause to let the user know planning started

        goal = ""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            goal = task.goal

        # Build a prompt for decomposition
        available_tools = list(TaskPlanner.TOOL_MAP.keys())
        prompt = (
            f"Goal: {goal}\n\n"
            f"Available tools: {', '.join(available_tools) if available_tools else '(none — report result directly)'}\n\n"
            f"Decompose this goal into a maximum of 8 concrete steps. "
            f"Each step should be actionable and describe what to do, not just report information. "
            f"For each step provide:\n"
            f"  - id: step number (1, 2, 3...)\n"
            f"  - description: what to do in Spanish\n"
            f"  - tool_name: the tool to use (if any), or null for reasoning-only steps\n"
            f"  - tool_args: arguments for the tool (key-value pairs), or null\n\n"
            f'Respond ONLY with a JSON array like: '
            f'[{{"id": "1", "description": "Buscar archivos relevantes en el proyecto", "tool_name": "find_file", "tool_args": {{"query": "presentacion"}}}}, ...]'
        )

        steps = []
        try:
            import google.genai as genai
            from dotenv import load_dotenv
            load_dotenv()
            client = genai.Client()
            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-04-17",
                contents=prompt
            )
            text = response.text.strip()
            # Try to parse JSON
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            parsed = json.loads(text)
            if isinstance(parsed, list):
                steps = [
                    Step(
                        id=p.get("id", str(i+1)),
                        description=p.get("description", ""),
                        tool_name=p.get("tool_name"),
                        tool_args=p.get("tool_args", {})
                    )
                    for i, p in enumerate(parsed)
                ]
        except Exception as e:
            print(f"[PLANNER] Decomposition error: {e}")
            # Fallback: single step
            steps = [Step(id="1", description=goal)]

        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            task.steps = steps
            task.status = "ready" if steps else "failed"
            task.updated_at = _now()
            if not steps:
                task.error = "Failed to decompose goal"
            self._save()

        # Notify: task ready
        if steps and self.on_notification:
            self.on_notification({
                "type": "task_ready",
                "text": f"Tarea lista: '{goal[:60]}' — {len(steps)} pasos. Ejecutando en background.",
                "action": "task_update"
            })

        # Auto-start execution
        if steps:
            self._execute_steps_async(task_id)

    # ------------------------------------------------------------------
    # Step execution (background thread)
    # ------------------------------------------------------------------
    def _execute_steps_async(self, task_id: str):
        threading.Thread(target=self._execute_steps, args=(task_id,), daemon=True).start()

    def _execute_steps(self, task_id: str):
        """Execute all pending steps in sequence."""
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return
            task.status = "running"
            task.updated_at = _now()
            self._save()

        total = len(task.steps)
        done_count = 0

        for i, step in enumerate(task.steps):
            # Check if cancelled
            with self._lock:
                t = self._tasks.get(task_id)
                if not t or t.status == "cancelled":
                    return

            step.status = "running"
            self._save()
            self._notify_progress(task, step, i+1, total)

            result = None
            error = None
            try:
                if step.tool_name and step.tool_name in TaskPlanner.TOOL_MAP:
                    fn = TaskPlanner.TOOL_MAP[step.tool_name]
                    args = step.tool_args or {}
                    # Run sync tool in thread
                    result = fn(**args)
                    step.result = result
                    step.status = "done"
                else:
                    # No tool — just mark done (reasoning step)
                    step.result = "(paso sin tool)"
                    step.status = "done"
            except Exception as e:
                step.error = str(e)
                step.status = "failed"
                error = str(e)

            done_count += 1
            task.current_step = done_count
            task.updated_at = _now()
            self._save()

        # Finalize
        with self._lock:
            t = self._tasks.get(task_id)
            if not t:
                return
            if t.status == "cancelled":
                return

            failed = [s for s in t.steps if s.status == "failed"]
            if failed:
                t.status = "failed"
                t.error = f"{len(failed)} paso(s) fallido(s): {failed[0].description[:60]}"
            else:
                t.status = "completed"
                done = [s for s in t.steps if s.status == "done"]
                t.result_summary = f"Completado: {len(done)}/{total} pasos exitosos."

            t.updated_at = _now()
            self._save()

        # Final notification
        if self.on_notification:
            if t.status == "completed":
                self.on_notification({
                    "type": "task_completed",
                    "text": f"Tarea completada: '{t.goal[:60]}' — {len(done)}/{total} pasos.",
                    "action": "task_update"
                })
            else:
                self.on_notification({
                    "type": "task_failed",
                    "text": f"Tarea con problemas: '{t.goal[:60]}' — {t.error}",
                    "action": "task_update"
                })

    def _notify_progress(self, task: Task, step: Step, num: int, total: int):
        """Send a brief progress notification."""
        if not self.on_notification:
            return
        pct = round((num - 1) / total * 100) if total > 1 else 0
        self.on_notification({
            "type": "step_progress",
            "text": f"[{num}/{total}] {step.description[:70]}",
            "action": "task_update",
            "task_id": task.id
        })

    # ------------------------------------------------------------------
    # Background loop (for periodic cleanup / idle monitoring)
    # ------------------------------------------------------------------
    def _run_loop(self):
        while self._running:
            try:
                # Clean up very old completed tasks (keep last 20)
                with self._lock:
                    all_tasks = sorted(self._tasks.values(), key=lambda t: t.created_at, reverse=True)
                    if len(all_tasks) > 20:
                        to_remove = [t for t in all_tasks[20:] if t.status in ("completed", "failed", "cancelled")]
                        for t in to_remove:
                            del self._tasks[t.id]
                        if to_remove:
                            self._save()
            except Exception as e:
                print(f"[PLANNER] Loop error: {e}")
            time.sleep(60)

    # ------------------------------------------------------------------
    # Quick execute (one-shot, no decomposition)
    # ------------------------------------------------------------------
    @staticmethod
    def quick_execute(goal: str, tools: list[dict] | None = None) -> dict:
        """
        Directly execute a goal with provided steps (no decomposition).
        tools: list of {"name": "...", "args": {...}}
        """
        import uuid
        task_id = f"quick-{uuid.uuid4().hex[:8]}"
        steps = []
        if tools:
            for i, t in enumerate(tools):
                steps.append(Step(
                    id=str(i+1),
                    description=t.get("description", t["name"]),
                    tool_name=t["name"],
                    tool_args=t.get("args", {})
                ))
        task = Task(task_id=task_id, goal=goal, steps=steps, status="ready" if steps else "failed")
        result_steps = []
        for s in steps:
            try:
                if s.tool_name in TaskPlanner.TOOL_MAP:
                    result = TaskPlanner.TOOL_MAP[s.tool_name](**(s.tool_args or {}))
                    s.result = result
                    s.status = "done"
                else:
                    s.status = "skipped"
                    s.error = f"Tool '{s.tool_name}' not available"
            except Exception as e:
                s.status = "failed"
                s.error = str(e)
            result_steps.append(s.to_dict())
        return {
            "id": task_id, "goal": goal,
            "status": "completed" if all(x.status != "failed" for x in steps) else "failed",
            "steps": result_steps
        }
