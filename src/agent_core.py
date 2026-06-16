# v5.7: de-duplicated from agent_core + rule_engine
# v8.1: resilient import — when loaded via importlib spec_from_file_location,
#       'from src._utils import DotDict' may fail. Use direct loading as fallback.
try:
    from src._utils import DotDict
except (ImportError, ModuleNotFoundError):
    import importlib.util as _iu2
    _utils_path = Path(__file__).resolve().parent / "_utils.py"
    _utils_spec = _iu2.spec_from_file_location("cognitive._utils", str(_utils_path))
    if _utils_spec and _utils_spec.loader:
        _utils_mod = _iu2.module_from_spec(_utils_spec)
        _sys.modules["cognitive._utils"] = _utils_mod
        _utils_spec.loader.exec_module(_utils_mod)
        DotDict = _utils_mod.DotDict
    else:
        # Ultimate fallback — inline the class
        class DotDict(dict):
            __slots__ = ()
            def __getattr__(self, key):
                try:
                    val = self[key]
                except KeyError:
                    raise AttributeError(f"'DotDict' has no attribute '{key}'")
                if isinstance(val, dict) and not isinstance(val, DotDict):
                    val = DotDict(val)
                    self[key] = val
                return val
            def __setattr__(self, key, value):
                self[key] = value
            def __delattr__(self, key):
                try:
                    del self[key]
                except KeyError:
                    raise AttributeError(f"'DotDict' has no attribute '{key}'")