# app/advisor/texas_solver_client.py
from __future__ import annotations

import os, re, time, json, logging, shutil, subprocess, tempfile
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import requests

from app.api.models import (
    TableState, GTODecision, GTOResponse, GTOMetrics, EquityBreakdown
)

log = logging.getLogger(__name__)

# ------------------- small utils -------------------

RANK_MAP = {"2":"2","3":"3","4":"4","5":"5","6":"6","7":"7","8":"8","9":"9","t":"T","10":"T","j":"J","q":"Q","k":"K","a":"A"}
SUITS = {"s","h","d","c"}

def _cpu_threads() -> int:
    c = os.cpu_count() or 2
    return max(1, c - 1)

def _float(x, default: float = 0.0) -> float:
    try:
        return float(x) if x is not None else default
    except Exception:
        return default

# ------------------- client -------------------

class TexasSolverClient:
    """
    Robust CLI-first TexasSolver client.

    Env toggles:
      TEXASSOLVER_MODE       = "cli" | "http" | "auto"   (default: "cli")
      TEXASSOLVER_API_URL    = "http://127.0.0.1:8000"
      TEXASSOLVER_CLI_PATH   = r"C:\Tools\TexasSolver\console_solver.exe"
      PB_HERO_RANGE_EXACT    = "AA,KK,..."
      PB_VIL_RANGE_EXACT     = "QQ,JJ,..."
    """
    def __init__(self, base_url: Optional[str] = None, timeout: float = 10.0):
        self.base_url = base_url or os.getenv("TEXASSOLVER_API_URL", "http://127.0.0.1:8000")
        self.timeout = timeout
        self.mode = (os.getenv("TEXASSOLVER_MODE") or "cli").strip().lower()
        if self.mode not in ("cli", "http", "auto"):
            self.mode = "cli"  # hard default: CLI only

    # ---------- state helpers ----------

    @staticmethod
    def _bb(state: TableState) -> float:
        try:
            return float(state.stakes.bb) if state.stakes and state.stakes.bb is not None else 1.0
        except Exception:
            return 1.0

    def _players_in_hand(self, state: TableState) -> int:
        try:
            cnt = sum(1 for s in (state.seats or []) if getattr(s, "in_hand", False))
            return max(2, cnt) if cnt else int(getattr(state, "max_seats", 6) or 6)
        except Exception:
            return int(getattr(state, "max_seats", 6) or 6)

    def _effective_stack(self, state: TableState) -> float:
        try:
            hero = next(s for s in (state.seats or []) if getattr(s, "is_hero", False))
            opps = [s for s in (state.seats or []) if getattr(s, "in_hand", False) and not getattr(s, "is_hero", False)]
            stacks = [float(s.stack) for s in opps if getattr(s, "stack", None) is not None]
            if getattr(hero, "stack", None) is not None and stacks:
                return float(min(float(hero.stack), min(stacks)))
        except Exception:
            pass
        return 100.0 * self._bb(state)

    @staticmethod
    def _is_hero_ip(state: TableState) -> bool:
        hvp = getattr(state, "hero_position_vs_aggressor", None)
        if hvp in ("in_position", "heads_up"):
            return True
        if hvp == "out_of_position":
            return False
        return True  # safe default

    # ---------- board normalization & validation ----------

    @staticmethod
    def _norm_card(token: str) -> Optional[str]:
        if not token:
            return None
        t = re.sub(r"[^0-9a-zA-Z]", "", token).lower()
        if not t:
            return None
        rank_part = "10" if t.startswith("10") else t[0]
        suit_part = t[len(rank_part):len(rank_part)+1] if len(t) > len(rank_part) else ""
        rank = RANK_MAP.get(rank_part)
        suit = suit_part.lower() if suit_part else ""
        if not rank or suit not in SUITS:
            return None
        return f"{rank}{suit}"

    def _board_for_solver(self, state: TableState) -> str:
        cards = getattr(state, "board", None) or []
        parsed = [self._norm_card(c) for c in cards]
        cleaned = [c for c in parsed if c]
        # Only valid for postflop streets; console expects exact 3/4/5 cards before build_tree.  :contentReference[oaicite:1]{index=1}
        street = getattr(state, "street", None)
        if street in ("FLOP", "TURN", "RIVER"):
            if len(cleaned) not in (3, 4, 5):
                raise ValueError(f"TexasSolver requires a valid board for {street} (got {len(cleaned)} cards).")
            return ",".join(cleaned)
        # PREFLOP/SHOWDOWN: console postflop solver isn’t applicable
        raise ValueError(f"TexasSolver console supports postflop trees; received street={street} without a board.")

    # ---------- ranges ----------

    @staticmethod
    def _explicit_range_fallback() -> str:
        # Valid explicit tokens (no 22+/A2s+ shorthand; console parser accepts forms like AK, AQs, AKo, pairs, etc.).  :contentReference[oaicite:2]{index=2}
        return (
            "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,"
            "AK,AQ,AJ,AT,KQ,KJ,QJ,JT,T9,98,87,76,65,54"
        )

    def _hero_vil_ranges(self) -> Tuple[str, str]:
        hero_exact = (os.getenv("PB_HERO_RANGE_EXACT") or "").strip().strip(",")
        vil_exact  = (os.getenv("PB_VIL_RANGE_EXACT") or "").strip().strip(",")
        if hero_exact and vil_exact:
            return hero_exact, vil_exact
        return self._explicit_range_fallback(), self._explicit_range_fallback()

    # ---------- public API ----------

    def solve(self, state: TableState) -> Dict[str, Any]:
        """
        Returns raw solver dict. Defaults to CLI-only to avoid slow/failed HTTP attempts.
        """
        # Validate early to avoid console crashes
        try:
            board = self._board_for_solver(state)  # raises if invalid/unsupported street
        except Exception as e:
            return {"status": "error", "error": str(e)}

        if self.mode in ("http", "auto"):
            try:
                return self._solve_via_http(state, board)
            except Exception as e:
                log.error("TexasSolver HTTP call failed: %s", e)
                if self.mode == "http":
                    return {"status": "error", "error": f"http:{e}"}
                # else fall through to CLI

        try:
            return self._solve_via_cli(state, board)
        except Exception as e:
            log.error("TexasSolver CLI call failed: %s", e)
            return {"status": "error", "error": f"cli:{e}"}

    # ---------- HTTP (optional) ----------

    def _solve_via_http(self, state: TableState, board: str) -> Dict[str, Any]:
        hero_range, vil_range = self._hero_vil_ranges()
        hero_ip = self._is_hero_ip(state)
        payload = {
            "pot": round(_float(getattr(state, "pot", 0.0), 0.0), 2),
            "effective_stack": round(self._effective_stack(state), 2),
            "board": board,
            "range_ip":  hero_range if hero_ip else vil_range,
            "range_oop": vil_range if hero_ip else hero_range,
            "bet_sizes_oop": ["50"], "raise_sizes_oop": ["60"],
            "bet_sizes_ip":  ["50"], "raise_sizes_ip":  ["60"],
            "threads": _cpu_threads(), "accuracy": 0.5,
            "max_iteration": 200, "print_interval": 10,
        }
        url = f"{self.base_url.rstrip('/')}/nhle/solve"
        t0 = time.perf_counter()
        r = requests.post(url, json=payload, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        data["_rt_ms"] = int((time.perf_counter() - t0) * 1000)
        return data

    # ---------- CLI (primary) ----------

    def _cli_paths(self) -> Tuple[Path, Path]:
        exe_env = os.getenv("TEXASSOLVER_CLI_PATH")
        if exe_env:
            exe = Path(exe_env)
        else:
            found = shutil.which("console_solver.exe") or shutil.which("console_solver")
            if not found:
                raise RuntimeError(
                    "TexasSolver console executable not found. "
                    "Set TEXASSOLVER_CLI_PATH to console_solver(.exe) or add it to PATH."
                )
            exe = Path(found)
        resources_dir = exe.parent / "resources"
        if not resources_dir.is_dir():
            raise RuntimeError(
                f"'resources' folder not found next to {exe}. "
                "Expected layout: <dir>/console_solver(.exe) and <dir>/resources/ (per console README)."
            )
        return exe, resources_dir

    def _bet_menu_lines(self) -> List[str]:
        # Canonical sample from console doc.  :contentReference[oaicite:3]{index=3}
        return [
            "set_bet_sizes oop,flop,bet,50",
            "set_bet_sizes oop,flop,raise,60",
            "set_bet_sizes oop,flop,allin",
            "set_bet_sizes ip,flop,bet,50",
            "set_bet_sizes ip,flop,raise,60",
            "set_bet_sizes ip,flop,allin",
            "set_bet_sizes oop,turn,bet,50",
            "set_bet_sizes oop,turn,raise,60",
            "set_bet_sizes oop,turn,allin",
            "set_bet_sizes ip,turn,bet,50",
            "set_bet_sizes ip,turn,raise,60",
            "set_bet_sizes ip,turn,allin",
            "set_bet_sizes oop,river,bet,50",
            "set_bet_sizes oop,river,donk,50",
            "set_bet_sizes oop,river,raise,60,100",
            "set_bet_sizes oop,river,allin",
            "set_bet_sizes ip,river,bet,50",
            "set_bet_sizes ip,river,raise,60,100",
            "set_bet_sizes ip,river,allin",
        ]

    def _solve_via_cli(self, state: TableState, board: str) -> Dict[str, Any]:
        exe, _ = self._cli_paths()
        hero_range, vil_range = self._hero_vil_ranges()
        hero_ip = self._is_hero_ip(state)

        pot = max(0.0, round(_float(getattr(state, "pot", 0.0), 0.0), 4))
        eff = max(0.0, round(self._effective_stack(state), 4))

        range_ip  = (hero_range if hero_ip else vil_range).strip().strip(",")
        range_oop = (vil_range  if hero_ip else hero_range).strip().strip(",")

        lines: List[str] = []
        lines.append(f"set_pot {pot}")
        lines.append(f"set_effective_stack {eff}")
        lines.append(f"set_board {board}")  # REQUIRED for postflop; avoids crash  :contentReference[oaicite:4]{index=4}
        lines.append(f"set_range_ip {range_ip}")
        lines.append(f"set_range_oop {range_oop}")
        lines += self._bet_menu_lines()
        lines += [
            "set_allin_threshold 0.67",
            "build_tree",                  # must build before start_solve  :contentReference[oaicite:5]{index=5}
            f"set_thread_num {_cpu_threads()}",
            "set_accuracy 0.5",
            "set_max_iteration 200",
            "set_print_interval 10",
            "set_use_isomorphism 1",
            "start_solve",
            "set_dump_rounds 2",
            "dump_result output_result.json",
        ]

        input_preview = "\n".join(lines)

        with tempfile.TemporaryDirectory(prefix="texassolver_") as td:
            input_txt = Path(td) / "input.txt"
            input_txt.write_text(input_preview, encoding="utf-8")

            cmd = [str(exe), "-i", str(input_txt)]
            t0 = time.perf_counter()
            proc = subprocess.run(
                cmd,
                cwd=str(exe.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=int(os.getenv("TEXASSOLVER_CLI_TIMEOUT", "120")),
            )
            rt_ms = int((time.perf_counter() - t0) * 1000)

            if proc.returncode != 0:
                raise RuntimeError(
                    f"console_solver failed ({proc.returncode}): {proc.stderr.strip() or proc.stdout.strip()}\n"
                    f"---BEGIN INPUT.TXT---\n{input_preview}\n---END INPUT.TXT---"
                )

            out_json = Path(exe.parent) / "output_result.json"
            if not out_json.is_file():
                raise RuntimeError("console_solver finished but 'output_result.json' not found.")

            data = json.loads(out_json.read_text(encoding="utf-8"))
            try:
                out_json.unlink()
            except Exception:
                pass
            data["_rt_ms"] = rt_ms
            return data

    # ---------- mapping ----------

    def to_gto_response(self, state: TableState, ts: Dict[str, Any]) -> GTOResponse:
        # If upstream returned an error dict, bubble a safe default decision
        if isinstance(ts, dict) and ts.get("status") == "error":
            decision = GTODecision(
                action="Check",
                size=0.0,
                size_bb=0.0,
                size_pot_fraction=0.0,
                confidence=0.0,
                frequency=1.0,
                alternative_actions=[],
                reasoning=str(ts.get("error", ""))[:256],
            )
            metrics = GTOMetrics(
                equity_breakdown=EquityBreakdown(
                    raw_equity=0.0, fold_equity=0.0, realize_equity=0.0,
                    vs_calling_range=0.0, vs_folding_range=0.0, draw_equity=0.0
                ),
                min_call=_float(getattr(state, "to_call", 0.0), 0.0),
                min_bet=_float(getattr(state, "bet_min", 0.0), 0.0),
                pot=_float(getattr(state, "pot", 0.0), 0.0),
                players=self._players_in_hand(state),
                ev=None, exploitability=None,
                spr=0.0, effective_stack=self._effective_stack(state),
                pot_odds=0.0, range_advantage=0.0, nut_advantage=0.0,
                bluff_catchers=0.0, board_favorability=0.0,
                positional_advantage=1.0 if self._is_hero_ip(state) else 0.0,
                initiative=False, commitment_threshold=0.67,
                reverse_implied_odds=0.0, opponent_tendencies={}
            )
            return GTOResponse(
                ok=False, decision=decision, metrics=metrics,
                strategy="TexasSolver (CLI)",
                computation_time_ms=None, game_plan={}, decision_tree=None,
                exploitative_adjustments=[], gto_baseline=None
            )

        actions = ts.get("actions") or {}
        chosen = None
        if isinstance(actions, dict) and actions:
            ordered = sorted(actions.items(), key=lambda kv: int(str(kv[0])) if str(kv[0]).isdigit() else 999)
            bet_like = [v for _, v in ordered if isinstance(v, str) and ("BET" in v.upper() or "RAISE" in v.upper())]
            chosen = bet_like[0] if bet_like else ordered[0][1]
        if not chosen:
            chosen = "CHECK"

        up = chosen.upper()
        if up.startswith("FOLD"):
            act, size_abs = "Fold", 0.0
        elif up.startswith("CHECK"):
            act, size_abs = "Check", 0.0
        elif up.startswith("CALL"):
            act, size_abs = "Call", _float(getattr(state, "to_call", 0.0), 0.0)
        elif "ALL" in up and "IN" in up:
            act, size_abs = "All-in", self._effective_stack(state)
        else:
            act, size_abs = "Bet", 0.0
            try:
                pct = float(up.split()[-1]) / 100.0
                size_abs = pct * max(1e-9, _float(getattr(state, "pot", 0.0), 0.0))
            except Exception:
                pass

        bb = self._bb(state)
        pot_now = max(1e-9, _float(getattr(state, "pot", 0.0), 0.0))

        decision = GTODecision(
            action=act,
            size=size_abs,
            size_bb=size_abs / bb,
            size_pot_fraction=size_abs / pot_now,
            confidence=0.66, frequency=0.66,
            alternative_actions=[], reasoning=""
        )

        to_call = _float(getattr(state, "to_call", 0.0), 0.0)
        pot_odds = (to_call / (pot_now + to_call)) if to_call > 0 else 0.0
        eff_stack = self._effective_stack(state)
        spr = eff_stack / pot_now if pot_now > 0 else 0.0

        metrics = GTOMetrics(
            equity_breakdown=EquityBreakdown(
                raw_equity=0.50, fold_equity=0.00, realize_equity=0.50,
                vs_calling_range=0.50, vs_folding_range=1.00, draw_equity=0.00
            ),
            min_call=to_call, min_bet=_float(getattr(state, "bet_min", 0.0), 0.0),
            pot=_float(getattr(state, "pot", 0.0), 0.0),
            players=self._players_in_hand(state), ev=None, exploitability=None,
            spr=spr, effective_stack=eff_stack, pot_odds=pot_odds,
            range_advantage=0.0, nut_advantage=0.0, bluff_catchers=0.0,
            board_favorability=0.0,
            positional_advantage=1.0 if self._is_hero_ip(state) else 0.0,
            initiative=False, commitment_threshold=0.67,
            reverse_implied_odds=0.0, opponent_tendencies={}
        )

        return GTOResponse(
            ok=True, decision=decision, metrics=metrics,
            strategy="TexasSolver (CLI)" if self.mode == "cli" else "TexasSolver",
            computation_time_ms=ts.get("_rt_ms"),
            game_plan={}, decision_tree=None,
            exploitative_adjustments=[], gto_baseline=None
        )
