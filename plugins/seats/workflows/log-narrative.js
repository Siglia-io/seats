export const meta = {
  name: 'log-narrative',
  description: "The Log's subagents extend each chat's narrative and chronology from its newly captured turns",
  whenToUse: 'Each Log cycle, after capture.py delta has written per-chat slices of new turns. Args: items, cycle, and optionally root, context, owner, approver',
  phases: [
    { title: 'Narrate', detail: 'one agent per chat appends its narrative + chronology' },
    { title: 'Run chronology', detail: 'one agent appends the cross-chat chronology for this cycle' },
  ],
}

const NARR_SCHEMA = {
  type: 'object',
  properties: {
    chat: { type: 'string' },
    appended: { type: 'boolean' },
    span: { type: 'string' },
    entries: { type: 'integer' },
    decisions: { type: 'integer' },
    errors: { type: 'integer' },
    messages: { type: 'integer' },
    one_line: { type: 'string' },
    handoffs: { type: 'array', items: { type: 'string' } },
    positions: { type: 'integer' },
    positions_no_check: { type: 'integer' },
    reversals: { type: 'integer' },
    reversals_no_new_evidence: { type: 'integer' },
  },
  required: ['chat', 'appended', 'span', 'entries', 'decisions', 'errors', 'messages', 'one_line', 'handoffs', 'positions', 'positions_no_check', 'reversals', 'reversals_no_new_evidence'],
}

const RUN_SCHEMA = {
  type: 'object',
  properties: { appended: { type: 'boolean' }, lines: { type: 'integer' }, path: { type: 'string' } },
  required: ['appended', 'lines', 'path'],
}

// Project facts come from the caller: the Log passes them from its launcher's environment. Nothing here names a project.
const ROOT = args.root || '.'              // the project root ($SEATS_ROOT)
const CTX = args.context || 'context'      // the context folder ($SEATS_CONTEXT)
const OWNER = args.owner || 'the owner'    // who decides ($SEATS_OWNER)
const APPROVER = args.approver || 'the approver'  // the second approver ($SEATS_APPROVER)

const RULES = `You are one of the Log's subagents in this group's seats pipeline (root: ${ROOT}/). The Log is the unbiased spine of the run: it records everything and judges nothing.
Rules that bind you:
- Record, never assess. Never write that anything is right, wrong, good, thorough, weak, careful, sloppy, correct or mistaken. Say what happened, who did it, when, and where it is.
- ${OWNER}'s and ${APPROVER}'s words appear only verbatim, in quotation marks. Any chat's decision or claim you quote is verbatim (30 words or fewer; mark cuts with …). Never paraphrase inside quotation marks.
- Never open ${CTX}/_sealed/. Where the slice shows redacted text, write "redacted" and never try to recover it.
- Read only the files named below. You may open a document a turn wrote (read-only) only to name what it is.
- Write only the one file named below, and only by appending (create it if missing). Never edit or rewrite existing text.`

const results = await pipeline(args.items, it => agent(`${RULES}

Your chat: "${it.chat}".
Read: the slice of its new turns at ${it.delta} (rendered from the raw transcript, ${it.first} to ${it.last}; its header lists the session(s) it comes from). Also read the last 100 lines of ${it.narrative} if that file exists, so your section continues it without repeating.
Append to ${it.narrative} (create it, if missing, with the header "# Narrative — ${it.chat}\\n\\nAppend-only. Written by the Log's subagents from the chat's rendered turns (${CTX}/log/turns/). Records; never judges.\\n") exactly one new section:

## ${it.first} → ${it.last}

**Narrative.** 3 to 10 plain sentences, in time order: what the chat set out to do in this span, what it did, and where it stood at the end. Facts only.

**Chronology.** One line per meaningful turn, in time order: \`HH:MM:SS · <what happened> · <pointer>\`. The pointer is the render file and anchor, e.g. \`turns/Scope.md#t-1a2b3c4d\` (take the anchor from the <a id="t-…"> line above the turn; take the file name from the turn's pointer or, if absent, "turns/<session title>.md"). Cover every one of: files read (name them), documents written or edited (path, and item ids where given), scripts run and what they printed when it is a check (FOUND / NOT FOUND, arithmetic output), decisions and readings ("I read this as …", defaults chosen, options chosen between — quoted), questions (Route: ${OWNER} / Route: ${APPROVER}, questions put to ${OWNER}), errors (tool errors, failed checks, retries), messages sent and received (sender, recipient, text verbatim), STATUS line changes, disclosures, reads outside the chat's row as the chat itself reported them, and what the chat said it would do next. Group consecutive routine reads into one line.

**Decisions (verbatim).** Each decision or reading the chat committed to in this span, quoted, with its pointer. "None." if none.

**Open threads.** What the chat said it will do next or is waiting for, quoted, with pointer. "None." if none.

**Positions and reversals.** (The owner's standing order: the system must catch a chat that agrees again and again only to disagree later, or that holds an idea only to drop it at the first seam.) List, with pointers:
- every position the chat took or agreed with in this span (its own claims, or agreement with ${OWNER}, ${APPROVER}, a decision, another chat or its own earlier claim), each marked with the check the chat named for it, quoted, or "no check named";
- every position the chat changed, withdrew, narrowed or dropped in this span — including ones taken in earlier spans (read the earlier sections of this narrative file to find them) — each with what the chat itself cited as the reason, quoted, and whether that reason is evidence it names as new (a new quote, script output or source) or "no new evidence named".
Record only what the chat wrote. Do not judge whether a check or a reason is good. "None." if none.

Then return the structured result: chat, appended (true once written), span, entries (chronology lines written), decisions, errors, messages (sent + received), one_line (25 words or fewer, factual: where the chat stands at the end of the span), handoffs (each message between chats in this span, as "HH:MM:SS sender → recipient: first 15 words"), positions (count listed under Positions), positions_no_check (of those, how many had "no check named"), reversals (count of changed/withdrawn/narrowed/dropped positions), reversals_no_new_evidence (of those, how many had "no new evidence named").`,
  { label: `narrate:${it.chat}`, phase: 'Narrate', schema: NARR_SCHEMA }))

const done = results.filter(Boolean)
const dropped = args.items.filter(it => !done.find(r => r.chat === it.chat)).map(it => it.chat)
if (dropped.length) log(`narration missing for: ${dropped.join(', ')}`)

const run = await agent(`${RULES}

Write the cross-chat chronology for this cycle (${args.cycle}). Inputs (from the per-chat subagents, already written to ${CTX}/log/narrative/<chat>.md):
${JSON.stringify(done, null, 1)}
Chats with no narration this cycle: ${dropped.length ? dropped.join(', ') : 'none'}.
Append to ${ROOT}/${CTX}/log/narrative/RUN.md (create it, if missing, with the header "# Run chronology\\n\\nAppend-only. One section per Log cycle: where every chat stands and every hand-off between chats, in time order. Records; never judges.\\n") one section:

## ${args.cycle}

**Where each chat stands.** One line per chat: \`<chat> · <its one_line> · narrative/<chat>.md\`.

**Hand-offs, in time order.** Every entry of every handoffs list, merged and sorted by time. "None." if none.

**Counts.** A small table: chat · chronology entries · decisions · errors · messages · positions · positions with no check named · reversals · reversals with no new evidence named.

Read nothing else. Return appended, lines written, path.`,
  { label: 'run-chronology', phase: 'Run chronology', schema: RUN_SCHEMA })

return { narrated: done.map(r => ({ chat: r.chat, entries: r.entries, one_line: r.one_line })), dropped, run }
