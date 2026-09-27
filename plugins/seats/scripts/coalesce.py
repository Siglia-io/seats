#!/usr/bin/env python3
"""The Log's coalesced ledger (the owner's order in the pilot run: the Log ledgers, coalesces and presents the
seats' findings as one account, connected where they meet and disjoint where they do not).

A scan, not a judgment. It reads every item block the seats filed in their FINAL documents and records each item
with the seat's own words and the seat's own label (its sort section, Kind, Severity), never a Log verdict.
It ties each item to the source lines its quotes come from, found by a whitespace- and case-insensitive search of the
source texts (the same method as sources/quote_check.py). Items from different seats that cite the same source line
are CONNECTED. Items that meet no other seat's item are DISJOINT. Where the seats' own labels on one passage differ,
the ledger says so, as a fact about the seats.

Output: $SEATS_ROOT/$SEATS_CONTEXT/chats/log/LEDGER-1.md (and LEDGER-1.json).
Run: SEATS_ROOT=<PROJECT_ROOT> SEATS_CONTEXT=<context> python3 coalesce.py
Sources: set SEATS_SOURCES to a JSON object {display name: path relative to the context folder}. A name ending in
" (reading order)" is another rendering of the source it names, and its hits count as that source's passages.
"""
import json
import os
import re
from collections import defaultdict

CTX = os.environ.get("SEATS_CONTEXT", "context")
N = os.path.join(os.path.abspath(os.environ.get("SEATS_ROOT") or os.getcwd()), CTX)
DOCS = [  # (seat, document) — the seats' FINAL documents that hold items
    ("Scope", "chats/scope/SCOPE.md"), ("Scope", "chats/scope/FOUNDATION-1.md"),
    ("Specifics", "chats/specifics/SPECIFICS.md"), ("Specifics", "chats/specifics/FOUNDATION-1.md"),
    ("Chain", "chats/chain/CHAIN.md"), ("Chain", "chats/chain/FOUNDATION-1.md"),
    ("Research", "chats/research/RESEARCH-1.md"), ("Research", "chats/research/FOUNDATION-1.md"),
    ("Vet", "chats/vet/FOUNDATION-1.md"), ("Verify", "chats/verify/FOUNDATION-1.md"),
    ("Refute", "chats/refute/FOUNDATION-1.md"),
]
# The source texts the quotes are searched in, in search order: {display name: path relative to the context folder}.
SOURCES = json.loads(os.environ.get("SEATS_SOURCES") or "null") or {
    "Source B": "sources/SOURCE_B.txt", "Source A": "sources/SOURCE_A.txt",
    "Source A (reading order)": "sources/SOURCE_A_flow.txt"}
ALT = " (reading order)"


def base_source(name):
    """An alternate rendering of a source counts as that source."""
    return name[:-len(ALT)] if name.endswith(ALT) else name


SORTS =["NONE OF THE ABOVE", "NOT CONSIDERED", "NEEDS MORE", "SUCCEEDS", "FAILS", "QUESTIONS", "NARROWED",
         "WITHDRAWN", "REVERSES"]
ITEM = re.compile(r"^(#{2,4})\s+(?:Reverses\s+)?((?:SC|SP|CH|R1|R2|VT|VF|RF)-\d+[a-z]?)\b\s*[·:\-–—]?\s*(.*)$")
HEAD = re.compile(r"^(#{1,4})\s+(.*)$")
QUOTE = re.compile(r'^\s*-\s*Quote(?:\s*\d)?\s*:\s*[“"](.+?)[”"]')
FIELD = re.compile(r"^\s*-\s*(Kind|Severity|Where|Route|Evidence)\s*:\s*(.+)$")


def norm(s):
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"').replace("—", "-").replace("–", "-")
    return re.sub(r"\s+", " ", s).strip().lower()


def load_sources():
    out = {}
    for name, rel in SOURCES.items():
        lines = open(os.path.join(N, rel), encoding="utf-8", errors="replace").read().split("\n")
        # a normalized running text with, for each character, the source line it came from
        buf, where = [], []
        for i, ln in enumerate(lines, 1):
            t = norm(ln) + " "
            buf.append(t)
            where.extend([i] * len(t))
        out[name] = ("".join(buf), where, rel)
    return out


def locate(q, srcs):
    nq = norm(q)
    if len(nq) < 12:
        return None
    for name in sorted(srcs, key=lambda n: n.endswith(ALT)):  # primary texts first, in SOURCES order
        text, where, rel = srcs[name]
        k = text.find(nq)
        if k >= 0:
            return (name, rel, where[k], where[min(k + len(nq) - 1, len(where) - 1)])
    return None


SORT_HEAD = re.compile(r"^(#{2,4})\s+(?:\d+(?:\.\d+)*\s+)?(NONE OF THE ABOVE|NOT CONSIDERED|NEEDS MORE|SUCCEEDS|FAILS|QUESTIONS)\b")
IDREF = re.compile(r"\b((?:SC|SP|CH|R1|R2|VT|VF|RF)-\d+[a-z]?)\b")


def sort_map(lines):
    """The seat's own labels: an id takes the label of the §8 subsection that first lists it."""
    m, cur, lvl = {}, None, 9
    for ln in lines:
        h = SORT_HEAD.match(ln)
        if h:
            cur, lvl = h.group(2), len(h.group(1))
            continue
        hh = HEAD.match(ln)
        if hh and len(hh.group(1)) <= lvl:
            cur = None
        if cur:
            for i in IDREF.findall(ln):
                m.setdefault(i, [])
                if cur not in m[i]:
                    m[i].append(cur)
    return {k: "+".join(v) for k, v in m.items()}


def parse(seat, rel, srcs):
    path = os.path.join(N, rel)
    lines = open(path, encoding="utf-8", errors="replace").read().split("\n")
    smap = sort_map(lines)
    items, cur, sort_ctx = [], None, ""
    for n, ln in enumerate(lines, 1):
        m = ITEM.match(ln)
        h = HEAD.match(ln)
        if h and not m:
            sh = SORT_HEAD.match(ln)
            if sh:
                sort_ctx = sh.group(2)
            elif len(h.group(1)) <= 3:
                sort_ctx = ""
        if m:
            if cur:
                items.append(cur)
            reverses = ln.lstrip("#").strip().lower().startswith("reverses")
            cur = dict(seat=seat, doc=rel, line=n, id=m.group(2), claim=m.group(3).strip(), sort=("REVERSES" if reverses else (sort_ctx or smap.get(m.group(2), ""))),
                       kind="", severity="", where="", quotes=[], anchors=[])
            continue
        if cur:
            if ln.startswith("#") and not m:
                items.append(cur)
                cur = None
                continue
            q = QUOTE.match(ln)
            if q:
                cur["quotes"].append(q.group(1))
                loc = locate(q.group(1), srcs)
                if loc:
                    cur["anchors"].append(loc)
            f = FIELD.match(ln)
            if f and f.group(1).lower() in ("kind", "severity", "where"):
                cur[f.group(1).lower()] = f.group(2).strip()
    if cur:
        items.append(cur)
    return items


def main():
    srcs = load_sources()
    items = []
    for seat, rel in DOCS:
        if os.path.exists(os.path.join(N, rel)):
            items += parse(seat, rel, srcs)
    # passages: group by (source, line) of each anchor's first line
    by_line = defaultdict(list)
    for it in items:
        for (name, rel, a, b) in it["anchors"]:
            key = (base_source(name), rel, a)
            by_line[key].append(it)
    connected, disjoint_passages = [], []
    for key, its in sorted(by_line.items(), key=lambda kv: (kv[0][0], kv[0][2])):
        seats = sorted(set(i["seat"] for i in its))
        (connected if len(seats) > 1 else disjoint_passages).append((key, its, seats))
    unanchored = [i for i in items if not i["anchors"]]
    # labels differing on one passage (a fact about the seats' own labels)
    def lab(i):
        return i["sort"] or i["kind"] or "—"
    differing = [(k, its) for k, its, seats in connected if len(set(lab(i) for i in its if i["sort"])) > 1]

    def link(rel, line, text):
        return f"[{text}]({CTX}/{rel}:{line})"

    out = ["# Ledger — Run 1: the seats' findings, coalesced", "",
           "**What this is:** the Log's scan of every item the seats filed in their FINAL documents (the owner's order: ledger, coalesce and present the findings as one, connected where they meet, disjoint where they do not). "
           "Each finding is the seat's own, in the seat's own words, with the seat's own label. The Log adds no verdict. **No finding here has been through the seats' back-and-forth yet** (the verification stage did not run), so each label is one seat's decision.",
           "", "**How items are tied to the documents:** each item's quotes are searched in the source texts (whitespace- and case-insensitive, as sources/quote_check.py does). Items from different seats whose quotes land on the same source line are CONNECTED. The rest are DISJOINT.",
           "", "## Counts", "",
           f"- Items scanned: {len(items)} (" + ", ".join(f"{s} {sum(1 for i in items if i['seat']==s)}" for s in ["Scope","Specifics","Chain","Research","Vet","Verify","Refute"]) + ")",
           f"- Source passages cited by two or more seats (connected): {len(connected)}",
           f"- Source passages cited by one seat only (disjoint): {len(disjoint_passages)}",
           f"- Items tied to no source line (outside facts, reasoning steps, questions, or quotes the scan could not place): {len(unanchored)}",
           f"- Connected passages where the seats' own labels differ: {len(differing)}", ""]
    out += ["## 1. Connected — passages two or more seats filed on", ""]
    for (docname, rel, line), its, seats in connected:
        q = next((qq for i in its for qq in i["quotes"] if locate(qq, srcs) and locate(qq, srcs)[2] == line), its[0]["quotes"][0] if its[0]["quotes"] else "")
        out.append(f"### {docname} line {line} — seats: {', '.join(seats)}")
        out.append(f"> \"{q[:300]}\" — {link(rel, line, f'{docname}, line {line}')}")
        out.append("")
        out.append("| seat | item | the seat's words | the seat's label | severity |")
        out.append("|---|---|---|---|---|")
        seen = set()
        for i in its:
            k = (i["seat"], i["id"], i["line"])
            if k in seen:
                continue
            seen.add(k)
            out.append(f"| {i['seat']} | {link(i['doc'], i['line'], i['id'])} | {i['claim'][:220].replace('|','¦')} | {lab(i)} | {i['severity'][:30].replace('|','¦')} |")
        out.append("")
    out += ["## 2. Where the seats' own labels differ on the same passage", "",
            "A fact about the seats' labels, not a verdict. These are the first candidates for the seats' back-and-forth.", ""]
    for (docname, rel, line), its in differing:
        labs = sorted(set(f"{i['seat']}: {lab(i)} ({i['id']})" for i in its if i["sort"]))
        out.append(f"- {link(rel, line, f'{docname}, line {line}')} — " + "; ".join(labs))
    out += ["", "## 3. Disjoint — passages one seat filed on", ""]
    for (docname, rel, line), its, seats in disjoint_passages:
        ids = ", ".join(sorted(set(link(i['doc'], i['line'], i['id']) for i in its)))
        out.append(f"- {link(rel, line, f'{docname}, line {line}')} · {seats[0]} · {ids}")
    out += ["", "## 4. Items tied to no source line", "",
            "Outside facts (Research's R1 items carry their own URL and access date), reasoning steps, questions, and items whose quotes the scan could not place. Listed per seat, with the seat's label.", ""]
    for s in ["Scope", "Specifics", "Chain", "Research", "Vet", "Verify", "Refute"]:
        its = [i for i in unanchored if i["seat"] == s]
        if not its:
            continue
        out.append(f"### {s} ({len(its)})")
        for i in its:
            out.append(f"- {link(i['doc'], i['line'], i['id'])} · {lab(i)} · {i['claim'][:200]}")
        out.append("")
    open(os.path.join(N, "chats/log/LEDGER-1.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    json.dump(items, open(os.path.join(N, "chats/log/LEDGER-1.json"), "w"), indent=1, default=str)
    print(f"items {len(items)} · connected passages {len(connected)} · disjoint passages {len(disjoint_passages)} · unanchored {len(unanchored)} · differing labels {len(differing)}")
    for s in ["Scope", "Specifics", "Chain", "Research", "Vet", "Verify", "Refute"]:
        its = [i for i in items if i["seat"] == s]
        print(f"  {s}: {len(its)} items, {sum(1 for i in its if i['anchors'])} tied to source lines, {sum(1 for i in its if i['quotes'])} with quotes")


if __name__ == "__main__":
    main()
