#!/usr/bin/env bash
# Runs every lab's test suite, one lab at a time, and reports a summary.
#
# Labs can't be tested in one combined `pytest labs/` run: every lab's
# solution/ and tests/ packages are named the same ("solution", "tests")
# on purpose, so each lab stays self-contained and its README's `cd
# labs/lab-NN-slug && pytest tests/` works standalone. Running two labs
# in the same pytest session collides on those package names instead.
set -uo pipefail
cd "$(dirname "$0")"

FAILED=()

for lab_dir in labs/*/; do
  lab_name="$(basename "$lab_dir")"
  [[ -d "${lab_dir}tests" ]] || continue

  echo "=== ${lab_name} ==="
  if (cd "$lab_dir" && python3 -m pytest --cov=solution --cov-report=term-missing --cov-fail-under=100 tests/ -q); then
    echo "PASS: ${lab_name}"
  else
    echo "FAIL: ${lab_name}"
    FAILED+=("$lab_name")
  fi
  echo
done

if [[ ${#FAILED[@]} -eq 0 ]]; then
  echo "All labs passed with 100% coverage."
  exit 0
else
  echo "Failed: ${FAILED[*]}"
  exit 1
fi
