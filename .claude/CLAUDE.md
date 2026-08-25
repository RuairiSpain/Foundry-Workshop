# Lab Development Guidelines

This repository builds the Foundry Workshop: a 33-lab, modular curriculum
teaching Microsoft Foundry through the Cascadia Outfitters case study. See
`docs/curriculum.md` for the full roadmap.

## Global rules

1. Never introduce a concept, SDK call, or Foundry feature before its
   assigned lab in `docs/curriculum.md`.
2. Every code snippet must run without edits.
3. Follow Google developer documentation style for all prose. See
   `.claude/skills/google_style/SKILL.md`.
4. Keep explanations short, clear, and direct.
5. Reuse starter templates and prior labs' solution code. Don't duplicate
   boilerplate across labs.

## Repository conventions

- Each lab lives in `labs/lab-NN-slug/`.
- Every lab folder contains `README.md`, `starter/`, `solution/`, `tests/`,
  and `requirements.txt`.
- Solution code ships 100% line and branch coverage. Mock Azure and Foundry
  SDK calls so tests run offline.
- Every lab's `solution/` and `tests/` packages are both named the same
  ("solution", "tests") on purpose, so each lab stays self-contained and
  its README's `cd labs/lab-NN-slug && pytest tests/` works standalone.
  This means labs can't be tested in one combined `pytest labs/` run —
  it collides on those package names. Use `./run_all_tests.sh` to run
  every lab's suite one at a time instead.
- Every `tests/test_*.py` imports `from solution.X import ...`, never
  `starter.X` — that's what lets `run_all_tests.sh` and CI prove the
  reference solution is correct at 100% coverage regardless of anyone's
  in-progress edits. An attendee checks their own `starter/` work with
  the same test file by setting `LAB_TARGET=starter` (see the root
  `conftest.py`), which every lab's README uses in its "run the tests"
  step. Plain `pytest tests/` with no env var always exercises
  `solution/`.
- Infrastructure-heavy labs (Durable Functions checkpoints, log/trace
  triage, private networking) additionally document smoke assertions in
  their README — state checks that prove the lab worked, since coverage
  alone doesn't verify infrastructure behavior.
- Labs 23, 31, and 32 are optional and license-gated. Their README states
  the required license in a Prerequisites section and includes an
  instructor-demo fallback.
- The case study is Cascadia Outfitters. Don't rename the company, its
  personas, or its case-study assets without updating
  `docs/curriculum.md` first.

## Roadmap

`docs/curriculum.md` is the source of truth for lab order, allowed
concepts per lab, and prerequisites. Update it before adding, reordering,
or renaming a lab.

## Agents and the build pipeline

Use the `build_lab` skill to draft, test, and polish a lab end to end. It
runs `curriculum_guard`, `lab_writer`, `lab_tester`, and `editor` in
sequence. See `.claude/skills/build_lab/SKILL.md`.
