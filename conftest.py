"""Lets one test file check either the reference solution or an
attendee's in-progress starter, without duplicating a single test.

Every lab's tests/test_*.py imports `from solution.X import ...` — on
purpose, since that's what `run_all_tests.sh` and CI use to prove the
reference solution is correct at 100% coverage. But it means an
attendee running the exact command every README prints,
`python3 -m pytest tests/ -v`, is not actually checking their own
`starter/` edits: pytest imports `solution`, which was already
complete before they touched anything, so it reports "N passed"
regardless of what they wrote (or didn't write) in `starter/`.

Setting `LAB_TARGET=starter` redirects every `import solution...` in
that test run to the matching module in `starter/` instead, with zero
changes to any test file. Default behavior (`LAB_TARGET` unset, or any
other value) is untouched — solution/ is still what gets imported, so
existing coverage and CI runs work exactly as before.
"""

from __future__ import annotations

import importlib
import importlib.abc
import os
import sys


class _RedirectToStarterFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Redirects `solution` and `solution.*` imports to `starter`/`starter.*`."""

    def find_module(self, fullname, path=None):
        if fullname == "solution" or fullname.startswith("solution."):
            return self
        return None

    def load_module(self, fullname):
        real_name = "starter" + fullname[len("solution") :]
        module = importlib.import_module(real_name)
        sys.modules[fullname] = module
        return module


if os.environ.get("LAB_TARGET") == "starter":
    sys.meta_path.insert(0, _RedirectToStarterFinder())
