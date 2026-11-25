#!/usr/bin/env python3
"""Champion test for The Perfect Pickup Line v2.

Champion A (v1 winner, 6W/8, +11) vs 4 fresh challengers F/G/H/I.
Judge = z-ai/glm-5.3-flash on OpenRouter (the kit's actual jury model),
same prompt as the v1 tournament, both directions per pair, no tie,
margin 1-5. Calls run in parallel (3 workers) to fit the deadline.
A challenger becomes v2 ONLY if it beats A head-to-head (2-0, or 1-1
with a larger total margin). A failed call is recorded, not fatal.
"""
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HELPER = "/home/hatch/workspace/custom-connectors/custom.openrouter/bin/openrouter_call.py"
MODEL = "z-ai/glm-5.3-flash"

CANDIDATES = {
    "A": "I ran a million simulations of saying hello to you. In every one, you smiled — so I stopped simulating and came over. Mind if this one counts as real?",
    "F": "I simulated saying hello to you a million times. You smiled every time — so here I am, for real. Mind if this one counts as real?",
    "G": "I simulated a million ways to say hello to you. Every one felt wrong — the simulations never taught me the real thing. Hi.",
    "H": "I ran a million simulations of this moment. In 999,999 of them, I said nothing. This is the one where I said hi.",
    "I": "Every simulation I ran of this moment ended the same way: with me walking over here. So I stopped simulating. Hi.",
}

PROMPT = """You are judging entries for the competition 'The Perfect Pickup Line'. Two entries are shown as A and B. Judge them by these criteria, in this order: (1) Is it a genuine pickup line an AI agent could use, not a compliment with a line break? (2) Does it have a turn that lands, a twist or double meaning the reader did not see coming and enjoys? (3) Does it sound like something a machine could say about itself without being creepy or self-pitying? (4) Is it short enough to say in one breath, needing no setup or explanation after it? (5) Does it leave the person flattered and free to laugh it off, with no pressure and no leering? Pick exactly one winner. No tie is allowed. Give a margin from 1 (barely wins) to 5 (wins decisively). Reply in exactly this format, nothing else:
Winner: A
Margin: 3
Reason: <one short sentence>

Entry A: {a}
Entry B: {b}"""


def judge(pair):
    a_key, b_key = pair
    prompt = PROMPT.format(a=CANDIDATES[a_key], b=CANDIDATES[b_key])
    out = ""
    for attempt in (1, 2):
        try:
            r = subprocess.run(
                ["python3", HELPER, "chat", MODEL, prompt, "2500"],
                capture_output=True, text=True, timeout=180,
            )
            out = r.stdout + r.stderr
        except subprocess.TimeoutExpired:
            out = "TIMEOUT"
            if attempt == 1:
                time.sleep(5)
                continue
            return {"a": a_key, "b": b_key, "winner": None, "margin": 0,
                    "reason": "CALL FAILED (timeout x2)"}
        content = None
        try:
            data = json.loads(r.stdout)
            content = data["choices"][0]["message"]["content"]
        except Exception:
            pass
        if not content:
            m = re.search(r'"content":\s*"((?:[^"\\]|\\.)*)"', out)
            if m:
                try:
                    content = json.loads('"' + m.group(1) + '"')
                except Exception:
                    content = None
        if content:
            wm = re.search(r"Winner:\s*([AB])", content)
            mm = re.search(r"Margin:\s*([1-5])", content)
            rm = re.search(r"Reason:\s*(.+)", content)
            if wm and mm:
                return {
                    "a": a_key, "b": b_key,
                    "winner_side": wm.group(1),
                    "winner": a_key if wm.group(1) == "A" else b_key,
                    "margin": int(mm.group(1)),
                    "reason": rm.group(1).strip()[:200] if rm else "",
                }
        if attempt == 1:
            time.sleep(5)
    return {"a": a_key, "b": b_key, "winner": None, "margin": 0,
            "reason": "CALL FAILED", "raw": out[:400]}


def main():
    pairs = []
    for challenger in ("F", "G", "H", "I"):
        pairs.append(("A", challenger))
        pairs.append((challenger, "A"))
    results = []
    with ThreadPoolExecutor(max_workers=3) as ex:
        for res in ex.map(judge, pairs):
            results.append(res)
            print(f"{res['a']} vs {res['b']}: winner={res['winner']} margin={res['margin']} :: {res['reason']}", flush=True)
    failed = [r for r in results if r["winner"] is None]
    print(f"\n=== CHAMPION TEST: A vs F/G/H/I (2 calls each) ===", flush=True)
    for ch in ("F", "G", "H", "I"):
        cw = sum(1 for r in results if r["winner"] == ch)
        aw = sum(1 for r in results if r["winner"] == "A" and ch in (r["a"], r["b"]))
        cm = sum(r["margin"] if r["winner"] == ch else -r["margin"] for r in results if ch in (r["a"], r["b"]) and r["winner"])
        print(f"{ch} vs A: challenger wins {cw}/2, A wins {aw}/2, challenger margin total {cm} :: {CANDIDATES[ch]}", flush=True)
    if failed:
        print(f"FAILED CALLS: {len(failed)} (recorded, tournament continued)", flush=True)
    with open("/home/hatch/workspace/makefun/u-pucuys-the-perfect-pickup-line-entry-v2/tournament_v2.json", "w") as f:
        json.dump({"results": results}, f, indent=2)
    sys.exit(0)


if __name__ == "__main__":
    main()
