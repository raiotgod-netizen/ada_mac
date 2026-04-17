"""
Long-Term Memory for ADA.
Stores, retrieves, and consolidates persistent facts about the user, projects,
preferences, and past interactions — survives restarts and grows smarter over time.

Architecture:
- Memory blocks: atomic units of knowledge (fact, preference, event, topic, skill)
- Embedding-based semantic search via simple TF-IDF (no external API needed)
- Consolidation: periodic summarization of recent events into condensed facts
- Categories: user_facts, project_context, interaction_history, preferences, skills
"""
from __future__ import annotations
import json
import time
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any


class MemoryBlock:
    """Single unit of stored knowledge."""

    def __init__(
        self,
        id: str | None = None,
        category: str = "general",  # user_facts | project_context | interaction_history | preferences | skills
        content: str = "",
        tags: list[str] | None = None,
        importance: int = 3,  # 1-5
        created_at: float | None = None,
        last_accessed: float | None = None,
        access_count: int = 0,
        metadata: dict | None = None,
    ):
        import uuid
        self.id = id or str(uuid.uuid4())[:12]
        self.category = category
        self.content = content
        self.tags = tags or []
        self.importance = max(1, min(5, importance))
        self.created_at = created_at or time.time()
        self.last_accessed = last_accessed or time.time()
        self.access_count = access_count
        self.metadata = metadata or {}

    def touch(self):
        self.last_accessed = time.time()
        self.access_count += 1

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "content": self.content,
            "tags": self.tags,
            "importance": self.importance,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "access_count": self.access_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MemoryBlock":
        return cls(
            id=d.get("id"),
            category=d.get("category", "general"),
            content=d.get("content", ""),
            tags=d.get("tags", []),
            importance=d.get("importance", 3),
            created_at=d.get("created_at"),
            last_accessed=d.get("last_accessed"),
            access_count=d.get("access_count", 0),
            metadata=d.get("metadata", {}),
        )


class LongTermMemory:
    """
    Persistent memory store for ADA.
    Semantic-ish search via TF-IDF keywords (offline, no API needed).
    """

    DEFAULT_MEMORY = [
        {
            "id": "seed_user_name",
            "category": "user_facts",
            "content": "El usuario se llama Diego. El creador y desarrollador de ADA. Se le llama 'Jefe' o 'Señor'.",
            "tags": ["identity", "user", "nombre"],
            "importance": 5,
        },
        {
            "id": "seed_language",
            "category": "preferences",
            "content": "ADA responde en español. El idioma principal es español. Estilo: directo, conciso, técnico, sin filler.",
            "tags": ["language", "preference"],
            "importance": 5,
        },
        {
            "id": "seed_timezone",
            "category": "user_facts",
            "content": "Zona horaria: America/Santiago (GMT-4). Ubicación aproximada: Chile.",
            "tags": ["timezone", "location"],
            "importance": 4,
        },
        {
            "id": "seed_projects",
            "category": "project_context",
            "content": "Proyecto activo: ADA3.0 en ruta OneDrive\\Escritorio\\ADA3.0\\ada_v2. Desarrollador activo también de ADA v1 (OneDrive\\Escritorio\\ADA\\ada_v1).",
            "tags": ["proyecto", "ADA", "desarrollo"],
            "importance": 5,
        },
        {
            "id": "seed_email",
            "category": "user_facts",
            "content": "Email de ADA: ada800694@gmail.com. Email del usuario (paracontextos): no registrado aún.",
            "tags": ["email", "contacto"],
            "importance": 3,
        },
    ]

    def __init__(self, storage_path: Path | str | None = None):
        self.storage_path = Path(storage_path) if storage_path else None
        self._blocks: dict[str, MemoryBlock] = {}
        self._index: dict[str, set[str]] = {}  # word -> block_ids
        self._last_consolidation: float = 0.0
        self._consolidation_interval = 3600  # 1 hour
        self._load()

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------
    def _load(self):
        if not self.storage_path:
            return
        try:
            if self.storage_path.exists():
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                for bd in data.get("blocks", []):
                    try:
                        block = MemoryBlock.from_dict(bd)
                        self._blocks[block.id] = block
                    except Exception:
                        pass
                self._last_consolidation = data.get("_last_consolidation", 0.0)
        except Exception as e:
            print(f"[LongTermMemory] load error: {e}")
        if not self._blocks:
            for md in self.DEFAULT_MEMORY:
                b = MemoryBlock(**md)
                self._blocks[b.id] = b
            self._save()

    def _save(self):
        if not self.storage_path:
            return
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "blocks": [b.to_dict() for b in self._blocks.values()],
                "_last_consolidation": self._last_consolidation,
            }
            self.storage_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            print(f"[LongTermMemory] save error: {e}")

    def _rebuild_index(self):
        """Rebuild word index from all blocks."""
        self._index.clear()
        for bid, block in self._blocks.items():
            words = self._extract_keywords(block.content)
            words.update(block.tags)
            for w in words:
                if w not in self._index:
                    self._index[w] = set()
                self._index[w].add(bid)

    def _extract_keywords(self, text: str) -> set[str]:
        """Simple keyword extraction from text."""
        text = text.lower()
        # Remove special chars, keep words >= 3 chars
        words = re.findall(r'\b[a-záéíóúñü]{3,}\b', text)
        # Remove common stopwords
        stopwords = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
            'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his',
            'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who',
            'boy', 'did', 'let', 'put', 'say', 'she', 'the', 'too', 'use', 'que',
            'del', 'las', 'los', 'con', 'por', 'una', 'para', 'como', 'pero',
            'este', 'esta', 'esto', 'ese', 'esa', 'ellos', 'ellas', 'ser', 'tan',
            'muy', 'más', 'menos', 'todo', 'sobre', 'entre', 'cuando', 'donde',
        }
        return {w for w in words if w not in stopwords}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add(
        self,
        content: str,
        category: str = "general",
        tags: list[str] | None = None,
        importance: int = 3,
        metadata: dict | None = None,
    ) -> MemoryBlock:
        """Add a new memory block."""
        block = MemoryBlock(
            category=category,
            content=content,
            tags=tags,
            importance=importance,
            metadata=metadata or {},
        )
        self._blocks[block.id] = block
        # Update index
        words = self._extract_keywords(content)
        words.update(tags or [])
        for w in words:
            if w not in self._index:
                self._index[w] = set()
            self._index[w].add(block.id)
        self._save()
        return block

    def update(self, block_id: str, content: str | None = None, tags: list | None = None, importance: int | None = None) -> bool:
        """Update an existing block."""
        if block_id not in self._blocks:
            return False
        block = self._blocks[block_id]
        if content is not None:
            block.content = content
        if tags is not None:
            block.tags = tags
        if importance is not None:
            block.importance = max(1, min(5, importance))
        self._rebuild_index()
        self._save()
        return True

    def delete(self, block_id: str) -> bool:
        if block_id not in self._blocks:
            return False
        del self._blocks[block_id]
        for idx_set in self._index.values():
            idx_set.discard(block_id)
        self._save()
        return True

    def search(self, query: str, top_k: int = 5, category: str | None = None) -> list[MemoryBlock]:
        """
        Search memory by semantic-ish keyword match.
        Returns top_k most relevant blocks.
        """
        query_words = self._extract_keywords(query)
        if not query_words:
            return []

        scores: dict[str, float] = {}
        for word in query_words:
            for bid in self._index.get(word, []):
                block = self._blocks.get(bid)
                if not block:
                    continue
                if category and block.category != category:
                    continue
                score = (
                    1.0 * len(word) / max(len(w) for w in query_words)  # longer match = higher
                    + 0.5 * block.importance / 5.0
                    + 0.3 * (1.0 / (1.0 + (time.time() - block.last_accessed) / 86400))  # recency boost
                    + 0.2 * min(1.0, block.access_count / 10.0)  # access count boost
                )
                scores[bid] = scores.get(bid, 0) + score

        ranked = sorted(scores.keys(), key=lambda b: scores[b], reverse=True)[:top_k]
        results = [self._blocks[bid] for bid in ranked if bid in self._blocks]
        # Mark as accessed
        for r in results:
            r.touch()
        return results

    def recall(self, query: str, top_k: int = 3) -> str:
        """
        Produce a textual recall of relevant memories for the given query.
        Used by ADA to incorporate memory into conversation context.
        """
        blocks = self.search(query, top_k=top_k)
        if not blocks:
            return ""
        lines = ["[MEMORIA RELEVANTE]"]
        for b in blocks:
            age = self._age_string(b.created_at)
            lines.append(f"• [{b.category}] {b.content} (creado: {age})")
        return "\n".join(lines)

    def _age_string(self, timestamp: float) -> str:
        delta = time.time() - timestamp
        if delta < 60:
            return "ahora"
        if delta < 3600:
            return f"hace {int(delta/60)}m"
        if delta < 86400:
            return f"hace {int(delta/3600)}h"
        if delta < 604800:
            return f"hace {int(delta/86400)}d"
        return datetime.fromtimestamp(timestamp).strftime("%d/%m")

    def get_by_category(self, category: str) -> list[MemoryBlock]:
        return [b for b in self._blocks.values() if b.category == category]

    def snapshot(self) -> dict:
        """Full state for system_state exposure."""
        blocks = list(self._blocks.values())
        by_cat: dict[str, int] = {}
        for b in blocks:
            by_cat[b.category] = by_cat.get(b.category, 0) + 1
        return {
            "total": len(blocks),
            "by_category": by_cat,
            "recent": [b.content[:80] for b in sorted(blocks, key=lambda x: x.last_accessed, reverse=True)[:5]],
        }

    def consolidate(self, recent_events: list[dict] | None = None) -> dict:
        """
        Periodic consolidation: summarize recent events into long-term facts.
        Called by a cron or on shutdown. Returns stats.
        """
        now = time.time()
        if now - self._last_consolidation < self._consolidation_interval:
            return {"skipped": True, "reason": "too soon"}
        self._last_consolidation = now

        stats = {"created": 0, "updated": 0, "pruned": 0}
        one_day_ago = now - 86400
        one_week_ago = now - 604800

        # Prune: very old low-importance blocks that haven't been accessed recently
        to_delete = []
        for bid, block in self._blocks.items():
            if block.importance <= 2 and block.last_accessed < one_week_ago:
                to_delete.append(bid)
        for bid in to_delete:
            self.delete(bid)
            stats["pruned"] += 1

        # Upgrade importance if block accessed frequently
        for bid, block in self._blocks.items():
            if block.access_count >= 5 and block.importance < 4:
                block.importance = 4
                stats["updated"] += 1

        self._save()
        return stats

    def add_user_fact(self, content: str, tags: list[str] | None = None):
        """Convenience: add a user fact."""
        return self.add(content, category="user_facts", tags=tags or ["user"], importance=4)

    def add_preference(self, content: str, tags: list[str] | None = None):
        """Convenience: add a preference."""
        return self.add(content, category="preferences", tags=tags or ["preference"], importance=5)

    def add_interaction(self, content: str, metadata: dict | None = None):
        """Convenience: log an interaction summary."""
        return self.add(content, category="interaction_history", tags=["interaction"], importance=2, metadata=metadata or {})

    def learn_from_text(self, text: str):
        """
        Extract potential facts from plain text and store them.
        Simple pattern matching for structured facts.
        E.g. 'my name is X' → user_fact
        """
        text = text.strip()
        if len(text) < 10 or len(text) > 500:
            return None

        lower = text.lower()

        # Name patterns
        m = re.search(r'me llamo\s+(.+?)(?:\.|,|$)', lower)
        if m:
            return self.add_user_fact(f"El usuario se llama {m.group(1).strip().title()}.", tags=["name", "identity"])

        m = re.search(r'my name is\s+(.+?)(?:\.|,|$)', lower)
        if m:
            return self.add_user_fact(f"El usuario se llama {m.group(1).strip().title()}.", tags=["name", "identity"])

        # Preference patterns
        m = re.search(r'prefiero\s+(.+?)(?:\.|,|$)', lower)
        if m:
            return self.add_preference(f"El usuario prefiere {m.group(1).strip()}.")

        m = re.search(r'no me gusta\s+(.+?)(?:\.|,|$)', lower)
        if m:
            return self.add_preference(f"El usuario no le gusta: {m.group(1).strip()}.")

        # Project patterns
        m = re.search(r'estoy trabajando en\s+(.+?)(?:\.|,|$)', lower)
        if m:
            return self.add(m.group(1).strip(), category="project_context", tags=["current_project"], importance=4)

        m = re.search(r'working on\s+(.+?)(?:\.|,|$)', lower)
        if m:
            return self.add(m.group(1).strip(), category="project_context", tags=["current_project"], importance=4)

        return None
