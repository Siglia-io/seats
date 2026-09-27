# seats — a Siglia plugin for building, running and learning from groups of chat seats

**Version 0.1.3 (27 Sep 2026).** Its rules, its Log tooling and its lessons come from a pilot run of the method; nothing in it is tied to that run's project.

## What it is
A group of separate Claude chats ("seats"), each with one job, one knowledge base and one priority, so that no single chat can talk itself into a conclusion:
- **The Log** records every turn, routes documents and presents the seats' findings as one ledger. It never decides.
- **Authors** read the subject: a macro reading, line-by-line depth, and the logical chain.
- **Research** gathers outside, sourced facts.
- **Checkers** judge items blind to authorship and to each other: Vet (mechanical checks), Verify (independent reproduction), Refute (the strongest case against). Planted true and false items measure whether they rubber-stamp or break by reflex.
- **Skills** watches every seat for repeated errors and builds tested skills.

Decisions come only from the seats' back-and-forth.

## What is in this version
- `skills/seats-new/`: the setup interview (five questions), which writes the group's rules, briefs, folders and a one-paste launcher that opens the Log first.
- **Project-specific skills are not shipped.** They are generated for each project: seats-new sets up the group's skill store, and the Skills seat builds and tests skills there from the errors it records in that project's run. Typical ones are row guards (read only what your role allows), quote-at-page checking, reading times from the clock, a pre-FINAL gate, attack-before-filing, and required-line coverage.
- `scripts/`:
  - `capture.py`: the Log's no-model capture, run every 2 minutes. It renders every chat's turns, events, document snapshots, a raw-transcript backup and the questions file, with sealed redaction.
  - `coalesce.py`: the ledger that coalesces the seats' findings (connected or disjoint) and decides nothing.
  - `setup_check.py` and `quote_check.py`.
  - Paths come from `SEATS_ROOT` and `SEATS_CONTEXT`; the names that decide (`Route:`) from `SEATS_OWNER` and `SEATS_APPROVER`; `coalesce.py` reads its source texts from `SEATS_SOURCES`.
- `workflows/log-narrative.js`: the Log's narrative subagents, which collect and never judge.
- `templates/`: the rules (PIPELINE, LEARNING-LOOP, LESSONS, the standing orders, process decisions), role briefs (the Log's, with lessons L-001 and L-002 built in), and the launchers. `templates/rules/LESSONS.pilot-run-1.md` holds the pilot run's lessons as worked examples.
- `docs/SPEC.md`: Skills' full design. `docs/SCHEMA.md`: the group config.

## Not built yet (the rules are instructions until these exist)
- Enforcement hooks: role injection at session start, a guard before every tool call, clock-stamped times, FINAL-stamp and freeze checks.
- The MCP spine, for portability across accounts.
- A behaviour test of the whole group.

## Install
With the Claude Code CLI:
```bash
claude plugin marketplace add Siglia-io/seats
```
```bash
claude plugin install seats@siglia-seats
```
Then open a chat in your project folder and run the `seats-new` skill to answer the five setup questions.
