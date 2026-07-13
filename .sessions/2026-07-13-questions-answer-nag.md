# 2026-07-13 — review: closed-but-unanswered nag on the questions ledger

> **Status:** `in-progress` — branch `claude/questions-answer-nag-0713`;
> building the backlog's "Closed-but-unanswered nag for the questions
> ledger" bullet: a pure-read advisory (bake print + /questions page
> banner) flagging ledger records whose GitHub issue closed without a
> published answer link.

- **📊 Model:** Claude 5 family · worker · backlog-slice

**What this session is about:** the bake sync (PR #297) flips a ledger
record's status to `closed` when its issue closes, but the answer link
stays hand-written — so a `[program-review]` question closed without a
published answer renders "closed / pending" forever, silently breaking
the ledger's promise. This slice adds the advisory the backlog bullet
asks for: `review/gen_questions.py` prints a loud nag line per
closed-but-unanswered record at bake time, and `/questions` renders a
visible warn banner listing them.

## What was done

- (filled at close-out)

## 💡 Session idea

(filled at close-out)

## ⟲ Previous-session review

(filled at close-out)
