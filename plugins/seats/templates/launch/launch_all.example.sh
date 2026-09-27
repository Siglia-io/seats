#!/bin/bash
# One paste moves every chat to its own Terminal window (example from a pilot run, 27 Sep 2026).
# 1) asks the Log to stop and retire the desktop copies, 2) waits for it (up to 3 minutes), 3) opens one Terminal window per chat.
# Set SEATS_ROOT to the project root (and SEATS_CONTEXT if the context folder is not "context") before running.
L="${SEATS_ROOT:?set SEATS_ROOT to the project root}/${SEATS_CONTEXT:-context}/chats/log"
date '+%Y-%m-%d %H:%M:%S' > "$L/state/cli-request.flag"
rm -f "$L/state/cli-retired.flag"
echo "Asked the Log to retire the desktop chats. Waiting for it (up to 3 minutes)..."
for i in $(seq 1 60); do [ -f "$L/state/cli-retired.flag" ] && break; sleep 3; done
[ -f "$L/state/cli-retired.flag" ] && echo "The Log confirmed. Opening the chats." || echo "No confirmation from the Log in 3 minutes; opening the chats anyway. Tell the Log."
for t in Scope Specifics Chain Research Vet Verify Refute Skills; do
  osascript -e "tell application \"Terminal\" to do script \"bash '$L/launch/$t.sh'\""
  sleep 2
done
echo "Done: eight Terminal windows, one per chat. You can close this window."
