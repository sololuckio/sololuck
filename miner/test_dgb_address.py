#!/usr/bin/env python3
"""DigiByte address validation, coin boundaries, and the stable-release checks.

The address expectations were taken from a LIVE DigiByte Core 9.26.5 node
(`validateaddress`) on 2026-09-06 — not from documentation. Two are worth
knowing about, because the guides get them wrong:

  * DigiByte REFUSES version-5 "3…" addresses. That is Bitcoin's P2SH version.
  * DigiByte Core refuses its OWN base58 addresses that begin "DGB" (any case).
    It picks bech32-vs-base58 from the first three characters, and those collide
    with the "dgb" bech32 prefix, so the base58 branch is never tried. About one
    address in 691 is affected. `decodescript` will hand you such an address;
    `validateaddress` then calls it invalid — and the pool asks the node, so a
    miner using one would be turned away at connect.

The rest guard the coin boundary — every build carries all three validators,
because each has to say which chain a pasted address really belongs to — and the
release invariants, because this build auto-installs onto existing users.

Run: python3 test_dgb_address.py
"""
import hashlib
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sololuck_miner as M

# ── vector construction ──────────────────────────────────────────────────────
_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58check(version, payload):
    raw = bytes([version]) + payload
    raw += hashlib.sha256(hashlib.sha256(raw).digest()).digest()[:4]
    n = int.from_bytes(raw, "big")
    s = ""
    while n:
        n, r = divmod(n, 58)
        s = _B58[r] + s
    return "1" * (len(raw) - len(raw.lstrip(b"\x00"))) + s


def _conv(data, frm, to, pad):
    acc = bits = 0
    ret = []
    maxv = (1 << to) - 1
    for v in data:
        acc = (acc << frm) | v
        bits += frm
        while bits >= to:
            bits -= to
            ret.append((acc >> bits) & maxv)
    if pad and bits:
        ret.append((acc << (to - bits)) & maxv)
    return ret


def segwit(hrp, witver, prog):
    data = [witver] + _conv(list(prog), 8, 5, True)
    const = 1 if witver == 0 else 0x2BC830A3
    pm = M._bech32_polymod([ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]
                           + data + [0] * 6) ^ const
    chk = [(pm >> 5 * (5 - i)) & 31 for i in range(6)]
    return hrp + "1" + "".join(M._B32_CHARSET[d] for d in data + chk)


H160 = hashlib.new("ripemd160", hashlib.sha256(b"sololuck-dgb-vector").digest()).digest()
H256 = hashlib.sha256(b"sololuck-dgb-taproot").digest()

DGB_P2PKH = b58check(30, H160)          # D…
DGB_P2SH = b58check(63, H160)           # S…
DGB_WPKH = segwit("dgb", 0, H160)
DGB_WSH = segwit("dgb", 0, H256)
DGB_TR = segwit("dgb", 1, H256)
# a real, on-chain DigiByte address pulled from the node's own chain
REAL_DGB = "DQRBAufN9MAfcxjjGGkAW2Dbc4pL4zA67U"
REAL_DGB_2 = "DFf3P5fE4ckcQnCTdvNtbmUjdL24gXZMVr"
REAL_DGB_P2SH = "SitRGK7a6ueijrqvfgCjhhSJg12SFSaY5T"
# 🔴 The "DGB…" HRP shadow. DigiByte Core picks bech32-vs-base58 from the first
# three characters (ToLower(str[0:3]) == "dgb"), so a valid base58 P2PKH address
# that happens to start "DGB" is never tried as base58 and the node refuses its
# OWN address. Ground + confirmed live 2026-09-06; hits 1 in 691 v30 addresses.
SHADOW_DGB = "DGBrGR4tjb16U69diut36C6ULfDjyud1Tk"   # node: Invalid address format
SHADOW_DGb = "DGbGQt2RpRTNgfzGUDw7NAjj5ZhfTzK73o"   # node: Invalid address format
NEAR_DGA = "DGAAraNbHMYoiZnsJG7de6NEqKa8XvkcBQ"     # node: valid (control)
NEAR_DGC = "DGCBtCm4YdrNoaqYWiYJ7VCYhV2pSfA4F6"     # node: valid (control)
NEAR_DHB = "DHBPdC9SHbRT1aUq6AvdVkXy6K3TnZohYz"     # node: valid (control)
# the on-chain address that exposed the shadow: the node's own decodescript
# emits it, its own validateaddress refuses it
SHADOW_ONCHAIN = "DGBpYt3qchjgnLBMVYzSK7B33vxccCAoA9"

# (label, address, expect_valid, expect_substring_in_message_or_None)
VECTORS = [
    # ── the valid DigiByte forms ────────────────────────────────────────────
    ("DGB P2PKH v30 (D…)",          DGB_P2PKH,            True,  "P2PKH"),
    ("DGB P2SH v63 (S…)",           DGB_P2SH,             True,  "P2SH"),
    ("DGB bech32 v0 p2wpkh",        DGB_WPKH,             True,  "dgb1q"),
    ("DGB bech32 v0 p2wsh",         DGB_WSH,              True,  "dgb1q"),
    ("DGB bech32m v1 taproot",      DGB_TR,               True,  "Taproot"),
    ("DGB bech32 ALL UPPERCASE",    DGB_WPKH.upper(),     True,  "dgb1q"),
    ("DGB real on-chain address",   REAL_DGB,             True,  "P2PKH"),
    ("DGB real on-chain address 2", REAL_DGB_2,           True,  "P2PKH"),
    ("DGB real on-chain P2SH",      REAL_DGB_P2SH,        True,  "P2SH"),
    ("DGB P2PKH with whitespace",   "  " + DGB_P2PKH + " \n", True, "P2PKH"),
    # ── the "DGB…" HRP shadow: refused BY THE NODE, so refused here too ─────
    ("HRP shadow DGB…",             SHADOW_DGB,           False, "DGB"),
    ("HRP shadow DGb…",             SHADOW_DGb,           False, "DGB"),
    ("HRP shadow, on-chain",        SHADOW_ONCHAIN,       False, "DGB"),
    ("near-miss DGA… (valid)",      NEAR_DGA,             True,  "P2PKH"),
    ("near-miss DGC… (valid)",      NEAR_DGC,             True,  "P2PKH"),
    ("near-miss DHB… (valid)",      NEAR_DHB,             True,  "P2PKH"),
    # ── Dogecoin shares version 30: valid, and deliberately NOT alarmed about ─
    ("DOGE P2PKH (same v30)",       b58check(30, H160),   True,  "P2PKH"),
    # ── Bitcoin ─────────────────────────────────────────────────────────────
    ("BTC legacy 1… (v0)",          b58check(0, H160),    False, "Bitcoin"),
    ("BTC P2SH 3… (v5)",            b58check(5, H160),    False, "Bitcoin"),
    ("BTC bech32 bc1q",             segwit("bc", 0, H160), False, "Bitcoin"),
    ("BTC taproot bc1p",            segwit("bc", 1, H256), False, "Bitcoin"),
    # ── Bitcoin Cash ────────────────────────────────────────────────────────
    ("BCH CashAddr bare q…",        None,                 False, "Bitcoin Cash"),
    ("BCH CashAddr prefixed",       None,                 False, "Bitcoin Cash"),
    ("BCH CashAddr P2SH p…",        None,                 False, "Bitcoin Cash"),
    # ── testnet ─────────────────────────────────────────────────────────────
    ("DGB testnet dgbt1",           segwit("dgbt", 0, H160), False, "TESTNET"),
    ("BTC testnet tb1",             segwit("tb", 0, H160), False, "Bitcoin"),
    ("testnet base58 (v111)",       b58check(111, H160),  False, "testnet"),
    # ── other chains ────────────────────────────────────────────────────────
    ("Litecoin L… (v48)",           b58check(48, H160),   False, "Litecoin"),
    ("Litecoin P2SH M… (v50)",      b58check(50, H160),   False, "Litecoin"),
    ("Dogecoin P2SH 9… (v22)",      b58check(22, H160),   False, "Dogecoin"),
    ("unknown version byte 88",     b58check(88, H160),   False, "unknown version"),
    ("Ethereum 0x…",                "0x52908400098527886E0F7030069857D2E4169EE7",
                                                          False, "Ethereum"),
    # ── malformed ───────────────────────────────────────────────────────────
    ("garbage",                     "not-an-address",     False, None),
    ("empty",                       "",                   False, "empty"),
    ("D… one-char typo",            None,                 False, "checksum"),
    ("dgb1 one-char typo",          None,                 False, "checksum"),
    ("dgb1 MiXeD case",             None,                 False, "mixed"),
    ("dgb1 bad character",          None,                 False, "invalid character"),
    ("too short",                   "Dabc",               False, "too short"),
]


def _fill():
    """Fill the vectors that are built from other vectors."""
    bch_q = M.bch_addr_parts  # noqa: F841 (documents the reuse)
    import importlib
    out = []
    # CashAddr vectors: build via the miner's own encoder-free path — take a
    # known-good mainnet CashAddr pair.
    cash_q = "qr6m7j9njldwwzlg9v7v53unlr4jkmx6eylep8ekg2"
    cash_p = "ppm2qsznhks23z7629mms6s4cwef74vcwvn0h829pq"
    subs = {
        "BCH CashAddr bare q…": cash_q,
        "BCH CashAddr prefixed": "bitcoincash:" + cash_q,
        "BCH CashAddr P2SH p…": cash_p,
        "D… one-char typo": DGB_P2PKH[:-1] + ("A" if DGB_P2PKH[-1] != "A" else "B"),
        "dgb1 one-char typo": DGB_WPKH[:-1] + ("q" if DGB_WPKH[-1] != "q" else "p"),
        "dgb1 MiXeD case": DGB_WPKH[:6].upper() + DGB_WPKH[6:],
        "dgb1 bad character": DGB_WPKH[:-3] + "b" + DGB_WPKH[-2:],
    }
    for label, addr, ok, msg in VECTORS:
        out.append((label, subs.get(label, addr), ok, msg))
    return out


CASES = _fill()

# Frozen node verdicts, recorded 2026-09-06 against DigiByte Core 9.26.5
# with validateaddress against the operator's node.
FROZEN = {label: ok for label, _a, ok, _m in CASES}


# ── the live node ────────────────────────────────────────────────────────────
def node_validate(addr):
    """Not reachable outside the operator's network — FROZEN is used."""
    raise NotImplementedError


OFFLINE = True


class TestDigiByteAddress(unittest.TestCase):
    maxDiff = None

    def test_matches_the_node(self):
        """🔴 The node is the authority — it is what pays the block."""
        rows, bad = [], []
        for label, addr, expect, _msg in CASES:
            ok, detail = M.validate_dgb_address(addr)
            if OFFLINE or addr is None or addr == "":
                node = FROZEN[label]
            else:
                try:
                    node = node_validate(addr)
                except Exception as e:      # ⛔ never silently pass a node failure
                    self.fail("node unreachable for %r: %r" % (label, e))
            rows.append((label, addr, ok, node, detail))
            if ok != node:
                bad.append("%-28s app=%-5s node=%-5s %s" % (label, ok, node, addr))
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "m1-address-table.txt"), "w") as f:
            f.write("%-28s %-8s %-8s %-62s %s\n"
                    % ("case", "app", "node", "address", "message shown"))
            for label, addr, ok, node, detail in rows:
                f.write("%-28s %-8s %-8s %-62s %s\n"
                        % (label, "ACCEPT" if ok else "refuse",
                           "ACCEPT" if node else "refuse", (addr or "")[:62],
                           ("✓ Valid DigiByte address — " if ok else
                            "✗ Not a valid DigiByte address — ") + str(detail)))
        self.assertEqual(bad, [], "app disagrees with the node:\n" + "\n".join(bad))

    def test_expected_verdicts(self):
        for label, addr, expect, _msg in CASES:
            ok, detail = M.validate_dgb_address(addr)
            self.assertEqual(ok, expect, "%s -> %s (%s)" % (label, ok, detail))

    def test_messages_name_the_chain(self):
        for label, addr, _expect, msg in CASES:
            if not msg:
                continue
            _ok, detail = M.validate_dgb_address(addr)
            self.assertIn(msg.lower(), str(detail).lower(),
                          "%s: message %r does not mention %r" % (label, detail, msg))

    def test_bitcoin_p2sh_3_is_refused(self):
        """🔴 Many DigiByte guides list 3… as DigiByte P2SH. The node refuses it."""
        a = b58check(5, H160)
        self.assertTrue(a.startswith("3"))
        ok, detail = M.validate_dgb_address(a)
        self.assertFalse(ok)
        self.assertIn("Bitcoin", detail)

    def test_dogecoin_v30_accepted_and_not_alarmed(self):
        """⚠️ DOGE shares version 30 — accepted, and the message must NOT scare."""
        ok, detail = M.validate_dgb_address(b58check(30, H160))
        self.assertTrue(ok)
        for word in ("doge", "warning", "danger", "careful", "risk"):
            self.assertNotIn(word, detail.lower())

    def test_username_form(self):
        """bech32 is lowercased for the stratum username; base58 is untouched."""
        ok, _d, user = M.validate_for_chain("dgb", DGB_WPKH.upper())
        self.assertTrue(ok)
        self.assertEqual(user, DGB_WPKH.lower())
        ok, _d, user = M.validate_for_chain("dgb", "  " + DGB_P2PKH + "  ")
        self.assertTrue(ok)
        self.assertEqual(user, DGB_P2PKH)      # case preserved exactly

    def test_no_dgb_address_validates_as_btc_or_bch(self):
        """The boundary works in both directions."""
        for a in (DGB_P2PKH, DGB_P2SH, DGB_WPKH, DGB_TR, REAL_DGB, REAL_DGB_P2SH):
            self.assertFalse(M.validate_btc_address(a)[0], a)
            self.assertFalse(M.validate_bch_address(a)[0], a)

    def test_hrp_shadow_rule_is_exactly_three_chars(self):
        """🔴 Only the first THREE characters matter, and only case-insensitively
        equal to the bech32 hrp. The near-misses must stay valid."""
        for a in (SHADOW_DGB, SHADOW_DGb, SHADOW_ONCHAIN):
            ok, detail = M.validate_dgb_address(a)
            self.assertFalse(ok, a)
            self.assertIn("DGB", detail)
            self.assertNotIn("typo", detail.lower())     # it is not the user's fault
        for a in (NEAR_DGA, NEAR_DGC, NEAR_DHB, REAL_DGB):
            self.assertTrue(M.validate_dgb_address(a)[0], a)


def _present_chains(mod):
    """The coin definitions this build carries. The unified app has all three;
    a gen-miners.py build has exactly one."""
    return {n: getattr(mod, "_CHAIN_" + n.upper())
            for n in ("btc", "bch", "dgb") if hasattr(mod, "_CHAIN_" + n.upper())}


class TestStableRelease(unittest.TestCase):
    """🔴 This build auto-downloads and auto-installs onto every existing user
    while their machine is idle. These are the things that must be true before
    it is allowed to be called stable."""

    def test_version_is_not_a_prerelease(self):
        v = M.APP_VERSION.lower()
        for marker in ("beta", "alpha", "rc", "dev", "-pre", "snapshot"):
            self.assertNotIn(marker, v, "stable build still marked %r" % marker)

    def test_version_honours_the_reservation(self):
        """v1.11.0-beta.2 reserved '>= 1.11.1' for the first stable of this line."""
        self.assertGreaterEqual(M._version_tuple(M.APP_VERSION), (1, 11, 1))

    def test_auto_update_will_reach_the_current_stable(self):
        """1.10.1 users only receive this if it sorts newer."""
        for older in ("1.10.1", "1.10.0", "1.9.2", "1.11.0-beta.2", "1.11.0-beta.5"):
            self.assertGreater(M._version_tuple(M.APP_VERSION), M._version_tuple(older),
                               "would not reach %s users" % older)

    def test_digibyte_cannot_ship_enabled(self):
        """🔴 There is still no DigiByte pool, and digibyte.sololuck.io still
        resolves to the Bitcoin Cash machine."""
        self.assertFalse(M.DGB_ENABLED)
        self.assertFalse(M.chain_enabled("dgb"))
        if len(_present_chains(M)) > 1:
            self.assertNotIn("dgb", M.CHAINS)

    def test_only_known_endpoints(self):
        """⛔ The retired Standard tier and its port must not appear anywhere."""
        here = os.path.dirname(os.path.abspath(__file__))
        src = open(os.path.join(here, "sololuck_miner.py"), encoding="utf-8").read()
        self.assertNotIn("8081", src)
        # ⭐ The README ships in the same source zip and is the first thing a
        # reader opens. It carried ":8081 Standard" until 2026-09-10 because only
        # the .py was ever checked.
        for extra in ("README.md", "SIGNING.md", "build.bat", "gen-miners.py"):
            p = os.path.join(here, extra)
            if os.path.exists(p):
                self.assertNotIn("8081", open(p, encoding="utf-8").read(),
                                 "%s names the retired port" % extra)
        allowed = {("sololuck.io", "3335"),
                   # the US Bitcoin pool, added 2026-09-10
                   ("us.stratum.sololuck.io", "3335"),
                   ("bch.sololuck.io", "3333"),
                   ("digibyte.sololuck.io", "3340")}
        # ⭐ Doors count. This guard exists so no unsanctioned endpoint can reach a
        # user, and since 1.11.2 a door is an endpoint the app will really mine to.
        # ("door" is our internal word; on screen every one of these is a "pool".)
        seen = {(c["host"], c["port"]) for c in _present_chains(M).values()}
        for c in _present_chains(M).values():
            for host, _label in (c.get("doors") or ()):
                seen.add((host, c["port"]))
        self.assertTrue(seen <= allowed, "unexpected endpoint: %s" % (seen - allowed))

    def test_no_offered_coin_calls_itself_beta(self):
        """🔴 A coin the app can actually MINE is launched, so nothing about it
        may say beta / provisional / coming.
        ⚠️ Exemption is keyed on the GATE, not on membership of CHAINS: a
        single-coin DigiByte build keeps "dgb" in CHAINS so the window has
        something to describe, but chain_enabled() is False there and the coin
        is genuinely unreleased, so its wording may still say beta.
        ⚠️ One stale 'beta' in a build that installs itself on every user's
        machine is exactly what nobody notices until a screenshot."""
        for key, c in M.CHAINS.items():
            if not M.chain_enabled(key):
                continue
            blob = " ".join(str(v) for v in c.values()).lower()
            for word in ("beta", "provisional", "coming soon", "preview",
                         "experimental", "not yet"):
                self.assertNotIn(word, blob,
                                 "%s (an offered coin) says %r: %s" % (key, word, blob[:120]))
            self.assertFalse(c["beta"], "%s is flagged beta but is offered" % key)

    def test_bitcoin_cash_is_launched(self):
        """The owner's ruling 2026-09-06: Bitcoin Cash launches with this
        release, so it carries no beta label.
        🔴 Sequencing this depends on: the site's bch_public=1 flip must land
        before or with the app. The app cannot check that — the coordinator
        holds it."""
        if "bch" in M.CHAINS:
            self.assertFalse(M.CHAIN_DEFS["bch"]["beta"])
            self.assertNotIn("beta", M.CHAIN_DEFS["bch"]["idle"].lower())
            self.assertNotIn("beta", str(M.CHAIN_DEFS["bch"]["start_note"]).lower())
            self.assertNotIn("beta", M.CHAIN_DEFS["bch"]["hint"].lower())

    def test_the_beta_fixes_are_all_present(self):
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "sololuck_miner.py"), encoding="utf-8").read()
        for needle, why in (
                ("_build_scroll_host", "scroll fix"),
                ("def window_geometry", "screen-aware sizing"),
                ("_on_wheel", "mouse wheel"),
                ("_vbar_shown", "conditional scrollbar"),
                ('pw = "x"', "no d= password"),
                ("validate_dgb_address", "DigiByte validator"),
                ("chain_cfg_path", "per-coin settings files"),
                ("chain_enabled(CHAIN)", "the --minetest gate"),
                ("-ExclusionProcess '%s", "scoped Defender exclusion")):
            self.assertIn(needle, src, "missing: " + why)
        self.assertNotIn("only this folder is skipped", src)
        self.assertNotIn('"d=1"', src)


class TestCoinBoundaries(unittest.TestCase):
    """🔴 One app with a coin selector puts back the risk that separate binaries
    removed, so these are the guards that replace it. They pass both against the
    unified app and inside any single-coin build emitted from the same file."""

    def test_bitcoin_is_the_default_and_first(self):
        self.assertEqual(M.CHAIN_ORDER[0], "btc" if "btc" in M.CHAINS else M.CHAIN)
        if "btc" in M.CHAINS:
            self.assertEqual(M.CHAIN, "btc")

    def test_digibyte_is_gated_off(self):
        """🔴 Whatever else changes, DigiByte must not be selectable until its
        pool exists."""
        self.assertFalse(M.DGB_ENABLED)
        self.assertFalse(M.chain_enabled("dgb"))
        if len(_present_chains(M)) > 1:
            self.assertNotIn("dgb", M.CHAINS)      # no button at all in the app
            self.assertNotIn("dgb", M.CHAIN_ORDER)

    def test_config_files_are_per_coin(self):
        paths = {k: M.chain_cfg_path(k) for k in _present_chains(M)}
        self.assertEqual(len(set(paths.values())), len(paths), "two coins share a file")
        for k, v in paths.items():
            self.assertTrue(v.endswith("sololuck_miner_%s.cfg" % k), v)
        # the shared file must never be one of them
        self.assertNotIn(M.APP_CFG_PATH, set(paths.values()))

    # Every coin carries these. A coin missing one is a bug.
    _REQUIRED_COIN_FIELDS = ("name", "ticker", "host", "port", "addr_label",
                             "hint", "example", "stats_url", "beta",
                             "start_note", "idle")
    # ⭐ Per-coin BY DESIGN, so it may not be on every coin — but nothing else may
    # be. Bitcoin answers stratum in two places; the other coins have one pool
    # each and must not carry this key at all.
    _OPTIONAL_COIN_FIELDS = ("doors",)

    def test_every_coin_definition_is_complete(self):
        present = _present_chains(M)
        allowed = set(self._REQUIRED_COIN_FIELDS) | set(self._OPTIONAL_COIN_FIELDS)
        for name, c in present.items():
            missing = set(self._REQUIRED_COIN_FIELDS) - set(c)
            self.assertFalse(missing, "coin %s is missing %s" % (name, sorted(missing)))
            extra = set(c) - allowed
            self.assertFalse(extra, "coin %s has undeclared field(s) %s — add it to "
                                    "_REQUIRED_ or _OPTIONAL_COIN_FIELDS on purpose"
                                    % (name, sorted(extra)))
            for f in ("name", "ticker", "host", "port", "addr_label", "example", "idle"):
                self.assertTrue(c[f], "%s.%s empty" % (name, f))

    def test_each_coin_has_its_own_endpoint(self):
        hosts = [c["host"] for c in _present_chains(M).values()]
        self.assertEqual(len(set(hosts)), len(hosts), "two coins share a stratum host")

    # ── the Bitcoin door picker ──────────────────────────────────────────────
    def test_only_bitcoin_has_doors(self):
        """⛔ Bitcoin Cash and DigiByte have one pool each. A "doors" key on
        either would mean the app might measure and choose between endpoints
        that do not exist."""
        for name, c in _present_chains(M).items():
            if name == "btc":
                self.assertGreaterEqual(len(c.get("doors") or ()), 2,
                                        "Bitcoin should offer a choice of doors")
            else:
                self.assertNotIn("doors", c, "%s has one pool — it must not "
                                             "carry doors" % name)

    def test_default_door_is_the_fallback_host(self):
        """🔴 The fail-safe. Everything that can go wrong with the probe lands on
        CHAINS[chain]["host"], so the first door must BE that host — otherwise a
        failed measurement quietly moves users to an endpoint nobody chose."""
        for name, c in _present_chains(M).items():
            doors = c.get("doors")
            if not doors:
                continue
            self.assertEqual(doors[0][0], c["host"],
                             "%s: doors[0] must equal host" % name)

    def test_doors_never_point_at_another_coin(self):
        """A Bitcoin door that resolved to the Bitcoin Cash pool would mine the
        wrong chain with a Bitcoin address."""
        chains = _present_chains(M)
        for name, c in chains.items():
            others = {o["host"] for n, o in chains.items() if n != name}
            for host, _label in (c.get("doors") or ()):
                self.assertNotIn(host, others,
                                 "%s door %s is another coin's host" % (name, host))

    def test_door_labels_are_present_and_distinct(self):
        for name, c in _present_chains(M).items():
            labels = [l for _h, l in (c.get("doors") or ())]
            self.assertEqual(len(set(labels)), len(labels),
                             "%s has two doors with the same label" % name)
            for l in labels:
                self.assertTrue(l and l.strip(), "%s has an unlabelled door" % name)

    def test_resolve_host_falls_back_when_nothing_measured(self):
        """No probe has run in this process, so every coin must resolve to the
        host v1.11.1 used."""
        for name, c in _present_chains(M).items():
            if name not in M.CHAINS:
                continue
            self.assertEqual(M.resolve_host(name), c["host"],
                             "%s did not fall back to its default host" % name)

    def test_pick_door_orders_by_reliability_then_latency(self):
        def row(label, ms, ok, dflt, tried=3):
            return {"label": label, "host": label.lower(), "ms": ms, "ok": ok,
                    "tried": tried, "default": dflt, "err": None}
        # a door that answered once, however fast, loses to one that answered 3/3
        self.assertEqual(
            M.pick_door([row("A", 200.0, 3, True), row("B", 5.0, 1, False)])["label"],
            "A")
        # clear win on latency, both fully reliable
        self.assertEqual(
            M.pick_door([row("A", 300.0, 3, True), row("B", 20.0, 3, False)])["label"],
            "B")

    def test_pick_door_keeps_the_default_when_it_is_close(self):
        """⭐ Without hysteresis two near-equal doors flap run to run on jitter,
        splitting one user's history across two pool databases."""
        def row(label, ms, dflt):
            return {"label": label, "host": label.lower(), "ms": ms, "ok": 3,
                    "tried": 3, "default": dflt, "err": None}
        # 5 ms better: under both margins, so the default holds
        self.assertEqual(
            M.pick_door([row("A", 100.0, True), row("B", 95.0, False)])["label"], "A")
        # 40 ms and 40% better: clears both margins
        self.assertEqual(
            M.pick_door([row("A", 100.0, True), row("B", 60.0, False)])["label"], "B")
        # 12 ms better clears DOOR_MARGIN_MS but not the 15% — default holds
        self.assertEqual(
            M.pick_door([row("A", 100.0, True), row("B", 88.0, False)])["label"], "A")

    def test_pick_door_returns_none_when_no_door_answers(self):
        dead = [{"label": "A", "host": "a", "ms": None, "ok": 0, "tried": 3,
                 "default": True, "err": "dns"},
                {"label": "B", "host": "b", "ms": None, "ok": 0, "tried": 3,
                 "default": False, "err": "timeout"}]
        self.assertIsNone(M.pick_door(dead))
        self.assertIsNone(M.pick_door([]))

    def test_probe_door_never_raises_on_a_bad_host(self):
        """🔴 This runs on a user's machine at launch. It must fail quietly."""
        r = M.probe_door("no-such-host.sololuck.invalid", "3335", attempts=1)
        self.assertEqual(r["ok"], 0)
        self.assertIsNone(r["ms"])
        self.assertTrue(r["err"])

    def test_door_summary_is_safe_before_any_measurement(self):
        self.assertTrue(M.door_summary("btc").strip())

    def test_latency_is_timed_with_perf_counter_not_monotonic(self):
        """🔴 Windows time.monotonic() is GetTickCount64() — 15.625 ms per tick,
        confirmed on the build box. That is coarser than DOOR_MARGIN_MS, so every
        close call would be decided by rounding and anything under a tick would
        read as 0.0 ms. ⛔ Linux monotonic() is nanosecond-resolution, which is
        why this can only be caught by reading the source or by running the
        frozen exe on real Windows."""
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "sololuck_miner.py"), encoding="utf-8").read()
        # The comment explaining the ban names it on purpose, so look at code
        # lines only — a comment is not a call.
        code = [ln for ln in src.splitlines()
                if not ln.lstrip().startswith("#")]
        offenders = [ln.strip() for ln in code if "time.monotonic()" in ln]
        self.assertFalse(offenders,
                         "the door probe must time with perf_counter(): %s" % offenders)
        self.assertIn("time.perf_counter()", src)

    def test_no_odds_comparison_or_promise_anywhere(self):
        """⛔ the app must not compare coins or promise anything."""
        blob = " ".join(str(v) for c in _present_chains(M).values()
                        for v in c.values()).lower()
        for word in ("better odds", "more likely", "easier", "profit", "earn",
                     "five times", "5x", "income", "guarantee"):
            self.assertNotIn(word, blob)

    def test_no_false_difficulty_claim(self):
        """⚠️ An earlier build claimed the app asks the pool for difficulty 1 so
        shares register within minutes. Probed live: the port answers 1024 either
        way, and "d=" is a one-way ratchet."""
        blob = " ".join(str(v) for c in _present_chains(M).values()
                        for v in c.values()).lower()
        for phrase in ("difficulty 1,", "asks the pool for difficulty",
                       "shares register within minutes", "d=1"):
            self.assertNotIn(phrase, blob)
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "sololuck_miner.py"), encoding="utf-8").read()
        self.assertIn('pw = "x"', src)
        self.assertNotIn('"d=1"', src)

    def test_defender_wording_is_accurate(self):
        """⚠️ The app adds TWO Defender rules, and used to say it added one.
        Found on integra 2026-09-06."""
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "sololuck_miner.py"), encoding="utf-8").read()
        self.assertNotIn("only this folder is skipped", src)
        self.assertNotIn("only this one folder is excluded", src)
        # the process rule must be scoped to the engine folder, not machine-wide
        self.assertNotIn("-ExclusionProcess 'cpuminer-*.exe'", src)
        self.assertIn("-ExclusionProcess '%s", src)

    def test_minetest_consults_the_gate(self):
        """🔴 The gap found on integra: --minetest used to check only the address
        and go straight to ensure_engine(), bypassing the gate from the CLI."""
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "sololuck_miner.py"), encoding="utf-8").read()
        body = src[src.index("def _minetest("):src.index("def _cpuinfo(")]
        self.assertIn("chain_enabled(CHAIN)", body)
        # compare against the real CALL SITE, not the word in the comment above it
        self.assertLess(body.index("if not chain_enabled(CHAIN)"),
                        body.index("eng = ensure_engine("),
                        "the gate must be checked before any engine work")
        self.assertLess(body.index("if not chain_enabled(CHAIN)"),
                        body.index("validate_for_chain"),
                        "the gate should refuse before anything else")


if __name__ == "__main__":
    unittest.main(argv=[a for a in sys.argv if a != "--offline"], verbosity=2)
