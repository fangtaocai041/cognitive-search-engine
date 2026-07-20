import sys; from pathlib import Path
_root = str(Path(__file__).resolve().parent.parent.parent); sys.path.insert(0, _root); sys.path.insert(0, str(Path(_root).parent))
# fishkb for FEA
_fishkb = str(Path(_root) / "fish-ecology-assistant" / "fishkb")
if Path(_fishkb).is_dir(): sys.path.insert(0, _fishkb)
for k in list(sys.modules):
    if k in ("scripts","adapter","src","shared_types") or k.startswith(("scripts.","src.","adapter.","shared_types.")): del sys.modules[k]
