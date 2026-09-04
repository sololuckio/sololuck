#!/usr/bin/env python3
"""pool-latency.py — measure YOUR latency to solo-mining pools, from wherever the miner will live.

What it measures, per pool:
  tcp_ms   median time to open a TCP connection (one network round trip)
  sub_ms   time for a real stratum "mining.subscribe" handshake on a fresh
           connection — connect + the pool's answer, i.e. what a miner waits for
  tls      for TLS ports: connect + TLS handshake + subscribe

Honest notes:
  * Latency does NOT change your odds of finding a block. It only affects how
    quickly your miner gets new work and how many shares go stale.
  * Run it from the network the miner will use. A phone hotspot, a VPN or an
    office line will give a different answer from the miner's home Wi-Fi.
  * Numbers move with time of day and routing. Run it twice, an hour apart.

Needs only Python 3 (python.org build is fine, no packages). Run:
    python3 pool-latency.py            # Linux / macOS
    py pool-latency.py                 # Windows
Add your own pool:  python3 pool-latency.py host:port [host:port ...]
"""
import json, socket, ssl, statistics, sys, time

POOLS = [
    # label,                     host,                      port,  tls
    ("ausolo.ckpool.org (AU)",   "ausolo.ckpool.org",       3333,  False),
    ("SoloLuck (Jakarta)",       "stratum.sololuck.io",     3333,  False),
    ("SoloLuck TLS (Jakarta)",   "stratum.sololuck.io",     3334,  True),
    ("solo.ckpool.org (US)",     "solo.ckpool.org",         3333,  False),
    ("public-pool.io (US)",      "public-pool.io",          21496, False),
    ("Braiins Solo (EU)",        "solo.stratum.braiins.com",3333,  False),
    ("AtlasPool (anycast)",      "solo.atlaspool.io",       3333,  False),
]
SAMPLES  = 6      # TCP connects per pool, spaced out (pools rate-limit bursts)
SPACING  = 0.5    # seconds between connects
TIMEOUT  = 5      # seconds per attempt
SUBSCRIBE = json.dumps({"id": 1, "method": "mining.subscribe",
                        "params": ["pool-latency/1.0"]}) + "\n"


def resolve(host):
    try:
        info = socket.getaddrinfo(host, None, socket.AF_INET, socket.SOCK_STREAM)
        return info[0][4][0]
    except Exception as e:
        return None


def tcp_connect_ms(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(TIMEOUT)
    t0 = time.perf_counter()
    try:
        s.connect((ip, port))
        return (time.perf_counter() - t0) * 1000.0
    except Exception:
        return None
    finally:
        s.close()


def subscribe_ms(host, ip, port, tls):
    """Fresh connection, optional TLS, send mining.subscribe, wait for one reply line."""
    raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    raw.settimeout(TIMEOUT)
    t0 = time.perf_counter()
    s = raw
    try:
        raw.connect((ip, port))
        if tls:
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(raw, server_hostname=host)
        s.sendall(SUBSCRIBE.encode())
        buf = b""
        while b"\n" not in buf:
            chunk = s.recv(4096)
            if not chunk:
                return None, "closed before answering"
            buf += chunk
        dt = (time.perf_counter() - t0) * 1000.0
        line = buf.split(b"\n", 1)[0].decode(errors="replace")
        try:
            ok = json.loads(line).get("result") is not None
        except Exception:
            ok = False
        return dt, ("subscribe ok" if ok else "answered, not stratum?")
    except ssl.SSLError as e:
        return None, "TLS failed: " + str(e)[:60]
    except Exception as e:
        return None, "no answer: " + (str(e)[:60] or type(e).__name__)
    finally:
        try:
            s.close()
        except Exception:
            pass


def main():
    pools = list(POOLS)
    for arg in sys.argv[1:]:
        h, _, p = arg.rpartition(":")
        if h and p.isdigit():
            pools.append((arg, h, int(p), False))
    print("Measuring from this machine to each pool ({} spaced connects + 1 stratum subscribe each)...".format(SAMPLES))
    print()
    print("{:<26} {:<16} {:>8} {:>8} {:>8}  {}".format("pool", "ip", "tcp_min", "tcp_med", "sub_ms", "note"))
    print("-" * 92)
    for label, host, port, tls in pools:
        ip = resolve(host)
        if not ip:
            print("{:<26} {:<16} {:>8} {:>8} {:>8}  {}".format(label, "-", "-", "-", "-", "DNS failed for " + host))
            continue
        times = []
        for _ in range(SAMPLES):
            dt = tcp_connect_ms(ip, port)
            if dt is not None:
                times.append(dt)
            time.sleep(SPACING)
        if not times:
            print("{:<26} {:<16} {:>8} {:>8} {:>8}  {}".format(label, ip, "-", "-", "-", "port {} unreachable".format(port)))
            continue
        sub, note = subscribe_ms(host, ip, port, tls)
        print("{:<26} {:<16} {:>8.1f} {:>8.1f} {:>8}  {}".format(
            label, ip, min(times), statistics.median(times),
            "-" if sub is None else "{:.1f}".format(sub),
            note + (" ({}/{} connects ok)".format(len(times), SAMPLES) if len(times) < SAMPLES else "")
            + (" [TLS]" if tls else "")))
        sys.stdout.flush()
    print()
    print("tcp_med = median TCP connect (ms). sub_ms = connect + stratum subscribe on one fresh connection.")
    print("Pick the shortest reliable hop for where the miner lives. Odds of a block are identical on every solo pool.")


if __name__ == "__main__":
    main()
