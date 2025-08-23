import json
import logging
import os
from pathlib import Path
from subprocess import Popen, PIPE, TimeoutExpired

from app.config import TEXASSOLVER_EXE, TEXASSOLVER_DIR
from app.advisor.texas_solver_client import smoke_test

def healthcheck():
    print(f"[HC] TEXASSOLVER_DIR: {TEXASSOLVER_DIR}")
    print(f"[HC] TEXASSOLVER_EXE: {TEXASSOLVER_EXE}")
    if not TEXASSOLVER_EXE.exists():
        print("[HC] ERROR: console_solver.exe not found.")
        return 1

    # Try --help quickly to catch EULA/prompts/AV blocks
    try:
        proc = Popen([str(TEXASSOLVER_EXE), "--help"], cwd=str(TEXASSOLVER_DIR), stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate(timeout=3)
        print("[HC] --help stdout:", (out or b"").decode(errors="ignore")[:300])
        print("[HC] --help stderr:", (err or b"").decode(errors="ignore")[:300])
        print(f"[HC] exit code: {proc.returncode}")
    except TimeoutExpired:
        print("[HC] TIMEOUT: '--help' did not return in 3s. This usually means a first-run prompt or AV/SmartScreen block.")
        print("     ACTION: Manually run console_solver.exe once from a Command Prompt to clear prompts.")
        return 2
    return 0

if __name__ == "__main__":
    # Basic logging so we can SEE solver output lines
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    print("== TexasSolver Healthcheck ==")
    code = healthcheck()
    if code != 0:
        raise SystemExit(code)

    print("\n== Running smoke_test (may take ~10–15s on first run) ==")
    data = smoke_test()
    # Print first 2KB to avoid floods
    print(json.dumps(data, indent=2)[:2000])
