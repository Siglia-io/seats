# Process decisions made by the Log

**Why the Log decides these — the owner's rule (pilot run, 27 Sep 2026, answering the question about the checkers' own items; paraphrased here, quoted verbatim in a real group):** the Log works out what is best itself. If it genuinely cannot, it looks at the wider chat structure or at any one chat; if that is not enough, it considers asking the chats. If it still cannot decide, either it has not tried hard enough, it is not being decisive, or the question is one of opinionated scope, design or direction. Only that last kind goes to the owner, and then not only in the questions file (kept there for recall): the Log always asks the owner in chat, and reminds them at each update.

The Log decides process questions: routing, sequencing, who checks what, and tooling. It does not decide what any claim about the documents or the world means; that stays with the chats and with the owner and the approver. Each decision below gives the structure it rests on. The owner can override any of them.

## PD-1 · Items the checkers filed themselves in Run 1 (Vet 23 VT, Verify 34 VF, Refute 59 RF)
**Decision.** No chat checks its own items. They go in batch 2, not batch 1:
- **VF (Verify's):** Vet vets them. They go to Refute only. Verify's filing stands as its HOLDS. If Refute says HOLDS, the item is settled. If Refute differs, there is one reply round (each sees the other's reasoning once), and an item still split is CONTESTED.
- **RF (Refute's):** the mirror image. Vet vets them, and they go to Verify only.
- **VT (Vet's):** Vet does not vet them. The Log runs the scripted mechanical checks only (quote_check.py, and the store's quote-at-page check), and bounces failures to Vet with the exact failure. The Log makes no split, merge or grade. The items then go to both Verify and Refute, since neither wrote them.
- Every checker's batch-2 queue carries the planted items as usual.
**Rests on:**
- PIPELINE.md §1: "A checker that sees an earlier 'confirmed' tends to agree with it."
- Verify's own request, verbatim: "I wrote the VF items, so route them to Refute, not back to me."
- Vet's open point 6, and its own suggested fix, verbatim: "for the Log to send VT items straight to the checkers after its own quote check."
- Batch 1 is defined as Scope, Specifics, Chain and Research pass 1, so batch 1 is unchanged and waits on nothing new.

## PD-2 · Vet's open point 1: quote_check.py doesn't check the cited page or capital letters
**Decision.** Vet's default stands: run quote_check.py, then a second, page-and-case check. The store now has that second check, a quote-at-page skill under `seats/skills/` (10/10 tests at 04:39 in the pilot run). **The skill store `seats/skills/` is readable by every chat:** it is the system's shared tooling, and by Skills' own rule it holds no chat's findings. Reading it is not a read into another chat's folder.
**Rests on:** the owner's order that landed skills go into one skill store; Skills' rule after its error E-009 (recorded in Skills' error register).

## PD-3 · Vet's open point 2: re-running cited scripts conflicts with the independence rule
**Decision.** The Log puts every script an item cites into the compiled batch, copied byte for byte under `COMPILED-<n>/scripts/<author>/`, each with its sha256. Vet runs them from there and never opens an author's folder.
**Rests on:** the owner's rule that only the Log reads (never edits) everything, as the unbiased spine. PIPELINE.md §4 (Vet): "Re-run every cited script".

## PD-4 · Vet's open point 3: grading a fact's source without the web
**Decision.** Vet's default stands. Vet grades from what the item states, and writes "source date: not stated in item" where the item gives none. Opening sources belongs to Verify and Refute.
**Rests on:** Vet's row in PIPELINE.md §2, which does not include the web; R2 does not require a source's own date.

## PD-5 · Vet's open point 4: checking before splitting can bounce a good claim
**Decision.** Vet's default stands. Run every check, split, then bounce claim by claim. Only a failing claim goes to BOUNCED-<n>.md.
**Rests on:** Vet's priority in PIPELINE.md §2: "nothing broken, compound or duplicate reaches them, and nothing is silently dropped."

## PD-6 · Vet's open point 5: the project memory note reaches every chat
**Closed.** Every CLI chat runs with `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` (see the launch scripts), and Vet itself confirmed at 05:00 that the index no longer loads. The note was read before the fix by the chats that disclosed it; those reads are in INTEGRITY.md.

## PD-7 · Vet's open point 7: Run 1's fails and succeeds against "You never judge whether an item is true"
**Decision.** Vet's default stands. Vet's FAILS and SUCCEEDS are results of mechanical tests, not verdicts on truth. When Vet vets, it quotes only the rubric line, and in any merge it keeps the other author's version.
**Rests on:** Vet's prompt (PIPELINE.md §4): "You never judge whether an item is true"; the owner's rule that the absence of critique is what prevents bias.

## PD-1a · Refinements to PD-1, adopted from the checkers' own points
- **An author's stance follows its filing.** A FAILS, NARROWED or NOT CONSIDERED item stands as the author's HOLDS. A NEEDS MORE or QUESTIONS item stands as CAN'T TELL on what it implies (Verify: "my HOLDS covers only the sentence as written; what each implies is CAN'T TELL"). So a CAN'T TELL from the other checker on those items is agreement, not a split.
- **Merged duplicates.** An item that Vet merges from a VF item and an RF item is recorded as "author-confirmed by both checkers", not as "checked", and is counted apart in VERDICTS. Neither checker is sent it, because each would be checking its own claim (Refute's point).
- **Post-FINAL corrections** in a checker's FOUNDATION-1 are carried, because the compile pins each document's version at compile time.
