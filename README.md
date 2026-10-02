# KubePrep

A visual Kubernetes interview study guide: 18 chapters, 268 questions, 263 diagrams (every topic has one), comparison tables, flashcards (spaced repetition), a mock interview and a command cheat sheet. Static site, no runtime dependencies; progress is stored in your browser only.

## Run locally
    python3 -m http.server 8077   # open http://localhost:8077

## Deploy to GitHub Pages
Push, then Settings → Pages → Deploy from branch → `main` / root. `.nojekyll` is included.

## Edit content
Edit `data/chN.json` (contract in `data/SCHEMA.md`), add diagrams under `diagrams/`, then run `python3 build.py` to regenerate `js/data.js`.
# kubernetes-interview-prep
