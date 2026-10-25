import importlib
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

passed = failed = 0
for mod_name in ("tests.test_price_tools", "tests.test_all_tools"):
    mod = importlib.import_module(mod_name)
    for name in sorted(n for n in dir(mod) if n.startswith("test_")):
        try:
            getattr(mod, name)()
            print("PASS", mod_name.split(".")[-1], name)
            passed += 1
        except Exception:
            print("FAIL", mod_name.split(".")[-1], name)
            traceback.print_exc()
            failed += 1
print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
