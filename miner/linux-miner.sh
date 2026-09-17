#!/usr/bin/env bash
# SoloLuck — Linux CPU solo miner (Debian/Ubuntu first; also Fedora/Arch/openSUSE).
# Finds or builds a CPU miner from source and points it at sololuck.io, mining
# Bitcoin solo to YOUR own address. No antivirus hassle on Linux — no exclusions,
# no prompts. A CPU's hashrate is tiny, so this is a low-power long shot.
#
#   curl -fLO https://sololuck.io/linux-miner.sh && less linux-miner.sh && bash linux-miner.sh
#   ./linux-miner.sh bc1qyouraddress
#
# Open-source, non-custodial, 0% fee: the entire reward on a solved block is
# paid straight to your address on-chain. We never hold it.
set -uo pipefail

POOL_HOST="stratum.sololuck.io"
POOL_PORT="3335"            # Nano tier (difficulty 1) — tuned for CPUs
ALGO="sha256d"
POOL_PASS="x"
WORKER="linux"

# ── which chain ───────────────────────────────────────────────────────────────
# Bitcoin Cash is the same proof of work on a smaller network, so the engine and
# ALGO above are unchanged -- only the door and the address form differ.
# 🔴 A legacy 1…/3… address is valid on BOTH chains, so --bch requires the bare
# CashAddr form. Accepting legacy here would let someone mine Bitcoin while
# believing they were mining Bitcoin Cash, with no error at all.
CHAIN="btc"; ADDR=""
for _a in "$@"; do
  case "$_a" in
    --bch|--bitcoincash) CHAIN="bch" ;;
    --btc|--bitcoin)     CHAIN="btc" ;;
    -*)                  ;;
    *) [ -z "$ADDR" ] && ADDR="$_a" ;;
  esac
done
if [ "$CHAIN" = "bch" ]; then
  POOL_HOST="bch.sololuck.io"; POOL_PORT="3333"; WORKER="linux-bch"
  # One Bitcoin Cash port serves every size of machine and starts each at
  # difficulty 1,024 -- hours per share for a CPU, and the pool only lowers a
  # difficulty after it has seen shares. "d=1" asks for the pool floor instead.
  POOL_PASS="d=1"
  COIN="Bitcoin Cash"; ADDR_HINT="bare CashAddr — starts q… or p…"
else
  COIN="Bitcoin";      ADDR_HINT="bc1q…"
fi
WORKDIR="$HOME/.sololuck-miner"

c_y(){ printf '\033[1;33m%s\033[0m\n' "$*"; }
c_r(){ printf '\033[1;31m%s\033[0m\n' "$*" >&2; }
c_g(){ printf '\033[1;32m%s\033[0m\n' "$*"; }

c_y "── SoloLuck · Linux CPU solo miner ─────────────────────────────"
echo "Mines $COIN (CPU) solo to YOUR address via $POOL_HOST:$POOL_PORT."
echo "Solo mining is a long shot — a CPU's hashrate is tiny, so think of it as a"
echo "cheap, low-power experiment. If your machine solves a block, the whole reward"
echo "is entirely yours — 0% fee — paid on-chain to your address. No account."
echo

[ "$(uname)" = "Linux" ] || { c_r "This installer is for Linux. Windows: https://sololuck.io/setup  ·  macOS: https://sololuck.io/mac-miner.sh"; exit 1; }
ARCH="$(uname -m)"   # x86_64 | aarch64 | armv7l …
echo "Detected: Linux on $ARCH"

# ── BTC payout address ────────────────────────────────────────────────────────
if [ -z "$ADDR" ]; then
  printf "Paste your %s payout address (%s): " "$COIN" "$ADDR_HINT"
  read -r ADDR < /dev/tty || true
fi
if [ "$CHAIN" = "bch" ]; then
  case "$ADDR" in
    q*|p*) : ;;
    bitcoincash:*) c_r "Drop the 'bitcoincash:' prefix — some miner firmware rejects the colon. Aborting."; exit 1 ;;
    bc1*) c_r "That is a Bitcoin address, not a Bitcoin Cash one. Aborting."; exit 1 ;;
    1*|3*) c_r "A legacy 1…/3… address is valid on BOTH chains, so it cannot say which you meant. Use the bare CashAddr form (q… or p…). Aborting."; exit 1 ;;
    *) c_r "That doesn't look like a Bitcoin Cash address. Aborting."; exit 1 ;;
  esac
else
  case "$ADDR" in
    bc1*|1*|3*) : ;;
    q*|p*) c_r "That looks like a Bitcoin Cash address. Re-run with --bch to mine Bitcoin Cash. Aborting."; exit 1 ;;
    *) c_r "That doesn't look like a Bitcoin address. Aborting."; exit 1 ;;
  esac
fi

# ── locate an already-installed engine ────────────────────────────────────────
find_engine(){
  local c p
  for c in cpuminer-opt cpuminer minerd cpuminer-multi; do
    command -v "$c" >/dev/null 2>&1 && { command -v "$c"; return 0; }
  done
  for p in /usr/local/bin /usr/bin "$WORKDIR/cpuminer-opt" "$WORKDIR/cpuminer-pooler"; do
    for c in cpuminer-opt cpuminer minerd; do
      [ -x "$p/$c" ] && { echo "$p/$c"; return 0; }
    done
  done
  return 1
}
ENGINE="$(find_engine || true)"

# ── build one from source if needed ───────────────────────────────────────────
if [ -z "$ENGINE" ]; then
  c_y "No CPU miner found — I'll build one from source (this can take a few minutes)."

  # sudo only if we're not already root and it exists.
  SUDO=""
  if [ "$(id -u)" -ne 0 ]; then
    if command -v sudo >/dev/null 2>&1; then SUDO="sudo"; else
      c_r "Need root (or sudo) to install build tools. Re-run as root, or install manually: https://sololuck.io/setup"; exit 1
    fi
  fi

  # Install build dependencies with whatever package manager is present.
  if command -v apt-get >/dev/null 2>&1; then
    c_y "Installing build dependencies (apt)…"
    $SUDO apt-get update -y >/dev/null 2>&1 || true
    DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y \
      build-essential automake autoconf libtool pkg-config git \
      libcurl4-openssl-dev libjansson-dev libssl-dev libgmp-dev zlib1g-dev >/dev/null 2>&1 \
      || c_r "apt install reported problems — continuing; the build may still work if the tools are present."
  elif command -v dnf >/dev/null 2>&1; then
    c_y "Installing build dependencies (dnf)…"
    $SUDO dnf install -y gcc gcc-c++ make automake autoconf libtool pkgconfig git \
      libcurl-devel jansson-devel openssl-devel gmp-devel zlib-devel >/dev/null 2>&1 || true
  elif command -v pacman >/dev/null 2>&1; then
    c_y "Installing build dependencies (pacman)…"
    $SUDO pacman -Sy --needed --noconfirm base-devel git curl jansson openssl gmp zlib >/dev/null 2>&1 || true
  elif command -v zypper >/dev/null 2>&1; then
    c_y "Installing build dependencies (zypper)…"
    $SUDO zypper --non-interactive install -t pattern devel_basis >/dev/null 2>&1 || true
    $SUDO zypper --non-interactive install git libcurl-devel libjansson-devel libopenssl-devel gmp-devel zlib-devel >/dev/null 2>&1 || true
  else
    c_r "No supported package manager found (apt/dnf/pacman/zypper)."
    c_r "Install these, then re-run: a C toolchain, autoconf, automake, libtool, pkg-config, git, and the curl/jansson/openssl/gmp/zlib dev headers."
    exit 1
  fi

  JOBS="$(nproc 2>/dev/null || echo 2)"
  mkdir -p "$WORKDIR"; cd "$WORKDIR"

  # cpuminer-opt's configure often leaves LIBCURL empty on modern toolchains, so
  # the link drops -lcurl ("undefined reference to curl_easy_perform"). Feed it
  # the curl libs/cflags explicitly (and also as make LIBS) so linking is solid.
  CURL_LIBS="$(pkg-config --libs libcurl 2>/dev/null || curl-config --libs 2>/dev/null || echo -lcurl)"
  CURL_CFLAGS="$(pkg-config --cflags libcurl 2>/dev/null || curl-config --cflags 2>/dev/null || true)"

  # Compiled ON this machine → -march=native gets the CPU's real SHA/AVX-512/AVX2
  # (or NEON on ARM) automatically, which is the fastest path. Fall back to a
  # portable -O3 build, then to pooler/cpuminer, so it works on odd toolchains.
  build_ok=""
  c_y "Fetching + building cpuminer-opt (native-optimised)…"
  rm -rf cpuminer-opt
  if git clone --depth 1 https://github.com/JayDDee/cpuminer-opt.git >/dev/null 2>&1 && cd cpuminer-opt; then
    ./autogen.sh >/dev/null 2>&1 || true
    if ./configure CFLAGS="-O3 -march=native -Wall" LIBCURL="$CURL_LIBS" LIBCURL_CFLAGS="$CURL_CFLAGS" >/dev/null 2>&1 \
       && make -j"$JOBS" LIBS="$CURL_LIBS" >/dev/null 2>&1 && [ -x ./cpuminer ]; then
      ENGINE="$WORKDIR/cpuminer-opt/cpuminer"; build_ok=1
    else
      c_r "native build failed — retrying portable (-O3)…"
      make clean >/dev/null 2>&1 || true
      if ./configure CFLAGS="-O3" LIBCURL="$CURL_LIBS" LIBCURL_CFLAGS="$CURL_CFLAGS" >/dev/null 2>&1 \
         && make -j"$JOBS" LIBS="$CURL_LIBS" >/dev/null 2>&1 && [ -x ./cpuminer ]; then
        ENGINE="$WORKDIR/cpuminer-opt/cpuminer"; build_ok=1
      fi
    fi
    cd "$WORKDIR"
  fi
  if [ -z "$build_ok" ]; then
    c_r "cpuminer-opt didn't build — falling back to pooler/cpuminer…"
    rm -rf cpuminer-pooler
    if git clone --depth 1 https://github.com/pooler/cpuminer.git cpuminer-pooler >/dev/null 2>&1 \
       && cd cpuminer-pooler && ./autogen.sh >/dev/null 2>&1 \
       && ./configure CFLAGS="-O3" LIBCURL="$CURL_LIBS" LIBCURL_CFLAGS="$CURL_CFLAGS" >/dev/null 2>&1 \
       && make -j"$JOBS" LIBS="$CURL_LIBS" >/dev/null 2>&1 && [ -x ./minerd ]; then
      ENGINE="$WORKDIR/cpuminer-pooler/minerd"
    else
      c_r "Automatic build failed on this system. Manual steps: https://sololuck.io/setup"; exit 1
    fi
  fi
fi

[ -n "$ENGINE" ] && [ -x "$ENGINE" ] || { c_r "No runnable engine. See https://sololuck.io/setup"; exit 1; }

# 75% of cores + low priority: the machine stays usable while it mines.
NCPU="$(nproc 2>/dev/null || echo 2)"
THREADS=$(( NCPU * 75 / 100 ))
[ "$THREADS" -ge 1 ] 2>/dev/null || THREADS=1

c_g "Engine ready: $ENGINE"
c_g "Mining to ${ADDR}.${WORKER} on $POOL_HOST:$POOL_PORT  (Ctrl-C to stop)"
echo "CPU load: 75% (${THREADS} of ${NCPU} threads, low priority - will not fight your real work)"
echo
exec nice -n 10 "$ENGINE" -a "$ALGO" -o "stratum+tcp://$POOL_HOST:$POOL_PORT" -u "${ADDR}.${WORKER}" -p "$POOL_PASS" -t "$THREADS"
