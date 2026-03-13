#!/usr/bin/env bash
set -euo pipefail

# build-backend.sh — Downloads python-build-standalone and packages the backend
# for Electron's extraResources directory.
#
# Output:
#   extraResources/python/   — standalone Python 3.11 installation
#   extraResources/backend/  — app code + .venv with production dependencies

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PYTHON_VERSION="3.11.11"
PBS_RELEASE="20250212"
OUT_DIR="$ROOT/extraResources"
PYTHON_DIR="$OUT_DIR/python"
BACKEND_DIR="$OUT_DIR/backend"

# --- Platform detection ---
detect_platform() {
  local os arch
  os="$(uname -s)"
  arch="$(uname -m)"

  case "$os" in
    Darwin) os="apple-darwin" ;;
    Linux)  os="unknown-linux-gnu" ;;
    *)      echo "Error: unsupported OS: $os" >&2; exit 1 ;;
  esac

  case "$arch" in
    arm64|aarch64) arch="aarch64" ;;
    x86_64)        arch="x86_64" ;;
    *)             echo "Error: unsupported arch: $arch" >&2; exit 1 ;;
  esac

  echo "${arch}-${os}"
}

# --- Download python-build-standalone ---
download_python() {
  local platform="$1"
  local url="https://github.com/indygreg/python-build-standalone/releases/download/${PBS_RELEASE}/cpython-${PYTHON_VERSION}+${PBS_RELEASE}-${platform}-install_only_stripped.tar.gz"
  local tarball="$OUT_DIR/python.tar.gz"

  echo "Downloading python-build-standalone..."
  echo "  URL: $url"

  mkdir -p "$OUT_DIR"
  curl -fSL --retry 3 -o "$tarball" "$url"

  echo "Extracting to $PYTHON_DIR..."
  rm -rf "$PYTHON_DIR"
  mkdir -p "$PYTHON_DIR"
  tar -xzf "$tarball" -C "$PYTHON_DIR" --strip-components=1

  # Clean up tarball
  rm -f "$tarball"

  echo "Python $(${PYTHON_DIR}/bin/python3.11 --version) installed."
}

# --- Package backend ---
package_backend() {
  echo "Packaging backend..."

  rm -rf "$BACKEND_DIR"
  mkdir -p "$BACKEND_DIR"

  # Copy app source code and pyproject.toml
  cp -r "$ROOT/backend/app" "$BACKEND_DIR/app"
  cp "$ROOT/backend/pyproject.toml" "$BACKEND_DIR/pyproject.toml"
  cp "$ROOT/backend/uv.lock" "$BACKEND_DIR/uv.lock"

  # Create venv using the standalone python and install production deps
  echo "Creating venv and installing dependencies with uv..."
  uv sync --no-dev --python "$PYTHON_DIR/bin/python3.11" --directory "$BACKEND_DIR"

  echo "Backend packaged."
}

# --- Main ---
main() {
  echo "=== build-backend.sh ==="
  echo "Root: $ROOT"

  local platform
  platform="$(detect_platform)"
  echo "Platform: $platform"

  download_python "$platform"
  package_backend

  echo ""
  echo "=== Done ==="
  echo "  Python: $PYTHON_DIR/bin/python3.11"
  echo "  Backend: $BACKEND_DIR"
  du -sh "$PYTHON_DIR" "$BACKEND_DIR"
}

main "$@"
