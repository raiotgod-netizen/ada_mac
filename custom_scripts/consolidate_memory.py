import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.append(str(root / 'backend'))

from learning_manager import consolidate_memory

summary = consolidate_memory()
print(json.dumps(summary, ensure_ascii=False, indent=2))
