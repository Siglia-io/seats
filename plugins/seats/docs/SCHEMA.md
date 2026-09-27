# seats.json — the one config file of a group (schema "seats/0")

Written by `/seats:new` to `<project_root>/.seats/<group>/seats.json`. Every script, hook and template reads only this file for project facts. Nothing in the plugin names a project, a person, a model or a session id.

Until the hooks that read this file are built, the launcher passes its project facts to the scripts as environment variables: `SEATS_ROOT` (`project_root`), `SEATS_CONTEXT` (the context folder), `SEATS_OWNER` and `SEATS_APPROVER` (`owner`, `approver`), and, for `coalesce.py`, `SEATS_SOURCES` (a JSON object mapping each source's display name to its path).

```json
{
  "schema": "seats/0",
  "project_root": "/abs/path/to/project",
  "group": "g1",
  "title_prefix": "g1·",
  "tier": "light | standard | full",
  "goal": "examine | research | build",
  "owner": "<name>",            "approver": "<name>",
  "sources":  [ { "id": "S1", "path": "rel/or/abs/doc.txt", "pages": "formfeed | marker | none", "cite": "S1 p.N" } ],
  "adjacent": [ { "id": "A1", "path": "rel/or/abs/reference.md" } ],
  "sealed_dir": "~/seats-sealed/<project-slug>/<group>",
  "folders": { "chats": "<group>/chats", "log": "<group>/log", "relay": "<group>/relay", "store": "<group>/store", "state": ".seats/<group>/state" },
  "seats": [
    { "name": "Log",    "role": "log",      "prefix": null, "reads": ["**"],                       "agents": true,  "web": false, "model": "<model id>", "effort": "max" },
    { "name": "Scope",  "role": "author",   "lens": "macro",  "prefix": "SC", "reads": ["@sources", "@own"], "agents": false, "web": false, "model": "<model id>", "effort": "max" },
    { "name": "Verify", "role": "checker",  "stance": "reproduce", "prefix": null, "reads": ["@sources", "@adjacent", "@own", "@queue"], "agents": false, "web": true, "model": "<model id>", "effort": "max" },
    { "name": "Refute", "role": "checker",  "stance": "break",     "prefix": null, "reads": ["@sources", "@adjacent", "@own", "@queue"], "agents": false, "web": true, "model": "<model id>", "effort": "max" },
    { "name": "Skills", "role": "skills",   "prefix": "SK", "reads": ["**"], "agents": true, "web": true, "model": "<model id>", "effort": "ultracode" }
  ],
  "messaging": { "checkers": ["Verify", "Refute"], "authors": ["Scope"] },
  "planted": { "per_kind_per_batch": 3 },
  "cadence": { "capture_seconds": 120, "log_minutes": 10, "skills_minutes": 30 },
  "backend": "terminal | tmux | print"
}
```

## Row semantics (what a seat may read)
- `reads` is a list of globs relative to `project_root`, or aliases:
  - `@sources`: every `sources[].path`;
  - `@adjacent`: every `adjacent[].path`;
  - `@own`: `folders.chats/<seat name lowercased>/`;
  - `@queue`: the queue file the Log writes for checkers (`folders.chats/log/QUEUE-*.md`);
  - `@relay`: `folders.relay/to-<seat>/`;
  - `**`: everything, still minus the always-denied list.
- **Always denied**, for every seat unless noted:
  - `sealed_dir`, except the Log's `CANARIES.md` while building queues; Skills is allowed only after `state/verification-complete` exists;
  - every other seat's folder under `folders.chats`, except for the Log and Skills;
  - `folders.log` (every seat's turns), except the Log and Skills;
  - other groups' folders (any `<root>/.seats/<other>/` and its `folders`);
  - the Claude transcript folder for this root, except the seat's own session (from the session map);
  - the auto-memory folder;
  - any other seat's `briefs/<seat>.md` (each seat sees only its own brief).
- A checker additionally may not read `folders.chats/log/COMPILED-*`, `VERDICTS-*`, or the other checker's folder.

## Seat titles
`title = title_prefix + name` (e.g. `g1·Log`). Titles are unique across groups because the prefix is.

## State files (`folders.state`)
- `sessions.json`: `{ "<session_id>": { "seat": "Log", "title": "g1·Log", "transcript": "...", "permission_mode": "...", "started": "<clock time>", "live": true } }`, written by the session-start hook.
- `verification-complete`: an empty flag file that the Log creates; it opens `sealed_dir` to Skills.
- `capture/`: the capture loop's state.
