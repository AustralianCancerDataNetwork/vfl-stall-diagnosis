"""Summarise a run_exp.sh series: outcome, round latency, deadline behaviour and minrtt per run and per cell.

Usage: analyse_exp.py <series>   (reads results/<series>/, writes runs.csv and cells.csv there)

Outcome per run, from the server log:
  completed  all rounds ended with 3 results and 0 failures
  deadline   the server finished, but round_timeout ended at least one round with failures
  stalled    the server never finished (killed by run_exp.sh)
  invalid    no server log: the ssh session that starts the server failed, so the run did not happen
"""
import csv
import re
import statistics
import sys
from math import sqrt
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "results" / sys.argv[1]
ROUND = re.compile(r"^(\d+\.\d+) ROUND_(START|END) (\d+)(?: results=(\d+) failures=(\d+))?")
ESTAB = re.compile(r"ESTAB\s.*?:5010\s+\S+:(\d+)")
MINRTT = re.compile(r"\bminrtt:([\d.]+)")


def wilson(x, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan")
    p, d = x / n, 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / d, z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def parse_run(d):
    log = (d / "server.log").read_text(errors="ignore") if (d / "server.log").exists() else ""
    starts, ends = {}, {}
    for line in log.splitlines():
        m = ROUND.match(line)
        if m:
            t, kind, r = float(m.group(1)), m.group(2), int(m.group(3))
            if kind == "START":
                starts[r] = t
            else:
                ends[r] = (t, int(m.group(4)), int(m.group(5)))
    if not log:
        outcome = "invalid"
    elif "SERVER_DONE" not in log:
        outcome = "stalled"
    elif all(res == 3 and fail == 0 for _, res, fail in ends.values()) and len(ends) == 5:
        outcome = "completed"
    else:
        outcome = "deadline"
    rounds = [ends[r][0] - starts[r] for r in sorted(ends) if r in starts and ends[r][2] == 0]
    minrtt = {}
    if (d / "ss.log").exists():
        lines = (d / "ss.log").read_text(errors="ignore").splitlines()
        for i, line in enumerate(lines[:-1]):
            m, mm = ESTAB.search(line), MINRTT.search(lines[i + 1])
            if m and mm:
                minrtt[m.group(1)] = min(minrtt.get(m.group(1), 1e9), float(mm.group(1)))
    return {
        "outcome": outcome,
        "rounds_ok": sum(1 for _, res, fail in ends.values() if fail == 0),
        "rounds_failed": sum(1 for _, res, fail in ends.values() if fail > 0),
        "first_fail_round_s": next((round(ends[r][0] - starts[r], 1) for r in sorted(ends) if ends[r][2] > 0 and r in starts), ""),
        "round_s_median": round(statistics.median(rounds), 3) if rounds else "",
        "minrtt_min": round(min(minrtt.values()), 3) if minrtt else "",
        "minrtt_all": " ".join(f"{v:.3f}" for v in sorted(minrtt.values())),
    }


rows = []
for line in (ROOT / "results.txt").read_text().splitlines():
    parts = line.split()
    label, cols, tls = parts[1], int(parts[2].split("=")[1]), int(parts[3].split("=")[1])
    rows.append({"label": label, "cols": cols, "tls": tls, "bytes": 10 * cols + 128,
                 "wall_s": parts[5].rstrip("s"), **parse_run(ROOT / label)})

with open(ROOT / "runs.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

cells = []
for cols in sorted({r["cols"] for r in rows}):
    for tls in (0, 1):
        sel = [r for r in rows if r["cols"] == cols and r["tls"] == tls and r["outcome"] != "invalid"]
        if not sel:
            continue
        n, ok = len(sel), sum(r["outcome"] == "completed" for r in sel)
        lo, hi = wilson(ok, n)
        lat = [r["round_s_median"] for r in sel if r["round_s_median"] != ""]
        rtt = [r["minrtt_min"] for r in sel if r["minrtt_min"] != ""]
        cells.append({
            "cols": cols, "bytes": 10 * cols + 128, "tls": tls, "n": n, "completed": ok,
            "deadline": sum(r["outcome"] == "deadline" for r in sel),
            "deadline_fired": sum(r["first_fail_round_s"] != "" for r in sel),
            "stalled": sum(r["outcome"] == "stalled" for r in sel),
            "rate": round(ok / n, 3), "ci_lo": round(lo, 3), "ci_hi": round(hi, 3),
            "round_s_median": round(statistics.median(lat), 3) if lat else "",
            "minrtt_median": round(statistics.median(rtt), 3) if rtt else "",
        })
with open(ROOT / "cells.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(cells[0]))
    w.writeheader()
    w.writerows(cells)

print("excluded (invalid):", " ".join(r["label"] for r in rows if r["outcome"] == "invalid"))
print(f"{'cols':>7} {'tls':>3} {'n':>3} {'ok':>3} {'ddl':>3} {'stl':>3}  rate [95% CI]        round(s)  minrtt(ms)")
for c in cells:
    print(f"{c['cols']:>7} {c['tls']:>3} {c['n']:>3} {c['completed']:>3} {c['deadline']:>3} {c['stalled']:>3}  "
          f"{c['rate']:.2f} [{c['ci_lo']:.2f}, {c['ci_hi']:.2f}]   {c['round_s_median']!s:>8}  {c['minrtt_median']!s:>8}")
