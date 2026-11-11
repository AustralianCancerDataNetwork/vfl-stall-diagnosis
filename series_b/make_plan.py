"""Write the interleaved run plan: REPS blocks, each holding every (size, transport) cell once in seeded random order.

Usage: make_plan.py <out file> [reps] [seed]
"""
import random
import sys

COLS = [50, 1000, 10000, 100000]  # Table I sizes, 5 x COLS float16
out, reps, seed = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 10, int(sys.argv[3]) if len(sys.argv) > 3 else 2026
rng = random.Random(seed)
with open(out, "w") as f:
    n = 0
    for rep in range(1, reps + 1):
        cells = [(c, t) for c in COLS for t in (0, 1)]
        rng.shuffle(cells)
        for cols, tls in cells:
            n += 1
            f.write(f"r{n:03d}_{'tls' if tls else 'plain'}_{cols} {cols} {tls}\n")
print(f"{n} runs written to {out} (seed {seed})")
