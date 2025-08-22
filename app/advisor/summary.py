# app/advisor/summary.py
from typing import Dict, Any, Tuple, Optional

def _pick_recommendation(strategy: Dict[str, float], min_weight=0.05) -> Tuple[str, float]:
    """
    Given a root strategy mapping action->probability, choose a single action.
    - Collapse BET x.y to unified 'BET' w/ size
    - If mixed, pick max prob above threshold; else pick argmax.
    Returns (action_name, size) where size=0 for non-bets.
    """
    if not strategy:
        return ("CHECK", 0.0)

    # Normalize
    total = sum(strategy.values()) or 1.0
    strat = {k: v/total for k, v in strategy.items()}

    # Extract bet sizes
    best_a, best_p, best_size = None, -1.0, 0.0
    for act, p in strat.items():
        size = 0.0
        act_upper = act.upper()
        if act_upper.startswith("BET "):
            try:
                size = float(act_upper.split()[1])
                base = "BET"
            except Exception:
                base = "BET"
        elif act_upper.startswith("RAISE "):
            try:
                size = float(act_upper.split()[1])
                base = "RAISE"
            except Exception:
                base = "RAISE"
        else:
            base = act_upper

        if p > best_p and p >= min_weight:
            best_a, best_p, best_size = base, p, size

    if best_a is None:
        # no action above threshold: take argmax
        best_a, best_size = max(((a, float(a.split()[1]) if a.upper().startswith(("BET","RAISE")) else 0.0, p)
                                 for a, p in strat.items()), key=lambda t: t[2])[:2]

        best_a = best_a.split()[0].upper()  # "BET", "CALL", etc.

    return best_a, best_size


def summarize_solver_result(data: Dict[str, Any],
                            to_call: float,
                            pot: float,
                            bb: float) -> Dict[str, Any]:
    """
    Returns a compact, user-friendly summary:
      - recommended_action: "CHECK" / "CALL" / "FOLD" / "BET" / "RAISE"
      - amount: numeric (chips), 0 for non-bet
      - pct_pot: for bet/raise, rounded pot %
      - mix: condensed strategy (top 3 actions)
      - notes: short line with EV/exploitability if present
    """
    # Strategy key varies by build; try common keys
    strat = data.get("strategy") or data.get("root_strategy") or {}

    # If strategy not at root, some builds place it under children of current player node.
    if not strat and "childrens" in data:
        # Best effort: if there’s exactly one acting node under root, look for its strategy
        for child in data["childrens"].values():
            if isinstance(child, dict) and ("strategy" in child or "root_strategy" in child):
                strat = child.get("strategy") or child.get("root_strategy")
                break

    rec_action, amount = _pick_recommendation(strat)

    # Round bet size to a friendly number (to nearest 0.5bb by default)
    def round_to_bb(x: float, step_bb=0.5):
        step = step_bb * bb
        return round(x / step) * step

    amount_rounded = round_to_bb(amount) if rec_action in ("BET", "RAISE") else 0.0
    pct_pot = (amount_rounded / pot * 100.0) if (rec_action in ("BET","RAISE") and pot > 0) else 0.0

    # Condense the mix (top 3)
    mix_sorted = sorted(strat.items(), key=lambda kv: kv[1], reverse=True)
    mix_short = [(a, round(p*100, 1)) for a, p in mix_sorted[:3]]

    # Optional EV/exploitability fields vary by build; include if present
    notes_parts = []
    if "exploitability" in data:
        notes_parts.append(f"exploitability {data['exploitability']:.2f}%")
    if "time_used" in data:
        notes_parts.append(f"time {data['time_used']:.2f}s")
    notes = " · ".join(notes_parts) if notes_parts else ""

    return {
        "recommended_action": rec_action,
        "amount": amount_rounded,
        "pct_pot": round(pct_pot),
        "mix": mix_short,
        "to_call": to_call,
        "pot": pot,
        "bb": bb,
        "notes": notes,
    }
