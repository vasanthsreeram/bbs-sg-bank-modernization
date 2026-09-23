#!/bin/sh
# Build an isolated, non-root GnuCOBOL (cobc) without touching global state.
#
# Why this exists: on this machine Homebrew lives in a read-only /opt/homebrew
# and there is no root, so `brew install gnu-cobol` fails. This script downloads
# the GnuCOBOL 3.2 release tarball and builds it with the system compiler into an
# isolated prefix (default /tmp/gcb-build/install), linking the already-installed
# gmp. Nothing outside the prefix is modified and no sudo is used.
#
# /tmp is cleared on reboot, so re-run this to rebuild the toolchain.
#
# Usage:
#   scripts/get_cobc.sh                          # -> /tmp/gcb-build/install
#   PREFIX=$HOME/.local/gnucobol scripts/get_cobc.sh
# The resulting bin/cobc is auto-discovered by scripts/harness.py, or point
# $COBC / $GNUBOL_PREFIX at it explicitly.

set -eu

VERSION="${GNUBOL_VERSION:-3.2}"
PREFIX="${PREFIX:-/tmp/gcb-build/install}"
BUILD_DIR="${BUILD_DIR:-$(dirname "$PREFIX")/src}"

if [ -x "$PREFIX/bin/cobc" ] && "$PREFIX/bin/cobc" --version >/dev/null 2>&1; then
    echo "cobc already present: $PREFIX/bin/cobc"
    "$PREFIX/bin/cobc" --version | head -1
    exit 0
fi

for tool in curl tar make; do
    command -v "$tool" >/dev/null 2>&1 || { echo "error: missing required tool: $tool" >&2; exit 1; }
done
command -v cc >/dev/null 2>&1 || command -v clang >/dev/null 2>&1 || {
    echo "error: no C compiler (cc/clang) found" >&2; exit 1;
}

# Locate a gmp to link against (Homebrew's copy is readable even when read-only).
GMP_CFLAGS=""
GMP_LIBS=""
for prefix in /opt/homebrew/opt/gmp /usr/local/opt/gmp "$HOME/.local"; do
    if [ -f "$prefix/include/gmp.h" ] || [ -f "$prefix/include/gmp/gmp.h" ]; then
        GMP_CFLAGS="-I$prefix/include"
        GMP_LIBS="-L$prefix/lib -lgmp"
        break
    fi
done
export GMP_CFLAGS GMP_LIBS
[ -n "$GMP_LIBS" ] || { echo "error: gmp not found; install libgmp first" >&2; exit 1; }

mkdir -p "$BUILD_DIR" "$PREFIX"
cd "$BUILD_DIR"

TARBALL="gnucobol-$VERSION.tar.xz"
if [ ! -f "$TARBALL" ]; then
    echo "downloading $TARBALL ..."
    curl -fsSL -o "$TARBALL" "https://ftp.gnu.org/gnu/gnucobol/$TARBALL"
fi

SRC="gnucobol-$VERSION"
[ -d "$SRC" ] || tar xf "$TARBALL"

JOBS="$( (sysctl -n hw.ncpu 2>/dev/null || getconf _NPROCESSORS_ONLN 2>/dev/null) || echo 4)"

echo "configuring (prefix=$PREFIX) ..."
( cd "$SRC" && ./configure \
    --prefix="$PREFIX" \
    --disable-nls \
    --with-json=no \
    --without-db \
    GMP_CFLAGS="$GMP_CFLAGS" GMP_LIBS="$GMP_LIBS" >configure.log 2>&1 ) \
    || { echo "configure failed; see $BUILD_DIR/$SRC/configure.log" >&2; exit 1; }

echo "building with -j$JOBS ..."
( cd "$SRC" && make -j"$JOBS" >make.log 2>&1 ) \
    || { echo "make failed; see $BUILD_DIR/$SRC/make.log" >&2; exit 1; }

echo "installing ..."
( cd "$SRC" && make install >install.log 2>&1 ) \
    || { echo "make install failed; see $BUILD_DIR/$SRC/install.log" >&2; exit 1; }

echo "installed: $PREFIX/bin/cobc"
"$PREFIX/bin/cobc" --version | head -1
