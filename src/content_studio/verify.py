"""Check the critic's marks against the packet. A mark below 4 counts only with a quote that really is in the packet."""
import re

CRITERIA = ("evidence", "value", "send_reason", "hook", "originality", "rules")
THRESHOLD = 18


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def verify_marks(packet: str, marks: list[dict], out_there: set[str] | frozenset = frozenset()) -> list[dict]:
    text = _norm(packet)
    results = []
    for m in marks:
        try:
            label, scores, quotes = m["option"], m["scores"], m.get("quotes") or {}
        except (KeyError, TypeError, AttributeError):
            raise ValueError("each mark needs option, scores and quotes") from None
        if set(scores) != set(CRITERIA) or not all(isinstance(v, int) and not isinstance(v, bool) and 1 <= v <= 5 for v in scores.values()):
            raise ValueError(f"option {label}: scores must be whole numbers 1 to 5 for exactly {', '.join(CRITERIA)}")
        rejected, valid = [], {}
        for c in CRITERIA:
            v, q = scores[c], _norm(str(quotes.get(c) or ""))
            if v < 4 and not (q and q in text):
                rejected.append(c)
                v = 4
            valid[c] = v
        total = sum(valid.values())
        below = total < THRESHOLD or 1 in valid.values()
        spared = below and label in out_there
        results.append({"option": label, "total": total, "dropped": below and not spared, "rejected": rejected,
                        "flag": "below threshold, your call" if spared else None})
    return results
