# app/advisor/texas_solver_client.py
import os, time, logging
from typing import Dict, Any, Tuple
import requests

from app.api.models import TableState, GTODecision, GTOResponse, GTOMetrics

log = logging.getLogger(__name__)

class TexasSolverClient:
    def __init__(self, base_url: str | None = None, timeout: float = 10.0):
        self.base_url = base_url or os.getenv("TEXASSOLVER_API_URL", "http://127.0.0.1:8000")
        self.timeout = timeout

    @staticmethod
    def _board_str(board_cards: list[str]) -> str:
        # Expecting lowercase like ["qs","jh","2h"]; TexasSolver accepts "Qs,Jh,2h"
        return ",".join([c[0].upper() + c[1].lower() for c in (board_cards or [])])

    @staticmethod
    def _default_unk_villain_range() -> str:
        # Safe generic: ~28–32% opening/defend; tune later.
        return "22+,A2s+,K9s+,QTs+,JTs,T9s,98s,87s,A9o+,KTo+,QTo+,JTo"

    def _hero_villain_ranges(self, state: TableState) -> Tuple[str, str]:
        # Minimal viable mapping: use your strategy file later; for now generic ranges.
        # If you already know position/open/3bet context, swap in tighter ranges.
        hero_range   = os.getenv("PB_HERO_RANGE",   self._default_unk_villain_range())
        villain_range= os.getenv("PB_VIL_RANGE",    self._default_unk_villain_range())
        return hero_range, villain_range

    def _effective_stack(self, state: TableState) -> float:
        # If your TableState has per-seat stacks, compute min(hero, nearest opponent).
        try:
            hero = next(s for s in state.seats if s.is_hero)
            opps = [s for s in state.seats if (s.in_hand and not s.is_hero)]
            stacks = [s.stack for s in opps if s.stack is not None]
            if hero.stack is not None and stacks:
                return float(min(hero.stack, min(stacks)))
        except Exception:
            pass
        # Fallback if unknown; 100bb is a sane default
        return max(1.0, float(getattr(state, "effective_stack", 100 * state.stakes.bb if state.stakes else 100.0)))

    def _pot(self, state: TableState) -> float:
        try:
            return float(state.pot)
        except Exception:
            return 0.0

    def _bet_menus(self) -> Dict[str, list[str]]:
        # Keep tree small for 5–7s solves: 1–2 sizes + all-in
        # You can tune per-street later (e.g., 33/66 on flop, 66 on turn, 75 on river)
        return {
            "bet_sizes_oop": ["33", "66"],
            "raise_sizes_oop": ["60"],
            "bet_sizes_ip": ["33", "66"],
            "raise_sizes_ip": ["60"]
        }

    def solve(self, state: TableState) -> Dict[str, Any]:
        hero_range, villain_range = self._hero_villain_ranges(state)
        payload = {
            "pot":             round(self._pot(state), 2),
            "effective_stack": round(self._effective_stack(state), 2),
            "board":           self._board_str(state.board),
            "range_ip":        hero_range if state.hero_in_position else villain_range,
            "range_oop":       villain_range if state.hero_in_position else hero_range,
            **self._bet_menus(),
            "threads": max(1, os.cpu_count() - 1),
            "accuracy": 1.0,
            "max_iteration": 120,
            "print_interval": 20
        }
        url = f"{self.base_url}/nhle/solve"
        t0 = time.perf_counter()
        try:
            r = requests.post(url, json=payload, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
            data["_rt_ms"] = int((time.perf_counter() - t0) * 1000)
            return data
        except Exception as e:
            log.error("TexasSolver call failed: %s", e)
            return {"status": "error", "error": str(e)}

    def to_gto_response(self, state: TableState, ts: Dict[str, Any]) -> GTOResponse:
        # Map solver output into your GTOResponse/GTODecision/GTOMetrics shapes.
        # 'actions' might be {0:"CHECK",1:"BET 50",...}. We pick the first for now.
        actions = ts.get("actions", {})
        # crude pick: first action; replace with highest-frequency once you parse ts["raw"] strategy table
        rec = list(actions.values())[0] if actions else "CHECK"
        action_name = "Check" if rec.startswith("CHECK") else (
            "Call" if rec.startswith("CALL") else (
                "Fold" if rec.startswith("FOLD") else (
                    "All-in" if "ALLIN" in rec.upper() else "Bet")))
        size_abs = 0.0
        # If "BET 50" style, treat as % pot and compute absolute
        if "BET" in rec.upper():
            try:
                pct = float(rec.split()[-1]) / 100.0
                size_abs = pct * self._pot(state)
            except Exception:
                pass

        decision = GTODecision(
            action=action_name, size=size_abs,
            size_bb=size_abs / (state.stakes.bb if state.stakes else 1.0),
            size_pot_fraction=(size_abs / max(1e-9, self._pot(state))),
            confidence=0.66, frequency=0.66,
            alternative_actions=[]
        )
        metrics = GTOMetrics(
            equity_breakdown={"our": 0.5, "villain": 0.5, "draw": 0.0},  # placeholder
            min_call=float(state.to_call or 0.0),
            min_bet=float(state.bet_min or 0.0),
            pot=self._pot(state),
            players=int(state.players or state.max_seats or 6),
            spr=float(self._effective_stack(state) / max(1e-9, self._pot(state))),
            effective_stack=self._effective_stack(state),
            pot_odds=0.0,
            range_advantage=0.0,
            nut_advantage=0.0,
            bluff_catchers=0.0
        )
        return GTOResponse(
            ok=True, decision=decision, metrics=metrics,
            strategy="TexasSolver (WSL bridge)"
        )
