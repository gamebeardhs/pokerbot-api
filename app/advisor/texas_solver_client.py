import json
import logging
import os
import shutil
import tempfile
import threading
import time
import textwrap
from pathlib import Path
from subprocess import Popen, PIPE, TimeoutExpired
from typing import Optional, Tuple, Dict, Any, Iterable

def _safe_threads():
    # cap to 8 to avoid native crashes on some builds
    cpu = os.cpu_count() or 1
    return min(cpu, 8)

from app.config import (
    TEXASSOLVER_EXE as CFG_TEXASSOLVER_EXE,
    TEXASSOLVER_DIR as CFG_TEXASSOLVER_DIR,
    RUNTIME_TMP_PREFIX,
    DEFAULT_SOLVER_TIMEOUT_SECONDS,
)

log = logging.getLogger(__name__)

class TexasSolverError(Exception):
    pass

class TexasSolverTimeout(TexasSolverError):
    pass

# ---- Resolve solver paths (env > config), ensure Path objects ----
_env_dir = os.getenv("TEXASSOLVER_DIR", None)
_env_exe = os.getenv("TEXASSOLVER_EXE", None)

_base_dir = Path(str(CFG_TEXASSOLVER_DIR)).resolve()
_exe = Path(str(CFG_TEXASSOLVER_EXE)) if CFG_TEXASSOLVER_EXE else (_base_dir / "console_solver.exe")

if _env_dir:
    _base_dir = Path(_env_dir).resolve()
if _env_exe:
    _exe = Path(_env_exe)

TEXASSOLVER_DIR: Path = _base_dir
TEXASSOLVER_EXE: Path = _exe


def _pump_stream(stream, tag: str):
    """Stream solver stdout/stderr line-by-line into our logs."""
    for line in iter(stream.readline, b''):
        try:
            decoded = line.decode(errors="replace").rstrip()
        except Exception:
            decoded = str(line)
        if decoded:
            log.info("[texassolver %s] %s", tag, decoded)
    try:
        stream.close()
    except Exception:
        pass


def verify_solver_install() -> None:
    """Make sure solver exe & resources are present and runnable."""
    exe = TEXASSOLVER_EXE if isinstance(TEXASSOLVER_EXE, Path) else Path(TEXASSOLVER_EXE)
    base = TEXASSOLVER_DIR if isinstance(TEXASSOLVER_DIR, Path) else Path(TEXASSOLVER_DIR)

    if not exe.exists():
        raise TexasSolverError(f"TexasSolver exe not found: {exe}")
    if exe.is_dir():
        raise TexasSolverError(f"TexasSolver exe points to a directory, not a file: {exe}")

    resources = base / "resources"
    if not resources.exists():
        raise TexasSolverError(f"TexasSolver resources/ folder not found at: {resources}")

    log.info("TexasSolver detected at %s", exe)


def build_fast_profile_input(
    pot: float,
    effective_stack: float,
    board_cards,
    ip_range_text: str,
    oop_range_text: str,
    betsize_pct: int = 50,
    threads: int = _safe_threads(),
    accuracy: float = 5.0,
    max_iteration: int = 50,
    allin_threshold: float = 0.67,
    output_path: str = "output_result.json",
) -> str:
    """
    Return a TexasSolver input.txt string for a tiny/fast tree:
      - 1 bet size per street (betsize_pct% pot)
      - include all-in on each street
      - loose accuracy & low iteration cap so it finishes quickly
    """
    board_str = ",".join(board_cards) if board_cards else ""

    script_lines = [
        f"set_pot {pot}",
        f"set_effective_stack {effective_stack}",
    ]
    if board_str:
        script_lines.append(f"set_board {board_str}")

    script_lines.extend([
        f"set_range_ip {ip_range_text}",
        f"set_range_oop {oop_range_text}",

        # bet sizes (1 size + shove)
        f"set_bet_sizes oop,flop,bet,{betsize_pct}",
        f"set_bet_sizes oop,flop,raise,{betsize_pct}",
        f"set_bet_sizes oop,flop,allin",
        f"set_bet_sizes ip,flop,bet,{betsize_pct}",
        f"set_bet_sizes ip,flop,raise,{betsize_pct}",
        f"set_bet_sizes ip,flop,allin",

        f"set_bet_sizes oop,turn,bet,{betsize_pct}",
        f"set_bet_sizes oop,turn,raise,{betsize_pct}",
        f"set_bet_sizes oop,turn,allin",
        f"set_bet_sizes ip,turn,bet,{betsize_pct}",
        f"set_bet_sizes ip,turn,raise,{betsize_pct}",
        f"set_bet_sizes ip,turn,allin",

        f"set_bet_sizes oop,river,bet,{betsize_pct}",
        f"set_bet_sizes oop,river,raise,{betsize_pct}",
        f"set_bet_sizes oop,river,allin",
        f"set_bet_sizes ip,river,bet,{betsize_pct}",
        f"set_bet_sizes ip,river,raise,{betsize_pct}",
        f"set_bet_sizes ip,river,allin",

        f"set_allin_threshold {allin_threshold}",

        "build_tree",

        f"set_thread_num {threads}",
        f"set_accuracy {accuracy}",
        f"set_max_iteration {max_iteration}",
        f"set_print_interval 1",
        "start_solve",
        "set_dump_rounds 2",
        f"dump_result {output_path}",
    ])

    return "\n".join(script_lines) + "\n"


def run_solver_with_input_text(input_text: str, timeout_sec: int = DEFAULT_SOLVER_TIMEOUT_SECONDS) -> dict:
    """
    Write input_text into a temp dir; run console_solver.exe with cwd=TEXASSOLVER_DIR.
    Stream logs, enforce timeout, parse output_result.json and return its JSON.
    """
    verify_solver_install()

    with tempfile.TemporaryDirectory(prefix=RUNTIME_TMP_PREFIX) as tmpdir:
        tmpdir_path = Path(tmpdir)
        input_path = tmpdir_path / "input.txt"
        output_path = Path(tempfile.gettempdir()) / (RUNTIME_TMP_PREFIX + "out.json")

        try:
            if output_path.exists():
                output_path.unlink()
        except Exception:
            pass

        input_path.write_text(input_text, encoding="utf-8")

        if "dump_result" not in input_path.read_text(encoding="utf-8"):
            raise TexasSolverError("Input script missing dump_result; expected caller to include it.")

        cmd = [
            str(TEXASSOLVER_EXE),
            "--input_file", str(input_path),
            "--resource_dir", "resources",  # relative to cwd below
        ]
        log.info("Launching TexasSolver: %s", " ".join(cmd))

        env = os.environ.copy()
        env.setdefault("OMP_NUM_THREADS", "1")
        env.setdefault("KMP_INIT_AT_FORK", "FALSE")

        proc = Popen(
            cmd,
            cwd=str(TEXASSOLVER_DIR),
            env=env,
            stdout=PIPE,
            stderr=PIPE,
        )
        t_out = threading.Thread(target=_pump_stream, args=(proc.stdout, "OUT"), daemon=True)
        t_err = threading.Thread(target=_pump_stream, args=(proc.stderr, "ERR"), daemon=True)
        t_out.start()
        t_err.start()

        try:
            rc = proc.wait(timeout=timeout_sec)
        except TimeoutExpired:
            data = None
            try:
                if output_path.exists():
                    data = json.loads(output_path.read_text(encoding="utf-8"))
            except Exception:
                data = None
            try:
                proc.kill()
            except Exception:
                pass
            if data is not None:
                return data
            raise TexasSolverTimeout(f"TexasSolver timed out after {timeout_sec}s")

        if rc != 0:
            if rc == 3221225477:
                raise TexasSolverError(
                    "TexasSolver crashed with 0xC0000005 (access violation). "
                    "Most common cause: resources not found due to working-directory issues. "
                    "We now run with cwd=C:\\TexasSolver and --resource_dir=resources. "
                    "If this persists, verify the tree/config names referenced by your input exist under C:\\TexasSolver\\resources."
                )
            raise TexasSolverError(f"TexasSolver exited with code {rc}")

        if not output_path.exists():
            raise TexasSolverError("TexasSolver completed but output_result.json not found (check dump_result path in your input).")

        try:
            data = json.loads(output_path.read_text(encoding="utf-8"))
        except Exception as e:
            raise TexasSolverError(f"Failed to parse output_result.json: {e}")

        return data


# Convenience: a tiny smoke test for a HU flop with toy ranges
def smoke_test() -> dict:
    ip_range = "AA,KK,QQ,JJ,TT,AKs,AQs,AJs,ATs,KQs,AKo,AQo"
    oop_range = "AA,KK,QQ,JJ,TT,99,AKs,AQs,AJs,KQs,AKo,AQo"
    out_path = Path(tempfile.gettempdir()) / (RUNTIME_TMP_PREFIX + "out.json")
    input_text = build_fast_profile_input(
        pot=10.0,
        effective_stack=100.0,
        board_cards=["Ah", "Kd", "2c"],
        ip_range_text=ip_range,
        oop_range_text=oop_range,
        betsize_pct=50,
        threads=_safe_threads(),
        accuracy=25.0,
        max_iteration=12,
        allin_threshold=0.67,
        output_path=str(out_path),
    )
    return run_solver_with_input_text(input_text, timeout_sec=15)


# ---------- NEW: script extraction helpers ----------

def _coerce_board_list(b: Any) -> Iterable[str]:
    if not b:
        return []
    if isinstance(b, (tuple, list)):
        return [str(x) for x in b if x]
    # allow comma-separated string
    if isinstance(b, str):
        return [s.strip() for s in b.split(",") if s.strip()]
    return []


def _build_script_from_state_like(state_like: Any) -> str:
    """
    Minimal HU postflop builder from a TableState-like object or dict.
    Uses conservative toy ranges if none provided.
    """
    # Access helpers to work with either attributes or dict keys
    def get(name: str, default=None):
        if isinstance(state_like, dict):
            return state_like.get(name, default)
        return getattr(state_like, name, default)

    board_cards = _coerce_board_list(get("board", []))
    pot = float(get("round_pot", 0.0) or get("pot", 0.0) or 0.0)
    if pot <= 0:
        pot = 6.0  # safe default if missing

    # Determine effective stack from players still in_hand
    seats = get("seats", []) or []
    in_players = []
    for s in seats:
        # s can be dict or pydantic model
        in_hand = s.get("in_hand") if isinstance(s, dict) else getattr(s, "in_hand", False)
        if in_hand:
            stack = s.get("stack") if isinstance(s, dict) else getattr(s, "stack", None)
            try:
                stack = float(stack)
            except Exception:
                stack = None
            if stack is not None:
                in_players.append(stack)

    effective_stack = min(in_players) if len(in_players) >= 2 else 100.0

    # Default toy ranges; if your state later carries ranges, thread them in here.
    ip_range = "AA,KK,QQ,JJ,TT,99,AKs,AQs,AJs,KQs,AKo,AQo"
    oop_range = "AA,KK,QQ,JJ,TT,99,AKs,AQs,AJs,KQs,AKo,AQo"

    # Allow overrides if present in a loose 'player_ranges'
    pr = get("player_ranges", None)
    try:
        if isinstance(pr, (list, tuple)) and len(pr) >= 2:
            # heuristically map the first to IP, second to OOP if they look like strings
            r0 = pr[0].get("range") if isinstance(pr[0], dict) else getattr(pr[0], "range", None)
            r1 = pr[1].get("range") if isinstance(pr[1], dict) else getattr(pr[1], "range", None)
            if isinstance(r0, str) and r0.strip():
                ip_range = r0
            if isinstance(r1, str) and r1.strip():
                oop_range = r1
    except Exception:
        pass

    out_path = Path(tempfile.gettempdir()) / (RUNTIME_TMP_PREFIX + "out.json")
    script = build_fast_profile_input(
        pot=pot,
        effective_stack=effective_stack,
        board_cards=board_cards,
        ip_range_text=ip_range,
        oop_range_text=oop_range,
        betsize_pct=50,
        threads=_safe_threads(),
        accuracy=25.0,
        max_iteration=12,
        allin_threshold=0.67,
        output_path=str(out_path),
    )
    return script


def _extract_solver_script(maybe_script: Any) -> str:
    # Already a script string
    if isinstance(maybe_script, str):
        return maybe_script

    # Try common adapters on objects (e.g., Pydantic models/services)
    for attr in ("to_solver_script", "build_solver_script"):
        fn = getattr(maybe_script, attr, None)
        if callable(fn):
            s = fn()
            if not isinstance(s, str) or not s.strip():
                raise TexasSolverError(f"{attr}() must return non-empty str")
            return s

    # Direct field holding a script
    val = getattr(maybe_script, "script", None)
    if isinstance(val, str) and val.strip():
        return val

    # dict style payload
    if isinstance(maybe_script, dict):
        s = maybe_script.get("script")
        if isinstance(s, str) and s.strip():
            return s

    # Pydantic BaseModel with a 'script' field
    try:
        from pydantic import BaseModel  # type: ignore
        if isinstance(maybe_script, BaseModel):
            data = maybe_script.model_dump() if hasattr(maybe_script, "model_dump") else maybe_script.dict()
            s = data.get("script")
            if isinstance(s, str) and s.strip():
                return s
    except Exception:
        pass

    # Fallback: build from TableState-like data (board, seats, pot)
    try:
        return _build_script_from_state_like(maybe_script)
    except Exception as e:
        raise TexasSolverError(
            "TexasSolverClient.solve expected a solver script (str). "
            "Got object without a way to extract one. Provide a string script or "
            "implement one of: to_solver_script(), build_solver_script(), or a 'script' field."
        ) from e


# =========================
# TexasSolverClient
# =========================

class TexasSolverClient:
    """
    Thin client wrapper exposing a stable interface for API endpoints.
    Uses the module-level helpers you already have.
    """

    def __init__(self, base_url: Optional[str] = None, **_ignored: Any):
        # Accept base_url for compatibility; not used by the local exe wrapper.
        self.base_url = base_url

    def healthcheck(self) -> Dict[str, Any]:
        exe = TEXASSOLVER_EXE if isinstance(TEXASSOLVER_EXE, Path) else Path(TEXASSOLVER_EXE)
        base = TEXASSOLVER_DIR if isinstance(TEXASSOLVER_DIR, Path) else Path(TEXASSOLVER_DIR)
        resources = base / "resources"
        return {
            "exe_path": str(exe),
            "exe_exists": exe.exists() and exe.is_file(),
            "dir_path": str(base),
            "dir_exists": base.exists() and base.is_dir(),
            "resources_path": str(resources),
            "resources_exists": resources.exists() and resources.is_dir(),
        }

    def solve(self, input_text: Any, timeout_s: Optional[int] = None) -> dict:
        """
        Accepts either:
          - a solver input script (str), or
          - an object/dict providing enough state to build a minimal HU script.
        Returns parsed solver JSON or raises TexasSolverError/Timeout.
        """
        script = _extract_solver_script(input_text)
        return run_solver_with_input_text(
            script,
            timeout_sec=timeout_s or DEFAULT_SOLVER_TIMEOUT_SECONDS,
        )

    def solve_from_text(self, input_text: Any, timeout_s: Optional[int] = None) -> Tuple[int, Optional[dict], Optional[str]]:
        """
        Returns: (exit_code, result_or_None, error_or_None).
        Accepts the same inputs as solve().
        """
        try:
            script = _extract_solver_script(input_text)
            result = run_solver_with_input_text(script, timeout_sec=timeout_s or DEFAULT_SOLVER_TIMEOUT_SECONDS)
            return (0, result, None)
        except TexasSolverTimeout as e:
            return (408, None, str(e))
        except TexasSolverError as e:
            return (500, None, str(e))
        except Exception as e:
            return (500, None, f"Unexpected error: {e!r}")

    def solve_tuple(self, input_text: Any, timeout_s: Optional[int] = None) -> Tuple[int, Optional[dict], Optional[str]]:
        """Alias for callers preferring a tuple contract."""
        return self.solve_from_text(input_text, timeout_s=timeout_s)

    def solve_fast_profile(
        self,
        *,
        pot: float,
        effective_stack: float,
        board_cards,
        ip_range_text: str,
        oop_range_text: str,
        betsize_pct: int = 50,
        threads: int = _safe_threads(),
        accuracy: float = 5.0,
        max_iteration: int = 50,
        allin_threshold: float = 0.67,
        timeout_s: Optional[int] = None,
    ) -> dict:
        """Helper: build a minimal fast-profile tree and solve it."""
        out_path = Path(tempfile.gettempdir()) / (RUNTIME_TMP_PREFIX + "out.json")
        script = build_fast_profile_input(
            pot=pot,
            effective_stack=effective_stack,
            board_cards=board_cards,
            ip_range_text=ip_range_text,
            oop_range_text=oop_range_text,
            betsize_pct=betsize_pct,
            threads=threads,
            accuracy=accuracy,
            max_iteration=max_iteration,
            allin_threshold=allin_threshold,
            output_path=str(out_path),
        )
        return run_solver_with_input_text(script, timeout_sec=timeout_s or DEFAULT_SOLVER_TIMEOUT_SECONDS)


__all__ = [
    "TexasSolverError",
    "TexasSolverTimeout",
    "verify_solver_install",
    "build_fast_profile_input",
    "run_solver_with_input_text",
    "smoke_test",
    "TexasSolverClient",
]
