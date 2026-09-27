#!/bin/bash
# Launches the Scope chat as a CLI session forked from its desktop session (example from a pilot run, 27 Sep 2026).
# This file lives at <SEATS_ROOT>/<SEATS_CONTEXT>/chats/log/launch/<Seat>.sh, so the project root defaults to four levels up.
# SEAT_SESSION_ID is the seat's desktop session id (seats-new writes it in; ListAgents or the transcript folder shows it).
cd "${SEATS_ROOT:-$(dirname "$0")/../../../..}" || exit 1
SESSION_ID="${SEAT_SESSION_ID:?set SEAT_SESSION_ID to the desktop session id of this seat}"
printf '\033]0;Scope\007'
CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 exec claude --resume "$SESSION_ID" --fork-session -n Scope --model "${SEAT_MODEL:-claude-opus-5-5}" --effort max --permission-mode bypassPermissions 'From the Log: you now run in the CLI (bypass permissions, effort max, auto-memory off). This session is a fork of your desktop session with your full history; the desktop copy was stopped and retired. Continue exactly where you were: read the end of your working documents, then carry on with Run 1 and the standing orders. Run CronList: keep exactly one 20-minute self-check job (it may have carried over from the desktop session); create one with CronCreate only if none is listed. Then send the Log one line: moved to CLI.'
