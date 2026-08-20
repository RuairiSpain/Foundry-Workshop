# Foundry Workshop

A hands-on curriculum teaching Microsoft Foundry through one case
study — Cascadia Outfitters, an outdoor-gear retailer building an AI
assistant ecosystem. Every lab is Python, uses the Foundry Toolkit for
VS Code where possible, and ships a tested, working solution.

See `docs/curriculum.md` for the full 33-lab roadmap, the case study
brief, and the locked provisioning model.

## Status

All 33 labs, plus the fine-tuning appendix, are written and tested —
the curriculum in `docs/curriculum.md` is complete.

## Repository layout

```
docs/curriculum.md   Roadmap: lab order, prerequisites, concepts, provisioning model
case-study/           Shared assets: product catalog, policy docs, mock orders API, test fakes
infra/                Setup scripts: the hub, the shared Cosmos DB, the shared AI Gateway
labs/lab-NN-slug/     One lab: README, starter, solution, tests, requirements
```

## Running a lab

```bash
cd labs/lab-01-toolkit-setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m pytest tests/ -v
```

Each lab's `README.md` has the full walkthrough.

## Running every lab's tests

```bash
./run_all_tests.sh
```

Runs each lab's suite one at a time with coverage enforced at 100%. See
the note in `.claude/CLAUDE.md` on why labs can't be tested in one
combined `pytest labs/` run. This assumes every lab's dependencies are
already installed in your active Python environment — see below to set
that up from a fresh machine in one step.

## Setting up one dev environment for every lab

```bash
./setup_dev_env.sh
source .venv/bin/activate
./run_all_tests.sh
```

Creates a single venv with `requirements-dev.txt` — the union of every
lab's `requirements.txt` — so `./run_all_tests.sh` runs standalone on a
fresh machine, without setting up 34 separate per-lab venvs first. This
is for verifying or demoing the whole workshop at once; an attendee
working through one lab still follows that lab's own README and
`requirements.txt`, per "Running a lab" above.

## Setting up the workshop environment

`infra/README.md` walks through standing up the hub, the shared Cosmos
DB account, and the shared AI Gateway, then provisioning one project,
Cosmos container, and gateway key per attendee.

## Building more labs

The `.claude/` directory defines a `build_lab` pipeline
(`curriculum_guard` → `lab_writer` → `lab_tester` → `editor`) for
drafting, testing, and polishing a lab end to end. See
`.claude/skills/build_lab/SKILL.md`.
