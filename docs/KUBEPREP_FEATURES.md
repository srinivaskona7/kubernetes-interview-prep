# KubePrep — features

| Area | What exists |
|---|---|
| Content | 18 chapters in 6 parts, 268 topics (junior/mid/senior), 268 diagrams (every topic has one), ~130 tables, 501 commands; paraphrased, no source attribution |
| Views | Chapters, chapter reader with topic tracking, Flashcards (Leitner 10m→30d), Mock interview (10 Qs + scorecard), Cheat sheet, Diagram gallery with zoom, ⌘K search |
| State | localStorage only (studied topics, card boxes) |
| Build | `build.py` validates ids, diagrams, banned terms (`.banned`, gitignored) → `js/data.js` |

## Deliberately not done
No backend, no accounts, no analytics, no author/book/publisher mentions.

## On the user's hands
Push and enable Pages; nothing else is required. Fonts load from Google Fonts (degrades to system fonts offline).
