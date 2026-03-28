"""Fleet templates — markdown formatters for all fleet output.

Each module produces publication-quality markdown for one surface:
- pr.py       — PR body with changelog, diff table, references
- comment.py  — task comments (accept, progress, complete, blocker)
- memory.py   — board memory (alert, decision, suggestion, PR notice)
- irc.py      — IRC event messages with emoji and URLs
"""