import os
from pathlib import Path

# TexasSolver base dir & exe
TEXASSOLVER_DIR = Path(os.environ.get("TEXASSOLVER_DIR", r"C:\TexasSolver")).resolve()
TEXASSOLVER_EXE = TEXASSOLVER_DIR / "console_solver.exe"

# Where we write temp input/output files (per-run temp dir inside OS temp)
RUNTIME_TMP_PREFIX = "texassolver_"
DEFAULT_SOLVER_TIMEOUT_SECONDS = 15  # hard stop (we keep this tight for day 1)
