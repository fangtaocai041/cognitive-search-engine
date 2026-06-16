"""Search 珠星三块鱼 via CognitiveSearchAdapter (HTTP mode)."""
import sys, os, json

engine_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, engine_root)
os.chdir(engine_root)

# Use the adapter directly - it loads meso_agent in HTTP mode
from src.adapter import CognitiveSearchAdapter

adapter = CognitiveSearchAdapter()
result = adapter.search("Tribolodon brandti", mode="adaptive")

print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
