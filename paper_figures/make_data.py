"""Build the pgfplots data files for the journal figures from the RITM0996804 evidence, the 3 Nov 2026 runs
and the 7 Nov 2026 interleaved matrix series (experiments/matrix_series_B, summarised by analyse_exp.py).

Run:  VFL_DATA=<raw data folder> python3 make_data.py   (needs tcpdump on PATH; writes to data/)
The raw captures and logs are not in this repository; see README.md for the folder layout VFL_DATA must have.
"""
import csv, os, re, subprocess
from math import sqrt
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "data"
ROOT = Path(os.environ.get("VFL_DATA", HERE.parent / "raw_data"))  # raw captures and logs
EV = ROOT / "melbourne_incident/evidence_RITM0996804/server_melbourne"
NOV = ROOT / "experiments/vfl_nov03_plain_vs_tls"
MAIN = ROOT / "experiments/matrix_series_B/results/main"  # series B: plain vs TLS, 4 sizes, interleaved, home clients

# (folder, TLS, client location: 0 = home network, 1 = cloud VMs in QLD)
SERIES = [
    (EV / "fldiag_run1", False, 0), (EV / "fldiag_run2", False, 0), (EV / "fldiag_series", False, 0),
    (EV / "fldiag_mac_noecn", False, 0), (EV / "fldiag_qld", False, 1),
    (EV / "fldiag_tls_smoke", True, 0), (EV / "fldiag_mac_tls", True, 0), (EV / "fldiag_qld_tls", True, 1),
    (NOV / "run1/server", False, 0), (NOV / "run2/server", False, 0), (NOV / "run3/server", False, 0),
    (NOV / "tls1/server", True, 0),
]
RTT_BOUND_MS = {0: 4.58, 1: 13.47}  # 2d/v, v = 2.04e8 m/s; d = 467 km (Canberra) / 1,375 km (Brisbane) to Melbourne

ESTAB = re.compile(r"ESTAB\s+\d+\s+\d+\s+\S+:5010\s+\[?(?:::ffff:)?([\d.]+)\]?:(\d+)")
MINRTT = re.compile(r"\bminrtt:([\d.]+)")
RX = re.compile(r"\bbytes_received:(\d+)")


def tcpdump(pcap, flt=""):
    cmd = ["tcpdump", "-nn", "-tt", "-r", str(pcap)] + ([flt] if flt else [])
    return subprocess.run(cmd, capture_output=True, text=True, env={**os.environ, "TZ": "UTC"}).stdout.splitlines()


def hms(t):
    h, m, s = t.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def run_dirs(folder):
    subs = [d for d in folder.iterdir() if d.is_dir() and d.name.startswith("run")]
    return sorted(subs, key=lambda d: int(d.name[3:])) or [folder]


def client_ports(pcap):
    """Peer ports seen in this run's capture; the early ss loggers outlived their run."""
    ports = set()
    for line in tcpdump(pcap):
        m = re.search(r"IP [\d.]+\.(\d+) > 115\.146\.84\.72\.5010:", line)
        if m:
            ports.add(m.group(1))
    return ports


def minrtt_per_conn(run):
    ports, best, lines = client_ports(run / "fl5010.pcap"), {}, (run / "ss.log").read_text(errors="ignore").splitlines()
    for i, line in enumerate(lines[:-1]):
        m = ESTAB.search(line)
        if m and m.group(2) in ports:
            mm = MINRTT.search(lines[i + 1])
            if mm:
                key = m.group(2)
                best[key] = min(best.get(key, 1e9), float(mm.group(1)))
    return sorted(best.values())


def wilson(x, n, z=1.96):
    p, d = x / n, 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / d, z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def write(name, header, rows):
    with open(OUT / name, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def series_b():
    return [r for r in csv.DictReader(open(MAIN / "runs.csv")) if r["outcome"] != "invalid"]


def fig_minrtt():
    rows, below, total = [], 0, 0
    for folder, tls, loc in SERIES:
        group = 2 * int(tls) + loc + 1  # 1 plain/home, 2 plain/QLD, 3 TLS/home, 4 TLS/QLD
        for k, run in enumerate(run_dirs(folder)):
            for j, v in enumerate(minrtt_per_conn(run)):
                jitter = ((k * 7 + j * 3) % 11 - 5) * 0.045  # deterministic spread
                rows.append((round(group - 0.17 + jitter * 0.6, 3), v, group, "A"))
                if not tls:
                    total += 1
                    below += v < RTT_BOUND_MS[loc]
    print(f"series A: plain connections below the physical bound: {below} of {total}")
    below, total = 0, 0
    for k, r in enumerate(series_b()):
        group = 3 if r["tls"] == "1" else 1
        for j, v in enumerate(float(x) for x in r["minrtt_all"].split()):
            jitter = ((k * 7 + j * 3) % 11 - 5) * 0.045
            rows.append((round(group + 0.17 + jitter * 0.6, 3), v, group, "B"))
            if r["tls"] == "0":
                total += 1
                below += v < RTT_BOUND_MS[0]
    print(f"series B: plain connections below the physical bound: {below} of {total}")
    write("minrtt.csv", ["x", "minrtt", "group", "series"], rows)


def fig_three_records():
    """3 Nov run2, client_H_1 connection (Mac port 50818)."""
    run = NOV / "run2"
    lines = tcpdump(run / "server/fl5010.pcap", "tcp port 50818")
    t0, isn, server_ack = None, None, []
    for line in lines:
        t = float(line.split()[0])
        if t0 is None:
            t0, isn = t, int(re.search(r"seq (\d+)", line).group(1))
        m = re.search(r"115\.146\.84\.72\.5010 > .*?\back (\d+)", line)
        if m and "Flags [S" not in line:
            server_ack.append((round(t - t0, 4), int(m.group(1)) - 1))  # relative ack: bytes in order at server
    keep = [r for i, r in enumerate(server_ack) if i == 0 or r[1] != server_ack[i - 1][1]]
    keep.append((round(float(lines[-1].split()[0]) - t0, 4), keep[-1][1]))
    write("server_ack.csv", ["t", "bytes"], keep)

    day0 = t0 % 86400
    ss, ts = [], None
    for line in (run / "server/ss.log").read_text(errors="ignore").splitlines():
        if line.startswith("### "):
            ts = hms(line[4:].strip())
        elif "50818" in line:
            ss.append([round(ts - day0, 3), None])
        elif ss and ss[-1][1] is None and (m := RX.search(line)):
            ss[-1][1] = int(m.group(1))
    write("server_socket.csv", ["t", "bytes"], [r for r in ss if r[1] is not None])

    q, ts = [], None
    for line in (run / "sendq.log").read_text(errors="ignore").splitlines():
        if line.startswith("### "):
            ts = hms(line[4:].strip())
        elif ".50818 " in line and "ESTABLISHED" in line:
            q.append((round(ts - day0, 3), int(line.split()[2])))
    write("client_sendq.csv", ["t", "bytes"], q)


def fig_completion():
    # Table I campaign (float16 5 x N, 20 attempts per cell). Serialised ndarray = 10 N + 128 bytes.
    e1 = {50: 20, 1000: 7, 10000: 3, 100000: 1}
    rows = []
    for n, x in e1.items():
        s = 10 * n + 128
        for env, ok in (("E1", x), ("E2", 20)):
            lo, hi = wilson(ok, 20)
            rows.append((s, env, ok / 20, ok / 20 - lo, hi - ok / 20))
    # Series B: same matrices, plain and TLS interleaved in one session (offset on x so the bars do not overlap)
    b = series_b()
    for cols in (50, 1000, 10000, 100000):
        for tls, env, shift in ((0, "B_plain", 0.8), (1, "B_tls", 1.25)):
            sel = [r for r in b if int(r["cols"]) == cols and int(r["tls"]) == tls]
            n, ok = len(sel), sum(r["outcome"] == "completed" for r in sel)
            lo, hi = wilson(ok, n)
            rows.append((round((10 * cols + 128) * shift), env, round(ok / n, 4), round(ok / n - lo, 4), round(hi - ok / n, 4)))
    write("completion.csv", ["bytes", "env", "rate", "elo", "ehi"], rows)


def fig_seqack():
    """One 1 MB server-to-client transfer (5 x 100,000 average, round 2+) in series B, plain vs TLS, same session.
    Data: end of each server data segment; ack: each acknowledgement the server receives. Relative to the first segment."""
    for run, port, t_from, mode in (("r054_plain_100000", "50900", 1794029552.371, "plain"),
                                    ("r052_tls_100000", "50856", 1794029516.115, "tls")):
        seg = re.compile(r"([\d.]+) IP 115\.146\.84\.72\.5010 > [\d.]+\.%s: Flags \[[^\]]*\], seq (\d+):(\d+)" % port)
        ack = re.compile(r"([\d.]+) IP [\d.]+\.%s > 115\.146\.84\.72\.5010: Flags \[[^\]]*\],(?: seq \S+,)? ack (\d+)" % port)
        data, acks, t0, s0 = [], [], None, None
        for line in tcpdump(MAIN / run / "fl5010.pcap", f"tcp port {port}"):
            t = float(line.split()[0])
            if t < t_from - 0.0005:
                continue
            if (m := seg.match(line)):
                if t0 is None:
                    t0, s0 = t, int(m.group(2))
                if not data or data[-1][1] < 1000:  # the message ends at ~1,000.7 KB; later frames are control
                    data.append((round((t - t0) * 1000, 3), round((int(m.group(3)) - s0) / 1000, 2)))
            elif t0 is not None and (m := ack.match(line)) and int(m.group(2)) > s0:
                acks.append((round((t - t0) * 1000, 3), round((int(m.group(2)) - s0) / 1000, 2)))
                if acks[-1][1] >= data[-1][1] >= 1000:
                    break
        write(f"seqack_{mode}_data.csv", ["t", "kb"], data)
        write(f"seqack_{mode}_ack.csv", ["t", "kb"], acks)
        print(f"seqack {mode}: {data[-1][1]} KB sent by {data[-1][0]} ms, acked {acks[-1][1]} KB by {acks[-1][0]} ms")


def fig_deadline():
    """Series B plain stalls: time from round 1 start to the first failed reply, then the hang until the run was stopped."""
    rows = []
    for r in series_b():
        if r["outcome"] != "stalled":
            continue
        d = MAIN / r["label"]
        log = (d / "server.log").read_text(errors="ignore")
        m = re.search(r"^(\d+\.\d+) ROUND_START 1", log, re.M)
        if not m or not r["first_fail_round_s"]:
            continue  # one run never reached round 1
        t_start = float(m.group(1))
        t0 = min(float(re.match(r"(\d+\.\d+)", (d / f"client_{c}.log").read_text()).group(1)) for c in (1, 2, 3))
        err = " ".join((d / f"client_{c}.log").read_text(errors="ignore") for c in (1, 2, 3))
        t_fail = float(r["first_fail_round_s"])
        cause = ("deadline" if t_fail >= 59.9 else "etimedout" if "Operation timed out" in err
                 else "epipe" if "Broken pipe" in err else "other")
        rows.append([int(r["cols"]), t_fail, round(t0 + float(r["wall_s"]) - t_start, 1), cause])
    rows.sort(key=lambda x: (x[0], x[1]))
    for i, x in enumerate(rows):
        x.insert(0, i + 1)
    write("deadline.csv", ["y", "cols", "tfail", "tend", "cause", "xa", "xb", "eb"],
          [x + [round(x[2] / 2, 2), round((x[3] + x[2]) / 2, 2), round((x[3] - x[2]) / 2, 2)] for x in rows])


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    fig_minrtt()
    fig_three_records()
    fig_completion()
    fig_deadline()
    fig_seqack()
    print("written to", OUT)
