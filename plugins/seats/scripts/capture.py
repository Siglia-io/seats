#!/usr/bin/env python3
"""The Log's capture script (seats plugin; PIPELINE.md §4 Log steps 1-3).

Run every cycle:  SEATS_ROOT=<PROJECT_ROOT> SEATS_CONTEXT=<context> python3 capture.py
Paths below are relative to $SEATS_ROOT/$SEATS_CONTEXT (the context folder, default "context").

What it does, mechanically (it judges nothing):
  1. Renders every run chat's transcript (user + assistant turns: text, tool calls,
     short tool results, timestamps; subagent turns too) into log/turns/<title>.md.
     Full regeneration from the raw .jsonl each run, so it is idempotent. A render whose raw
     transcript has disappeared is kept, never deleted, and marked.
  2. Redacts sealed material from the renders: any tool call whose input touches
     _sealed/ (and its result), and any line sharing an 8-word run with a
     file in _sealed/ that does not also occur in the public corpus. Nothing sealed is printed.
  3. Appends new events (opens, titles, the owner's typed words verbatim, messages in and out,
     doc writes, errors, quote checks not found, replies, questions, items, FINAL lines)
     to log/<local date>.md below the Log marker. Append-only; each event once.
  4. Copies every item with "Route: <owner>" or "Route: <approver>" from chats/*/ docs into
     QUESTIONS.md (append-only, each item once, changes appended as updates).
  5. Writes chats/log/STATUS.md (every chat doc: FINAL or not, sha256) and
     snapshots any doc whose line 1 reads STATUS: FINAL into chats/log/snapshots/.
  6. Prints what routing is due (the Log sends messages itself; this script sends nothing).

Subcommands:
  capture.py                  run a cycle
  capture.py compile 1|2      write chats/log/COMPILED-<n>.md verbatim from the FINAL docs
  capture.py sent <key> <to>  record in the routing ledger that <key> was sent to <to>
  capture.py note "<text>"    append the Log's own note to today's log
  capture.py delta            write per-chat slices of turns not yet narrated (chats/log/deltas/), print JSON
  capture.py narrated <chat> <epoch>   record that the narrative for <chat> covers turns up to <epoch>
"""
import datetime as dt
import glob
import hashlib
import json
import os
import re
import shutil
import sys

HOME = os.path.expanduser("~")
# seats plugin: every path comes from the environment (set by the launcher) or the working directory
ROOT = os.path.abspath(os.environ.get("SEATS_ROOT") or os.getcwd())
NORM = os.path.join(ROOT, os.environ.get("SEATS_CONTEXT", "context"))
PROJ = os.path.join(HOME, ".claude/projects", re.sub(r"[^A-Za-z0-9]", "-", ROOT))
TURNS = os.path.join(NORM, "log", "turns")
LOGDIR = os.path.join(NORM, "log")
MINE = os.path.join(NORM, "chats", "log")
STATE = os.path.join(MINE, "state")
SEALED = os.path.join(NORM, "_sealed")
QUESTIONS = os.path.join(NORM, "QUESTIONS.md")
if os.environ.get("LOG_OUT"):  # dry run: read the real inputs, write every output under LOG_OUT
    _o = os.environ["LOG_OUT"]
    TURNS, LOGDIR, MINE = os.path.join(_o, "log", "turns"), os.path.join(_o, "log"), os.path.join(_o, "chats", "log")
    STATE, QUESTIONS = os.path.join(MINE, "state"), os.path.join(_o, "QUESTIONS.md")

# Sessions that are not chats of this run. PIPELINE.md §3 R3 forbids the run's chats to read them,
# so the Log does not copy them into log/turns/ (their raw transcripts stay where they are).
EXCLUDE = {}  # session ids not to capture (e.g. sessions from before the run)
EXCLUDE_TITLES = set(t for t in os.environ.get("SEATS_EXCLUDE_TITLES", "").split("|") if t)
CENTRAL = os.environ.get("SEATS_CENTRAL_TITLE", "Central")
# who decides: the names that appear after "Route:" (set by the launcher from the group's config)
OWNER = os.environ.get("SEATS_OWNER", "Owner")
APPROVER = os.environ.get("SEATS_APPROVER", "Approver")
ROUTE_NAMES = "|".join(re.escape(n) for n in (OWNER, APPROVER) if n)
CTX_DIR = re.escape(os.path.basename(NORM))  # the context folder's name, for spotting shell writes into it
PIPELINE_TITLES = ["Log", "Scope", "Specifics", "Chain", "Research", "Vet", "Verify", "Refute", "Skills", CENTRAL]

# Documents the routing depends on (PIPELINE.md §4).
DOCS = {
    "scope": "chats/scope/SCOPE.md",
    "specifics": "chats/specifics/SPECIFICS.md",
    "chain": "chats/chain/CHAIN.md",
    "research1": "chats/research/RESEARCH-1.md",
    "research2": "chats/research/RESEARCH-2.md",
    "vet1": "chats/vet/QUEUE-1.md",
    "vet2": "chats/vet/QUEUE-2.md",
    "verify1": "chats/verify/VERDICTS-1.md",
    "verify2": "chats/verify/VERDICTS-2.md",
    "refute1": "chats/refute/VERDICTS-1.md",
    "refute2": "chats/refute/VERDICTS-2.md",
    "skills": "chats/skills/SKILLS.md",
}

TRUNC = 1500
LOG_MARKER = "<!-- LOG-CHAT-RECORD: everything below this line is appended by the Log chat's capture script; the entries above it are the Central chat's and are never edited -->"
Q_MARKER = f"### Copied by the Log (items with Route: {OWNER} or Route: {APPROVER} in chats/*/ docs)"


# ---------------------------------------------------------------- helpers
def now_local():
    return dt.datetime.now().astimezone()


def parse_ts(s):
    if not s:
        return None
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone()
    except ValueError:
        return None


def fmt_ts(t):
    return t.strftime("%Y-%m-%d %H:%M:%S %Z") if t else "?"


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha8(s):
    return hashlib.sha256(s.encode("utf-8", "replace")).hexdigest()[:8]


def write_if_changed(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        with open(path, encoding="utf-8", errors="replace") as f:
            if f.read() == text:
                return False
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)
    return True


def load_json(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=True)
    os.replace(tmp, path)


def trunc(s, n=TRUNC):
    s = s if isinstance(s, str) else json.dumps(s, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + f"\n… [+{len(s) - n} chars not rendered; full text in the raw transcript]"


def one_line(s, n=300):
    s = re.sub(r"\s+", " ", s or "").strip()
    s = s.replace("|", "¦")
    return s if len(s) <= n else s[:n] + " …"


def safe_name(title):
    return re.sub(r'[/\\:*?"<>|]', "-", title).strip() or "untitled"


# ---------------------------------------------------------------- sealed redaction
WORD = re.compile(r"[a-z0-9]+")


def shingles(text, k=8):
    w = WORD.findall(text.lower())
    return {" ".join(w[i:i + k]) for i in range(len(w) - k + 1)}


def build_sealed_filter():
    sealed = set()
    for p in glob.glob(os.path.join(SEALED, "**", "*"), recursive=True):
        if os.path.isfile(p) and not os.path.relpath(p, SEALED).startswith("raw-transcripts"):  # the backup is not sealed text
            with open(p, encoding="utf-8", errors="replace") as f:
                sealed |= shingles(f.read())
    public = set()
    corpus = glob.glob(os.path.join(NORM, "sources", "*.txt")) + glob.glob(os.path.join(NORM, "*.md")) \
        + glob.glob(os.path.join(ROOT, "seats", "*.md"))
    for p in corpus:
        with open(p, encoding="utf-8", errors="replace") as f:
            public |= shingles(f.read())
    return sealed - public


def redact_lines(text, sealed_only):
    if not sealed_only:
        return text, 0
    out, n = [], 0
    for line in text.split("\n"):
        if len(line) > 30 and shingles(line) & sealed_only:
            out.append("[line redacted by the Log: it matches text in _sealed/]")
            n += 1
        else:
            out.append(line)
    return "\n".join(out), n


PRIVATE = load_json(os.path.join(SEALED, "log-private.json"), {}) if "load_json" in globals() else {}
PRIVATE_MARK = "\u27e6private\u27e7"
PRIVATE_PATHS = ("/memory/", "log-private")
WITHHELD = "*(owner note to the Log: withheld from the chats at the owner's instruction; kept sealed)*"


def is_private_record(d):
    return (d.get("uuid") or "") in set(PRIVATE.get("uuids", []))


SEALED_PATH = re.compile(r"_sealed(?:/[\w.\-]+)*")
WRITE_TOOLS = ("Write", "Edit", "NotebookEdit", "MultiEdit")


def sealed_rule(name, inp, raw):
    """(hide_input, hide_result) for a tool call, by whether it touches _sealed/."""
    if any(pp in raw for pp in PRIVATE_PATHS) or PRIVATE_MARK in raw:
        return True, True
    if "_sealed" not in raw:
        return False, False
    if name in WRITE_TOOLS:
        hit = "_sealed" in str(inp.get("file_path", "")) if isinstance(inp, dict) else True
        return hit, hit
    if name == "Read":
        hit = "_sealed" in str(inp.get("file_path", "")) if isinstance(inp, dict) else True
        return False, hit
    if name == "Bash":
        cmd = inp.get("command", "") if isinstance(inp, dict) else raw
        c2 = re.sub(r"\d?>\s*/dev/null|2>&1", "", cmd)
        writes = bool(re.search(r"<<|>\s*\S|\.write\(|open\(|\bcp\b|\bmv\b|\btee\b", c2))
        return writes, True
    if name == "SendMessage":
        return False, False
    return False, True


# ---------------------------------------------------------------- transcript parsing
PASTE = re.compile(r"<pasted_content[^>]*>(.*?)</pasted_content[^>]*>", re.S)
XSESS = re.compile(r'<cross-session-message[^>]*from="([^"]*)"[^>]*>(.*?)</cross-session-message>', re.S)


def load_prompts():
    """PIPELINE.md §4 startup prompts, to note whether a pasted block is one of them verbatim."""
    p = os.environ.get("SEATS_RULES") or os.path.join(ROOT, "seats", "PIPELINE.md")
    try:
        text = open(p, encoding="utf-8").read()
    except OSError:
        return {}
    prompts = {}
    for m in re.finditer(r"^### (\w+)\n```\n(.*?)\n```", text, re.S | re.M):
        prompts[m.group(1)] = m.group(2).strip()
    return prompts


PROMPTS = load_prompts()


def classify_user_text(s):
    """Return (who, typed_text, pasted_blocks, xsess_list)."""
    if "<task-notification>" in s:
        return "system (task notification)", s, [], []
    if s.startswith("[Request interrupted by user"):
        return "interrupt", s, [], []
    m = re.search(r"<command-name>(.*?)</command-name>", s, re.S)
    if m:
        args = re.search(r"<command-args>(.*?)</command-args>", s, re.S)
        return "command", f"{m.group(1).strip()} {args.group(1).strip() if args else ''}".strip(), [], []
    if s.startswith("<local-command-") or s.startswith("Caveat: The messages below"):
        return "system (local command output)", s, [], []
    xs = XSESS.findall(s)
    if xs:
        return "cross-session", "", [], xs
    pasted = PASTE.findall(s)
    typed = PASTE.sub("", s).strip()
    if typed.startswith("<!-- reply -->"):
        # a reply: the leading "> " lines quote someone else's text; only what follows is the owner's
        lines = typed[len("<!-- reply -->"):].strip("\n").split("\n")
        i = 0
        while i < len(lines) and (lines[i].startswith(">") or not lines[i].strip()):
            i += 1
        quoted = "\n".join(ln[1:].lstrip() for ln in lines[:i] if ln.startswith(">"))
        typed = "\n".join(lines[i:]).strip()
        return "owner", typed, [p.strip() for p in pasted], [("__reply_to__", quoted)]
    return "owner", typed, [p.strip() for p in pasted], []


def prompt_match(block):
    for name, p in PROMPTS.items():
        if block.strip() == p:
            return f"identical to PIPELINE.md §4 {name} prompt"
    for name, p in PROMPTS.items():
        if block.strip()[:120] == p[:120]:
            return f"starts like PIPELINE.md §4 {name} prompt but is NOT identical ({len(block)} vs {len(p)} chars)"
    return "not a PIPELINE.md §4 prompt"


def read_jsonl(path):
    recs = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except ValueError:
                continue
            d["_line"] = i
            recs.append(d)
    return recs


TITLE_OVERRIDE = {}  # session id -> title, for closed sessions whose title would collide


def session_title(recs, sid):
    if sid in TITLE_OVERRIDE:
        return TITLE_OVERRIDE[sid]
    title = None
    for d in recs:
        if d.get("type") == "custom-title" and d.get("customTitle"):
            title = d["customTitle"]
    if not title:
        t = load_json(os.path.join(PROJ, sid, "custom-title.json"), {}).get("customTitle")
        title = t or f"untitled-{sid[:8]}"
    return title


class Session:
    def __init__(self, sid, path):
        self.sid, self.path = sid, path
        self.recs = read_jsonl(path)
        self.title = session_title(self.recs, sid)
        ts = [parse_ts(d.get("timestamp")) for d in self.recs if d.get("timestamp")]
        ts = [t for t in ts if t]
        self.first = min(ts) if ts else None
        self.last = max(ts) if ts else None
        self.subagents = []
        base = os.path.join(PROJ, sid, "subagents")
        for sp in sorted(glob.glob(os.path.join(base, "**", "*.jsonl"), recursive=True)):
            if os.path.basename(sp) == "journal.jsonl":
                continue  # a workflow's result journal, not turns
            meta = load_json(sp[:-6] + ".meta.json", {})
            rel = os.path.relpath(sp, base)[:-6]
            if not meta.get("description") and os.sep in rel:
                meta = dict(meta, description=f"workflow {rel.split(os.sep)[1] if rel.startswith('workflows') else rel}")
            self.subagents.append((rel, meta, read_jsonl(sp)))


class _Chunker:
    """Collects one record's rendered text as its own chunk (raw line, time, text)."""
    def __init__(self, chunks, line, t):
        self.chunks, self.line, self.t = chunks, line, t

    def append(self, text):
        self.chunks.append((self.line, self.t, text))


SEALED_RISK = tuple(t for t in os.environ.get("SEATS_SEALED_RISK", "").split("|") if t)  # Skills E-039: a build subagent grepped through _sealed/; hide every tool result


def render_records(recs, src_label, sealed_only, events, sess_title, is_sub=False, want_chunks=False, hide_results=False):
    """Render records to markdown lines; append events (dicts) to `events`."""
    chunks = []
    sealed_tool_ids = set()
    tool_names = {}
    last_title = None
    last_t, last_ptr = None, f"turns/{safe_name(sess_title)}.md"
    for d in recs:
        typ = d.get("type")
        t = parse_ts(d.get("timestamp")) or last_t
        last_t = t
        uid = (d.get("uuid") or f"L{d['_line']}")[:8]
        anchor = f't-{uid}'
        ptr = f"turns/{safe_name(sess_title)}.md#{anchor}"
        head = f'<a id="{anchor}"></a>\n#### {fmt_ts(t)} · '
        foot = f"*({src_label} line {d['_line']})*"
        out = _Chunker(chunks, d['_line'], t)
        if typ == "custom-title":
            if d.get("customTitle") != last_title and not is_sub:
                if last_title is not None:
                    events.append(dict(key=f"title|{d['_line']}|{src_label}", t=t, who=sess_title, kind="title",
                                       what=f"title changed from \"{last_title}\" to \"{d.get('customTitle')}\"", ptr=last_ptr))
                last_title = d.get("customTitle")
            continue
        if typ == "system" and d.get("subtype") == "compact_boundary":
            out.append(f"{head}system\n\n*(context compacted here)* {foot}\n")
            events.append(dict(key=f"compact|{d.get('uuid')}", t=t, who=sess_title, kind="compaction",
                               what="context compacted", ptr=ptr))
            continue
        if typ == "attachment":
            a = d.get("attachment") or {}
            if a.get("type") == "queued_command" and isinstance(a.get("prompt"), str):
                typ, content = "user", a["prompt"]
            else:
                continue
        elif typ in ("user", "assistant"):
            content = (d.get("message") or {}).get("content")
        else:
            continue

        last_ptr = ptr
        if is_private_record(d):
            out.append(f"{head}owner\n\n{WITHHELD} {foot}\n")
            continue
        if typ == "user":
            blocks = [{"type": "text", "text": content}] if isinstance(content, str) else (content or [])
            if d.get("isMeta"):
                txt = " ".join(b.get("text", "") for b in blocks if b.get("type") == "text")
                m = re.search(r"<command-name>(.*?)</command-name>", txt)
                label = f"command/skill `{m.group(1)}`" if m else "harness-injected text"
                out.append(f"{head}meta\n\n*({label}, {len(txt)} chars — not rendered)* {foot}\n")
                continue
            parts = []
            for b in blocks:
                bt = b.get("type")
                if bt == "text":
                    s = b.get("text", "")
                    if is_sub:
                        parts.append(f"**{'task prompt' if not parts else 'user'}:**\n\n```text\n{trunc(s, 4000)}\n```")
                        continue
                    who, typed, pasted, xs = classify_user_text(s)
                    if who == "owner":
                        for frm, q in xs:
                            if frm == "__reply_to__":
                                parts.append(f"*{OWNER} is replying to this quoted text (not their words):*\n\n" + "\n".join(">> " + ln for ln in q.split("\n")))
                        if typed:
                            parts.append(f"**{OWNER} (typed, verbatim):**\n\n" + "\n".join("> " + ln for ln in typed.split("\n")))
                            events.append(dict(key=f"owner|{d.get('uuid')}|{sha8(typed)}", t=t, who=OWNER, kind=f"{OWNER} said",
                                               what=typed, ptr=ptr, verbatim=True))
                        for pb in pasted:
                            pm = prompt_match(pb)
                            parts.append(f"**Pasted by {OWNER}** ({len(pb)} chars, sha256 {sha8(pb)}; {pm}):\n\n```text\n{pb}\n```")
                            events.append(dict(key=f"paste|{d.get('uuid')}|{sha8(pb)}", t=t, who=OWNER, kind="pasted",
                                               what=f"{pm}; first line: {one_line(pb.splitlines()[0] if pb.strip() else '', 160)}", ptr=ptr))
                    elif who == "cross-session":
                        for frm, body in xs:
                            parts.append(f"**Message from `{frm}`:**\n\n" + "\n".join("> " + ln for ln in body.strip().split("\n")))
                            events.append(dict(key=f"xin|{d.get('uuid')}|{sha8(body)}", t=t, who=frm, kind="message in",
                                               what=f"to {sess_title}: {body.strip()}", ptr=ptr, verbatim=True))
                    elif who in ("interrupt", "command"):
                        parts.append(f"**{OWNER} — {who}:** `{one_line(typed, 300)}`")
                        events.append(dict(key=f"{who}|{d.get('uuid')}", t=t, who=OWNER, kind=who,
                                           what=f"in {sess_title}: {typed}", ptr=ptr))
                    else:
                        parts.append(f"**{who}:**\n\n```text\n{trunc(s, 800)}\n```")
                elif bt == "tool_result":
                    tid = b.get("tool_use_id")
                    c = b.get("content")
                    if isinstance(c, list):
                        c = "\n".join(x.get("text", "[image]" if x.get("type") == "image" else "") for x in c)
                    c = c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)
                    err = " **(error)**" if b.get("is_error") else ""
                    name = tool_names.get(tid, "tool")
                    if tid in sealed_tool_ids or hide_results:
                        parts.append(f"**result of {name}**{err}: *[redacted by the Log: this call touches _sealed/]*")
                    else:
                        parts.append(f"**result of {name}**{err}:\n\n```text\n{trunc(c)}\n```")
                    if b.get("is_error"):
                        events.append(dict(key=f"err|{d.get('uuid')}|{tid}", t=t, who=sess_title, kind="tool error",
                                           what=f"{name}: {one_line(c, 240)}", ptr=ptr))
                    cmd = tool_names.get(f"{tid}:cmd", "")
                    if re.search(r"python3?\s[^|;&]*quote_check\.py", cmd) and re.search(r"^\s*NOT FOUND", c, re.M):
                        events.append(dict(key=f"qnf|{d.get('uuid')}|{tid}", t=t, who=sess_title, kind="quote not found",
                                           what=one_line(c, 240), ptr=ptr))
                elif bt == "image":
                    parts.append("*[image]*")
            if parts:
                label = "user" if not is_sub else "subagent input"
                out.append(f"{head}{label}\n\n" + "\n\n".join(parts) + f"\n\n{foot}\n")
        else:  # assistant
            blocks = content if isinstance(content, list) else [{"type": "text", "text": str(content)}]
            parts = []
            for b in blocks:
                bt = b.get("type")
                if bt == "text" and PRIVATE_MARK in b.get("text", ""):
                    parts.append(WITHHELD.replace("owner note to the Log", "the Log's reply to an owner note"))
                    continue
                if bt == "text" and b.get("text", "").strip():
                    parts.append(b["text"])
                    if not is_sub:
                        events.append(dict(key=f"say|{d.get('uuid')}|{sha8(b['text'])}", t=t, who=sess_title, kind="assistant text",
                                           what=one_line(b["text"], 400), ptr=ptr))
                elif bt == "thinking" and b.get("thinking", "").strip():
                    parts.append("*thinking:*\n\n```text\n" + trunc(b["thinking"]) + "\n```")
                elif bt == "tool_use":
                    name, inp, tid = b.get("name", "?"), b.get("input") or {}, b.get("id")
                    tool_names[tid] = name
                    raw = json.dumps(inp, ensure_ascii=False)
                    if isinstance(inp, dict) and isinstance(inp.get("command"), str):
                        tool_names[f"{tid}:cmd"] = inp["command"]
                    hide_in, hide_out = sealed_rule(name, inp, raw)
                    if hide_out:
                        sealed_tool_ids.add(tid)
                    if hide_in or hide_out:
                        paths = sorted(set(m.group(0) for m in SEALED_PATH.finditer(raw)))
                        shown = "" if hide_in else (": " + one_line(inp.get("command") or inp.get("file_path") or raw, 300) if isinstance(inp, dict) else "")
                        events.append(dict(key=f"sealed|{d.get('uuid')}|{tid}", t=t, who=sess_title,
                                           kind="writes into _sealed" if (hide_in and name in WRITE_TOOLS) else "call references _sealed",
                                           what=f"{name} ({', '.join(paths)}){shown}", ptr=ptr))
                    if hide_in:
                        parts.append(f"**tool call `{name}`**: *[input redacted by the Log: touches {', '.join(paths)}]*")
                        continue
                    lines = [f"**tool call `{name}`**"]
                    if isinstance(inp, dict):
                        for k, v in inp.items():
                            if isinstance(v, str) and ("\n" in v or len(v) > 200):
                                lines.append(f"- {k}:\n\n```text\n{trunc(v)}\n```")
                            else:
                                lines.append(f"- {k}: `{one_line(v if isinstance(v, str) else json.dumps(v, ensure_ascii=False), 600)}`")
                    else:
                        lines.append(f"```text\n{trunc(raw)}\n```")
                    parts.append("\n".join(lines))
                    if not is_sub:
                        add_tool_events(events, name, inp, t, sess_title, ptr, d)
            if parts:
                out.append(f"{head}{'assistant' if not is_sub else 'subagent'}\n\n" + "\n\n".join(parts) + f"\n\n{foot}\n")
    total = 0
    red = []
    for line, t, txt in chunks:
        rt, n = redact_lines(txt, sealed_only)
        total += n
        red.append((line, t, rt))
    if want_chunks:
        return red, total
    return "\n".join(c[2] for c in red), total


ITEM_HDR = re.compile(r"^###\s+((?:SC|SP|CH|R1|R2|V)-\d+)\s*[·:\-–—]\s*(.+)$", re.M)


def add_tool_events(events, name, inp, t, who, ptr, d):
    uid = d.get("uuid")
    if not isinstance(inp, dict):
        return
    if name == "SendMessage":
        events.append(dict(key=f"xout|{uid}", t=t, who=who, kind="message out",
                           what=f"to {inp.get('to')}: {inp.get('message', '')}", ptr=ptr, verbatim=True))
    elif name == "AskUserQuestion":
        qs = "; ".join(q.get("question", "") for q in inp.get("questions", []) if isinstance(q, dict))
        events.append(dict(key=f"ask|{uid}", t=t, who=who, kind=f"question to {OWNER}", what=qs, ptr=ptr, verbatim=True))
    elif name in ("Write", "Edit", "NotebookEdit", "MultiEdit"):
        p = inp.get("file_path", "")
        rel = p.replace(ROOT + "/", "")
        body = inp.get("content") or inp.get("new_string") or ""
        items = ITEM_HDR.findall(body)
        st = " · writes line 1 'STATUS: FINAL'" if re.match(r"STATUS: FINAL", body) else ""
        what = f"{name} {rel}" + (f" · items {', '.join(i for i, _ in items[:12])}{' …' if len(items) > 12 else ''}" if items else "") + st
        events.append(dict(key=f"write|{uid}|{p}", t=t, who=who, kind="doc write", what=what, ptr=ptr))
    elif name == "Bash":
        cmd = inp.get("command", "")
        if re.search(r">\s*\"?[^|&;]*" + CTX_DIR + "/", cmd) or "tee " in cmd:
            events.append(dict(key=f"bashwrite|{uid}", t=t, who=who, kind="shell write", what=one_line(cmd, 240), ptr=ptr))
    elif name in ("Agent", "Workflow", "Task"):
        events.append(dict(key=f"agent|{uid}", t=t, who=who, kind="agent spawned",
                           what=one_line(inp.get("description") or inp.get("script", "")[:200], 200), ptr=ptr))
    elif name in ("CronCreate", "ScheduleWakeup", "CronDelete"):
        events.append(dict(key=f"cron|{uid}", t=t, who=who, kind="schedule", what=one_line(json.dumps(inp), 240), ptr=ptr))


# ---------------------------------------------------------------- docs
def doc_status():
    rows = []
    for p in sorted(glob.glob(os.path.join(NORM, "chats", "*", "**", "*.md"), recursive=True)):
        rel = os.path.relpath(p, NORM)
        if rel.startswith("chats/log/") or re.search(r"/(__pycache__|sweep|turns|tests|lib)/", rel):
            continue  # a chat's copies of transcripts and test fixtures are not its documents
        with open(p, encoding="utf-8", errors="replace") as f:
            first = f.readline().strip()
        final = first.startswith("STATUS: FINAL")
        st = os.stat(p)
        rows.append(dict(rel=rel, first=first, final=final, sha=sha256_file(p), size=st.st_size,
                         mtime=dt.datetime.fromtimestamp(st.st_mtime).astimezone()))
    return rows


ITEM_BLOCK = re.compile(r"^###\s+(.+?)$(.*?)(?=^#{1,3}\s|\Z)", re.M | re.S)


def route_items(rows):
    out = []
    for r in rows:
        if r["rel"].count("/") != 2:
            continue  # only a chat's top-level documents carry its own Route items
        with open(os.path.join(NORM, r["rel"]), encoding="utf-8", errors="replace") as f:
            text = f.read()
        for m in ITEM_BLOCK.finditer(text):
            head, body = m.group(1).strip(), m.group(2)
            iid, _, claim = head.partition(" · ")
            iid, claim = (iid.strip(), claim.strip()) if claim else (head, head)
            if not re.match(r"^(?:SC|SP|CH|R1|R2|V)-\d+$", iid):
                iid = f"{r['rel'].split('/')[1]} {os.path.basename(r['rel'])[:-3]} {iid}"
            rm = re.search(r"^\s*-\s*Route:\s*(.+)$", body, re.M)
            if not rm:
                continue
            route = rm.group(1).strip()
            if not re.search(rf"\b({ROUTE_NAMES})\b", route):
                continue
            sev = re.search(r"Severity:\s*([^·\n]+)", body)
            where = re.search(r"^\s*-\s*Where:\s*(.+)$", body, re.M)
            out.append(dict(doc=r["rel"], id=iid, claim=claim, route=route, block=m.group(0),
                            sev=sev.group(1).strip() if sev else "", where=where.group(1).strip() if where else "",
                            h=sha8(m.group(0))))
        # questions written as list lines rather than item blocks ("… *Route: <owner>.*")
        for n, line in enumerate(text.split("\n"), 1):
            if re.match(r"^\s*-\s*Route:", line) or not re.search(rf"Route:\**\s*\**\s*({ROUTE_NAMES})\b", line):
                continue
            rt = re.search(r"Route:\**\s*\**\s*([^*\n]+)", line).group(1).strip(" .")
            out.append(dict(doc=r["rel"], id=f"{r['rel'].split('/')[1]} {os.path.basename(r['rel'])[:-3]} line {n}", claim=line.strip(),
                            route=rt, block=line, sev="", where="", h=sha8(line)))
    return out


def copy_questions(items, state, stamp):
    seen = state.setdefault("questions", {})
    blocks = []
    for it in items:
        k = f"{it['doc']}#{it['id']}"
        if seen.get(k) == it["h"]:
            continue
        note = "copied" if k not in seen else "copied again: its claim or route changed in the source doc"
        seen[k] = it["h"]
        blocks.append(f"\n#### {it['id']} · route: {one_line(it['route'], 80)} · from `{it['doc']}` · {note} {stamp} · status: open\n\n"
                      + "\n".join("> " + ln for ln in it["block"].rstrip().split("\n")) + "\n")
    if not blocks:
        return 0
    with open(QUESTIONS, encoding="utf-8") as f:
        text = f.read()
    add = ""
    if Q_MARKER not in text:
        add += ("\n\n" + Q_MARKER + "\n\nEach item is copied verbatim from its chat's document (the whole block). "
                f"The Log does not answer, rank or judge them. Status changes only when {OWNER} or {APPROVER} answers, recorded in their own words.\n")
    add += "".join(blocks)
    with open(QUESTIONS, "a", encoding="utf-8") as f:
        f.write(add)
    return len(blocks)


def snapshot_finals(rows, state):
    snaps = state.setdefault("snapshots", {})
    made = []
    for r in rows:
        if not r["final"]:
            continue
        k = f"{r['rel']}|{r['sha']}"
        if k in snaps:
            continue
        base = os.path.basename(r["rel"])[:-3]
        chat = r["rel"].split("/")[1]
        dst = os.path.join(MINE, "snapshots", f"{chat}-{base}-{r['sha'][:12]}.md")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(NORM, r["rel"]), dst)
        snaps[k] = dict(path=os.path.relpath(dst, NORM), taken=fmt_ts(now_local()))
        made.append((r, dst))
    return made


# ---------------------------------------------------------------- daily log
def append_events(events, state, stamp_dt):
    seen = set(state.setdefault("events_seen", []))
    fresh = [e for e in events if e["key"] not in seen]
    if not fresh:
        return 0
    fresh.sort(key=lambda e: (e["t"] or stamp_dt))
    by_day = {}
    for e in fresh:
        day = (e["t"] or stamp_dt).strftime("%Y-%m-%d")
        by_day.setdefault(day, []).append(e)
    state["cycle"] = state.get("cycle", 0) + 1
    for day, evs in sorted(by_day.items()):
        path = os.path.join(LOGDIR, f"{day}.md")
        existing = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
        chunk = ""
        if LOG_MARKER not in existing:
            chunk += ("\n\n---\n\n" if existing else f"# Log — {day}\n\n") + LOG_MARKER + "\n\n" \
                     "## The Log's record\n\nAppend-only. Written by `chats/log/capture.py` each cycle, plus the Log's own notes. " \
                     "Times are local. Pointers are `turns/<chat>.md#t-<id>` in this folder. The owner's and other chats' words are verbatim; " \
                     "\"assistant text\" rows are cut to 400 characters and the full text is at the pointer. The Log judges nothing.\n"
        chunk += f"\n### Cycle {state['cycle']} · written {fmt_ts(stamp_dt)} · {len(evs)} new events\n\n"
        table = [e for e in evs if not e.get("verbatim")]
        verb = [e for e in evs if e.get("verbatim")]
        if table:
            chunk += "| time | who | kind | what | pointer |\n|---|---|---|---|---|\n"
            for e in table:
                chunk += f"| {fmt_ts(e['t'])[11:19] if e['t'] else '?'} | {e['who']} | {e['kind']} | {one_line(e['what'], 400)} | {e['ptr']} |\n"
        for e in verb:
            chunk += f"\n**{fmt_ts(e['t'])[11:19] if e['t'] else '?'} · {e['who']} · {e['kind']}** ({e['ptr']})\n\n"
            chunk += "\n".join("> " + ln for ln in e["what"].split("\n")) + "\n"
        with open(path, "a", encoding="utf-8") as f:
            f.write(chunk)
    seen.update(e["key"] for e in fresh)
    state["events_seen"] = sorted(seen)
    return len(fresh)


# ---------------------------------------------------------------- state snapshots
SNAP_MIN_GAP = 300  # seconds between two versioned snapshots of the same doc (a FINAL line always snapshots)
RAW_MIRROR = os.path.join(SEALED, "raw-transcripts")  # backup of raw transcripts; sealed because they hold sealed writes


def snapshot_docs(rows, state, stamp_dt):
    """Versioned copy of every chat doc whose content changed, at most one per doc per SNAP_MIN_GAP."""
    last = state.setdefault("doc_snaps", {})
    made = 0
    for r in rows:
        prev = last.get(r["rel"])
        if prev and prev["sha"] == r["sha"]:
            continue
        if prev and not r["final"] and (stamp_dt.timestamp() - prev["at"]) < SNAP_MIN_GAP:
            continue
        chat = r["rel"].split("/")[1]
        flat = r["rel"].split("/", 2)[2].replace("/", "__")[:-3]
        dst = os.path.join(MINE, "snapshots", chat, f"{flat}@{stamp_dt.strftime('%Y%m%d-%H%M%S')}-{r['sha'][:8]}.md")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(NORM, r["rel"]), dst)
        last[r["rel"]] = dict(sha=r["sha"], at=stamp_dt.timestamp(), path=os.path.relpath(dst, NORM))
        made += 1
    return made


def mirror_raw():
    """Copy every raw transcript (and subagent transcript) that changed into _sealed/raw-transcripts/."""
    n = 0
    for src in glob.glob(os.path.join(PROJ, "*.jsonl")) + glob.glob(os.path.join(PROJ, "*", "subagents", "**", "*"), recursive=True):
        if not os.path.isfile(src):
            continue
        rel = os.path.relpath(src, PROJ)
        dst = os.path.join(RAW_MIRROR, rel)
        try:
            st = os.stat(src)
            if os.path.exists(dst):
                dt_ = os.stat(dst)
                if dt_.st_size == st.st_size and int(dt_.st_mtime) == int(st.st_mtime):
                    continue
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            n += 1
        except OSError:
            continue
    return n


def timeline(sessions, rows, stamp_dt):
    rec = dict(t=fmt_ts(stamp_dt),
               sessions={s.title: dict(sid=s.sid[:8], last=fmt_ts(s.last), records=sum(1 for d in s.recs if d.get("type") in ("user", "assistant")))
                         for s in sessions},
               docs={r["rel"]: dict(sha=r["sha"][:12], bytes=r["size"], final=r["final"]) for r in rows})
    with open(os.path.join(STATE, "timeline.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------- narrative deltas (for the Log's subagents)
RETIRED = " (desktop, retired)"
NARR = os.path.join(LOGDIR, "narrative")


def base_chat(title):
    return title[:-len(RETIRED)] if title.endswith(RETIRED) else title


def make_deltas():
    """Write, per chat, the rendered turns newer than what the narrative already covers. Prints JSON."""
    state = load_json(os.path.join(STATE, "state.json"), {})
    upto = state.setdefault("narrated_upto", {})
    sealed_only = build_sealed_filter()
    ddir = os.path.join(MINE, "deltas")
    os.makedirs(ddir, exist_ok=True)
    per_chat = {}
    for p in sorted(glob.glob(os.path.join(PROJ, "*.jsonl"))):
        sid = os.path.basename(p)[:-6]
        if sid in EXCLUDE:
            continue
        s = Session(sid, p)
        if s.title in EXCLUDE_TITLES or s.title.startswith("untitled-"):
            continue
        chat = base_chat(s.title)
        chunks, _ = render_records(s.recs, os.path.basename(p), sealed_only, [], safe_name(s.title), want_chunks=True)
        since = upto.get(chat)
        new = [c for c in chunks if c[1] and (since is None or c[1].timestamp() > since)]
        seen_keys = per_chat.setdefault(chat + "\x00keys", set())
        for c in new:
            k = (c[1].timestamp(), "\n".join(c[2].split("\n")[2:-2]))  # a forked session repeats its parent's turns
            if k in seen_keys:
                continue
            seen_keys.add(k)
            per_chat.setdefault(chat, []).append((c, s))
    out = []
    for chat, items in sorted((k, v) for k, v in per_chat.items() if not k.endswith("\x00keys")):
        items.sort(key=lambda x: x[0][1])
        t0, t1 = items[0][0][1], items[-1][0][1]
        path = os.path.join(ddir, f"{safe_name(chat)}@{t0.strftime('%H%M%S')}-{t1.strftime('%H%M%S')}.md")
        body = [f"# New turns — {chat} — {fmt_ts(t0)} to {fmt_ts(t1)}\n",
                f"Sessions: {', '.join(sorted(set(s.sid[:8] + ' ' + s.title for _, s in items)))}\n"]
        body += [c[2] for c, _ in items]
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(body))
        out.append(dict(chat=chat, delta=path, first=fmt_ts(t0), last=fmt_ts(t1), upto=t1.timestamp(), chunks=len(items),
                        bytes=os.path.getsize(path), narrative=os.path.join(NARR, f"{safe_name(chat)}.md")))
    print(json.dumps(out, ensure_ascii=False, indent=1))


def mark_narrated(chat, upto):
    state = load_json(os.path.join(STATE, "state.json"), {})
    state.setdefault("narrated_upto", {})[chat] = float(upto)
    save_json(os.path.join(STATE, "state.json"), state)
    print("narrated", chat, "up to", fmt_ts(dt.datetime.fromtimestamp(float(upto)).astimezone()))


# ---------------------------------------------------------------- main cycle
def cycle():
    stamp_dt = now_local()
    state = load_json(os.path.join(STATE, "state.json"), {})
    sealed_only = build_sealed_filter()
    os.makedirs(TURNS, exist_ok=True)
    events = []
    manifest = state.setdefault("manifest", {})
    used_names = {}
    sessions = []
    for p in sorted(glob.glob(os.path.join(PROJ, "*.jsonl"))):
        sid = os.path.basename(p)[:-6]
        if sid in EXCLUDE:
            continue
        s = Session(sid, p)
        if s.title in EXCLUDE_TITLES:
            continue
        sessions.append(s)
    sessions.sort(key=lambda s: s.first or stamp_dt)
    report = []
    for s in sessions:
        name = safe_name(s.title)
        if name in used_names and used_names[name] != s.sid:
            name = f"{name} ({s.sid[:8]})"
        used_names[name] = s.sid
        if s.sid not in manifest:
            events.append(dict(key=f"open|{s.sid}", t=s.first, who=s.title, kind="chat seen",
                               what=f"session {s.sid} first seen by the Log (first record {fmt_ts(s.first)})", ptr=f"turns/{name}.md"))
        old = manifest.get(s.sid, {}).get("file")
        body, nred = render_records(s.recs, os.path.basename(s.path), sealed_only, events, name)
        subs = []
        for aid, meta, recs in s.subagents:
            sb, nr = render_records(recs, f"{s.sid}/subagents/{aid}.jsonl", sealed_only, [], name, is_sub=True,
                                    hide_results=any(r in aid for r in SEALED_RISK))
            nred += nr
            subs.append(f"\n---\n\n## Subagent {aid} — {meta.get('description', '')} ({meta.get('agentType', '')})\n\n{sb}")
            ek = f"sub|{s.sid}|{aid}"
            if ek not in state.get("events_seen", []):
                ts = [parse_ts(r.get('timestamp')) for r in recs if r.get('timestamp')]
                events.append(dict(key=ek, t=min([x for x in ts if x], default=None), who=s.title, kind="subagent",
                                   what=f"{aid}: {meta.get('description', '')}", ptr=f"turns/{name}.md"))
        nturns = sum(1 for d in s.recs if d.get("type") in ("user", "assistant"))
        header = (f"# Turns — {s.title}\n\n- session: `{s.sid}`\n- raw transcript: `{s.path}`\n"
                  f"- first record: {fmt_ts(s.first)} · last record: {fmt_ts(s.last)}\n- user/assistant records: {nturns} · subagents: {len(s.subagents)}\n"
                  f"- lines redacted as sealed: {nred}\n\nRendered by the Log's `chats/log/capture.py` from the raw transcript; regenerated in full each cycle. "
                  "Tool inputs and results are cut at 1500 characters; the raw transcript line is given under each turn.\n\n---\n\n")
        write_if_changed(os.path.join(TURNS, f"{name}.md"), header + body + "".join(subs))
        if old and old != f"{name}.md" and os.path.exists(os.path.join(TURNS, old)):
            os.remove(os.path.join(TURNS, old))  # same session, renamed: its render moved to the new title
        manifest[s.sid] = dict(file=f"{name}.md", title=s.title, first=fmt_ts(s.first), last=fmt_ts(s.last), turns=nturns)
        report.append((s, name, nturns, nred))
    # sessions whose raw transcript has disappeared: keep their render, record the loss once
    live = {s.sid for s in sessions}
    for sid, m in manifest.items():
        if sid not in live and not m.get("gone"):
            m["gone"] = fmt_ts(stamp_dt)
            events.append(dict(key=f"gone|{sid}", t=stamp_dt, who=m.get("title", sid), kind="transcript gone",
                               what=f"raw transcript for session {sid} no longer on disk; render kept at turns/{m.get('file')}", ptr=f"turns/{m.get('file')}"))
    # docs
    rows = doc_status()
    finals = state.setdefault("finals", {})
    for r in rows:
        k = f"{r['rel']}|{r['sha']}"
        if r["final"] and k not in finals:
            finals[k] = fmt_ts(stamp_dt)
            events.append(dict(key=f"final|{k}", t=r["mtime"], who=r["rel"].split("/")[1], kind="FINAL",
                               what=f"{r['rel']} line 1: \"{r['first']}\" · sha256 {r['sha']}", ptr=r["rel"]))
    snaps = snapshot_finals(rows, state)
    nsnap = snapshot_docs(rows, state, stamp_dt)
    nraw = mirror_raw()
    timeline(sessions, rows, stamp_dt)
    nq = copy_questions(route_items(rows), state, fmt_ts(stamp_dt))
    nev = append_events(events, state, stamp_dt)
    # turns index + status
    idx = ["# Turns index\n", "| file | title | session | first | last | user/assistant records | note |", "|---|---|---|---|---|---|---|"]
    for sid, m in sorted(manifest.items(), key=lambda kv: kv[1].get("first", "")):
        idx.append(f"| [{m['file']}]({m['file'].replace(' ', '%20')}) | {m['title']} | `{sid}` | {m['first']} | {m['last']} | {m['turns']} | {('raw transcript gone ' + m['gone']) if m.get('gone') else ''} |")
    idx.append("\nNot captured (PIPELINE.md §3 R3 pre-run sessions): " + "; ".join(f"`{k}` {v}" for k, v in EXCLUDE.items()))
    write_if_changed(os.path.join(TURNS, "INDEX.md"), "\n".join(idx) + "\n")
    st = ["# Status of the chats' documents\n", f"Regenerated each cycle. Last cycle: {fmt_ts(stamp_dt)}.\n",
          "| doc | line 1 | FINAL | sha256 | bytes | modified |", "|---|---|---|---|---|---|"]
    for r in rows:
        st.append(f"| `{r['rel']}` | {one_line(r['first'], 80)} | {'yes' if r['final'] else 'no'} | `{r['sha']}` | {r['size']} | {fmt_ts(r['mtime'])} |")
    write_if_changed(os.path.join(MINE, "STATUS.md"), "\n".join(st) + "\n")
    save_json(os.path.join(STATE, "state.json"), state)
    # print
    print(f"cycle at {fmt_ts(stamp_dt)} · sealed-only shingles: {len(sealed_only)}")
    for s, name, n, nred in report:
        print(f"  {name:<34} {s.sid[:8]} records={n:<4} subagents={len(s.subagents)} redacted={nred} last={fmt_ts(s.last)}")
    for sid, m in manifest.items():
        if m.get("gone"):
            print(f"  GONE {m['title']} {sid[:8]} since {m['gone']}")
    print(f"  new events: {nev} · questions copied: {nq} · FINAL snapshots: {len(snaps)} · doc versions: {nsnap} · raw files mirrored: {nraw}")
    for r in rows:
        print(f"  doc {r['rel']:<34} {'FINAL' if r['final'] else '-':<5} {r['sha'][:12]} {r['first'][:60]}")
    for due in routing_due(rows, state):
        print("  DUE:", due)


# ---------------------------------------------------------------- routing
def routing_due(rows, state):
    fin = {r["rel"]: r for r in rows if r["final"]}
    sent = state.get("sent", {})
    due = []
    def is_final(k):
        return DOCS[k] in fin
    def sha(k):
        return fin[DOCS[k]]["sha"]
    if is_final("scope") and f"scope|{sha('scope')}|Research" not in sent:
        due.append(f"send Scope snapshot (sha {sha('scope')[:12]}) to Research for pass 1  → key scope|{sha('scope')}")
    if all(is_final(k) for k in ("scope", "specifics", "chain", "research1")):
        if "compiled1" not in state:
            due.append("compile COMPILED-1.md  → capture.py compile 1")
        else:
            c = state["compiled1"]
            for to in ("Research", "Vet"):
                if f"compiled1|{c['sha']}|{to}" not in sent:
                    due.append(f"send COMPILED-1.md (sha {c['sha'][:12]}) to {to}  → key compiled1|{c['sha']}")
    if is_final("research2"):
        if "compiled2" not in state:
            due.append("compile COMPILED-2.md  → capture.py compile 2")
        elif f"compiled2|{state['compiled2']['sha']}|Vet" not in sent:
            due.append(f"send COMPILED-2.md to Vet  → key compiled2|{state['compiled2']['sha']}")
    for n in ("1", "2"):
        if is_final(f"vet{n}") and f"queue{n}" not in state:
            due.append(f"build the checkers' queue {n} from {DOCS['vet' + n]} (planted items from _sealed/CANARIES.md)")
        if is_final(f"verify{n}") and is_final(f"refute{n}") and f"reconciled{n}" not in state:
            due.append(f"reconcile batch {n}: Verify and Refute are both FINAL")
    # a doc that changed after the Log sent it
    for k, v in sent.items():
        pass
    return due


def compile_batch(n):
    state = load_json(os.path.join(STATE, "state.json"), {})
    rows = {r["rel"]: r for r in doc_status()}
    keys = ["scope", "specifics", "chain", "research1"] if n == "1" else ["research2"]
    parts, meta = [], []
    for k in keys:
        rel = DOCS[k]
        r = rows.get(rel)
        if not r or not r["final"]:
            sys.exit(f"not compiled: {rel} is not FINAL")
        with open(os.path.join(NORM, rel), encoding="utf-8") as f:
            body = f.read()
        meta.append(f"| `{rel}` | `{r['sha']}` | {r['size']} | {fmt_ts(r['mtime'])} |")
        parts.append(f"\n\n<!-- BEGIN {rel} · sha256 {r['sha']} -->\n\n{body}\n\n<!-- END {rel} -->\n")
    stamp = fmt_ts(now_local())
    text = (f"# COMPILED-{n}\n\nCompiled by the Log, {stamp}. Each document below is copied verbatim, byte for byte, between its BEGIN and END markers. "
            "The Log added nothing else and judged nothing.\n\n| document | sha256 | bytes | modified |\n|---|---|---|---|\n" + "\n".join(meta) + "".join(parts))
    out = os.path.join(MINE, f"COMPILED-{n}.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
    state[f"compiled{n}"] = dict(path=os.path.relpath(out, NORM), sha=sha256_file(out), at=stamp, docs={DOCS[k]: rows[DOCS[k]]["sha"] for k in keys})
    save_json(os.path.join(STATE, "state.json"), state)
    print(out, state[f"compiled{n}"]["sha"])


def add_note(text):
    """The Log's own hand entry (a point, decision or hand-off the script cannot see), appended to today's log."""
    stamp = now_local()
    path = os.path.join(LOGDIR, f"{stamp.strftime('%Y-%m-%d')}.md")
    existing = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
    chunk = "" if LOG_MARKER in existing else (("\n\n---\n\n" if existing else "") + LOG_MARKER + "\n\n## The Log's record\n")
    chunk += f"\n**{fmt_ts(stamp)[11:19]} · Log · note**\n\n" + text.strip() + "\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(chunk)
    print("noted in", path)


def mark_sent(key, to):
    state = load_json(os.path.join(STATE, "state.json"), {})
    stamp = fmt_ts(now_local())
    state.setdefault("sent", {})[f"{key}|{to}"] = stamp
    save_json(os.path.join(STATE, "state.json"), state)
    with open(os.path.join(MINE, "ROUTING.md"), "a", encoding="utf-8") as f:
        if f.tell() == 0:
            f.write("# Routing ledger\n\nAppend-only. One line per message the Log sent that moves a document between chats.\n\n| sent | what (key) | to |\n|---|---|---|\n")
        f.write(f"| {stamp} | `{key}` | {to} |\n")
    print("recorded", key, "→", to, stamp)


if __name__ == "__main__":
    import fcntl
    os.makedirs(STATE, exist_ok=True)
    _lock = open(os.path.join(STATE, ".lock"), "w")
    fcntl.flock(_lock, fcntl.LOCK_EX)  # one run at a time (the routine and the Log may both call it)
    a = sys.argv[1:]
    if not a:
        cycle()
    elif a[0] == "delta":
        make_deltas()
    elif a[0] == "narrated" and len(a) == 3:
        mark_narrated(a[1], a[2])
    elif a[0] == "compile" and len(a) == 2:
        compile_batch(a[1])
    elif a[0] == "sent" and len(a) == 3:
        mark_sent(a[1], a[2])
    elif a[0] == "note" and len(a) == 2:
        add_note(a[1])
    else:
        sys.exit(__doc__)
