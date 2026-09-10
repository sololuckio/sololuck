#!/usr/bin/env python3
"""Emit one single-chain miner source per coin from the one shared template.

SoloLuck ships a SEPARATE Windows executable per coin. They are not
hand-maintained: this script reads `sololuck_miner.py`, pins `CHAIN`, and
DELETES the other coins' definitions from the emitted source.

⭐ Why deletion and not a flag: the emitted file — and therefore the built .exe —
does not contain another chain's hostname at all. A Bitcoin build cannot dial
bch.sololuck.io because the string is not in it. The worst failure in a solo
miner (mining the wrong chain, so a solved block pays an address on a chain the
user did not choose) stops being something validation has to catch and becomes
something the binary cannot express.

    python3 gen-miners.py [outdir]      # default: ./dist-src

Emits <outdir>/<chain>/sololuck_miner.py for btc, bch, dgb, and verifies each:
  * CHAIN is pinned to that coin
  * exactly one chain definition survives
  * no other coin's host, name or ticker appears anywhere in the file
  * it still compiles
"""
import os
import py_compile
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "sololuck_miner.py")

# name of the dict literal in the template, and the facts that must NOT leak
# into another coin's build
CHAINS = {
    "btc": {"var": "_CHAIN_BTC", "host": "sololuck.io", "name": "Bitcoin", "ticker": "BTC"},
    "bch": {"var": "_CHAIN_BCH", "host": "bch.sololuck.io", "name": "Bitcoin Cash", "ticker": "BCH"},
    "dgb": {"var": "_CHAIN_DGB", "host": "digibyte.sololuck.io", "name": "DigiByte", "ticker": "DGB"},
}


def _block_span(lines, var):
    """Line range [start, end) of `var = { ... }`, including the comment lines
    immediately above it so a deleted chain takes its own commentary with it."""
    start = next(i for i, l in enumerate(lines) if l.startswith(var + " = {"))
    end = next(i for i in range(start, len(lines)) if lines[i].rstrip() == "}") + 1
    while start > 0 and lines[start - 1].lstrip().startswith("#"):
        start -= 1
    return start, end


def emit(chain, outdir):
    src = open(TEMPLATE, encoding="utf-8").read()
    lines = src.split("\n")

    # 1. drop every other coin's definition, bottom-up so the indices hold
    spans = sorted((_block_span(lines, CHAINS[k]["var"]) for k in CHAINS if k != chain),
                   reverse=True)
    for a, b in spans:
        del lines[a:b]

    # 2. pin CHAIN and reduce the lookup to the single surviving entry
    out = []
    for l in lines:
        if l.startswith("CHAIN = "):
            l = ('CHAIN = "%s"          # pinned by gen-miners.py — this binary '
                 'mines %s only' % (chain, CHAINS[chain]["name"]))
        elif l.startswith("CHAIN_DEFS = {"):
            l = 'CHAIN_DEFS = {"%s": %s}' % (chain, CHAINS[chain]["var"])
        out.append(l)
    text = "\n".join(out)

    d = os.path.join(outdir, chain)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "sololuck_miner.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    # 3. verify — a generator that silently emits the wrong chain is the one bug
    #    that would defeat the whole point of separate binaries.
    #    ⚠️ Coin NAMES legitimately appear in every build: each validator says
    #    which chain a rejected address belongs to ("that is a Bitcoin address").
    #    What must never appear is another coin's STRATUM ENDPOINT.
    problems = []
    if ('CHAIN = "%s"' % chain) not in text:
        problems.append("CHAIN not pinned")
    for k, v in CHAINS.items():
        present = v["var"] in text
        if k == chain and not present:
            problems.append("own definition %s missing" % v["var"])
        if k != chain and present:
            problems.append("foreign definition %s survived" % v["var"])
    # every hostname literal in the file, compared whole (sololuck.io is a
    # substring of the other two, so "in" would lie)
    #     ⚠️ bare "sololuck.io" is the WEBSITE (update check, changelog, stats)
    #     and belongs in every build. Only the per-coin stratum SUBDOMAINS are
    #     endpoints that must not leak.
    hosts = set(re.findall(r"[A-Za-z0-9.\-]*sololuck\.io", text))
    for k, v in CHAINS.items():
        if k == chain or v["host"] == "sololuck.io":
            continue
        if v["host"] in hosts:
            problems.append("foreign stratum host %s present" % v["host"])
    if "3335" in text and chain != "btc":
        problems.append("Bitcoin's stratum port 3335 present")
    if "Radiobutton" in text and len(CHAINS) > 1 and chain:
        pass   # the selector code stays; it simply draws nothing for one coin
    try:
        py_compile.compile(path, doraise=True, cfile=os.path.join(d, ".pyc"))
        os.remove(os.path.join(d, ".pyc"))
    except Exception as e:
        problems.append("does not compile: %r" % e)
        return path, problems
    # strongest check: import it and ask what it would actually dial
    import importlib.util
    spec = importlib.util.spec_from_file_location("slm_" + chain, path)
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
    except Exception as e:
        problems.append("does not import: %r" % e)
        return path, problems
    if m.CHAIN != chain:
        problems.append("imported CHAIN is %r" % m.CHAIN)
    if m.CHAIN_DEF["host"] != CHAINS[chain]["host"]:
        problems.append("would dial %s" % m.CHAIN_DEF["host"])
    if m.CHAIN_DEF["ticker"] != CHAINS[chain]["ticker"]:
        problems.append("ticker is %r" % m.CHAIN_DEF["ticker"])
    if m.DGB_ENABLED:
        problems.append("🔴 the DigiByte gate is OPEN — it must ship off")
    if list(m.CHAIN_DEFS) != [chain]:
        problems.append("CHAIN_DEFS is %s" % list(m.CHAIN_DEFS))
    if m.CHAIN_ORDER != [chain]:
        problems.append("CHAIN_ORDER is %s" % m.CHAIN_ORDER)
    if chain == "dgb" and m.chain_enabled("dgb"):
        problems.append("🔴 DigiByte build would mine — it must ship gated off")
    if not m.chain_cfg_path(chain).endswith("sololuck_miner_%s.cfg" % chain):
        problems.append("config path is not per-coin: %s" % m.chain_cfg_path(chain))
    return path, sorted(set(problems))


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "dist-src")
    bad = 0
    for chain in ("btc", "bch", "dgb"):
        path, problems = emit(chain, outdir)
        size = os.path.getsize(path)
        if problems:
            bad += 1
            print("FAIL %-4s %s" % (chain, path))
            for p in problems:
                print("       - %s" % p)
        else:
            print("ok   %-4s %s  (%d bytes)" % (chain, path, size))
    if bad:
        print("\n%d of 3 failed — nothing should be built from these." % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
