---
name: build_lab
description: Runs the end-to-end lab creation and verification pipeline for one or all labs. Use when the user asks to build, generate, or regenerate a lab.
---

# Process

Run these steps in order for the requested lab number. When the user says
"build all," repeat the full pipeline for every lab in
`docs/curriculum.md`, in order.

1. Invoke `curriculum_guard` to confirm the lab's allowed scope, concepts,
   and prerequisites.
2. Invoke `lab_writer` to draft `labs/lab-NN-slug/README.md`, `starter/`,
   `solution/`, `tests/`, and `requirements.txt`.
3. Invoke `curriculum_guard` again on the draft. If it flags an issue,
   send the findings to `lab_writer` and repeat step 2.
4. Invoke `lab_tester` to run the lab from a clean state.
5. If `lab_tester` fails, send the failing step to `lab_writer` and
   repeat from step 2. Retry up to 3 times before stopping and reporting
   the failure.
6. If `lab_tester` passes, invoke `editor` to polish formatting and
   style.
7. Report the finished lab's path and test result.

# Modes

- `build lab NN` — run the pipeline for one lab.
- `build all` — run the pipeline for every lab in `docs/curriculum.md`,
  without asking for confirmation between labs. Stop and report if any
  lab fails after 3 retries through step 5.

# Notes

- Each step works only inside the current lab's `labs/lab-NN-slug/`
  folder. Don't touch other labs' folders.
- Pass each agent only the current lab's entry from `docs/curriculum.md`,
  not the full roadmap, to keep context small.
