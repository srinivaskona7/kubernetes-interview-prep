#!/usr/bin/env python3
"""Build js/data.js from data/ch*.json. Inlines each diagram's <svg>. Fails on broken refs or banned terms."""
import json, re, sys, pathlib
root = pathlib.Path(__file__).parent
banned = []
if (root / ".banned").exists():
    banned = [l.strip().lower() for l in (root / ".banned").read_text().splitlines() if l.strip()]
PARTS = [(2, "Part 1 · Introduction to Kubernetes"), (5, "Part 2 · Workloads and Scaling"), (9, "Part 3 · Networking, Storage and Security"), (11, "Part 4 · Deployment and GitOps"), (15, "Part 5 · Reliability, Monitoring and Recovery"), (99, "Part 6 · Troubleshooting and Interview Skills")]
chapters, errors = [], []
svg_cache = {}
def svg_of(rel):
    if rel not in svg_cache:
        p = root / rel
        if not p.exists():
            errors.append(f"missing diagram {rel}"); svg_cache[rel] = ""
        else:
            m = re.search(r"<svg\b.*?</svg>", p.read_text(), re.S)
            if not m: errors.append(f"no <svg> in {rel}")
            svg_cache[rel] = m.group(0) if m else ""
    return svg_cache[rel]
for f in sorted((root / "data").glob("ch*.json"), key=lambda p: int(re.sub(r"\D", "", p.stem))):
    d = json.loads(f.read_text())
    ids = set()
    for t in d["topics"]:
        if t["id"] in ids: errors.append(f"dup id {t['id']}")
        ids.add(t["id"])
        if t.get("diagram"):
            t["diagram"]["svg"] = svg_of(t["diagram"]["file"])
    d["part"] = next(v for k, v in PARTS if d["number"] <= k)
    d["diagrams"] = []  # files not needed client-side
    chapters.append(d)
blob = json.dumps(chapters, ensure_ascii=False)
for b in banned:
    if b in blob.lower(): errors.append(f"banned term in data: {b!r}")
if errors:
    print("\n".join(errors)); sys.exit(1)
(root / "js").mkdir(exist_ok=True)
(root / "js" / "data.js").write_text("window.KP_DATA=" + blob + ";\n")
n = sum(len(c["topics"]) for c in chapters)
print(f"{len(chapters)} chapters, {n} topics, {len(svg_cache)} diagrams, {len(blob)//1024} KB")
