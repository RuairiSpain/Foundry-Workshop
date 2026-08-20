#!/usr/bin/env bash
# Creates one venv with every lab's dependencies installed, so
# ./run_all_tests.sh runs standalone on a fresh machine — no need to
# set up 34 separate per-lab venvs first.
#
# This is for the instructor's own dev/CI environment. It doesn't
# replace each lab's own venv instructions in its README — an attendee
# working through one lab still creates their own venv from that lab's
# requirements.txt, per "Running a lab" in the root README.
set -euo pipefail
cd "$(dirname "$0")"

VENV_DIR="${1:-.venv}"

if [[ -d "$VENV_DIR" ]]; then
  echo "Reusing existing venv at $VENV_DIR"
else
  echo "Creating venv at $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "Installing requirements-dev.txt (union of every lab's requirements.txt)..."
pip install --upgrade pip --quiet
pip install -r requirements-dev.txt

echo
echo "Done. Activate with:"
echo "  source $VENV_DIR/bin/activate"
echo "Then run every lab's tests with:"
echo "  ./run_all_tests.sh"
