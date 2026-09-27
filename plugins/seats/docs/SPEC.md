STATUS: SPEC v0, with the owner's answers O1–O4 in section 8, at 2026-09-27 05:10. The build was stopped at close-out before any component was written. What exists is only the skeleton: the marketplace and plugin manifests (publisher Siglia), SCHEMA.md and a fixture config. No zip was made, because no working version exists yet.

# Seats: a plugin that builds and enforces multi-chat systems like this one

**Status:** spec v0, 27 Sep 2026, written by Skills during a pilot run of the method. **Asked by the owner** (relayed by the Log), in short: can a plugin, or a marketplace of skills, make it easy to create and maintain a chat system like this one? It would ask the user a few questions, then design, orchestrate and enforce the system as in the pilot, opening on the Log chat. It should port across organisations, accounts and users, and let one user create several chat groups in the same project, each built for its own scope, intensity or complexity. Skills may use or create any durable, transferable store of skill, automation or knowledge: MCP servers, agents or others.

**Evidence base:** five maps written during the pilot run (not shipped): the plugin system's facts, plugins installed on disk, the Log's tooling, the method, and this run's failures turned into requirements. Where a map's claim was load-bearing, I checked it against the disk. One claim from the documentation map was wrong ("SessionStart cannot inject context"): the superpowers plugin on disk does inject context at session start, through `additionalContext`.

---

## The answer

- **Yes.** A Claude Code plugin, published through a marketplace, can carry every part this run needed: skills (interview and procedures), hooks (enforcement and opening each chat in its role), agents, bundled scripts (capture, guards, clock, page check), and optionally an MCP server. It ports to any org, account or user with one `marketplace add` and one `install`.
- **What makes it more than templates is hooks.** A hook at session start opens each chat in its seat. A hook before every tool call blocks what the seat may not do. A per-seat settings file, passed by the launcher, adds operating-system limits on reads. This run's biggest lesson was that my skills could catch errors but could not reach the chats; hooks and settings do reach them.
- **The tradeoff:** the enforcing version (approach B below) needs a one-time person step, the command line's bypass acceptance and pasting one launcher, and a little more to maintain than a skills-only kit. I think it is worth it, because every error type this run recorded twice was one that a hook or a settings file could have stopped.
- **What I recommend:** build approach B now, as v0. Add the MCP spine (approach C) only once B has run a real group.
- **Open for the owner:** four questions, in section 7. v0 is built on the defaults stated there and is reversible.

## In short

A user types `/seats:new`. It asks five questions: where, what is being examined, the goal and intensity, who decides, and how to open terminals. It then writes a group:
- a config file;
- one brief per seat, holding only that seat's rules;
- one settings file per seat, with its reads denied at the operating-system level;
- a launcher.

The user pastes one command. The Log opens first, with its brief injected at session start; then the other seats open in their own terminals, each in its role. From then on the plugin's hooks enforce the rows, the clock, the frozen framework and the FINAL stamp, and keep a session map. The Log's capture runs as a no-model background loop, and the learning loop's files are created from templates. Several groups can live in one project, each in its own folder, with its own prefix and its own limits, and none able to read another's.

---

## 1. Requirements (each traced to this run)

| # | requirement | the recorded failure it answers (maps/failure-requirements.md) |
|---|---|---|
| R1 | Each seat reads only its row, enforced by the system, not by the chat's memory: a settings deny on built-in reads, a sandbox read-deny for Bash, and a fail-closed guard hook as a second layer. | reads outside a row (A1, A2), skipped guard checks (A5), guard holes (A6) |
| R2 | Each seat gets its own brief file. No shared file holds other seats' prompts or the planted-item rate. | A2 |
| R3 | Sealed material (planted items, answer key) is authored outside the project root, denied to every seat, and opened only by a state flag the Log sets. | A3, B12 |
| R4 | Every seat starts in the terminal from the beginning, with a unique name, model, effort, permission mode and settings file; nothing is moved mid-run. | B1, B3, B8, B11 |
| R5 | A session map (title → session id → transcript → permission mode) is written by a hook at start, and the guard blocks tool calls from sessions that are not the seat's live one. | B1, B2, B3, pointer drift (my E-030) |
| R6 | Times come from the clock: a clock tool, and a write-time lint that blocks approximate or future times. | A13, B7, B14 |
| R7 | Quotes are checked at their cited place, and pointers against their targets, as gates before FINAL. | A7, A8, A15 |
| R8 | The item template carries Status, and a Strongest counter naming what was tried. A counter test runs before filing at 70% confidence or more. | A9, A10, A21 |
| R9 | A FINAL file cannot change without a new stamp and a revision note; a frozen framework is checked by hash. | A16 |
| R10 | Self-checks are mechanical, at turn end (a Stop hook), not only on crons that die with the session or fire only when idle. | B4, B5, B6 |
| R11 | Auto-memory is off for every seat, and the root sits outside folders holding unrelated instruction files. | A1, B10 |
| R12 | Messaging bounds are enforced: the checkers cannot message each other before both report, and no message names authorship or planted items to a checker. | the Log's messaging order; A23 |
| R13 | Portable: no hard-coded paths, names, models or session ids. Everything project-specific lives in one config file. | the Log's tooling notes 1–18; method portability blockers |
| R14 | Several groups per project, each with its own folder, prefix, state and limits. | method: multiple groups; Log note 13 |
| R15 | The learning loop is built in: retro, lessons, runs, the integrity register, and the skill store with requests and reviews. | LEARNING-LOOP.md; the owner's skill-store order |

## 2. Approaches considered

| | A · skills only | **B · skills + hooks + per-seat settings + launcher (recommended)** | C · B plus an MCP "spine" server |
|---|---|---|---|
| What it is | Prompts, role cards and scripts, invoked by the model | A adds a SessionStart role injection, a PreToolUse guard, a Stop checkpoint, generated settings files and a launcher | a local server holding state, routing, relays, the clock and the session map as tools |
| Enforcement | none: the chat must choose to run a check. This is the "reach" failure this run exposed | structural: the operating system and hooks block. The model cannot skip it | structural, and routing is by tool rather than by files |
| Portability | highest | high: plain files, Python 3 stdlib, and `${CLAUDE_PLUGIN_ROOT}` paths | medium: a server to run and keep alive |
| Risk | chats ignore it | hook bugs can block good work, so hooks must fail closed on reads but be tested hard (Refute-style probes) | more to break; long-lived process management |
| When | never alone | **v0, now** | v1, once a real group has run on B |

## 3. The design (v0 = approach B)

### 3.1 Layout
```
<PROJECT_ROOT>/seats/skills/marketplace/          the marketplace root (portable folder or git repo)
  .claude-plugin/marketplace.json                   {"name":"seats-marketplace", "plugins":[{"name":"seats","source":"./plugins/seats"}]}
  plugins/seats/
    .claude-plugin/plugin.json                      name "seats", version, description, userConfig (defaults)
    skills/new/SKILL.md                             /seats:new: interview → config → generate a group
    skills/group/SKILL.md                           /seats:group: status, add a seat, retire a seat, launch
    skills/log/SKILL.md                             the Log's procedures (injected for the Log seat)
    skills/skills/SKILL.md                          the Skills seat's procedures (sweep, store, requests)
    skills/rules/SKILL.md                           the shared rules, R1–R7 plus the standing orders, in one place
    templates/roles/{log,author,research,vet,checker,skills,central}.md   role cards with {placeholders}
    templates/{brief,item-block,run-brief,retro,foundation}.md
    templates/tiers/{light,standard,full}.json      seat sets and dials
    hooks/hooks.json                                SessionStart, PreToolUse, Stop
    scripts/seats.py                                CLI: generate · launch · map · status · retire · check
    scripts/hook_session_start.py                   inject the brief; register the session; warn on memory or mode
    scripts/hook_pre_tool.py                        the guard: reads, writes, messages, live session, FINAL, clock
    scripts/hook_stop.py                            the checkpoint: self-audit lite; one line to the seat's log
    scripts/capture.py                              the Log's no-model capture, from config (generalized)
    scripts/{quote_at,clock,freeze,xref,selfaudit}.py   tools from this run, generalized
    tests/                                          generation, guard probes, hook I/O, one live smoke test
```

### 3.2 The interview (`/seats:new`): five questions, the rest defaulted
1. **Where and what.** The project root, a group name, and the paths of what is being examined, with its citation form (pages, sections, URLs).
2. **Goal and intensity.** The goal: examine documents, research, or build. The tier: light, standard or full (section 3.5).
3. **Who decides.** The owner and the approver, which become the values of `Route:`.
4. **How terminals open.** macOS Terminal, tmux, or "print the commands for me".
5. **Model and effort defaults,** proposed from the tier.

It writes `<root>/.seats/<group>/seats.json` and generates the group (section 3.3). Everything else takes a stated default, and every default is written into the config for the user to change.

### 3.3 What a group is, on disk
```
<root>/.seats/<group>/seats.json      the config: seats, rows, sources, owner/approver, tier, cadence, backend, model/effort
<root>/.seats/<group>/briefs/<seat>.md   one per seat, its own rules and prompt only (R2)
<root>/.seats/<group>/settings/<seat>.json   permissions.deny Read(...) + sandbox denyRead + autoMemory off (R1, R11)
<root>/.seats/<group>/launch.sh       opens the Log first, then the others; checks bypass acceptance first (R4)
<root>/.seats/<group>/state/          session map, flags (verification complete), capture state (R5)
<root>/<group>/chats/<seat>/          each seat's writing folder
<root>/<group>/log/                   the Log's captures and daily log
<root>/<group>/relay/to-<seat>/       transfers from the Log
<root>/<group>/store/                 the skill store: INDEX, REQUESTS, REVIEWS
~/seats-sealed/<project>/<group>/     planted items and answer key, outside the root (R3)
```
Seat titles carry the group prefix (`<group>·Log`), so two groups never share a name (R14). Each seat's settings deny the other groups' folders.

### 3.4 Enforcement, layer by layer
1. **The operating system.** The launcher starts each seat with `--settings briefs/../settings/<seat>.json`. That file denies built-in reads of every path outside the row, denies sandbox reads for Bash, and turns auto-memory off. The failure map cites the documentation for this; **I have not yet verified it on disk, and v0's live smoke test checks it before anything relies on it.**
2. **The guard hook (PreToolUse).** It runs this run's fail-closed guard, generalized to read rows from `seats.json`, on Read, Grep, Glob, Bash, WebFetch and WebSearch. It blocks with exit code 2 and a reason. It also blocks:
   - tool calls whose `session_id` is not the seat's live id;
   - writes that change a FINAL file without a new stamp;
   - writes containing typed times;
   - SendMessage calls that break the messaging bounds.
3. **The role hook (SessionStart, matcher `startup|clear|compact`).** It injects the seat's brief, as the superpowers plugin does, and records the session in the map. A `SUBAGENT-STOP` block keeps subagents out of the role.
4. **The checkpoint hook (Stop).** At the end of every turn it runs the self-audit lite (clock lint, FINAL stamps, register ids) and appends one line to the seat's log.

### 3.5 The tiers (my proposal; nothing calibrates the counts yet)
| | light | standard | full |
|---|---|---|---|
| seats | Log, 1 author, 1 checker (reproduces *and* breaks; verdicts labelled "checked once") | Log, up to 3 authors, Research (one pass), Vet, Verify, Refute, Skills | standard + a second Research pass, batch 2, and an optional Enforcement seat |
| planted items per kind per batch | 2 | 3 | 5, rotated |
| enforcement | all of section 3.4 | all | all |
| learning loop | retro and lessons | plus the skill store and the 30-minute watch | plus the integrity register and red-teamed lessons |

Anti-pandering rules bind every tier, because the owner defined ruthless as impartial.

### 3.6 Portability
Every path is derived from `seats.json` or `${CLAUDE_PLUGIN_ROOT}`. The scripts are Python 3 with the standard library only. The transcript folder is computed from the root. Models and efforts are config values. The launcher has three backends (Terminal, tmux, print). Nothing names the owner, the approver or the project: owner and approver are config.

### 3.7 Testing
- **Generation:** a fixture answers file → a group in a temp folder → every expected file present, with no text from the pilot project.
- **Guard:** this run's 21 probes and the must-still-block cases, adapted per seat, all passing before any release.
- **Hooks:** JSON fed on stdin to each hook script → the expected exit code and output.
- **One live smoke test:** `claude -p --plugin-dir <plugin>` in a temp project. It checks that the brief is injected and a forbidden read is blocked. It is the only test that proves the settings layer works.

## 4. What v0 does not do
- **No MCP server.** Files and SendMessage carry the routing (approach C comes later).
- **It does not write the planted items.** The interview tells the user how and where to author them, outside the root.
- **It does not publish itself.** Pushing the marketplace to a repository is the owner's decision.

## 5. Risks (my judgment)
- **A hook bug can block good work.** Mitigation: the probe suites, fail-closed on reads only, and a clear reason on every block.
- **Settings-file semantics may differ from the documentation.** Mitigation: the live smoke test before release.
- **Terminal automation differs by platform.** Mitigation: a print backend is always available.

## 6. Build order (v0)
1. Plugin skeleton, manifest, marketplace.
2. `seats.py generate` from templates, with its tests.
3. The generalized guard plus the pre-tool hook, with the probes.
4. The session-start and stop hooks, with I/O tests.
5. Launcher backends.
6. The capture generalization.
7. The live smoke test.
8. Review, then land in the store; the Log reviews.

## 7. Questions for the owner, and the defaults v0 uses
| # | question (Route: owner) | v0 default | what changes if it stays open |
|---|---|---|---|
| O1 | The plugin's name | `seats` | only the name |
| O2 | Where it is published (an organisation's repository, or kept local) | kept local in `seats/skills/marketplace/`, loaded with `--plugin-dir` | other orgs can't add it until it is pushed |
| O3 | Default tier for a first run | standard | the first group's size |
| O4 | Should the Log open the other seats itself (needs terminal control, one allow), or should the user paste one launcher? | one paste of `launch.sh`, which opens the Log first, then the rest | one extra paste per group |

## 8. The owner's answers (relayed by the Log), and what they change
In short: 1. the name is seats. 2. deliver it as a file the owner can open in their own account; it is a Siglia creation; also load it in the pilot project. 3. yes. 4. one launcher, which opens the Log, starts as much deterministic setup as possible, and leaves the rest to the Log, which has the intelligence and the context.
- **O1:** the name is `seats`.
- **O2:** it is a Siglia creation. The marketplace is `siglia-seats` and the publisher is Siglia, Inc. It ships as a single zip plugin package the owner can open in their own account, and it is also loaded in the pilot project with `--plugin-dir`.
- **O3:** the default tier is standard.
- **O4:** one launcher. It opens the Log first and does every step that needs no judgment: folders, config, briefs, settings, hooks, the capture loop, snapshots, and the other seats' terminals. Anything that needs intelligence or context is left to the Log. The Log's brief says so explicitly.
