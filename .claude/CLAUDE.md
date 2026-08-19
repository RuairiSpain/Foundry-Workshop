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
