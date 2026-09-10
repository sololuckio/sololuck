#!/usr/bin/env python3
"""
SoloLuck Miner — a simple Start/Stop GUI that drives the cpuminer-opt CPU engine
and points it at the SoloLuck solo Bitcoin pool (sololuck.io).

A PC's hashrate is tiny next to an ASIC, so this is a long shot — which is
exactly the point of a solo pool. If your CPU happens to solve a block, the whole
reward is paid straight to your address on-chain (0% pool fee, finders keepers).

This is a CLEAN WRAPPER: it contains no mining code itself. On first run it detects
your CPU and downloads the matching build from the PINNED cpuminer-opt release
(Jay D Dee's, GPLv2), verifies its SHA-256 against the manifest baked into this
file, and only then runs it. An engine that fails verification is quarantined
and never executed. Nothing to install. (Advanced
users can drop their own cpuminer-opt.exe next to this app to skip the download.)

Why a clean wrapper: a GUI with no embedded miner isn't itself flagged as a coin
miner, so the app always launches; antivirus only ever flags the downloaded engine,
which you whitelist once. Pure Python standard library (tkinter + urllib).
"""
import base64
import hashlib
import io
import json
import os
import queue
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
import zipfile
try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except ImportError:  # headless (tests) — GUI not needed for the engine logic
    tk = messagebox = ttk = None

APP_NAME = "SoloLuck Miner"
ALGO = "sha256d"   # Bitcoin
ENGINE_DIR_NAME = "SoloLuckMiner-engine"
# 🔴 STABLE. v1.11.0-beta.2 reserved ">= 1.11.1" for the first stable of this
# line, so this is 1.11.1 — not 1.11.0, which the betas already sort inside.
# Every v1.10.1 user auto-downloads and auto-installs this while idle, so
# nothing unfinished may ride in it.
APP_VERSION = "1.11.2"
CHANGELOG_URL = "https://sololuck.io/changelog"
# ── coins ────────────────────────────────────────────────────────────────────
# ONE Windows app with a coin selector (Bitcoin, Bitcoin Cash, DigiByte).
#
# ⭐ The same file also builds a SINGLE-COIN app: gen-miners.py deletes the other
# coins' definitions and rewrites CHAIN_DEFS, and the selector then disappears on
# its own because there is nothing to choose. Both shapes stay tested, so the
# split is one command away if it is wanted again.
#
# 🔴 Because one binary knows all three coins, the boundary the split gave for
# free has to be enforced here instead — and the one that matters is the payout
# address. Each coin keeps its OWN settings file; nothing is shared. Switching
# coin never carries an address across, and a stored address is loaded only if it
# still validates for that coin. An address that reaches the wrong chain is how a
# solved block gets paid somewhere the user cannot spend from.
CHAIN = "btc"          # the default and headline coin (the only one in a split build)

_CHAIN_BTC = {
    "name": "Bitcoin", "ticker": "BTC", "host": "sololuck.io", "port": "3335",
    "addr_label": "BTC payout address", "hint": "  🔒 Nano tier · fixed",
    "example": "e.g. bc1q…",
    "stats_url": "https://sololuck.io/users/%s",
    # ⭐ The two places SoloLuck answers Bitcoin stratum. Measured at launch;
    # the closest one wins. The FIRST entry is the default and the fail-safe —
    # it must stay identical to "host" above, so that a build whose probe finds
    # nothing behaves exactly like v1.11.1 did.
    # ⛔ Bitcoin only. Bitcoin Cash and DigiByte have one pool each and carry no
    # "doors" key at all, so resolve_host() hands back their "host" untouched.
    "doors": (("sololuck.io", "Jakarta"),
              ("us.stratum.sololuck.io", "Phoenix")),
    "beta": False,
    "start_note": None,
    "idle": "A found block pays its whole reward to this address.",
}
_CHAIN_BCH = {
    "name": "Bitcoin Cash", "ticker": "BCH", "host": "bch.sololuck.io", "port": "3333",
    "addr_label": "BCH payout address", "hint": "  🔒 single tier · fixed",
    "example": "your CashAddr, q…",
    # ⭐ Same URL as Bitcoin: the site routes /users/<addr> BY ADDRESS FORM, so a
    # CashAddr gets the Bitcoin Cash logbook and a Bitcoin address gets the
    # Bitcoin one. Verified against the site's own canon_bch_addr(), whose
    # docstring says the route is keyed on the "canonical bare lowercase
    # CashAddr (no 'bitcoincash:' prefix)" — which is exactly the username form
    # validate_for_chain() returns and _cur_addr holds.
    # 🔴 Live only once the site sets bch_public=1; until then that URL answers
    # "invalid address". The launch runbook flips the site BEFORE publishing the
    # app, so no user of this build ever meets the pre-flip answer.
    "stats_url": "https://sololuck.io/users/%s",
    # Bitcoin Cash launches WITH this release, so it is not labelled a beta.
    # 🔴 Sequencing: the site's bch_public=1 flip must land before or at the same
    # moment this build is published. If the app shipped first, every
    # auto-updated user would see a coin the website still has switched off.
    "beta": False,
    # ⚠️ The difficulty is the POOL's decision, not ours. An earlier build claimed
    # this app "asks the pool for difficulty 1, so shares register within minutes".
    # That was false: the port answers with difficulty 1024 whether or not a
    # "d=" password is sent, because ckpool's mindiff clamps the request up and
    # "d=" is a one-way ratchet anyway. Say what actually happens instead.
    "start_note": "Bitcoin Cash: the pool sets your difficulty from your share rate "
                  "and moves it up or down as that changes, never below the port's floor. "
                  "A found block pays your CashAddr in BCH.",
    "idle": "A found block pays this address in BCH. The pool sets the difficulty "
            "from your share rate, with a floor set by the port.",
}
_CHAIN_DGB = {
    "name": "DigiByte", "ticker": "DGB", "host": "digibyte.sololuck.io", "port": "3340",
    "addr_label": "DGB payout address", "hint": "  beta · SHA256d door",
    "example": "D…, S… or dgb1…",
    # ⛔ Stays None. There is no /dgb route on the production site at all —
    # /dgb/users/<addr> is a 404 as of 2026-09-06 — and DigiByte is gated off
    # with no pool, so the link could never render anyway. Set this only when
    # the gate opens AND the route is confirmed live.
    "stats_url": None,
    "beta": True,
    "start_note": "DigiByte beta: SoloLuck mines DigiByte's SHA256d algorithm, one of "
                  "its five. A found block pays your address in DGB.",
    # Plain and non-comparative: what the chain is and what a block pays.
    # ⛔ No odds, no comparison with the other coins, no earnings talk.
    "idle": "DigiByte beta: SoloLuck mines DigiByte's SHA256d algorithm, one of its five. "
            "A found block pays this address in DGB. A CPU's chance of solving one is small.",
}
CHAIN_DEFS = {"btc": _CHAIN_BTC, "bch": _CHAIN_BCH, "dgb": _CHAIN_DGB}

# ── the DigiByte gate ─────────────────────────────────────────────────────────
# 🔴 OFF. There is no DigiByte pool yet. While this is False DigiByte is not in
# CHAINS, so the app draws no DigiByte button, no saved config can select it and
# start() cannot resolve its host — there is no reachable path to that pool.
# (In a single-coin DigiByte build there is nothing else to fall back to, so that
# build instead runs with Start disabled and the reason on screen.)
# Flip to True ONLY once ALL of these are true:
#   1. A DigiByte ckpool is actually listening on the DigiByte stratum host and
#      port above, and its mining.notify carries DigiByte work.
#   2. That host resolves to the DigiByte pool's own address — as of 2026-09-06
#      it resolves to the same box as the Bitcoin Cash pool, whose stratum is
#      live there. Until that changes, a connection would reach the wrong chain.
#   3. The DigiByte node has finished its initial block download and its
#      getblocktemplate returns pow_algo == "sha256d" (an unconfigured node
#      hands back Scrypt silently, and every SHA-256 share is then worthless).
#   4. A real DigiByte address has been paid by a real solved block on that pool.
DGB_ENABLED = False
CHAIN_DISABLED_WHY = ("The DigiByte pool is not live yet, so this build cannot mine "
                      "it. A later build will enable it once the pool is running.")


def chain_enabled(key):
    """May this coin mine? Only DigiByte is ever gated."""
    return key != "dgb" or DGB_ENABLED


# The coins this build actually offers. A gated coin is dropped entirely — no
# greyed button, nothing to select. If that would leave nothing (a single-coin
# DigiByte build), the coin stays but chain_enabled() keeps it from mining.
CHAINS = {k: v for k, v in CHAIN_DEFS.items() if chain_enabled(k)} or dict(CHAIN_DEFS)
CHAIN_ORDER = [k for k in ("btc", "bch", "dgb") if k in CHAINS]   # Bitcoin first, always
if CHAIN not in CHAINS:
    CHAIN = CHAIN_ORDER[0]
CHAIN_DEF = CHAINS[CHAIN]          # the coin selected at startup


# ── choosing a door ───────────────────────────────────────────────────────────
# Bitcoin answers in Jakarta and in Phoenix. Shares that cross the Pacific and
# back are shares racing the rest of the network with a handicap, so the app
# measures both at launch and mines to whichever replies fastest.
#
# ⭐ Not ICMP. A --noconsole build cannot run ping.exe without flashing a console
# window, and raw ICMP sockets need Administrator on Windows. The TCP handshake
# to the real stratum port is privilege-free, measures the path that will carry
# the work, and proves the port answers. The mining.subscribe after it proves a
# live ckpool is behind that port — so a door that accepts connections while its
# pool is down can never win.
#
# 🔴 Every failure lands on DOORS[0], which is the same host v1.11.1 used. A
# probe that breaks costs nothing.
# 🔴 perf_counter(), NEVER monotonic(). On Windows — the only platform this app
# ships on — time.monotonic() is GetTickCount64() with a resolution of 15.625 ms
# (confirmed on the build box, Python 3.12.7). Every latency under one tick reads
# as 0.0 ms, DOOR_MARGIN_MS below is smaller than a single tick, and the picker
# cannot tell two nearby doors apart. perf_counter() is QueryPerformanceCounter()
# at 0.1 µs. ⛔ On Linux monotonic() is nanosecond-resolution, so this bug is
# INVISIBLE in local testing — the frozen exe on real Windows is what caught it.
DOOR_ATTEMPTS      = 3       # take the best of three: min RTT is the honest one
DOOR_CONNECT_TMO   = 2.0     # seconds, TCP handshake
DOOR_SUBSCRIBE_TMO = 2.5     # seconds, waiting for the stratum reply
# A challenger must beat the default by BOTH of these to displace it. Without a
# margin two near-equal doors flap run to run on jitter alone, and one user's
# history ends up split across two pool databases.
DOOR_MARGIN_PCT    = 0.15
DOOR_MARGIN_MS     = 10.0

_door_lock  = threading.Lock()
_door_state = {"done": False, "results": [], "host": None, "picked": None}


def probe_door(host, port, attempts=DOOR_ATTEMPTS):
    """Time the TCP handshake to a stratum port and confirm a pool is behind it.

    Returns a dict; never raises. ms is the best of `attempts` successful
    handshakes, or None if none succeeded."""
    out = {"host": host, "port": port, "ip": None, "ms": None,
           "ok": 0, "tried": 0, "err": None}
    try:
        infos = socket.getaddrinfo(host, int(port), 0, socket.SOCK_STREAM)
    except Exception as e:
        out["err"] = "dns: %s" % e
        return out
    if not infos:
        out["err"] = "dns: no address"
        return out
    fam, typ, proto, _cn, sa = infos[0]
    out["ip"] = sa[0]
    best = None
    for _ in range(attempts):
        out["tried"] += 1
        sk = None
        try:
            sk = socket.socket(fam, typ, proto)
            sk.settimeout(DOOR_CONNECT_TMO)
            t0 = time.perf_counter()
            sk.connect(sa)
            ms = (time.perf_counter() - t0) * 1000.0
            # ⭐ The handshake is the measurement; the subscribe is the proof.
            sk.settimeout(DOOR_SUBSCRIBE_TMO)
            sk.sendall(b'{"id":1,"method":"mining.subscribe",'
                       b'"params":["sololuck-probe"]}\n')
            buf = b""
            deadline = time.perf_counter() + DOOR_SUBSCRIBE_TMO
            while b"\n" not in buf and time.perf_counter() < deadline:
                chunk = sk.recv(4096)
                if not chunk:
                    break
                buf += chunk
            line = buf.split(b"\n", 1)[0].decode("utf-8", "replace").strip()
            if not line:
                raise IOError("no stratum reply")
            msg = json.loads(line)
            # ckpool answers {"result":[[["mining.notify",..]],"<xnonce1>",N],..}
            if msg.get("result") in (None, False):
                raise IOError("stratum refused")
            out["ok"] += 1
            if best is None or ms < best:
                best = ms
        except Exception as e:
            out["err"] = "%s" % e
        finally:
            if sk is not None:
                try:
                    sk.close()
                except Exception:
                    pass
    out["ms"] = best
    return out


def measure_doors(doors, port):
    """Probe every door at once. Always returns one row per door, in order."""
    res = [None] * len(doors)

    def run(i, host):
        try:
            res[i] = probe_door(host, port)
        except Exception as e:                       # belt and braces
            res[i] = {"host": host, "port": port, "ip": None, "ms": None,
                      "ok": 0, "tried": 0, "err": "%s" % e}

    threads = []
    for i, (host, _label) in enumerate(doors):
        t = threading.Thread(target=run, args=(i, host), daemon=True)
        t.start()
        threads.append(t)
    budget = DOOR_ATTEMPTS * (DOOR_CONNECT_TMO + DOOR_SUBSCRIBE_TMO) + 2.0
    end = time.perf_counter() + budget
    for t in threads:
        t.join(max(0.0, end - time.perf_counter()))
    for i, (host, label) in enumerate(doors):
        if res[i] is None:
            res[i] = {"host": host, "port": port, "ip": None, "ms": None,
                      "ok": 0, "tried": 0, "err": "timed out"}
        res[i]["label"] = label
        res[i]["default"] = (i == 0)
    return res


def pick_door(results):
    """The winning row, or None if no door answered.

    Reliability first (a door that answered 3 of 3 beats one that answered 1 of
    3 however fast it was), then latency. The default door keeps the win unless
    a challenger clears both margins."""
    live = [r for r in results if r["ok"] and r["ms"] is not None]
    if not live:
        return None
    live.sort(key=lambda r: (-r["ok"], r["ms"], not r["default"]))
    win = live[0]
    dft = next((r for r in live if r["default"]), None)
    if dft is not None and win is not dft and win["ok"] == dft["ok"]:
        gain = dft["ms"] - win["ms"]
        if gain < DOOR_MARGIN_MS or gain < dft["ms"] * DOOR_MARGIN_PCT:
            return dft                               # too close to be worth moving
    return win


def run_door_probe(chain="btc"):
    """Measure this coin's doors and remember the answer. Safe to call twice."""
    c = CHAINS.get(chain) or CHAIN_DEFS[chain]
    doors = c.get("doors")
    if not doors:
        return None
    try:
        results = measure_doors(doors, c["port"])
        winner = pick_door(results)
    except Exception as e:                           # never let this kill startup
        results, winner = [], None
        try:
            _verify_log("door probe failed: %r" % e)
        except Exception:
            pass
    with _door_lock:
        _door_state["results"] = results
        _door_state["picked"] = winner
        _door_state["host"] = winner["host"] if winner else None
        _door_state["done"] = True
    return winner


def door_state():
    with _door_lock:
        return dict(_door_state)


def resolve_host(chain, wait=0.0):
    """The host to mine this coin to, right now.

    🔴 The fail-safe is CHAINS[chain]["host"] — what v1.11.1 shipped. A coin with
    no doors, a probe that has not finished, a probe that found nothing: all
    three land there."""
    c = CHAINS.get(chain) or CHAIN_DEFS[chain]
    fallback = c["host"]
    if not c.get("doors"):
        return fallback
    if wait > 0:
        end = time.perf_counter() + wait
        while time.perf_counter() < end:
            with _door_lock:
                if _door_state["done"]:
                    break
            time.sleep(0.05)
    st = door_state()
    if st["done"] and st["host"]:
        return st["host"]
    return fallback


def door_summary(chain="btc"):
    """One short line for the UI: which door won and what both measured."""
    st = door_state()
    if not st["done"]:
        return "checking latency…"
    rows = st["results"]
    win = st["picked"]
    if not win:
        return "latency check failed · using the default door"
    others = ["%s %s" % (r["label"], ("%.0f ms" % r["ms"]) if r["ms"] is not None
                         else "no answer")
              for r in rows if r is not win]
    tail = (" (%s)" % ", ".join(others)) if others else ""
    return "%s · %.0f ms%s" % (win["label"], win["ms"], tail)
# CPU load slider: gentle by default. Full load makes a PC noticeably slower,
# so 100% is opt-in via an explicit checkbox; without it the slider tops out
# at the soft max.
CPU_PCT_MIN = 25
CPU_PCT_SOFT_MAX = 80      # green "recommended" ceiling; above this is amber "high load"
CPU_PCT_HARD_MAX = 90      # v1.8: absolute cap — the miner never uses more, so the PC
                          # stays usable and we shed only the top threads (little hashrate,
                          # lots of heat). There is no 100% option any more.
CPU_PCT_DEFAULT = 25
# ── pinned mining engine ──────────────────────────────────────────────────────
# Exact release, exact bytes. The app never fetches "latest", never falls back
# to another URL or version, and never executes an engine file whose SHA-256
# does not match this manifest (fail closed). Hashes computed from the official
# release asset at pin time.
ENGINE_VERSION = "v26.1"
ENGINE_ZIP_URL = ("https://github.com/JayDDee/cpuminer-opt/releases/download/"
                  "v26.1/cpuminer-opt-26.1-windows.zip")
ENGINE_ZIP_SHA256 = "caf59deb12831e40475c5245a76bf42f9ba2ff620065be5386b80ec55c998e9c"
ENGINE_FILE_SHA256 = {
    "cpuminer-aes-sse42.exe": "454f52e4d9074a089fe2c0daefb5635ad5eae32a4bcb94b878190ae8843db547",
    "cpuminer-avx2.exe": "4823226ef2031ad356d6a01d75d3dbce0aeb57054e2ef9d0e9bfc96e68bd42c7",
    "cpuminer-avx2-sha.exe": "d4d1b9b66060e9453f597f54c3ee5704b82239bf94ff445a5f0f5de78af94519",
    "cpuminer-avx2-sha-vaes.exe": "5cbae7a39b6ea0f3ca400523c300880a828b40a8470e1194890722807af9d780",
    "cpuminer-avx512.exe": "453c351dfd0af95e497346fe2f2b8d7b3dbc90757169f09679d7b6fe8b0958ec",
    "cpuminer-avx512-sha-vaes.exe": "a41c835bff8c404f0dc79a4f86a666f1e44dac9e5758bc31845b9dd7072f2b17",
    "cpuminer-avx.exe": "adda67c2db1398c90adfd60498425df81b59ae0cd4924ed8d4a5c7d13d731005",
    "cpuminer-sse2.exe": "f32e00a6947113c7da8a83940172b6f4519fa658fd0d2839ce69a00464f3798a",
    "libcurl-4.dll": "218cfc4073bab4eddf0de0804f96b204687311e20a9e97994bff54c9b0e01ee9",
    "libgcc_s_seh-1.dll": "c82f84171b9246d1cac261100b2199789c96c37b03b375f33b2c72afab060b05",
    "libstdc++-6.dll": "baef1f4cabebdadc52213761b4c8e2bf381976a67bd7c490f952c38f6831b036",
    "libwinpthread-1.dll": "2f9984c591a5654434c53e8b4d0c5c187f1fd0bab95247d5c9bc1c0bd60e6232",
    "zlib1.dll": "61b71a00bf87ea1a63a66677de5208db7e4407287ff668e526ad609a70ef3f12",
}
# cpuminer-opt isn't statically linked — these ride next to whichever build we use.
ENGINE_DLLS = ["libcurl-4.dll", "libgcc_s_seh-1.dll", "libstdc++-6.dll",
               "libwinpthread-1.dll", "zlib1.dll"]
# user-supplied override builds we recognise in the app folder.
MINER_NAMES = [
    "cpuminer-opt.exe", "cpuminer.exe",
    "cpuminer-avx2.exe", "cpuminer-avx512.exe", "cpuminer-avx.exe",
    "cpuminer-zen.exe", "cpuminer-zen3.exe", "cpuminer-zen4.exe", "cpuminer-zen5.exe",
    "cpuminer-sse2.exe", "cpuminer-sse42.exe", "cpuminer-aes-sse42.exe",
    "cpuminer-opt", "cpuminer",   # non-Windows dev fallbacks
]
HASH_RE = re.compile(r"([\d.]+)\s*([kKMGTP]?)[hH]/s")
ACCEPT_RE = re.compile(r"[Aa]ccepted\s+(\d+)/(\d+)")
# connection-state classification of cpuminer output lines (order matters:
# a failure line often also contains the word "stratum"/"connect")
_FAIL_RE = re.compile(r"connection (failed|interrupted|timed? ?out|refused|reset|closed|lost)"
                      r"|failed to connect|unable to connect|connect failed"
                      # bare timeouts count, but ckpool's benign 'Extranonce disabled,
                      # subscribe timed out' on every connect does not
                      r"|(?<!subscribe )timed? ?out"
                      r"|retry (in|after)|retrying"
                      r"|stratum authentication failed|authorization failed|login failed", re.I)
_LIVE_RE = re.compile(r"difficulty (set|changed)|stratum diff|new (work|job|block)"
                      r"|threads? started|extranonce|authoriz|subscrib"
                      r"|connection established|connected to", re.I)


def classify_line(line):
    """'fail' (connection/auth problem), 'live' (talking to the pool), or None."""
    if _FAIL_RE.search(line):
        return "fail"
    if _LIVE_RE.search(line):
        return "live"
    return None


# Windows NTSTATUS exit codes worth translating for the user.
_EXIT_HELP = {
    0xC000001D: "illegal instruction — this engine build needs CPU features this machine doesn't have",
    0xC0000005: "access violation — the engine crashed",
    0xC0000135: "a required DLL is missing from the engine folder",
    0xC0000409: "the engine crashed (stack error)",
}


def explain_exit(code):
    """Human hint for an engine exit code ('' when there is nothing to add)."""
    if code is None:
        return ""
    msg = _EXIT_HELP.get(code & 0xFFFFFFFF)
    return (" — " + msg) if msg else ""


def is_cpu_mismatch_exit(code):
    """True for the crash signatures a too-new build throws on an older CPU."""
    return code is not None and (code & 0xFFFFFFFF) in (0xC000001D, 0xC0000005)


def threads_for(pct, ncpu):
    """Miner thread count for a CPU-load percentage. Always at least 1."""
    try:
        pct = int(pct)
    except (TypeError, ValueError):
        pct = CPU_PCT_DEFAULT
    pct = max(CPU_PCT_MIN, min(CPU_PCT_HARD_MAX, pct))
    return max(1, int(round((ncpu or 1) * pct / 100.0)))


# ── Bitcoin address validation (real checksums, not just shape) ───────────────
_B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_B32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def _bech32_polymod(values):
    gen = (0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3)
    chk = 1
    for v in values:
        b = chk >> 25
        chk = ((chk & 0x1FFFFFF) << 5) ^ v
        for i in range(5):
            if (b >> i) & 1:
                chk ^= gen[i]
    return chk


def validate_btc_address(addr):
    """(ok, detail): base58check for 1…/3…, BIP-173/BIP-350 bech32(m) for bc1….
    detail = the address kind when valid, else why it failed. Mainnet only —
    a mistyped payout address on a solo pool means an unclaimable block."""
    a = (addr or "").strip()
    if not a:
        return (False, "empty")
    low = a.lower()
    if low.startswith(("tb1", "bcrt1")) or a[0] in "mn2" or a[:2] == "0x":
        return (False, "not a mainnet Bitcoin address" if a[:2] != "0x"
                else "that looks like an Ethereum address")
    if len(a) < 14:
        return (False, "too short")
    if a[0] in "13":
        n = 0
        for ch in a:
            i = _B58_ALPHABET.find(ch)
            if i < 0:
                return (False, "invalid character '%s'" % ch)
            n = n * 58 + i
        raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
        raw = b"\x00" * (len(a) - len(a.lstrip("1"))) + raw
        if len(raw) != 25:
            return (False, "wrong length")
        if hashlib.sha256(hashlib.sha256(raw[:21]).digest()).digest()[:4] != raw[21:]:
            return (False, "checksum failed — typo?")
        return (True, "legacy P2PKH" if raw[0] == 0x00 else "P2SH")
    if low.startswith("bc1"):
        if a != low and a != a.upper():
            return (False, "mixed upper/lower case")
        sep = low.rfind("1")
        if low[:sep] != "bc":
            return (False, "unrecognized format")
        vals = []
        for ch in low[sep + 1:]:
            i = _B32_CHARSET.find(ch)
            if i < 0:
                return (False, "invalid character '%s'" % ch)
            vals.append(i)
        if len(vals) < 7:
            return (False, "too short")
        hrpexp = [ord(c) >> 5 for c in "bc"] + [0] + [ord(c) & 31 for c in "bc"]
        witver = vals[0]
        if witver > 16:
            return (False, "bad witness version")
        want = 1 if witver == 0 else 0x2BC830A3   # bech32 v0, bech32m v1+
        if _bech32_polymod(hrpexp + vals) != want:
            return (False, "checksum failed — typo?")
        acc = bits = 0
        prog = []
        for v in vals[1:-6]:
            acc = (acc << 5) | v
            bits += 5
            while bits >= 8:
                bits -= 8
                prog.append((acc >> bits) & 0xFF)
        if bits >= 5 or (acc & ((1 << bits) - 1)):
            return (False, "invalid padding")
        n = len(prog)
        if witver == 0:
            if n == 20:
                return (True, "SegWit bc1q")
            if n == 32:
                return (True, "SegWit bc1q (script)")
            return (False, "wrong program length")
        if not 2 <= n <= 40:
            return (False, "wrong program length")
        if witver == 1 and n == 32:
            return (True, "Taproot bc1p")
        return (True, "SegWit v%d" % witver)
    return (False, "unrecognized format")

# ── Bitcoin Cash CashAddr (same decoder the site uses) ───────────────────────
_CASH_CHARSET = _B32_CHARSET
_CASH_REV = {c: i for i, c in enumerate(_CASH_CHARSET)}
BCH_PREFIX = "bitcoincash"


def _cash_polymod(values):
    """CashAddr checksum polynomial (spec form, including the final ^1)."""
    c = 1
    for d in values:
        c0 = c >> 35
        c = ((c & 0x07FFFFFFFF) << 5) ^ d
        if c0 & 0x01:
            c ^= 0x98F2BC8E61
        if c0 & 0x02:
            c ^= 0x79B76D99E2
        if c0 & 0x04:
            c ^= 0xF33E5FB3C4
        if c0 & 0x08:
            c ^= 0xAE2EABE2A8
        if c0 & 0x10:
            c ^= 0x1E4F43E470
    return c ^ 1


def _cash_convert_5_to_8(data):
    """5-bit groups -> bytes. None if the leftover padding is not all-zero."""
    acc = bits = 0
    ret = []
    for value in data:
        if value < 0 or (value >> 5):
            return None
        acc = ((acc << 5) | value) & 0x1FFF
        bits += 5
        while bits >= 8:
            bits -= 8
            ret.append((acc >> bits) & 0xFF)
    if bits >= 5 or ((acc << (8 - bits)) & 0xFF):
        return None
    return ret


def bch_addr_parts(addr):
    """Decode a mainnet CashAddr -> (type_nibble, hash160) or None.
    Rejects mixed case, a wrong or foreign prefix, bad characters, a bad
    checksum, reserved version bits, non-160-bit hashes and unknown types."""
    if not isinstance(addr, str) or not addr:
        return None
    if any(c.islower() for c in addr) and any(c.isupper() for c in addr):
        return None
    if ":" in addr:
        prefix, _, payload = addr.partition(":")
        if prefix.lower() != BCH_PREFIX:
            return None
    else:
        payload = addr
    payload = payload.lower()
    if not (14 <= len(payload) <= 112):
        return None
    data = []
    for ch in payload:
        if ch not in _CASH_REV:
            return None
        data.append(_CASH_REV[ch])
    if len(data) < 9:
        return None
    if _cash_polymod([ord(c) & 0x1F for c in BCH_PREFIX] + [0] + data) != 0:
        return None
    decoded = _cash_convert_5_to_8(data[:-8])
    if decoded is None or len(decoded) != 21:
        return None
    version = decoded[0]
    if version & 0x80:
        return None
    kind = (version >> 3) & 0x0F
    if kind not in (0, 1):
        return None
    if version & 0x07:
        return None
    return kind, bytes(decoded[1:])


def validate_bch_address(addr):
    """(ok, detail, bare): a checksum-valid mainnet CashAddr -> its bare
    lowercase form (the stratum username the pool keys on); else why it
    failed. Legacy 1…/3… and Bitcoin bc1… are refused ON PURPOSE: the pool
    would accept them and pay somewhere a Bitcoin wallet cannot spend from."""
    a = (addr or "").strip()
    if not a:
        return (False, "empty", None)
    low = a.lower()
    if a[:2] == "0x":
        return (False, "that looks like an Ethereum address", None)
    if low.startswith(("bchtest:", "bchreg:")):
        return (False, "not a mainnet Bitcoin Cash address", None)
    if low.startswith(("bc1", "tb1")):
        return (False, "that is a Bitcoin address — paste your Bitcoin Cash address (q…)", None)
    if a[0] in "13" and ":" not in a:
        return (False, "legacy format — use the CashAddr form (q…) from your wallet", None)
    if any(c.islower() for c in a) and any(c.isupper() for c in a):
        return (False, "mixed upper/lower case", None)
    parts = bch_addr_parts(a)
    if parts is None:
        body = low.partition(":")[2] if ":" in low else low
        if ":" in low and low.partition(":")[0] != BCH_PREFIX:
            return (False, "wrong prefix — mainnet is bitcoincash:", None)
        if body[:1] not in ("q", "p"):
            return (False, "unrecognized format", None)
        if len(body) < 42:
            return (False, "too short", None)
        for ch in body:
            if ch not in _CASH_REV:
                return (False, "invalid character '%s'" % ch, None)
        return (False, "checksum failed — typo?", None)
    kind, _h = parts
    bare = low.partition(":")[2] if ":" in low else low
    return (True, "CashAddr P2PKH (q…)" if kind == 0 else "CashAddr P2SH (p…)", bare)


# ── DigiByte ─────────────────────────────────────────────────────────────────
# Verified against a live DigiByte Core 9.26.5 node (validateaddress), not from
# guides: DigiByte accepts base58 version 30 ("D…", P2PKH), version 63 ("S…",
# P2SH), and bech32/bech32m under the hrp "dgb".
#
# 🔴 It REFUSES version 5 ("3…"). That is BITCOIN's P2SH version. A great many
# DigiByte "supported address formats" guides list 3… as DigiByte P2SH; the node
# says otherwise, and the node is what pays the block. Confirmed refused live.
#
# ⚠️ Known, deliberate ambiguity: DOGECOIN also uses base58 version 30, so a
# Dogecoin address is byte-for-byte a valid DigiByte P2PKH address and is
# accepted here. That is correct behaviour, not a hole: the address commits to a
# hash160 of the user's own public key, so the same private key spends the DGB
# output — the coins are reachable, just from a wallet the user has to import the
# key into. It is not a wrong-chain loss like a Bitcoin address would be, so the
# UI deliberately does NOT raise an alarm about it.
DGB_HRP = "dgb"
DGB_VERSIONS = {30: "P2PKH (D…)", 63: "P2SH (S…)"}
# base58 version bytes that belong to some OTHER chain — so a refusal can name
# the chain the pasted address really belongs to instead of a bare "invalid".
_DGB_FOREIGN_B58 = {
    0: "a Bitcoin address (legacy 1…)",
    5: "a Bitcoin address (P2SH 3…) — DigiByte does not use version 5",
    22: "a Dogecoin P2SH address (9…/A…)",
    48: "a Litecoin address (L…)",
    50: "a Litecoin P2SH address (M…)",
    111: "a testnet address",
    196: "a testnet P2SH address",
}


def _b58check_decode(a):
    """(version, payload) for a 25-byte base58check string, or (None, reason)."""
    n = 0
    for ch in a:
        i = _B58_ALPHABET.find(ch)
        if i < 0:
            return (None, "invalid character '%s'" % ch)
        n = n * 58 + i
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    raw = b"\x00" * (len(a) - len(a.lstrip("1"))) + raw
    if len(raw) != 25:
        return (None, "wrong length")
    if hashlib.sha256(hashlib.sha256(raw[:21]).digest()).digest()[:4] != raw[21:]:
        return (None, "checksum failed — typo?")
    return (raw[0], raw[1:21])


def _segwit_decode(low, hrp):
    """Generic BIP-173/BIP-350 decode for a given hrp.
    -> (witver, program_bytes) or (None, reason). `low` must already be
    lowercase; the caller decides how mixed case is treated."""
    sep = low.rfind("1")
    if sep < 0 or low[:sep] != hrp:
        return (None, "unrecognized format")
    vals = []
    for ch in low[sep + 1:]:
        i = _B32_CHARSET.find(ch)
        if i < 0:
            return (None, "invalid character '%s'" % ch)
        vals.append(i)
    if len(vals) < 7:
        return (None, "too short")
    hrpexp = [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]
    witver = vals[0]
    if witver > 16:
        return (None, "bad witness version")
    want = 1 if witver == 0 else 0x2BC830A3   # bech32 for v0, bech32m for v1+
    if _bech32_polymod(hrpexp + vals) != want:
        return (None, "checksum failed — typo?")
    acc = bits = 0
    prog = []
    for v in vals[1:-6]:
        acc = (acc << 5) | v
        bits += 5
        while bits >= 8:
            bits -= 8
            prog.append((acc >> bits) & 0xFF)
    if bits >= 5 or (acc & ((1 << bits) - 1)):
        return (None, "invalid padding")
    return (witver, bytes(prog))


def validate_dgb_address(addr):
    """(ok, detail): a real mainnet DigiByte payout address, or why it is not.

    On a solo pool the address IS the payout destination, so this refuses every
    foreign form and, where it can tell, says WHICH chain the pasted address
    belongs to. Mainnet only."""
    a = (addr or "").strip()
    if not a:
        return (False, "empty")
    low = a.lower()
    if a[:2] == "0x":
        return (False, "that looks like an Ethereum address")
    # testnet/regtest first: dgbt1… would otherwise fall through as "unrecognized"
    if low.startswith(("dgbt1", "dgbrt1", "dgbreg1")):
        return (False, "that is a DigiByte TESTNET address — this pool is mainnet")
    if low.startswith(("bc1", "tb1", "bcrt1")):
        return (False, "that is a Bitcoin address — paste your DigiByte address")
    if low.startswith(("bitcoincash:", "bchtest:", "bchreg:")):
        return (False, "that is a Bitcoin Cash address — paste your DigiByte address")
    if low.startswith(("ltc1", "doge1")):
        return (False, "that is not a DigiByte address — paste your DigiByte address")
    if low.startswith(DGB_HRP):
        # 🔴 The node decides bech32-vs-base58 purely on the first 3 characters
        # (DecodeDestination: `is_bech32 = ToLower(str[0:3]) == hrp`, and the
        # base58 branch is skipped when that is true). DigiByte's base58 P2PKH
        # addresses start with "D", so a perfectly good "DGB…" address is
        # shadowed by the "dgb" bech32 prefix and DigiByte Core REFUSES ITS OWN
        # ADDRESS — decodescript hands it out, validateaddress then says
        # "Invalid address format". Verified live, 2026-09-06.
        # ckpool asks the node, so the pool would refuse such an address at
        # connect time. Refusing it here, with a message that explains it, beats
        # a green tick followed by a connection the user cannot explain.
        if not low.startswith(DGB_HRP + "1"):
            return (False, "DigiByte Core itself refuses addresses starting "
                           "\"DGB\" — use another receiving address from your wallet")
        if a != low and a != a.upper():
            return (False, "mixed upper/lower case")
        # uppercase is a legal bech32 form and the node folds it — so do we
        witver, prog = _segwit_decode(low, DGB_HRP)
        if witver is None:
            return (False, prog)
        n = len(prog)
        if witver == 0:
            if n == 20:
                return (True, "SegWit dgb1q")
            if n == 32:
                return (True, "SegWit dgb1q (script)")
            return (False, "wrong program length")
        if not 2 <= n <= 40:
            return (False, "wrong program length")
        if witver == 1 and n == 32:
            return (True, "Taproot dgb1p")
        return (True, "SegWit v%d" % witver)
    # a bare CashAddr body (q…/p… with a valid CashAddr checksum) is Bitcoin Cash
    if low[:1] in ("q", "p") and bch_addr_parts(a) is not None:
        return (False, "that is a Bitcoin Cash address — paste your DigiByte address")
    if len(a) < 14:
        return (False, "too short")
    if a[0] not in _B58_ALPHABET:
        return (False, "unrecognized format")
    version, payload = _b58check_decode(a)
    if version is None:
        return (False, payload)          # payload holds the reason here
    if version in DGB_VERSIONS:
        # ⚠️ version 30 is shared with Dogecoin (see the note above). Accepted on
        # purpose, and deliberately not flagged in the UI: same key, spendable.
        return (True, DGB_VERSIONS[version])
    known = _DGB_FOREIGN_B58.get(version)
    if known:
        return (False, "that is %s" % known)
    return (False, "not a DigiByte address (unknown version byte %d)" % version)


def validate_for_chain(chain, addr):
    """(ok, detail, username) — the ONE place a chain is mapped to its address
    rule, so the on-screen check and the Start check can never drift apart.
    `username` is the exact stratum username form for that chain, or None."""
    a = (addr or "").strip()
    if chain == "btc":
        ok, detail = validate_btc_address(a)
        return (ok, detail, a if ok else None)
    if chain == "bch":
        ok, detail, bare = validate_bch_address(a)
        return (ok, detail, bare if ok else None)      # bare lowercase CashAddr
    if chain == "dgb":
        ok, detail = validate_dgb_address(a)
        # bech32 is case-insensitive but lowercase is the canonical form every
        # decoder accepts; base58 is case-SIGNIFICANT and must pass through as-is.
        if ok and a[:4].lower() == "dgb1":
            a = a.lower()
        return (ok, detail, a if ok else None)
    raise KeyError("no address rule for chain %r" % chain)


# ── window sizing ─────────────────────────────────────────────────────────────
# 🔴 The full layout is about 900 px tall. A 14-inch laptop is 1366x768, and a
# 1080p panel at Windows' 150% scaling reports 1280x720 to Tk — so on the very
# hardware a CPU miner runs on, a fixed 900 px window puts Start Mining, the
# status line, the tiles and the whole log below the fold with no way to reach
# them. The app therefore opens to fit the screen it is actually on, and its
# content scrolls. Pure function so it can be tested without a display.
WIN_NATURAL_W = 600
WIN_NATURAL_H = 900
WIN_MIN_W = 520
WIN_MIN_H = 420
WIN_CHROME_H = 80          # title bar + taskbar allowance


def window_geometry(screen_w, screen_h, natural_w=WIN_NATURAL_W, natural_h=WIN_NATURAL_H,
                    min_w=WIN_MIN_W, min_h=WIN_MIN_H, chrome=WIN_CHROME_H):
    """(width, height) for the initial window: never taller than the usable
    screen, never below the minimum, never larger than the natural size."""
    usable_h = max(min_h, int(screen_h) - chrome)
    usable_w = max(min_w, int(screen_w) - 40)
    return (max(min_w, min(natural_w, usable_w)),
            max(min_h, min(natural_h, usable_h)))


# colours (brand-ish, works on the default tk theme)
BG = "#0b0e14"
CARD = "#11161f"
FG = "#dfe6f0"
MUTED = "#9fb0c5"
ORANGE = "#f7931a"
ORANGE_HOT = "#ffa733"
GREEN = "#3ad17a"
RED = "#ff6b6b"
BORDER = "#1c2534"

# 32×32 window icon (orange rounded square + bolt), PNG, generated at build time
ICON_B64 = ("iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABCklEQVR42tWXsQ3CMBBF0yNRESBI"
            "lHRMQEPNCizAArABG7AEezAHc1Aa/UgnWVbi+O47JkT6RaQo/8n/7DtX1dSfz2PjGP3ElIIZyzwJ"
            "YmzzKAT70+dl3coMwZi/743bbWtuFRiA475uZQZgzK+nlZvNF+58WNprgckd5pAm/ywAkrsA4L0o"
            "ADIXc4jajtbcRZb8zQB+7iJEAYhQr1uTFyDMPaaUVVEDhLn3CZApRakCCHOPKXVHJAN05d4nUz8Y"
            "+hDFJM1G1BUHVqnYOYAi8821vYAGsBRdNgCY+QBD+z07ANuEaADJ33oE0zMBMtdOQFknImvRZQHQ"
            "Dp9FJ+O/uBtM/2o2ictpyecL3pHtrp/wV0YAAAAASUVORK5CYII=")


def app_dir():
    """Folder the app lives in — works for both `python script.py` and a
    PyInstaller --onefile .exe."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


# 🔴 Settings are split so that NO FILE EVER HOLDS TWO COINS' ADDRESSES.
#   sololuck_miner.cfg        — machine-level only: last coin picked, CPU load.
#   sololuck_miner_<coin>.cfg — that coin's payout address and worker name.
# Switching coin writes the old coin's file and reads the new one; there is no
# shared address, worker or key for anything to leak through.
APP_CFG_PATH = os.path.join(app_dir(), "sololuck_miner.cfg")


def chain_cfg_path(key):
    return os.path.join(app_dir(), "sololuck_miner_%s.cfg" % key)


# ── CPU feature detection (decides which cpuminer-opt build to fetch) ──────────
_PF = {"SSE42": 38, "AVX": 39, "AVX2": 40, "AVX512F": 41}


def _has(feat):
    """True if the running CPU/OS reports the given instruction-set feature."""
    if os.name != "nt":
        return False
    try:
        import ctypes
        return bool(ctypes.windll.kernel32.IsProcessorFeaturePresent(_PF[feat]))
    except Exception:
        return False


def _cpuid(leaf, subleaf=0):
    """x86-64 CPUID via a tiny ctypes shellcode stub → (eax,ebx,ecx,edx). Win64 only."""
    if os.name != "nt":
        raise OSError("cpuid: Windows only")
    import ctypes
    if ctypes.sizeof(ctypes.c_void_p) != 8:
        raise OSError("cpuid: 64-bit only")
    code = bytes((
        0x53, 0x4D, 0x89, 0xC1, 0x89, 0xC8, 0x89, 0xD1, 0x0F, 0xA2,
        0x41, 0x89, 0x01, 0x41, 0x89, 0x59, 0x04, 0x41, 0x89, 0x49, 0x08,
        0x41, 0x89, 0x51, 0x0C, 0x5B, 0xC3,
    ))
    k = ctypes.windll.kernel32
    k.VirtualAlloc.restype = ctypes.c_void_p
    k.VirtualAlloc.argtypes = (ctypes.c_void_p, ctypes.c_size_t, ctypes.c_ulong, ctypes.c_ulong)
    addr = k.VirtualAlloc(None, len(code), 0x3000, 0x40)
    if not addr:
        raise OSError("cpuid: VirtualAlloc failed")
    try:
        ctypes.memmove(addr, code, len(code))
        out = (ctypes.c_uint32 * 4)()
        proto = ctypes.CFUNCTYPE(None, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p)
        proto(addr)(leaf, subleaf, ctypes.cast(out, ctypes.c_void_p))
        return (out[0], out[1], out[2], out[3])
    finally:
        k.VirtualFree.argtypes = (ctypes.c_void_p, ctypes.c_size_t, ctypes.c_ulong)
        k.VirtualFree(addr, 0, 0x8000)


def cpu_features():
    """AVX-family from the OS; AES/SHA-NI/VAES from CPUID. Fails safe to False."""
    f = {"AVX512F": _has("AVX512F"), "AVX2": _has("AVX2"),
         "AVX": _has("AVX"), "SSE42": _has("SSE42"),
         "AES": False, "SHA": False, "VAES": False}
    try:
        _, _, ecx1, _ = _cpuid(1)
        _, ebx7, ecx7, _ = _cpuid(7, 0)
        f["AES"] = bool(ecx1 & (1 << 25))
        f["SHA"] = bool(ebx7 & (1 << 29))
        f["VAES"] = bool(ecx7 & (1 << 9))
        if not f["SSE42"]:
            f["SSE42"] = bool(ecx1 & (1 << 20))
    except Exception:
        pass
    return f


def cpu_signature():
    import platform
    fe = cpu_features()
    flags = "".join("1" if fe[k] else "0" for k in
                    ("AVX512F", "AVX2", "AVX", "SSE42", "AES", "SHA", "VAES"))
    try:
        brand = platform.processor() or ""
    except Exception:
        brand = ""
    return flags + "|" + brand


def preferred_builds():
    """cpuminer-opt build names best→safest for THIS CPU; ends at the universal sse2."""
    f = cpu_features()
    c = []
    if f["AVX512F"]:
        if f["SHA"] and f["VAES"]:
            c.append("cpuminer-avx512-sha-vaes.exe")
        c.append("cpuminer-avx512.exe")
    if f["AVX2"]:
        if f["SHA"] and f["VAES"]:
            c.append("cpuminer-avx2-sha-vaes.exe")
        if f["SHA"]:
            c.append("cpuminer-avx2-sha.exe")
        c.append("cpuminer-avx2.exe")
    if f["AVX"]:
        c.append("cpuminer-avx.exe")
    if f["SSE42"] and f["AES"]:
        c.append("cpuminer-aes-sse42.exe")
    c.append("cpuminer-sse2.exe")
    seen, out = set(), []
    for x in c:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


# ── CPU identity (for the spec readout) ───────────────────────────────────────
def tier_of(build_name):
    """Human name for the SIMD path a cpuminer build uses (drives per-core speed)."""
    n = (build_name or "").lower()
    if "avx512-sha" in n:
        return "AVX-512 + SHA"
    if "avx512" in n:
        return "AVX-512"
    if "avx2-sha" in n:
        return "AVX2 + SHA"
    if "avx2" in n:
        return "AVX2"
    if "avx" in n:
        return "AVX"
    if "aes-sse42" in n or "sse42" in n:
        return "SSE4.2 + AES"
    if "sse2" in n:
        return "SSE2 (baseline)"
    return ""


def cpu_brand():
    """Marketing name of the CPU (e.g. 'AMD Ryzen 7 9800X3D'). CPUID brand string
    on Windows; falls back to platform/env. Never raises."""
    if os.name == "nt":
        try:
            if _cpuid(0x80000000)[0] >= 0x80000004:
                buf = b""
                for leaf in (0x80000002, 0x80000003, 0x80000004):
                    for reg in _cpuid(leaf):
                        buf += int(reg).to_bytes(4, "little")
                s = buf.split(b"\x00")[0].decode("ascii", "replace").strip()
                if s:
                    return " ".join(s.split())  # collapse the padding spaces
        except Exception:
            pass
    try:
        import platform
        return platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", "CPU")
    except Exception:
        return "CPU"


def physical_cores():
    """Physical core count via GetLogicalProcessorInformation (Win64). None if
    unknown — the caller shows logical threads instead."""
    if os.name != "nt":
        return None
    try:
        import ctypes

        class _SLPI(ctypes.Structure):
            _fields_ = [("mask", ctypes.c_size_t),
                        ("relationship", ctypes.c_uint32),
                        ("_pad", ctypes.c_ubyte * 20)]
        k = ctypes.windll.kernel32
        rl = ctypes.c_uint32(0)
        k.GetLogicalProcessorInformation(None, ctypes.byref(rl))  # sizing call
        n = rl.value // ctypes.sizeof(_SLPI)
        if n <= 0:
            return None
        arr = (_SLPI * n)()
        if not k.GetLogicalProcessorInformation(arr, ctypes.byref(rl)):
            return None
        cores = sum(1 for x in arr if x.relationship == 0)  # RelationProcessorCore
        return cores or None
    except Exception:
        return None


def cpu_spec():
    """{brand, physical, logical, tier, build} — everything the spec line shows."""
    logical = os.cpu_count() or 1
    builds = preferred_builds()
    build = builds[0] if builds else ""
    return {"brand": cpu_brand(), "physical": physical_cores(),
            "logical": logical, "tier": tier_of(build), "build": build}


class CpuMeter:
    """Per-logical-core busy% from NtQuerySystemInformation (Win64, no deps).
    sample() returns a list of 0-100 ints (one per logical CPU) or None."""
    _SPPI = 8  # SystemProcessorPerformanceInformation

    def __init__(self):
        self.n = os.cpu_count() or 1
        self._prev = None
        self._ok = os.name == "nt"
        if self._ok:
            try:
                import ctypes

                class _PI(ctypes.Structure):
                    _fields_ = [("Idle", ctypes.c_int64), ("Kernel", ctypes.c_int64),
                                ("User", ctypes.c_int64), ("Dpc", ctypes.c_int64),
                                ("Int", ctypes.c_int64), ("IntCount", ctypes.c_uint32)]
                self._PI = _PI
                self._ntdll = ctypes.windll.ntdll
                self._ctypes = ctypes
            except Exception:
                self._ok = False

    def _read(self):
        c = self._ctypes
        arr = (self._PI * self.n)()
        ret = c.c_uint32(0)
        st = self._ntdll.NtQuerySystemInformation(self._SPPI, arr, c.sizeof(arr), c.byref(ret))
        if st != 0:
            return None
        return [(p.Idle, p.Kernel, p.User) for p in arr]

    def sample(self):
        if not self._ok:
            return None
        try:
            cur = self._read()
        except Exception:
            self._ok = False
            return None
        if not cur:
            return None
        out, prev = None, self._prev
        if prev and len(prev) == len(cur):
            out = []
            for (i0, k0, u0), (i1, k1, u1) in zip(prev, cur):
                total = (k1 - k0) + (u1 - u0)   # KernelTime includes idle
                idle = i1 - i0
                busy = 0 if total <= 0 else max(0.0, min(1.0, (total - idle) / total))
                out.append(int(round(busy * 100)))
        self._prev = cur
        return out


# ── auto-update (check sololuck.io, verify the new exe's SHA-256, relaunch) ────
LATEST_URL = "https://sololuck.io/miner-latest.json"


def _version_tuple(s):
    out = []
    for part in str(s).split("."):
        digits = "".join(ch for ch in part if ch.isdigit())
        out.append(int(digits) if digits else 0)
    return tuple(out) or (0,)


def check_for_update(current=APP_VERSION):
    """Ask the site for the latest version. Returns the release dict
    {version,file,url,sha256} only if it is strictly newer than `current`,
    else None. Never raises (offline / blocked → None)."""
    try:
        info = _http_get(LATEST_URL, want_json=True, timeout=15)
    except Exception:
        return None
    if not isinstance(info, dict) or "version" not in info:
        return None
    if _version_tuple(info["version"]) <= _version_tuple(current):
        return None
    url = info.get("url") or ("https://sololuck.io/" + info.get("file", ""))
    sha = (info.get("sha256") or "").lower()
    if not (info.get("file") and re.fullmatch(r"[0-9a-f]{64}", sha)):
        return None
    info["url"] = url
    return info


def _update_dir():
    """A writable folder to drop the new exe in (prefer next to the current app)."""
    for base in (app_dir(), os.environ.get("USERPROFILE", ""), os.environ.get("TEMP", "")):
        if not base:
            continue
        try:
            t = os.path.join(base, ".sl_wtest")
            with open(t, "w"):
                pass
            os.remove(t)
            return base
        except Exception:
            continue
    return app_dir()


def download_update(info, report=lambda s: None):
    """Fetch the newer versioned exe, verify its SHA-256 against the manifest
    (fail closed), and return the local path. No overwrite of the running exe —
    the file is versioned, so the new one just sits beside the old."""
    dest = os.path.join(_update_dir(), info["file"])
    report("Downloading %s…" % info["file"])
    blob = _http_get(info["url"], timeout=300)
    got = hashlib.sha256(blob).hexdigest()
    if got != info["sha256"].lower():
        raise RuntimeError("SECURITY: the downloaded update does not match the "
                           "published SHA-256.\nExpected %s\nGot      %s\nNothing was saved."
                           % (info["sha256"], got))
    with open(dest, "wb") as f:
        f.write(blob)
    report("Update verified — SHA-256 OK.")
    return dest


# ── engine location (a stable, antivirus-excludable folder next to the app) ───
def engine_dir():
    """A stable, writable folder to keep the downloaded engine in (so the path
    doesn't change and the user can add ONE antivirus exclusion that sticks)."""
    for base in (app_dir(), os.environ.get("LOCALAPPDATA", ""), os.environ.get("TEMP", "")):
        if not base:
            continue
        d = os.path.join(base, ENGINE_DIR_NAME)
        try:
            os.makedirs(d, exist_ok=True)
            t = os.path.join(d, ".wtest")
            with open(t, "w"):
                pass
            os.remove(t)
            return d
        except Exception:
            continue
    return os.path.join(app_dir(), ENGINE_DIR_NAME)


def _ps_run(command, timeout=15):
    """Run a short PowerShell command hidden, return stdout (Windows only)."""
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    out = subprocess.run(["powershell", "-NoProfile", "-Command", command],
                         capture_output=True, text=True, timeout=timeout,
                         creationflags=flags)
    return out.stdout or ""


def av_exclusion_present():
    """Is the engine folder already a Windows Defender path-exclusion?
    True / False on Windows; None when we can't tell (not Windows, no Defender,
    query blocked) — callers hide the UI on None rather than nag."""
    if os.name != "nt":
        return None
    try:
        d = os.path.normcase(os.path.normpath(engine_dir()))
        paths = [os.path.normcase(os.path.normpath(p.strip()))
                 for p in _ps_run("(Get-MpPreference).ExclusionPath").splitlines() if p.strip()]
        return d in paths
    except Exception:
        return None


def add_av_exclusion():
    """Add Windows Defender exclusions for the engine folder so the mining engine
    is never quarantined: a PATH exclusion for the folder and a PROCESS exclusion
    for cpuminer executables INSIDE that folder. Real-time protection stays on for
    everything else — but two rules are added, not one, and both persist until
    they are removed by hand. Exclusions are machine-wide and need admin, so it
    elevates via a single UAC prompt and WAITS for it to finish (synchronous, so a
    caller can safely download into the folder right after). Also restores anything
    already quarantined from the folder. Returns True only when the exclusion is
    confirmed in place; False if declined / failed / non-Windows.

    Call this OFF the UI thread — it blocks on the elevation prompt."""
    if os.name != "nt":
        return False
    try:
        d = engine_dir().replace("'", "''")
        # elevated child: add the path + process exclusions, then un-quarantine any
        # engine Defender already took from the folder (best-effort).
        #
        # 🔴 The process rule is scoped to the engine folder's FULL PATH. It used
        # to be a bare 'cpuminer-*.exe', which matched a process of that name in
        # ANY folder, machine-wide, and outlived uninstalling this app — a lasting
        # hole the user was never told about and the app could not see to remove.
        # Narrowing it cannot break the engine: the folder path exclusion above
        # already covers everything in that directory.
        inner = ("Add-MpPreference -ExclusionPath '%s'; "
                 "Add-MpPreference -ExclusionProcess '%s\\cpuminer-*.exe'; "
                 "$m=Join-Path $env:ProgramFiles 'Windows Defender\\MpCmdRun.exe'; "
                 "if(Test-Path $m){ & $m -Restore -Path '%s' 2>$null }" % (d, d, d))
        b64 = base64.b64encode(inner.encode("utf-16-le")).decode()
        # non-elevated launcher raises the ONE UAC prompt and waits for the child
        outer = ("try{ Start-Process powershell -Verb RunAs -Wait -WindowStyle Hidden "
                 "-ArgumentList @('-NoProfile','-EncodedCommand','%s'); exit 0 }"
                 "catch{ exit 1 }" % b64)
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        r = subprocess.run(["powershell", "-NoProfile", "-Command", outer],
                           timeout=180, creationflags=flags)
        return r.returncode == 0 and av_exclusion_present() is True
    except Exception:
        return False


def _shield_engine_folder(report=lambda s: None):
    """Exclude the engine folder from Defender BEFORE the engine is written to disk,
    so a fresh download is never quarantined. Real-time protection stays fully ON —
    this tells Defender to skip the engine folder and cpuminer programs within it. Best-effort: if it's already
    excluded we do nothing, and if the user declines the prompt we still try the
    download (the engine may then be blocked, and the UI offers 'Shield it' + retry)."""
    if os.name != "nt":
        return
    try:
        if av_exclusion_present():
            return
        report("Adding two Windows Security exclusions for the engine folder — approve "
               "the prompt. Real-time protection stays ON everywhere else; this skips "
               "the engine folder and cpuminer programs inside it. Both rules stay "
               "until you remove them in Windows Security…")
        if add_av_exclusion():
            report("Engine folder shielded — the fast engine won't be quarantined.")
        else:
            report("Not shielded (you can click ‘Shield it’ later). Continuing…")
    except Exception:
        pass


def find_user_miner():
    """A user-supplied cpuminer build dropped in the app folder (skips the download)."""
    d = app_dir()
    for name in MINER_NAMES:
        p = os.path.join(d, name)
        if os.path.isfile(p):
            return p
    try:
        for f in os.listdir(d):
            low = f.lower()
            if low == ENGINE_DIR_NAME.lower():
                continue
            if low.startswith("cpuminer") and (low.endswith(".exe") or "." not in low):
                return os.path.join(d, f)
    except OSError:
        pass
    return None


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify_log(msg):
    """Verification audit trail: engine-verify.log next to the engine + stdout."""
    line = "%s %s" % (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), msg)
    try:
        with open(os.path.join(engine_dir(), "engine-verify.log"), "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass
    print(line)


def verify_engine_file(path):
    """True iff the file's bytes match the pinned manifest for its filename."""
    name = os.path.basename(path)
    want = ENGINE_FILE_SHA256.get(name)
    if not want:
        _verify_log("verify %s: not in the pinned %s manifest -> UNVERIFIED" % (name, ENGINE_VERSION))
        return False
    try:
        got = _sha256_file(path)
    except OSError as e:
        _verify_log("verify %s: unreadable (%s) -> FAIL" % (name, e))
        return False
    ok = got == want
    _verify_log("verify %s: expected=%s actual=%s -> %s" % (name, want, got, "OK" if ok else "MISMATCH"))
    return ok


def _quarantine(path):
    """Never execute a bad engine — move it aside (or delete if rename fails)."""
    try:
        os.replace(path, path + ".quarantined")
        _verify_log("quarantined %s" % path)
    except OSError:
        try:
            os.remove(path)
            _verify_log("deleted unverifiable %s" % path)
        except OSError:
            pass


def find_local_engine():
    """The best already-downloaded build in the engine folder, SHA-256-verified
    against the pinned manifest. A cached file is never assumed trusted; a
    mismatching one is quarantined and never returned."""
    d = engine_dir()
    for b in preferred_builds():
        p = os.path.join(d, b)
        if os.path.isfile(p):
            if verify_engine_file(p):
                return p
            _quarantine(p)
    return None


def _http_get(url, want_json=False, timeout=180):
    req = urllib.request.Request(url, headers={"User-Agent": "SoloLuckMiner",
                                               "Accept": "application/octet-stream" if not want_json
                                               else "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    return json.loads(data.decode("utf-8")) if want_json else data


def download_engine(report=lambda s: None):
    """Fetch the PINNED cpuminer-opt release archive, verify its SHA-256, then
    extract the build matching this CPU (+ sse2 fallback + runtime DLLs), each
    re-verified on disk. Fails closed: any mismatch aborts with a security
    error and nothing unverified is left behind. No mirrors, no 'latest'."""
    dest = engine_dir()
    # Shield the folder FIRST so Windows Defender can't quarantine the engine as it
    # lands — real-time protection stays on; only this folder is excluded.
    _shield_engine_folder(report)
    report("Downloading the pinned mining engine cpuminer-opt %s (~18 MB, one time)…" % ENGINE_VERSION)
    _verify_log("download url=%s engine=%s" % (ENGINE_ZIP_URL, ENGINE_VERSION))
    blob = _http_get(ENGINE_ZIP_URL, timeout=300)
    got = hashlib.sha256(blob).hexdigest()
    _verify_log("archive expected=%s actual=%s -> %s"
                % (ENGINE_ZIP_SHA256, got, "OK" if got == ENGINE_ZIP_SHA256 else "MISMATCH"))
    if got != ENGINE_ZIP_SHA256:
        raise RuntimeError(
            "SECURITY: the downloaded engine archive does not match the pinned "
            "SHA-256 for cpuminer-opt %s.\nExpected %s\nGot      %s\n"
            "Nothing was installed. Check your connection (proxy or antivirus "
            "interception can cause this) and try again." % (ENGINE_VERSION, ENGINE_ZIP_SHA256, got))
    report("Archive verified · unpacking…")
    zf = zipfile.ZipFile(io.BytesIO(blob))
    members = {os.path.basename(n): n for n in zf.namelist() if not n.endswith("/")}
    wanted = []
    for b in preferred_builds():
        if b in members and b in ENGINE_FILE_SHA256:
            wanted.append(b)
            break
    if ("cpuminer-sse2.exe" in members and "cpuminer-sse2.exe" in ENGINE_FILE_SHA256
            and "cpuminer-sse2.exe" not in wanted):
        wanted.append("cpuminer-sse2.exe")
    if not any(w.endswith(".exe") for w in wanted):
        raise RuntimeError("Unsupported CPU: no matching cpuminer-opt %s build for this machine."
                           % ENGINE_VERSION)
    for d in ENGINE_DLLS:
        if d in members:
            wanted.append(d)
    os.makedirs(dest, exist_ok=True)
    for name in wanted:
        p = os.path.join(dest, name)
        with zf.open(members[name]) as srcf, open(p, "wb") as out:
            out.write(srcf.read())
        if not verify_engine_file(p):
            _quarantine(p)
            raise RuntimeError("SECURITY: %s failed verification after extraction; "
                               "it was quarantined and will not run." % name)
    eng = find_local_engine()
    if not eng:
        raise RuntimeError("Engine unpacked but no runnable verified build was produced.")
    report("Engine cpuminer-opt %s installed — SHA-256 verified." % ENGINE_VERSION)
    return eng


def _confirm_unverified_user_engine(path):
    """A user-supplied engine that is NOT the pinned build runs only after an
    explicit, informed yes. Headless: refuse (fail closed)."""
    if messagebox is None:
        return False
    try:
        return bool(messagebox.askyesno(
            APP_NAME,
            "You placed your own engine next to the app:\n%s\n\n"
            "It is NOT the SHA-256-verified cpuminer-opt %s build this app pins, so "
            "SoloLuck cannot vouch for it.\n\nRun YOUR file anyway?" % (path, ENGINE_VERSION)))
    except Exception:  # no display / dialog failure — fail closed
        return False


def ensure_engine(report=lambda s: None, confirm_unverified=None):
    """Resolve a runnable engine: user override (verified, or explicitly
    user-confirmed) → verified cached copy → verified pinned download."""
    up = find_user_miner()
    if up:
        if verify_engine_file(up):
            report("Engine cpuminer-opt %s (your copy) — SHA-256 verified." % ENGINE_VERSION)
            return up
        ok = (confirm_unverified or _confirm_unverified_user_engine)(up)
        _verify_log("user-supplied engine %s unverified -> %s"
                    % (up, "user accepted" if ok else "refused"))
        if ok:
            return up
    eng = find_local_engine()
    if eng:
        report("Engine cpuminer-opt %s — SHA-256 verified." % ENGINE_VERSION)
        return eng
    return download_engine(report)


def _engine_missing_msg():
    """Actionable message when the engine isn't available — download failure or, most
    often, antivirus blocking the downloaded cpuminer engine."""
    folder = engine_dir()
    return ("The mining engine isn't available.\n\n"
            "Either the one-time download didn't finish (check your internet), or — most "
            "likely — your antivirus / Windows Defender blocked or removed it. EVERY CPU "
            "miner trips this false-positive; it's the cpuminer-opt engine, not this app, "
            "and it does nothing but hash.\n\n"
            "Fix it once:\n"
            "  1. Windows Security  →  Virus & threat protection.\n"
            "  2. Under \"Protection history\", Allow / Restore any SoloLuck or cpuminer item.\n"
            "  3. Add an Exclusion (Folder) for:\n"
            "       %s\n"
            "  4. Reopen SoloLuck Miner (it will re-download if needed) and click Start.\n\n"
            "Note: only engine files whose SHA-256 matches the pinned engine manifest run "
            "automatically (audit trail: engine-verify.log in that folder).\n"
            "Advanced: drop your own cpuminer-opt.exe next to this app (you will be "
            "asked to confirm it)." % folder)


class MinerApp:
    def __init__(self, root):
        self.root = root
        self.proc = None
        self.reader = None
        self.q = queue.Queue()
        self.accepted = 0
        self.rejected = 0
        self.hashrate = "—"
        self.engine_path = None
        self.engine_ready = False
        self.engine_error = None
        self._start_ts = 0
        self._saw_hash = False
        self._fellback = False          # one automatic retry on the sse2 build per session
        self._user_engine_choice = None  # remembered answer for an unverified user engine
        self._cur_addr = ""
        self._spec = cpu_spec()
        self.meter_src = CpuMeter()
        self._last_cores = None
        self._last_meter_ts = 0
        self._update_info = None
        self._update_path = None
        self._update_downloading = False
        root.title("%s %s v%s · engine cpuminer-opt %s"
                   % (APP_NAME, CHAIN_DEF["name"], APP_VERSION, ENGINE_VERSION))
        root.configure(bg=BG)
        root.minsize(WIN_MIN_W, WIN_MIN_H)
        root.resizable(True, True)
        try:
            w, h = window_geometry(root.winfo_screenwidth(), root.winfo_screenheight())
            root.geometry("%dx%d" % (w, h))
        except Exception:
            pass
        try:
            self._icon = tk.PhotoImage(data=ICON_B64)
            root.iconphoto(True, self._icon)
        except Exception:
            pass
        self._build_scroll_host()
        self._build_ui()
        self._load_cfg()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(200, self._pump)
        threading.Thread(target=self._init_engine, daemon=True).start()
        threading.Thread(target=self._check_update, daemon=True).start()
        threading.Thread(target=self._door_run, daemon=True).start()

    # ---------- scrollable host ----------
    def _build_scroll_host(self):
        """Everything the app draws lives inside a scrolling canvas.

        🔴 Without this the window is ~900 px tall and a 14-inch laptop cannot
        reach the Start button. The scrollbar only appears when the content is
        actually taller than the window, and the wheel is bound too — a
        scrollbar a trackpad cannot drive is only half a fix."""
        outer = tk.Frame(self.root, bg=BG)
        outer.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(outer, bg=BG, highlightthickness=0, bd=0,
                                takefocus=0)
        self.vbar = ttk.Scrollbar(outer, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self._on_scroll_set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self._vbar_shown = False
        # every widget below is packed into self.body, not self.root
        self.body = tk.Frame(self.canvas, bg=BG)
        self._body_id = self.canvas.create_window((0, 0), window=self.body, anchor="nw")
        self.body.bind("<Configure>", self._sync_scrollregion)
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        # Windows/macOS send <MouseWheel>; X11 sends Button-4/5
        self.root.bind_all("<MouseWheel>", self._on_wheel, add="+")
        self.root.bind_all("<Button-4>", self._on_wheel, add="+")
        self.root.bind_all("<Button-5>", self._on_wheel, add="+")

    def _sync_scrollregion(self, _event=None):
        try:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except Exception:
            pass

    def _on_canvas_resize(self, event):
        """Content always spans the canvas width; when it is shorter than the
        window it is stretched so the background does not end mid-page."""
        try:
            self.canvas.itemconfigure(self._body_id, width=event.width)
            need = self.body.winfo_reqheight()
            self.canvas.itemconfigure(self._body_id,
                                      height=max(need, event.height))
        except Exception:
            pass
        self._sync_scrollregion()

    def _on_scroll_set(self, first, last):
        """Show the scrollbar only when there is something to scroll."""
        try:
            self.vbar.set(first, last)
            need = not (float(first) <= 0.0 and float(last) >= 1.0)
            if need and not self._vbar_shown:
                self.vbar.pack(side="right", fill="y")
                self._vbar_shown = True
            elif not need and self._vbar_shown:
                self.vbar.pack_forget()
                self._vbar_shown = False
        except Exception:
            pass

    def _on_wheel(self, event):
        """Wheel scrolls the page — unless the pointer is over the miner log,
        which has its own scrollbar and should keep its own wheel."""
        if not self._vbar_shown:
            return
        try:
            w = self.root.winfo_containing(event.x_root, event.y_root)
        except Exception:
            w = None
        node = w
        while node is not None:
            if node is getattr(self, "log", None):
                return
            node = getattr(node, "master", None)
        if getattr(event, "num", None) == 4:
            self.canvas.yview_scroll(-3, "units")
        elif getattr(event, "num", None) == 5:
            self.canvas.yview_scroll(3, "units")
        elif event.delta:
            self.canvas.yview_scroll(int(-event.delta / 40), "units")

    # ---------- UI ----------
    def _build_ui(self):
        pad = {"padx": 14, "pady": 3}
        head = tk.Frame(self.body, bg=BG)
        head.pack(fill="x", pady=(8, 2))
        tk.Label(head, text="SoloLuck", fg=ORANGE, bg=BG,
                 font=("Segoe UI", 20, "bold")).pack()
        # names the selected coin — one of the places the coin must be unmistakable
        self.head_lbl = tk.Label(head, text="", fg=MUTED, bg=BG, font=("Segoe UI", 10))
        self.head_lbl.pack()

        # update banner — created hidden, shown when a newer version is found
        self.update_bar = tk.Frame(self.body, bg="#132015", highlightbackground=GREEN,
                                   highlightthickness=1)
        self.update_lbl = tk.Label(self.update_bar, text="", bg="#132015", fg=GREEN,
                                   font=("Segoe UI", 9, "bold"))
        self.update_lbl.pack(side="left", padx=(12, 8), pady=6)
        self.update_btn = tk.Button(self.update_bar, text="Update now", command=self._do_update,
                                    bg=GREEN, fg="#08120b", relief="flat", cursor="hand2",
                                    font=("Segoe UI", 9, "bold"), padx=12, pady=3)
        self.update_btn.pack(side="right", padx=(0, 10), pady=5)
        _wc = tk.Label(self.update_bar, text="What changed ↗", bg="#132015", fg=MUTED,
                       cursor="hand2", font=("Segoe UI", 8, "underline"))
        _wc.pack(side="right", padx=8)
        _wc.bind("<Button-1>", lambda _e: webbrowser.open(CHANGELOG_URL))

        self._build_cpu_card()

        form = tk.Frame(self.body, bg=CARD, highlightbackground=BORDER,
                        highlightthickness=1, bd=0)
        form.pack(fill="x", padx=14, pady=6)
        inner = tk.Frame(form, bg=CARD)
        inner.pack(fill="x", padx=12, pady=8)

        def row(label, default=""):
            fr = tk.Frame(inner, bg=CARD)
            fr.pack(fill="x", pady=2)
            lbl = tk.Label(fr, text=label, fg=MUTED, bg=CARD, width=18, anchor="w",
                           font=("Segoe UI", 9))
            lbl.pack(side="left")
            var = tk.StringVar(value=default)
            ent = tk.Entry(fr, textvariable=var, bg=BG, fg=FG, insertbackground=FG,
                           relief="flat", font=("Consolas", 10),
                           highlightthickness=1, highlightbackground=BORDER,
                           highlightcolor=ORANGE)
            ent.pack(side="left", fill="x", expand=True, ipady=4)
            return var, ent, lbl

        # A single-coin build (gen-miners.py) has nothing to choose, so no row is
        # drawn at all — not a row with one disabled button.
        self.chain_var = tk.StringVar(value=CHAIN)
        self.chain_btns = []
        if len(CHAIN_ORDER) > 1:
            cf = tk.Frame(inner, bg=CARD)
            cf.pack(fill="x", pady=2)
            tk.Label(cf, text="Coin", fg=MUTED, bg=CARD, width=18, anchor="w",
                     font=("Segoe UI", 9)).pack(side="left")
            for key in CHAIN_ORDER:
                c = CHAINS[key]
                rb = tk.Radiobutton(cf, text=c["name"] + (" (beta)" if c["beta"] else ""),
                                    variable=self.chain_var, value=key,
                                    command=self._on_chain, bg=CARD, fg=FG, selectcolor=BG,
                                    activebackground=CARD, activeforeground=FG,
                                    highlightthickness=0, font=("Segoe UI", 9))
                rb.pack(side="left", padx=(0, 12))
                self.chain_btns.append(rb)

        self.addr_var, _, self.addr_lbl = row(CHAIN_DEF["addr_label"], "")
        self.addr_status = tk.Label(inner, text="", fg=MUTED, bg=CARD, anchor="w",
                                    font=("Segoe UI", 8))
        self.addr_status.pack(fill="x", padx=(122, 0))
        self.addr_var.trace_add("write", lambda *_a: self._on_addr())
        self.worker_var, _, _ = row("Worker name", "pc")

        pf = tk.Frame(inner, bg=CARD)
        pf.pack(fill="x", pady=2)
        tk.Label(pf, text="Pool", fg=MUTED, bg=CARD, width=18, anchor="w",
                 font=("Segoe UI", 9)).pack(side="left")
        self.pool_lbl = tk.Label(pf, text="", fg=FG, bg=CARD, anchor="w",
                                 font=("Consolas", 10))
        self.pool_lbl.pack(side="left", ipady=4)
        self.pool_hint = tk.Label(pf, text=CHAIN_DEF["hint"], fg=MUTED, bg=CARD,
                                  font=("Segoe UI", 8))
        self.pool_hint.pack(side="left")

        self._ncpu = os.cpu_count() or 1
        ldf = tk.Frame(inner, bg=CARD)
        ldf.pack(fill="x", pady=(8, 0))
        tk.Label(ldf, text="CPU load", fg=MUTED, bg=CARD, width=18, anchor="w",
                 font=("Segoe UI", 9)).pack(side="left")
        self.pct_var = tk.IntVar(value=CPU_PCT_DEFAULT)
        self.pct_scale = tk.Scale(ldf, from_=CPU_PCT_MIN, to=CPU_PCT_HARD_MAX, orient="horizontal",
                                  variable=self.pct_var, command=self._on_pct,
                                  showvalue=0, bg=ORANGE, fg=FG, troughcolor=BG,
                                  activebackground=ORANGE_HOT, highlightthickness=0,
                                  bd=0, relief="flat", sliderrelief="flat",
                                  sliderlength=22, width=10)
        self.pct_scale.pack(side="left", fill="x", expand=True, padx=(0, 0))
        self.pct_lbl = tk.Label(inner, text="", bg=CARD, anchor="w",
                                font=("Segoe UI", 9, "bold"))
        self.pct_lbl.pack(anchor="w", padx=(118, 0))
        tk.Label(inner, text="Capped at 90% — the top threads add heat, not hashrate.",
                 bg=CARD, fg=MUTED, font=("Segoe UI", 8), anchor="w",
                 justify="left", wraplength=520).pack(anchor="w", padx=(118, 0))
        # Antivirus shield (Windows only): a quarantined fast engine silently drops
        # you to the slow baseline build — the single biggest hashrate loss — so offer
        # to exclude the engine folder from Windows Defender.
        self.av_frame = tk.Frame(inner, bg=CARD)
        self.av_frame.pack(anchor="w", padx=(118, 0), pady=(3, 0))
        self.av_lbl = tk.Label(self.av_frame, text="", bg=CARD, fg=MUTED,
                               font=("Segoe UI", 8), anchor="w", justify="left", wraplength=430)
        self.av_lbl.pack(side="left")
        self.av_btn = tk.Label(self.av_frame, text="", fg=ORANGE, bg=CARD, cursor="hand2",
                               font=("Segoe UI", 8, "underline"))
        self.av_btn.pack(side="left", padx=(6, 0))
        self.av_btn.bind("<Button-1>", lambda _e: self._shield_av())
        self._refresh_av_ui()
        self._on_pct()
        self._on_addr()

        btns = tk.Frame(self.body, bg=BG)
        btns.pack(fill="x", **pad)
        self.btn_row = btns
        self.start_btn = tk.Button(btns, text="▶  Start Mining", command=self.start,
                                   bg=ORANGE, fg="#0b0e14", relief="flat",
                                   font=("Segoe UI", 11, "bold"), activebackground=ORANGE_HOT,
                                   cursor="hand2", padx=16, pady=8)
        self.start_btn.pack(side="left")
        self.stop_btn = tk.Button(btns, text="■  Stop", command=self.stop,
                                  bg=CARD, fg=FG, relief="flat", state="disabled",
                                  font=("Segoe UI", 11, "bold"), activebackground=BORDER,
                                  cursor="hand2", padx=16, pady=8)
        self.stop_btn.pack(side="left", padx=8)

        def hover(btn, normal, hot):
            btn.bind("<Enter>", lambda _e: btn["state"] == "normal" and btn.config(bg=hot))
            btn.bind("<Leave>", lambda _e: btn.config(bg=normal))
        hover(self.start_btn, ORANGE, ORANGE_HOT)
        hover(self.stop_btn, CARD, BORDER)
        # 🔴 Gated-coin banner — created hidden. In this build DigiByte is dropped
        # from CHAINS entirely so it never shows; a single-coin DigiByte build has
        # nothing else to select, and then this is what says why Start is dead.
        self.gate_bar = tk.Frame(self.body, bg="#20180d", highlightbackground=ORANGE,
                                 highlightthickness=1)
        self.gate_lbl = tk.Label(self.gate_bar, text="", bg="#20180d", fg=ORANGE,
                                 font=("Segoe UI", 9, "bold"), anchor="w")
        self.gate_lbl.pack(fill="x", padx=12, pady=(6, 0))
        self.gate_why = tk.Label(self.gate_bar, text="", bg="#20180d", fg=MUTED,
                                 font=("Segoe UI", 8), anchor="w", justify="left",
                                 wraplength=520)
        self.gate_why.pack(fill="x", padx=12, pady=(0, 6))

        stats = tk.Frame(self.body, bg=BG)
        stats.pack(fill="x", **pad)
        self.status_lbl = tk.Label(stats, text="● stopped · Bitcoin", fg=MUTED, bg=BG,
                                   font=("Segoe UI", 10, "bold"))
        self.status_lbl.grid(row=0, column=0, sticky="w", columnspan=2, pady=(0, 6))
        self.time_lbl = tk.Label(stats, text="", fg=MUTED, bg=BG, font=("Segoe UI", 9))
        self.time_lbl.grid(row=0, column=2, sticky="e", pady=(0, 6))

        def stat(col, title):
            f = tk.Frame(stats, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
            f.grid(row=1, column=col, sticky="nsew", padx=4)
            stats.grid_columnconfigure(col, weight=1)
            t = tk.Label(f, text=title, fg=MUTED, bg=CARD, font=("Segoe UI", 8))
            t.pack(pady=(9, 0))
            v = tk.Label(f, text="—", fg=FG, bg=CARD, font=("Segoe UI", 15, "bold"))
            v.pack(pady=(0, 9))
            return t, v

        # every tile carries the coin's ticker: these counters are per-coin and
        # are never carried across a chain switch, so they must never look shared
        self.hr_title, self.hr_lbl = stat(0, "HASHRATE")
        self.acc_title, self.acc_lbl = stat(1, "ACCEPTED")
        self.rej_title, self.rej_lbl = stat(2, "REJECTED")
        self._stat_titles = (("HASHRATE", self.hr_title), ("ACCEPTED", self.acc_title),
                             ("REJECTED", self.rej_title))

        # appears after the first accepted share — opens the pool's stats page
        self.link_lbl = tk.Label(self.body, text="", fg=ORANGE, bg=BG, cursor="hand2",
                                 font=("Segoe UI", 9, "underline"))
        self.link_lbl.bind("<Button-1>", self._open_stats)

        self.engine_lbl = tk.Label(self.body, text="Engine: checking…",
                                    fg=MUTED, bg=BG, font=("Segoe UI", 8))
        self.engine_lbl.pack(anchor="w", padx=18, pady=(2, 0))

        logf = tk.Frame(self.body, bg=BG)
        logf.pack(fill="both", expand=True, padx=14, pady=(6, 2))
        tk.Label(logf, text="Miner log", fg=MUTED, bg=BG,
                 font=("Segoe UI", 9)).pack(anchor="w")
        body = tk.Frame(logf, bg=BG, highlightbackground=BORDER, highlightthickness=1)
        body.pack(fill="both", expand=True)
        self.log = tk.Text(body, bg="#080b10", fg=MUTED, relief="flat", wrap="word",
                           font=("Consolas", 9), height=7, insertbackground=FG)
        sb = ttk.Scrollbar(body, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)
        self.log.configure(state="disabled")

        foot = tk.Frame(self.body, bg=BG)
        foot.pack(fill="x", padx=16, pady=(4, 10))
        # short form: at 600 px the long version string pushed "What's new" off
        tk.Label(foot, text="v%s · engine %s" % (APP_VERSION, ENGINE_VERSION),
                 fg=MUTED, bg=BG, font=("Segoe UI", 8)).pack(side="left")
        self.updchk_lbl = tk.Label(foot, text="Check for updates ↻", fg=ORANGE, bg=BG,
                                   cursor="hand2", font=("Segoe UI", 8, "underline"))
        self.updchk_lbl.pack(side="left", padx=(10, 0))
        self.updchk_lbl.bind("<Button-1>", lambda _e: self._manual_check())
        self.verify_lbl = tk.Label(foot, text="Verify build ✓", fg=ORANGE, bg=BG,
                                   cursor="hand2", font=("Segoe UI", 8, "underline"))
        self.verify_lbl.pack(side="left", padx=(10, 0))
        self.verify_lbl.bind("<Button-1>", lambda _e: self._verify_build())
        wn = tk.Label(foot, text="What's new ↗", fg=ORANGE, bg=BG, cursor="hand2",
                      font=("Segoe UI", 8, "underline"))
        wn.pack(side="right")
        wn.bind("<Button-1>", lambda _e: webbrowser.open(CHANGELOG_URL))

    # ---------- CPU spec card + live per-core meter ----------
    def _build_cpu_card(self):
        spec = self._spec
        card = tk.Frame(self.body, bg=CARD, highlightbackground=BORDER,
                        highlightthickness=1, bd=0)
        card.pack(fill="x", padx=14, pady=6)
        inner = tk.Frame(card, bg=CARD)
        inner.pack(fill="x", padx=12, pady=8)

        top = tk.Frame(inner, bg=CARD)
        top.pack(fill="x")
        tk.Label(top, text="🖥", bg=CARD, font=("Segoe UI", 15)).pack(side="left", padx=(0, 8))
        nm = tk.Frame(top, bg=CARD)
        nm.pack(side="left", fill="x", expand=True)
        tk.Label(nm, text=spec["brand"], fg=FG, bg=CARD, anchor="w",
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")
        cores = ("%d cores · %d threads" % (spec["physical"], spec["logical"])
                 if spec["physical"] else "%d threads" % spec["logical"])
        sub = cores + (("  ·  mining path: " + spec["tier"]) if spec["tier"] else "")
        tk.Label(nm, text=sub, fg=MUTED, bg=CARD, anchor="w",
                 font=("Segoe UI", 8)).pack(anchor="w")

        row = tk.Frame(inner, bg=CARD)
        row.pack(fill="x", pady=(8, 0))
        tk.Label(row, text="Per-core load", fg=MUTED, bg=CARD,
                 font=("Segoe UI", 8)).pack(side="left")
        self.core_count_lbl = tk.Label(row, text="", fg=MUTED, bg=CARD,
                                       font=("Segoe UI", 8))
        self.core_count_lbl.pack(side="right")
        self.meter = tk.Canvas(inner, height=34, bg=BG, highlightthickness=1,
                               highlightbackground=BORDER, bd=0)
        self.meter.pack(fill="x", pady=(3, 0))
        self.meter.bind("<Configure>", lambda _e: self._draw_meter(self._last_cores))
        self.meter.bind("<Enter>", lambda _e: None)

    def _draw_meter(self, pcts):
        c = self.meter
        c.delete("all")
        w = c.winfo_width() or 1
        h = c.winfo_height() or 34
        n = self._spec["logical"]
        if not pcts:
            c.create_text(w // 2, h // 2, text="waiting for CPU data…" if os.name == "nt"
                          else "per-core view is Windows-only",
                          fill=MUTED, font=("Segoe UI", 8))
            return
        pad, gap = 4, 2
        bw = max(2.0, (w - 2 * pad - gap * (n - 1)) / n)
        active = 0
        for i, p in enumerate(pcts[:n]):
            x0 = pad + i * (bw + gap)
            x1 = x0 + bw
            c.create_rectangle(x0, pad, x1, h - pad, fill="#0f141c", outline="")
            fh = (h - 2 * pad) * (p / 100.0)
            # a busy core is GREEN (it's earning); idle cores stay dim
            if p >= 15:
                active += 1
            col = "#243040" if p < 12 else GREEN
            if fh > 0:
                c.create_rectangle(x0, h - pad - fh, x1, h - pad, fill=col, outline="")
        self.core_count_lbl.config(text="%d of %d cores active" % (active, n))

    def _update_meter(self):
        pcts = self.meter_src.sample() if self.meter_src else None
        if pcts:
            self._last_cores = pcts
            self._draw_meter(pcts)

    def _chain(self):
        """The selected coin, clamped to what this build offers. A hand-edited
        config naming a gated-off coin lands on Bitcoin, not on a coin with no
        pool behind it."""
        c = self.chain_var.get() if hasattr(self, "chain_var") else CHAIN
        return c if c in CHAINS else CHAIN_ORDER[0]

    def _on_chain(self):
        """Coin switch. 🔴 Per-coin state is swapped, never shared: the outgoing
        coin's address and worker are written to its own file and the incoming
        coin's are read from its own file. An address is NEVER carried across."""
        new = self._chain()
        old = getattr(self, "_ui_chain", None)
        # ⛔ never mid-run: switching coin needs an explicit Stop first
        if self.proc is not None and old is not None and new != old:
            self.chain_var.set(old)
            messagebox.showinfo(APP_NAME,
                "Stop mining before switching coin.\n\nEach coin has its own pool, its "
                "own payout address and its own share count — they are never mixed.")
            return
        if old is not None and old != new:
            self._write_chain_cfg(old)
            # per-coin statistics: a new coin starts from zero, never continues
            self.accepted = self.rejected = 0
            self.hashrate = "—"
            self._cur_addr = ""
            self.hr_lbl.config(text="—")
            self.acc_lbl.config(text="—")
            self.rej_lbl.config(text="—")
            self.time_lbl.config(text="")
            try:
                self.link_lbl.pack_forget()
            except Exception:
                pass
            self._logln("── switched to %s — its own pool, address and share count ──"
                        % CHAINS[new]["name"], MUTED)
        self._ui_chain = new
        if old != new:
            addr, worker = self._read_chain_cfg(new)
            self.addr_var.set(addr)
            self.worker_var.set(worker)
        self._apply_chain_labels()
        self._on_addr()
        if old is not None:
            self._save_cfg()

    def _apply_chain_labels(self):
        """Put the selected coin everywhere the user looks: window title, header,
        address label, endpoint, status line and every stat tile. ⛔ A user must
        never have to remember which coin they picked."""
        key = self._chain()
        c = CHAINS[key]
        self.root.title("%s %s v%s · engine cpuminer-opt %s"
                        % (APP_NAME, c["name"], APP_VERSION, ENGINE_VERSION))
        # ⭐ Bitcoin has two doors, so the endpoint on screen is the one the
        # latency check picked — not the static default. The other coins have
        # one pool each and read exactly as they always did.
        host = resolve_host(key)
        self.head_lbl.config(text="Miner — CPU solo mining %s to %s" % (c["name"], host))
        self.pool_lbl.config(text="stratum+tcp://%s:%s" % (host, c["port"]))
        self.pool_hint.config(
            text=(c["hint"] + "  ·  " + door_summary(key)) if c.get("doors")
                 else c["hint"])
        self.addr_lbl.config(text=c["addr_label"])
        for base, lbl in self._stat_titles:
            lbl.config(text="%s · %s" % (base, c["ticker"]))
        if self.proc is None:
            self.status_lbl.config(text="● stopped · %s" % c["name"], fg=MUTED)
        for rb in self.chain_btns:
            rb.config(state="disabled" if self.proc is not None else "normal")
        # a gated coin can only be the selection in a single-coin build
        gated = not chain_enabled(key)
        if hasattr(self, "start_btn"):
            self.start_btn.config(
                state="disabled" if gated else "normal",
                text="▶  Start Mining (not yet)" if gated else "▶  Start Mining",
                bg=CARD if gated else ORANGE, fg=MUTED if gated else "#0b0e14")
        if hasattr(self, "gate_bar"):
            if gated:
                self.gate_lbl.config(text="%s mining is not enabled in this build" % c["name"])
                self.gate_why.config(text=CHAIN_DISABLED_WHY)
                if not self.gate_bar.winfo_ismapped():
                    self.gate_bar.pack(fill="x", padx=14, pady=(0, 4), after=self.btn_row)
            elif self.gate_bar.winfo_ismapped():
                self.gate_bar.pack_forget()

    def _on_addr(self):
        a = self.addr_var.get().strip()
        key = self._chain()
        if not a:
            self.addr_status.config(
                text="%s  ·  %s" % (CHAINS[key]["example"], CHAINS[key]["idle"]), fg=MUTED)
            return
        ok, detail, _user = validate_for_chain(key, a)
        name = CHAINS[key]["name"]
        if ok:
            self.addr_status.config(text="✓ Valid %s address — %s" % (name, detail), fg=GREEN)
        else:
            self.addr_status.config(text="✗ Not a valid %s address — %s" % (name, detail), fg=RED)

    def _open_stats(self, _event=None):
        tmpl = CHAINS[self._chain()].get("stats_url")
        if self._cur_addr and tmpl:
            webbrowser.open(tmpl % self._cur_addr)

    # ---------- auto-update ----------
    def _check_update(self):
        info = check_for_update()
        if info:
            self.q.put(("__UPDATE__", info))

    def _manual_check(self):
        """Footer 'Check for updates' link — reports both outcomes (the silent
        startup check only surfaces a banner when something newer exists)."""
        self.updchk_lbl.config(text="Checking…")
        threading.Thread(target=self._manual_check_run, daemon=True).start()

    def _manual_check_run(self):
        try:
            info = check_for_update()
        except Exception:
            info = None
            self.q.put(("__NOUPD__", "err"))
            return
        self.q.put(("__UPDATE__", info) if info else ("__NOUPD__", "ok"))

    def _verify_build(self):
        """Footer 'Verify build' link — SHA-256s the running .exe and checks it
        against the checksum published on sololuck.io (fail-loud on mismatch)."""
        self.verify_lbl.config(text="Verifying…")
        threading.Thread(target=self._verify_run, daemon=True).start()

    def _verify_run(self):
        try:
            if not getattr(sys, "frozen", False):
                self.q.put(("__VERIFY__", {"mode": "source"}))
                return
            path = sys.executable
            h = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    h.update(chunk)
            res = {"mode": "exe", "path": path, "sha": h.hexdigest(),
                   "app_version": APP_VERSION}
            try:
                latest = _http_get(LATEST_URL, want_json=True, timeout=15)
            except Exception:
                latest = None
            if isinstance(latest, dict):
                res["latest_version"] = latest.get("version")
                res["latest_sha"] = (latest.get("sha256") or "").lower()
            self.q.put(("__VERIFY__", res))
        except Exception as e:
            self.q.put(("__VERIFY__", {"mode": "error", "err": str(e)}))

    def _on_verify_result(self, res):
        self.verify_lbl.config(text="Verify build ✓")
        mode = res.get("mode")
        if mode == "source":
            messagebox.showinfo("Verify build",
                "You're running from source, so there's no released .exe to verify.\n\n"
                "Download the signed release from sololuck.io/setup, or read the source "
                "on GitHub: github.com/sololuckio/sololuck")
            return
        if mode == "error":
            messagebox.showwarning("Verify build", "Couldn't verify this file:\n%s" % res.get("err"))
            return
        sha, av = res["sha"], res["app_version"]
        lv, ls = res.get("latest_version"), res.get("latest_sha")
        head = "This file:\n  %s\n\nSHA-256:\n  %s\n\n" % (res["path"], sha)
        if lv and av == lv and ls:
            if sha == ls:
                messagebox.showinfo("Verify build ✓", head +
                    "✓ MATCH — this is the authentic SoloLuck Miner v%s.\n"
                    "Its checksum matches sololuck.io exactly." % av)
            else:
                messagebox.showerror("Verify build ✗", head +
                    "✗ MISMATCH — this file does NOT match the published v%s checksum!\n"
                    "  published: %s\n\n"
                    "Do not trust this file. Re-download from sololuck.io/setup." % (av, ls))
        else:
            messagebox.showinfo("Verify build", head +
                "Your build: v%s   (site's current release: v%s)\n\n"
                "Compare the SHA-256 above against the published checksum for v%s at:\n"
                "  sololuck.io/SHA256SUMS.txt\n"
                "  or the GitHub release: github.com/sololuckio/sololuck/releases"
                % (av, lv or "?", av))

    def _start_download(self):
        """Fetch + verify the update in the background (only meaningful frozen)."""
        if not getattr(sys, "frozen", False) or self._update_downloading:
            return
        self._update_downloading = True
        threading.Thread(target=self._run_update, args=(self._update_info,), daemon=True).start()

    def _run_update(self, info):
        try:
            path = download_update(info, lambda s: self.q.put(("__ENGMSG__", s)))
        except Exception as e:
            self.q.put(("__UPDERR__", str(e)))
            return
        self.q.put(("__UPDREADY__", path))

    def _do_update(self, _event=None):
        """Banner button. Source builds open the download page; frozen builds
        apply the verified update now (or the moment the download finishes)."""
        if not getattr(sys, "frozen", False):
            webbrowser.open("https://sololuck.io/setup")
            return
        if self._update_path:
            self._apply_update()
        else:
            self._start_download()
            self.update_btn.config(state="disabled", text="Downloading…")

    def _apply_update(self):
        """Stop mining if needed, launch the verified new exe, and close."""
        if not self._update_path:
            return
        self.stop(user=False)
        self._logln("Applying update — restarting into the new version…", GREEN)
        try:
            subprocess.Popen([self._update_path],
                             cwd=os.path.dirname(self._update_path) or None)
            self.root.after(400, self.on_close)
        except Exception as e:
            self.update_btn.config(state="normal", text="Update now")
            messagebox.showerror(APP_NAME, "Couldn't launch the update:\n%s\n\n"
                                 "Download it from sololuck.io/setup." % e)

    # ---------- CPU load slider ----------
    def _on_pct(self, _value=None):
        pct = self.pct_var.get()
        # hard cap: the slider tops out at 90%, but clamp anyway in case an older
        # saved config or a stray value pushed it higher.
        if pct > CPU_PCT_HARD_MAX:
            pct = CPU_PCT_HARD_MAX
            self.pct_var.set(pct)
        t = threads_for(pct, self._ncpu)
        # green while inside the recommended threshold, amber above it (up to the cap)
        safe = pct <= CPU_PCT_SOFT_MAX
        tag = "✓ recommended" if safe else "⚠ high load"
        self.pct_lbl.config(text="%d%% · %d of %d threads · %s" % (pct, t, self._ncpu, tag),
                            fg=GREEN if safe else ORANGE)

    # ---------- antivirus shield ----------
    def _refresh_av_ui(self):
        """Show the shield row only on Windows, and only nag when not yet excluded."""
        present = av_exclusion_present()
        if present is None:                 # not Windows / can't tell → hide entirely
            self.av_frame.pack_forget()
            return
        if present:
            self.av_lbl.config(text="🛡 Mining engine is shielded from antivirus ✓", fg=GREEN)
            self.av_btn.config(text="")
        else:
            self.av_lbl.config(
                text="🛡 Shield the engine so antivirus can't quarantine it (keeps you on "
                     "the fast build). Real-time protection stays ON — only this folder "
                     "is excluded. No need to turn anything off.", fg=ORANGE)
            self.av_btn.config(text="Shield it")

    def _shield_av(self):
        if not self.av_btn.cget("text") or getattr(self, "_shielding", False):
            return
        self._shielding = True
        self.av_btn.config(text="Shielding…")
        self._logln("Approve the Windows prompt to exclude the mining-engine folder. "
                    "Real-time protection stays on — only this one folder is skipped.", GREEN)
        threading.Thread(target=self._shield_av_run, daemon=True).start()

    def _shield_av_run(self):
        ok = add_av_exclusion()          # blocks on the UAC prompt (off the UI thread)
        self.q.put(("__SHIELD__", ok))

    def _on_shield_result(self, ok):
        self._shielding = False
        if ok:
            self._logln("Shielded ✓ — the fast engine won't be quarantined. If you were on "
                        "the slow build, click Stop then Start to pick up the fast one.", GREEN)
        else:
            self._logln("Couldn't add the exclusion (prompt declined?). In Windows Security → "
                        "Virus & threat protection → Manage settings → Exclusions, add this "
                        "folder:\n%s" % engine_dir(), ORANGE)
        self._refresh_av_ui()

    def _logln(self, text, color=None):
        self.log.configure(state="normal")
        if color:
            tag = "c_" + color.lstrip("#")
            self.log.tag_configure(tag, foreground=color)
            self.log.insert("end", text + "\n", tag)
        else:
            self.log.insert("end", text + "\n")
        self.log.see("end")
        if int(self.log.index("end-1c").split(".")[0]) > 600:
            self.log.delete("1.0", "200.0")
        self.log.configure(state="disabled")

    # ---------- which Bitcoin door is closest (off the UI thread) ----------
    def _door_run(self):
        """Measure the Bitcoin doors once at launch and hand the answer to the
        UI thread. ⛔ Never touches a widget from here."""
        try:
            run_door_probe("btc")
        except Exception:
            pass                       # run_door_probe already fails safe
        try:
            self.q.put(("__DOORS__", door_state()))
        except Exception:
            pass

    def _on_door_result(self, st):
        self._apply_chain_labels()     # repaint with the door that won
        win = st.get("picked")
        if st.get("results"):
            self._logln("Latency check — SoloLuck answers Bitcoin in two places:", MUTED)
        for r in st.get("results") or []:
            self._logln("  %-8s %-24s %s" % (
                r["label"], r["host"],
                ("%.0f ms" % r["ms"]) if r["ms"] is not None
                else ("no answer" + ((" — " + r["err"]) if r["err"] else ""))),
                MUTED)
        # ⛔ Chain-neutral wording: the user may be sitting on Bitcoin Cash when
        # this lands, and they are not mining Bitcoin anywhere.
        if win:
            # ⛔ Never print "the faster of the two" directly above two numbers
            # that say otherwise. When hysteresis keeps the default door, the
            # line has to say that is what happened.
            quicker = [r for r in (st.get("results") or [])
                       if r is not win and r["ms"] is not None
                       and win["ms"] is not None and r["ms"] < win["ms"]]
            if quicker:
                q = min(quicker, key=lambda r: r["ms"])
                self._logln("Bitcoin will mine to the %s door (%s) — %s answered "
                            "%.0f ms quicker, too little to be worth moving for."
                            % (win["label"], win["host"], q["label"],
                               win["ms"] - q["ms"]), MUTED)
            else:
                self._logln("Bitcoin will mine to the %s door (%s) — the quickest "
                            "to answer." % (win["label"], win["host"]), MUTED)
        elif st.get("results"):
            self._logln("Neither Bitcoin door answered the latency check — Bitcoin "
                        "will use %s." % CHAINS["btc"]["host"], MUTED)

    # ---------- engine resolution (off the UI thread) ----------
    def _engine_ok(self, path, why):
        self.engine_path = path
        self.engine_ready = True
        self.engine_error = None
        self.q.put(("__ENG__", os.path.basename(path), why))

    def _init_engine(self):
        """Same trust rules as ensure_engine(), but the 'run YOUR unverified
        file?' question is bounced to the UI thread via the queue."""
        try:
            over = find_user_miner()
            if over:
                if verify_engine_file(over):
                    self._engine_ok(over, "your copy — SHA-256 verified")
                    return
                if self._user_engine_choice is True:
                    self._engine_ok(over, "your own build (unverified — you approved it)")
                    return
                if self._user_engine_choice is None:
                    self.q.put(("__CONFIRM__", over))
                    return  # resolution continues after the user answers
            # accept a cached engine only if it's the BEST build this CPU can run;
            # if a faster build is missing (e.g. antivirus removed it, leaving only
            # the slow sse2 baseline) re-fetch it — download_engine() shields the
            # folder first so the refetch survives with real-time protection ON.
            local = find_local_engine()
            ideal = (preferred_builds() or [None])[0]
            ideal_ok = bool(ideal and os.path.isfile(os.path.join(engine_dir(), ideal))
                            and verify_engine_file(os.path.join(engine_dir(), ideal)))
            if local and ideal_ok:
                self._engine_ok(local, "SHA-256 verified")
                return
            try:
                p = download_engine(lambda s: self.q.put(("__ENGMSG__", s)))
                self._engine_ok(p, "downloaded + SHA-256 verified")
            except Exception:
                if local:   # refetch failed but a slower verified build is present
                    self._engine_ok(local, "SHA-256 verified (baseline — ‘Shield it’ for full speed)")
                    return
                raise
        except Exception as e:
            self.engine_error = str(e)
            self.q.put(("__ENGERR__", str(e)))

    def _tier_from_name(self, name):
        n = name.lower()
        if "avx512" in n:
            return "AVX-512"
        if "avx2-sha" in n:
            return "AVX2 + SHA"
        if "avx2" in n:
            return "AVX2"
        if "aes-sse42" in n or "sse42" in n:
            return "SSE4.2 + AES"
        if "sse2" in n:
            return "SSE2 (baseline)"
        return ""

    # ---------- config ----------
    # ---------- settings (per coin, never shared) ----------
    def _read_chain_cfg(self, key):
        """That coin's own file -> (addr, worker). 🔴 The address is adopted only
        if it still validates for THIS coin: a file that has been edited, copied
        between machines, or written by an older shared-config build could be
        holding another chain's address, and that must never be offered."""
        try:
            with open(chain_cfg_path(key)) as f:
                c = json.load(f)
            if not isinstance(c, dict):
                return ("", "pc")
        except Exception:
            return ("", "pc")
        addr = str(c.get("addr") or "").strip()
        worker = str(c.get("worker") or "pc").strip() or "pc"
        if addr:
            try:
                ok, _detail, _user = validate_for_chain(key, addr)
            except KeyError:
                ok = False
            if not ok:
                return ("", "pc")       # dropped, not shown, never re-offered
        return (addr, worker)

    def _write_chain_cfg(self, key):
        """Persist ONLY the currently shown fields, into that coin's own file."""
        try:
            with open(chain_cfg_path(key), "w") as f:
                json.dump({"chain": key,
                           "addr": self.addr_var.get().strip(),
                           "worker": self.worker_var.get().strip()}, f)
        except Exception:
            pass

    def _migrate_legacy_cfg(self, c):
        """Older builds kept the address in the shared file (<= v1.11.0-beta.2) or
        in a per-coin sub-dict (beta.3). Move each into that coin's own file, and
        only where it validates there. ⛔ Nothing is ever moved between coins."""
        moved = []
        chains = c.get("chains")
        if isinstance(chains, dict):                       # beta.3 shape
            for k, v in chains.items():
                if k in CHAIN_DEFS and isinstance(v, dict) and v.get("addr"):
                    moved.append((k, str(v.get("addr")).strip(),
                                  str(v.get("worker") or "pc").strip()))
        elif c.get("addr"):                                # <= beta.2 flat shape
            k = c.get("chain") if c.get("chain") in CHAIN_DEFS else "btc"
            moved.append((k, str(c["addr"]).strip(), str(c.get("worker") or "pc").strip()))
        for k, addr, worker in moved:
            if os.path.exists(chain_cfg_path(k)):
                continue                                   # already migrated
            try:
                ok, _d, _u = validate_for_chain(k, addr)
            except KeyError:
                ok = False
            if not ok:
                continue
            try:
                with open(chain_cfg_path(k), "w") as f:
                    json.dump({"chain": k, "addr": addr, "worker": worker or "pc"}, f)
            except Exception:
                pass

    def _load_cfg(self):
        c = {}
        try:
            with open(APP_CFG_PATH) as f:
                c = json.load(f)
            if not isinstance(c, dict):
                c = {}
        except Exception:
            c = {}
        self._migrate_legacy_cfg(c)
        # 🔴 clamped to what this build offers: a config naming a gated-off coin
        # selects Bitcoin, it does not resurrect the coin.
        self.chain_var.set(c["chain"] if c.get("chain") in CHAINS else CHAIN_ORDER[0])
        try:
            if "cpu_pct" in c:
                pct = int(c["cpu_pct"])
                # migrate v1.7 and earlier: full_cpu=true (or any >90%) meant 100% —
                # now hard-capped at 90%.
                if c.get("full_cpu"):
                    pct = CPU_PCT_HARD_MAX
            elif str(c.get("threads", "")).isdigit():
                # pre-1.3.0 cfg stored a thread count — map it onto the slider
                pct = int(round(int(c["threads"]) * 100.0 / self._ncpu))
            else:
                pct = CPU_PCT_DEFAULT
            self.pct_var.set(max(CPU_PCT_MIN, min(CPU_PCT_HARD_MAX, pct)))
            self._on_pct()
        except Exception:
            pass
        # ⛔ NOT wrapped in try/except: this loads the selected coin's own address
        # and paints the coin into the title, header, endpoint, status and every
        # stat tile. A silent failure would leave the window unlabelled — exactly
        # the confusion the per-coin boundary exists to prevent.
        self._ui_chain = None
        self._on_chain()

    def _save_cfg(self):
        """The shared file carries NO coin state — only which coin was last used
        and the machine-wide CPU load."""
        self._write_chain_cfg(self._chain())
        try:
            with open(APP_CFG_PATH, "w") as f:
                json.dump({"chain": self._chain(), "cpu_pct": self.pct_var.get()}, f)
        except Exception:
            pass

    # ---------- mining control ----------
    def _resolve_start_engine(self):
        """Engine for this Start click. A user-dropped build still wins, but only
        SHA-256-verified — or after the same explicit yes the init path uses
        (remembered for the session). After an auto-fallback, stick to it."""
        if self._fellback:
            return self.engine_path
        up = find_user_miner()
        if up and up != self.engine_path:
            if verify_engine_file(up):
                return up
            if self._user_engine_choice is None:
                self._user_engine_choice = _confirm_unverified_user_engine(up)
                _verify_log("user-supplied engine %s unverified -> %s"
                            % (up, "user accepted" if self._user_engine_choice else "refused"))
            if self._user_engine_choice:
                return up
        return self.engine_path or find_local_engine()

    def start(self):
        if self.proc:
            return
        addr = self.addr_var.get().strip()
        worker = re.sub(r"[^A-Za-z0-9_-]", "", self.worker_var.get().strip())
        chain = self._chain()
        # 🔴 Last line of defence for a gated coin (DigiByte until its pool is
        # live). It is normally not even in CHAINS; the Start button is disabled
        # where it is. Refuse anyway rather than resolve a host.
        if chain not in CHAINS or not chain_enabled(chain):
            messagebox.showinfo(APP_NAME, CHAIN_DISABLED_WHY)
            return
        # per coin, never typed. For Bitcoin this is whichever door the launch
        # latency check picked; wait briefly if it is somehow still running, then
        # fall back to the default host rather than make the user wait.
        host, port = resolve_host(chain, wait=3.0), CHAINS[chain]["port"]
        self._on_pct()  # sync the label with the current slider value
        # the load is hard-capped at 90% — clamp here too so nothing (a stale cfg,
        # a stray value) can ever push the miner above the cap.
        eff_pct = min(self.pct_var.get(), CPU_PCT_HARD_MAX)
        threads = str(threads_for(eff_pct, self._ncpu))

        ok, detail, user_addr = validate_for_chain(chain, addr)
        if not ok:
            messagebox.showerror(APP_NAME,
                "That is not a valid %s address (%s).\n\nUse the address you want the "
                "block reward paid to (%s). In solo mode the address IS your "
                "login — a typo here would make a found block unclaimable."
                % (CHAINS[chain]["name"], detail, CHAINS[chain]["example"]))
            return
        addr = user_addr             # the exact stratum username form for this chain

        miner = self._resolve_start_engine()
        if not miner or not os.path.isfile(miner):
            if not self.engine_ready and not self.engine_error:
                messagebox.showinfo(APP_NAME,
                    "The mining engine is still downloading (one-time, ~18 MB). "
                    "Give it a moment, then click Start again.")
            elif self.engine_error and messagebox.askretrycancel(
                    APP_NAME, _engine_missing_msg() + "\n\nRetry the download now?"):
                self.engine_error = None
                self.engine_lbl.config(text="Engine: downloading…", fg=MUTED)
                threading.Thread(target=self._init_engine, daemon=True).start()
            elif not self.engine_error:
                messagebox.showerror(APP_NAME, _engine_missing_msg())
            return
        self.engine_path = miner

        user = ("%s.%s" % (addr, worker)) if worker else addr
        url = "stratum+tcp://%s:%s" % (host, port)
        # ⚠️ Always the plain default. A "d=" password does NOT lower the pool's
        # difficulty — ckpool clamps the request up to the port's mindiff and the
        # ratchet only ever goes one way — so sending one would buy nothing and
        # invite a false claim on screen.
        pw = "x"
        cmd = [miner, "-a", ALGO, "-o", url, "-u", user, "-p", pw]
        if threads.isdigit():
            cmd += ["-t", threads]

        self.accepted = 0
        self.rejected = 0
        self.acc_lbl.config(text="0")
        self.rej_lbl.config(text="0")
        self.hr_lbl.config(text="…")
        self._saw_hash = False
        self._start_ts = time.time()
        self._cur_addr = addr
        self._save_cfg()
        note = CHAINS[chain].get("start_note")
        if note:
            self._logln(note, MUTED)
        self._logln("$ %s -a %s -o %s -u %s -p %s%s"
                    % (os.path.basename(miner), ALGO, url, user, pw,
                       (" -t " + threads) if threads.isdigit() else ""), ORANGE)

        creationflags = 0
        if os.name == "nt":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        try:
            self.proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL, text=True, bufsize=1,
                universal_newlines=True, creationflags=creationflags,
                cwd=app_dir())
        except OSError as e:
            self.proc = None
            if isinstance(e, FileNotFoundError) or getattr(e, "winerror", None) in (2, 225, 226):
                messagebox.showerror(APP_NAME, _engine_missing_msg())
            else:
                messagebox.showerror(APP_NAME, "Couldn't launch the miner:\n%s" % e)
            return
        except Exception as e:
            self.proc = None
            messagebox.showerror(APP_NAME, "Couldn't launch the miner:\n%s" % e)
            return

        self.reader = threading.Thread(target=self._read_output, args=(self.proc,), daemon=True)
        self.reader.start()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_lbl.config(text="● connecting… · %s" % CHAINS[chain]["name"], fg=ORANGE)
        for rb in self.chain_btns:      # ⛔ no coin switch mid-run
            rb.config(state="disabled")

    def _read_output(self, p):
        try:
            for line in p.stdout:
                self.q.put(line.rstrip("\n"))
        except Exception:
            pass
        self.q.put(("__EXIT__", p.poll(), p))

    def stop(self, user=True):
        p, self.proc = self.proc, None
        if p:
            # terminate now; wait/kill off the UI thread so the window never freezes
            try:
                p.terminate()
            except Exception:
                pass
            def _reap():
                try:
                    p.wait(timeout=4)
                except Exception:
                    try:
                        p.kill()
                    except Exception:
                        pass
            threading.Thread(target=_reap, daemon=True).start()
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_lbl.config(text="● stopped · %s" % CHAINS[self._chain()]["name"], fg=MUTED)
        self.hr_lbl.config(text="—")
        for rb in self.chain_btns:      # switching coin is allowed again once stopped
            rb.config(state="normal")
        if user:
            self._logln("— stopped —", MUTED)
            # a verified update was waiting for the miner to stop → apply it now
            if self._update_path:
                self.root.after(300, self._apply_update)

    # ---------- events / output ----------
    def _pump(self):
        try:
            while True:
                item = self.q.get_nowait()
                if isinstance(item, tuple) and item:
                    self._handle_event(item)
                    continue
                self._handle_line(item)
        except queue.Empty:
            pass
        if self.proc is not None and self._start_ts:
            s = int(time.time() - self._start_ts)
            self.time_lbl.config(text="⏱ %d:%02d:%02d" % (s // 3600, s % 3600 // 60, s % 60))
        elif self.time_lbl.cget("text"):
            self.time_lbl.config(text="")
        now = time.time()
        if now - self._last_meter_ts >= 1.0:   # CPU% needs a ~1s delta window
            self._last_meter_ts = now
            self._update_meter()
        self.root.after(200, self._pump)

    def _handle_event(self, item):
        kind = item[0]
        if kind == "__EXIT__":
            if len(item) > 2 and item[2] is not self.proc:
                return  # a previous run's reader finishing — not the live miner
            if self.proc is not None:
                code = item[1]
                self._logln("— miner exited (code %s%s) —" % (code, explain_exit(code)), RED)
                if self._try_sse2_fallback(code):
                    return
                self.stop(user=False)
        elif kind == "__ENG__":
            name, why = item[1], item[2]
            tier = self._tier_from_name(name)
            self.engine_lbl.config(
                text="Engine: %s%s · %s" % (name, (" (" + tier + ")") if tier else "", why),
                fg=MUTED)
            self._logln("Engine ready: %s%s [%s]"
                        % (name, (" — " + tier) if tier else "", why), MUTED)
        elif kind == "__ENGMSG__":
            self.engine_lbl.config(text=item[1], fg=MUTED)
            self._logln(item[1], MUTED)
        elif kind == "__ENGERR__":
            self.engine_lbl.config(text="Engine: unavailable — press Start for help", fg=RED)
            self._logln("Engine could not be prepared: %s" % item[1], RED)
        elif kind == "__CONFIRM__":
            self._user_engine_choice = _confirm_unverified_user_engine(item[1])
            _verify_log("user-supplied engine %s unverified -> %s"
                        % (item[1], "user accepted" if self._user_engine_choice else "refused"))
            threading.Thread(target=self._init_engine, daemon=True).start()
        elif kind == "__SHIELD__":
            self._on_shield_result(item[1])
        elif kind == "__DOORS__":
            self._on_door_result(item[1])
        elif kind == "__VERIFY__":
            self._on_verify_result(item[1])
        elif kind == "__NOUPD__":
            self.updchk_lbl.config(
                text="Up to date ✓" if item[1] == "ok" else "Check failed — retry ↻")
            self.root.after(4000, lambda: self.updchk_lbl.config(text="Check for updates ↻"))
        elif kind == "__UPDATE__":
            self.updchk_lbl.config(text="Check for updates ↻")
            self._update_info = item[1]
            ver = item[1]["version"]
            self.update_bar.pack(fill="x", padx=14, pady=(0, 4),
                                 after=self.body.winfo_children()[0])
            if getattr(sys, "frozen", False):
                # auto-download+verify in the background straight away
                self.update_lbl.config(text="⬆ v%s available — downloading…" % ver)
                self.update_btn.config(state="disabled", text="Downloading…")
                self._start_download()
            else:
                self.update_lbl.config(text="⬆ SoloLuck Miner v%s is available" % ver)
                self.update_btn.config(text="Get it")
            self._logln("A newer version (v%s) is available." % ver, GREEN)
        elif kind == "__UPDREADY__":
            self._update_path = item[1]
            self.update_btn.config(state="normal", text="Update now")
            if self.proc is None:
                self._logln("Update verified — installing now…", GREEN)
                self._apply_update()       # idle → auto-install
            else:
                self.update_lbl.config(
                    text="⬆ v%s downloaded — installs when you Stop" % self._update_info["version"])
                self._logln("Update downloaded and verified — it will install when you stop "
                            "mining, or click Update now.", GREEN)
        elif kind == "__UPDERR__":
            self._update_downloading = False
            self.update_btn.config(state="normal", text="Retry update")
            self._logln("Update failed: %s" % item[1], RED)

    def _try_sse2_fallback(self, code):
        """A too-new build crashing on launch (illegal instruction) auto-retries
        once on the universal sse2 build instead of leaving a cryptic error."""
        ran_short = time.time() - self._start_ts < 12
        if (self._fellback or self._saw_hash or not ran_short
                or not is_cpu_mismatch_exit(code)):
            return False
        cur = os.path.basename(self.engine_path or "")
        if cur == "cpuminer-sse2.exe":
            return False
        sse2 = os.path.join(engine_dir(), "cpuminer-sse2.exe")
        if not (os.path.isfile(sse2) and verify_engine_file(sse2)):
            return False
        self._fellback = True
        self.engine_path = sse2
        self.stop(user=False)
        self._logln("That engine build crashed right away — your CPU may not support it. "
                    "Retrying with the baseline SSE2 build (works on any 64-bit CPU)…", ORANGE)
        self.start()
        return True

    def _handle_line(self, line):
        low = line.lower()
        color = None
        state = classify_line(line)
        name = CHAINS[self._chain()]["name"]     # the readout always names the coin
        if "accepted" in low or "yes!" in low:
            color = GREEN
            self.status_lbl.config(text="● mining · %s" % name, fg=GREEN)
        elif "rejected" in low or "booo" in low:
            color = RED
        elif state == "fail":
            color = RED
            self.status_lbl.config(text="● reconnecting… · %s" % name, fg=ORANGE)
        elif state == "live":
            self.status_lbl.config(text="● mining · %s" % name, fg=GREEN)

        m = ACCEPT_RE.search(line)
        if m:
            acc, total = int(m.group(1)), int(m.group(2))
            self.accepted = acc
            self.rejected = max(0, total - acc)
            self.acc_lbl.config(text=str(self.accepted))
            self.rej_lbl.config(text=str(self.rejected))
        elif "accepted" in low:
            self.accepted += 1
            self.acc_lbl.config(text=str(self.accepted))
        elif "rejected" in low:
            self.rejected += 1
            self.rej_lbl.config(text=str(self.rejected))
        # ⛔ only offered for a coin that actually HAS a per-worker stats page —
        # never a link that would show one chain's address on another's page.
        if (self.accepted > 0 and self._cur_addr and CHAINS[self._chain()].get("stats_url")
                and not self.link_lbl.winfo_ismapped()):
            self.link_lbl.config(text="Share accepted — see your worker at "
                                      "sololuck.io/users/%s…" % self._cur_addr[:12])
            self.link_lbl.pack(anchor="w", padx=18, pady=(2, 0),
                               before=self.engine_lbl)

        if "h/s" in low and not low.lstrip("[0123456789:.\\- ]").startswith("cpu #"):
            hm = HASH_RE.search(line)
            if hm:
                self._saw_hash = True
                self.hashrate = "%s %sH/s" % (hm.group(1), hm.group(2) or "")
                self.hr_lbl.config(text=self.hashrate)

        self._logln(line, color)

    def on_close(self):
        self.stop(user=False)
        self.root.destroy()


def _selftest():
    """Headless build-validation: resolve the engine (downloading if needed) and run
    it with -V to confirm it launches. Writes the result to a file beside the app."""
    out = os.path.join(app_dir(), "sololuck_selftest_%s.txt" % CHAIN)
    lines = []
    def w(s):
        lines.append(str(s))
    try:
        w("features: %s" % cpu_features())
        w("preferred: %s" % preferred_builds())
        w("engine_dir: %s" % engine_dir())
        eng = ensure_engine(lambda s: w("  " + s))
        w("engine: %s" % eng)
        if not eng:
            w("RESULT: FAIL (no engine)")
        else:
            w("engine_files: %s" % sorted(os.listdir(os.path.dirname(eng))))
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) if os.name == "nt" else 0
            r = subprocess.run([eng, "-V"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               timeout=30, creationflags=flags, text=True)
            w("engine -V exit: %s" % r.returncode)
            for ln in (r.stdout or "").splitlines()[:5]:
                w("  " + ln)
            ok = r.returncode == 0 and "cpuminer" in (r.stdout or "").lower()
            w("RESULT: %s" % ("PASS — engine downloaded + launches" if ok else "FAIL"))
    except Exception as e:
        w("error: %r" % e)
        w("RESULT: FAIL")
    try:
        open(out, "w").write("\n".join(lines) + "\n")
    except Exception:
        pass


def _minetest(seconds, addr, threads):
    """Headless end-to-end test: resolve the engine and mine live for `seconds`,
    exactly like the Start button. Writes result beside the app.
    Usage: SoloLuckMiner.exe --minetest <seconds> <btc-address> [threads]"""
    out = os.path.join(app_dir(), "sololuck_minetest_%s.txt" % CHAIN)
    log = []
    def w(s):
        log.append(str(s))
    # 🔴 The gate applies here too. Found on integra 2026-09-06: this path used to
    # check only the address and go straight to ensure_engine(), so --minetest
    # could mine a gated coin from the command line while the GUI refused.
    if not chain_enabled(CHAIN):
        w("%s is gated off in this build — refusing to mine" % CHAIN_DEF["name"])
        w("RESULT: FAIL")
        open(out, "w").write("\n".join(log) + "\n"); return
    if not validate_for_chain(CHAIN, addr or "")[0]:
        w("bad or missing %s address %r" % (CHAIN_DEF["ticker"], addr)); w("RESULT: FAIL")
        open(out, "w").write("\n".join(log) + "\n"); return
    if CHAIN_DEF.get("doors"):
        threading.Thread(target=run_door_probe, args=(CHAIN,), daemon=True).start()
    try:
        eng = ensure_engine(lambda s: w(s))
    except Exception as e:
        w("engine error: %r" % e); w("RESULT: FAIL")
        open(out, "w").write("\n".join(log) + "\n"); return
    w("engine: %s" % eng)
    _mt_host = resolve_host(CHAIN, wait=20.0)
    if CHAIN_DEF.get("doors"):
        w("door: %s" % door_summary(CHAIN))
    url = "stratum+tcp://%s:%s" % (_mt_host, CHAIN_DEF["port"])
    cmd = [eng, "-a", ALGO, "-o", url, "-u", "%s.%s" % (addr, "bundletest"), "-p", "x", "-t", str(threads)]
    w("cmd: %s" % " ".join(cmd))
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) if os.name == "nt" else 0
    captured = []
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, bufsize=1, creationflags=flags)
    except Exception as e:
        w("launch error: %r" % e); w("RESULT: FAIL")
        open(out, "w").write("\n".join(log) + "\n"); return
    threading.Thread(target=lambda: [captured.append(l.rstrip()) for l in p.stdout], daemon=True).start()
    end = time.time() + seconds
    while time.time() < end and p.poll() is None:
        time.sleep(0.5)
    try:
        p.terminate(); p.wait(timeout=5)
    except Exception:
        try: p.kill()
        except Exception: pass
    low = "\n".join(captured).lower()
    connected = "stratum" in low and ("connect" in low or "subscrib" in low or "authoriz" in low or "difficulty" in low)
    gotwork = "new work" in low or "new job" in low or "stratum diff" in low
    hashing = "h/s" in low or "hash rate" in low
    w("--- last 25 lines ---")
    for ln in captured[-25:]:
        w("  " + ln)
    w("--- signals: connected=%s gotwork=%s hashing=%s" % (connected, gotwork, hashing))
    w("RESULT: %s" % ("PASS — mining live to the pool" if (connected and (gotwork or hashing)) else "FAIL"))
    try:
        open(out, "w").write("\n".join(log) + "\n")
    except Exception:
        pass


def _cpuinfo():
    """Headless dump of what the spec card would show + a per-core meter sample.
    Usage: SoloLuckMiner.exe --cpuinfo

    ⚠️ This is a --noconsole binary: print() goes nowhere when it is launched
    without a console, so THE FILE IS THE ONLY OUTPUT. It is therefore written
    even if something raises — a diagnostic that vanishes silently is worse than
    no diagnostic, and that is exactly how a beta.5 packaging problem hid on
    2026-09-06: exit 0, no file, nothing to go on."""
    out = os.path.join(app_dir(), "sololuck_cpuinfo.txt")
    lines = []
    def w(s):
        lines.append(str(s))
        try:
            print(s)
        except Exception:
            pass
    try:
        sp = cpu_spec()
        w("brand: %s" % sp["brand"])
        w("physical_cores: %s" % sp["physical"])
        w("logical_threads: %s" % sp["logical"])
        w("mining_path: %s (%s)" % (sp["tier"], sp["build"]))
        w("features: %s" % cpu_features())
        m = CpuMeter()
        m.sample(); time.sleep(1.0)
        pcts = m.sample()
        w("per_core_sample: %s" % pcts)
        w("update_check: %s" % (check_for_update() or "none/uptodate"))
        ok = bool(sp["brand"] and sp["logical"] >= 1 and sp["tier"])
        w("RESULT: %s" % ("PASS" if ok else "FAIL"))

    except Exception:
        import traceback
        w("ERROR: %s" % traceback.format_exc())
        w("RESULT: FAIL")
    try:
        open(out, "w").write("\n".join(lines) + "\n")
    except Exception:
        pass


def _doors():
    """Run the latency check and report it. For support: "run this and send me
    the file" answers "which pool should I be on?" in one line.

    🔴 Writes to a FILE as well as stdout. The shipped build is --noconsole, so
    it has no stdout at all — a print-only diagnostic is invisible in exactly
    the build a user would run it from. --selftest and --minetest write files
    for the same reason."""
    out = os.path.join(app_dir(), "sololuck_doors.txt")
    lines = []
    def w(s=""):
        lines.append(str(s))
        print(s)
    w("SoloLuck Miner v%s — stratum latency check" % APP_VERSION)
    w(time.strftime("%Y-%m-%d %H:%M:%S"))
    w()
    for key in CHAIN_ORDER:
        c = CHAINS[key]
        if not c.get("doors"):
            w("%-14s %s:%s  (one pool — nothing to choose)"
              % (c["name"], c["host"], c["port"]))
            continue
        w("%s — measuring %d doors on port %s"
          % (c["name"], len(c["doors"]), c["port"]))
        rows = measure_doors(c["doors"], c["port"])
        win = pick_door(rows)
        for r in rows:
            w("  %-8s %-24s %-16s %-10s %s"
              % (r["label"], r["host"], r["ip"] or "-",
                 ("%.1f ms" % r["ms"]) if r["ms"] is not None else "no answer",
                 "%d/%d ok" % (r["ok"], r["tried"])
                 + ((" — " + r["err"]) if r["err"] else "")))
        w("  -> %s" % (("%s (%s)" % (win["label"], win["host"])) if win
                       else "no door answered — would use " + c["host"]))
    try:
        open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        print("\nwrote %s" % out)
    except Exception as e:
        print("could not write %s: %r" % (out, e))


def main():
    if "--selftest" in sys.argv:
        _selftest()
        return
    if "--cpuinfo" in sys.argv:
        _cpuinfo()
        return
    if "--doors" in sys.argv:
        _doors()
        return
    if "--minetest" in sys.argv:
        i = sys.argv.index("--minetest")
        rest = sys.argv[i + 1:]
        secs = int(rest[0]) if len(rest) > 0 and rest[0].isdigit() else 90
        addr = rest[1] if len(rest) > 1 else ""
        thr = int(rest[2]) if len(rest) > 2 and rest[2].isdigit() else 2
        _minetest(secs, addr, thr)
        return
    if os.name == "nt":
        # crisp text on high-DPI displays (Tk then picks up the real DPI itself)
        try:
            import ctypes
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    root = tk.Tk()
    try:
        if float(root.tk.call("tk", "scaling")) < 1.2:
            root.tk.call("tk", "scaling", 1.2)
    except Exception:
        pass
    MinerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
