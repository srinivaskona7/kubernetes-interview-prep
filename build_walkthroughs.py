#!/usr/bin/env python3
import json, glob, os, html

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "walkthroughs")

# chapter -> scene labels + broken/healthy status words
SCENE = {
 1: ("container runtime", "pod/app", "CrashLoopBackOff", "Running"),
 2: ("control plane", "kube-apiserver", "NotReady", "Ready"),
 3: ("workload", "deployment/app", "Progressing", "Available"),
 4: ("scheduler", "pod/app", "Pending", "Running"),
 5: ("autoscaler", "hpa/app", "Unknown", "Healthy"),
 6: ("service mesh", "svc/app", "NoEndpoints", "HasEndpoints"),
 7: ("ingress", "ingress/app", "503", "200"),
 8: ("storage", "pvc/data", "Pending", "Bound"),
 9: ("rbac", "role/app", "Forbidden", "Allowed"),
 10: ("rollout", "deployment/app", "Progressing", "Available"),
 11: ("gitops", "application/app", "OutOfSync", "Synced"),
 12: ("operator", "crd/app", "NotEstablished", "Established"),
 13: ("cluster", "node/cp-1", "NotReady", "Ready"),
 14: ("observability", "pod/app", "NoMetrics", "Scraping"),
 15: ("backup", "volume/snap", "Failed", "Ready"),
 16: ("troubleshoot", "pod/app", "CrashLoopBackOff", "Running"),
 17: ("registry", "image/app", "ImagePullBackOff", "Pulled"),
 18: ("scenario", "cluster", "Degraded", "Healthy"),
}

def esc(s):
    return html.escape(str(s)) if s is not None else ""

def classify(cmd):
    c = cmd.lower()
    if any(k in c for k in [" get ", "describe ", " logs", " top ", "events", " rollout status", "auth can-i", "get "]) :
        return "diag"
    return "fix"

def sample_output(cmd):
    c = cmd.strip().lower()
    if "get pods" in c:
        return ["NAME                     READY   STATUS    RESTARTS   AGE",
                "app-7d9f4b6c8-x2kpq      1/1     Running   0          2m",
                "app-7d9f4b6c8-9qz1v      1/1     Running   0          2m"]
    if "get nodes" in c:
        return ["NAME       STATUS   ROLES           AGE   VERSION",
                "cp-1       Ready    control-plane   10d   v1.30.0",
                "worker-1   Ready    <none>          10d   v1.30.0",
                "worker-2   Ready    <none>          10d   v1.30.0"]
    if "get svc" in c or "get services" in c:
        return ["NAME   TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE",
                "app    ClusterIP   10.96.42.10    <none>        80/TCP    2m"]
    if "get deploy" in c:
        return ["NAME   READY   UP-TO-DATE   AVAILABLE   AGE",
                "app    2/2     2            2           2m"]
    if "get pvc" in c or "get pv" in c:
        return ["NAME   STATUS   VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE",
                "data   Bound    pv-1     10Gi       RWO            standard       2m"]
    if "get ingress" in c:
        return ["NAME   CLASS   HOSTS            ADDRESS         PORTS   AGE",
                "app    nginx   app.example.com  203.0.113.10    80      2m"]
    if "get nodes" in c:
        return ["NAME       STATUS   ROLES   AGE   VERSION", "node-1   Ready    <none>   5d   v1.30.0"]
    if "describe" in c:
        return ["Name:         app-7d9f4b6c8-x2kpq",
                "Namespace:    default",
                "Status:       Running",
                "Events:       Normal  Pulled  Successfully pulled image",
                "              Normal  Created Created container app",
                "              Normal  Started Started container app"]
    if "logs" in c:
        return ["2026-... INFO  server listening on :8080",
                "2026-... INFO  ready to accept connections"]
    if "rollout status" in c:
        return ["deployment \"app\" successfully rolled out"]
    if "rollout" in c:
        return ["deployment.apps/app rolled out"]
    if "apply" in c:
        return ["deployment.apps/app configured", "service/app unchanged"]
    if "delete" in c:
        return ["pod \"app-7d9f4b6c8-x2kpq\" deleted"]
    if "create" in c:
        return ["deployment.apps/app created"]
    if "exec" in c:
        return ["# interactive shell opened"]
    if "top " in c:
        return ["NAME                     CPU(cores)   MEMORY(bytes)",
                "app-7d9f4b6c8-x2kpq      12m          64Mi"]
    if "auth can-i" in c:
        return ["yes"]
    if c.startswith("docker "):
        return ["$ docker: command completed successfully"]
    if "helm " in c:
        return ["STATUS: deployed", "REVISION: 1"]
    if "kubectl get" in c:
        return ["NAME   READY   STATUS    RESTARTS   AGE", "app    1/1     Running   0          2m"]
    return ["# command completed"]

def broken_output(cloud, pod, broken_status):
    return [
        "NAME                     READY   STATUS             RESTARTS   AGE",
        "%-24s 0/1     %-18s 6          4m" % (pod, broken_status),
    ]

def synth_symptom(topic):
    pits = topic.get("pitfalls") or []
    if pits:
        return pits[0]
    return "A common misstep when answering '%s' leads to the failure shown." % topic["question"]

def build_steps(topic, chnum):
    cloud, pod, broken_status, healthy_status = SCENE.get(chnum, ("cluster", "pod/app", "Failing", "Healthy"))
    steps = []
    cmds = topic.get("commands") or []
    cmd_notes = {c["cmd"]: c.get("note", "") for c in cmds}
    diag_cmds = [c for c in cmds if classify(c["cmd"]) == "diag"]
    fix_cmds = [c for c in cmds if classify(c["cmd"]) == "fix"]
    # Step 1 symptom
    first_diag = diag_cmds[0]["cmd"] if diag_cmds else "kubectl get pods -A"
    steps.append({
        "title": "1. Symptom — what went wrong",
        "visual": "broken",
        "caption": synth_symptom(topic),
        "terminal": [{"type": "cmd", "text": first_diag, "note": cmd_notes.get(first_diag, "")}] + [{"type": "err", "text": t} for t in broken_output(cloud, pod, broken_status)],
    })
    # Step 2 diagnose
    if diag_cmds:
        diag_lines = []
        for c in diag_cmds[:3]:
            diag_lines.append({"type": "cmd", "text": c["cmd"], "note": c.get("note", "")})
            for ln in sample_output(c["cmd"]):
                diag_lines.append({"type": "out", "text": ln})
    else:
        diag_lines = [{"type": "cmd", "text": "kubectl describe " + pod, "note": ""}]
        for ln in sample_output("kubectl describe x"):
            diag_lines.append({"type": "out", "text": ln})
        diag_lines.append({"type": "cmd", "text": "kubectl logs " + pod + " --previous", "note": ""})
        for ln in sample_output("kubectl logs x"):
            diag_lines.append({"type": "out", "text": ln})
    # flatten nested (none now)
    diag_lines = [x for x in diag_lines]
    steps.append({
        "title": "2. Diagnose — inspect evidence",
        "visual": "diagnose",
        "caption": (topic.get("explain") or ["Inspect the failing resource and its events/logs."])[0],
        "terminal": diag_lines,
    })
    # Step 3 fix
    if fix_cmds:
        fix_lines = []
        for c in fix_cmds[:4]:
            fix_lines.append({"type": "cmd", "text": c["cmd"], "note": c.get("note", "")})
            for ln in sample_output(c["cmd"]):
                fix_lines.append({"type": "out", "text": ln})
    else:
        fc = "kubectl rollout restart deployment/app"
        fix_lines = [{"type": "cmd", "text": fc, "note": ""}] + [{"type": "out", "text": ln} for ln in sample_output(fc)]
    steps.append({
        "title": "3. Fix — apply the change",
        "visual": "fix",
        "caption": (topic.get("key_points") or ["Apply the smallest correct change, then verify."])[0],
        "terminal": fix_lines,
    })
    # Step 4 verify: prefer a topic command that checks status, else a relevant get
    verify_cmd = "kubectl get pods -A"
    for c in (topic.get("commands") or []):
        cl = c["cmd"].lower()
        if "get " in cl or "status" in cl or "rollout status" in cl:
            verify_cmd = c["cmd"]; break
    steps.append({
        "title": "4. Verify — confirm recovery",
        "visual": "healthy",
        "caption": topic.get("say_first") or "Confirm the workload returns to a healthy state.",
        "terminal": [{"type": "cmd", "text": verify_cmd, "note": cmd_notes.get(verify_cmd, "")}] + [{"type": "out", "text": ln.replace(broken_status, healthy_status) if broken_status in ln else ln} for ln in sample_output(verify_cmd)],
    })
    # diagram svg for concept-accurate visual
    diag_svg = ""
    d = topic.get("diagram")
    if d and d.get("file"):
        dp = os.path.join(ROOT, d["file"])
        if os.path.exists(dp):
            import re as _re
            m = _re.search(r"<svg\b.*?</svg>", open(dp).read(), _re.S)
            if m: diag_svg = m.group(0)
    return steps, cloud, pod, broken_status, healthy_status, diag_svg

def li_items(items):
    return "".join("<li>" + esc(x) + "</li>" for x in items)

def build_index(entries, studied_ids):
    entries = sorted(entries, key=lambda e: e[0])
    rows = ""
    cur = None
    for chnum, tid, title, level in entries:
        if chnum != cur:
            if cur is not None:
                rows += "</ul>"
            cur = chnum
            rows += "<h2>Chapter %d</h2><ul class='list'>" % chnum
        rows += ("<li><a href='%s.html' data-id='%s'>%s</a> <span class='lvl %s'>%s</span> <span class='chk' data-id='%s'></span></li>"
                 % (tid, tid, esc(title), level, level, tid))
    rows += "</ul>"
    return ("<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>KubePrep walkthroughs</title>"
            "<link href='https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap' rel='stylesheet'>"
            "<style>*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}body{background:#0b0f14;color:#e6edf3;font-family:Inter,system-ui,sans-serif;padding:24px;max-width:960px;margin:0 auto}"
            "a{color:#58a6ff;text-decoration:none}h1{font-family:'Space Grotesk',sans-serif;margin-bottom:8px}h2{margin:24px 0 8px;font-size:18px;color:#ff7a45}"
            "input#q{width:100%;padding:10px 12px;background:#111722;border:1px solid #21262d;border-radius:8px;color:#e6edf3;font-family:Inter,sans-serif;margin:12px 0 8px}"
            "ul.list{list-style:none;padding:0}ul.list li{padding:8px 12px;border-bottom:1px solid #21262d;display:flex;justify-content:space-between;gap:12px;align-items:center}"
            "span.lvl{font-family:'JetBrains Mono',monospace;font-size:11px;color:#8b949e}span.lvl.junior{color:#3fb950}span.lvl.mid{color:#d29922}span.lvl.senior{color:#a371f7}"
            ".chk{font-size:12px;color:#3fb950;min-width:16px;text-align:right}"
            ".top{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;flex-wrap:wrap;gap:8px}a.back{font-family:'JetBrains Mono',monospace;font-size:12px;color:#8b949e}"
            ".stats{color:#8b949e;font-family:'JetBrains Mono',monospace;font-size:12px;margin-bottom:8px}"
            "</style></head><body><div class='top'><h1>Walkthroughs</h1><a class='back' href='../index.html'>← guide</a></div>"
            "<p style='color:#8b949e;font-size:13px'>One animated walkthrough per question: symptom, diagnosis, fix, verification.</p>"
            "<div class='stats' id='stats'></div>"
            "<input id='q' type='search' placeholder='Filter questions…'>"
            + rows + "<script>"
            "const KEY='kp_walkthroughs_studied';"
            "function studied(){try{return JSON.parse(localStorage.getItem(KEY)||'[]')}catch(e){return []}}"
            "function paint(){const s=new Set(studied());document.querySelectorAll('.chk').forEach(el=>{el.textContent=s.has(el.dataset.id)?'✓':''});"
            "const tot=document.querySelectorAll('ul.list li').length; document.getElementById('stats').textContent=studied().length+'/'+tot+' studied';}"
            "document.getElementById('q').addEventListener('input',e=>{const v=e.target.value.toLowerCase();"
            "document.querySelectorAll('ul.list li').forEach(li=>{li.style.display=li.textContent.toLowerCase().includes(v)?'':'none'});});"
            "paint();</script></body></html>")

TEMPLATE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ — KubePrep walkthrough</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
 --paper:#0b0f14; --panel:#111722; --panel2:#161e2b; --ink:#e6edf3; --muted:#8b949e; --accent:#ff7a45; --green:#3fb950; --red:#f85149; --blue:#58a6ff; --border:#21262d;
 --sans:'Inter',system-ui,sans-serif; --display:'Space Grotesk',system-ui,sans-serif; --mono:'JetBrains Mono',ui-monospace,monospace;
}
html,body{background:var(--paper);color:var(--ink);font-family:var(--sans);min-height:100vh}
a{color:var(--blue);text-decoration:none}
.top{position:sticky;top:0;z-index:10;background:rgba(11,15,20,.85);backdrop-filter:blur(8px);border-bottom:1px solid var(--border)}
.top .wrap{max-width:1280px;margin:0 auto;padding:14px 24px;display:flex;align-items:center;gap:16px}
.brand{font-family:var(--display);font-weight:700;color:var(--ink);letter-spacing:-.02em}
.brand span{color:var(--accent)}
.back{margin-left:auto;font-family:var(--mono);font-size:12px;color:var(--muted)}
.wrap{max-width:1280px;margin:0 auto;padding:24px}
.hero{padding:8px 0 20px}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);margin-bottom:8px}
h1{font-family:var(--display);font-size:clamp(1.4rem,2.4vw+1rem,2rem);font-weight:600;letter-spacing:-.02em;line-height:1.2;margin-bottom:10px}
.meta{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}
.badge{font-family:var(--mono);font-size:11px;padding:4px 10px;border-radius:999px;border:1px solid var(--border);color:var(--muted)}
.badge.lvl-junior{border-color:#2ea043;color:#3fb950}
.badge.lvl-mid{border-color:#9e6a03;color:#d29922}
.badge.lvl-senior{border-color:#a371f7;color:#a371f7}
.sayfirst{background:var(--panel);border:1px solid var(--border);border-left:3px solid var(--accent);padding:14px 16px;border-radius:8px;margin-bottom:20px}
.sayfirst .label{font-family:var(--mono);font-size:10px;letter-spacing:.18em;text-transform:uppercase;color:var(--accent);margin-bottom:6px}
.sayfirst p{line-height:1.55}
.stage{display:grid;grid-template-columns:1.1fr 1fr;gap:16px;margin-bottom:20px}
@media(max-width:900px){.stage{grid-template-columns:1fr}}
.card{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:16px}
.card h3{font-family:var(--display);font-size:13px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-bottom:12px}
.visual{min-height:260px;position:relative;display:flex;align-items:center;justify-content:center;overflow:hidden}
.diagrambox{margin-top:10px;max-height:200px;overflow:auto;border-top:1px solid var(--border);padding-top:8px;animation:fadein .5s ease both}
.diagrambox svg{width:100%;height:auto;display:block}
.diagrambox:empty{display:none}
.scene{transition:background .4s ease}
.pod{transition:all .6s ease}
.cloud{transition:all .4s ease}
.statusline{transition:color .4s ease,opacity .4s ease}
@keyframes fadein{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes pulse{0%{transform:scale(1)}50%{transform:scale(1.08)}100%{transform:scale(1)}}
.scene.healthy .pod{animation:pulse .6s ease}
/* reduced motion */
@media (prefers-reduced-motion: reduce){
  *,*::before,*::after{animation-duration:.01ms !important;animation-iteration-count:1 !important;transition-duration:.01ms !important}
  .tline{animation:none !important;opacity:1 !important}
}
/* fullscreen stage */
body.fs .wrap{max-width:100%;padding:8px}
body.fs .stage{grid-template-columns:1fr 1fr}
body.fs .scene{height:360px}
body.fs .diagrambox{max-height:300px}
body.light{--paper:#f6f8fa;--panel:#ffffff;--panel2:#f0f2f5;--ink:#24292f;--muted:#57606a;--accent:#d94a1a;--green:#1a7f37;--red:#cf222e;--blue:#0969da;--border:#d0d7de}
.scene{position:relative;width:100%;height:260px}
.cloud{position:absolute;top:20px;left:50%;transform:translateX(-50%);width:220px;height:90px;border:2px solid var(--blue);border-radius:12px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:4px;background:rgba(88,166,255,.06)}
.cloud .t{font-family:var(--mono);font-size:12px;color:var(--blue)}
.pod{position:absolute;bottom:30px;left:50%;transform:translateX(-50%);width:160px;height:70px;border:2px solid var(--muted);border-radius:10px;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:4px;background:rgba(139,148,158,.06);transition:all .6s}
.pod .t{font-family:var(--mono);font-size:12px}
.pod .s{font-size:11px;color:var(--muted)}
.scene.broken .pod{border-color:var(--red);background:rgba(248,81,73,.1)}
.scene.broken .pod .s{color:var(--red)}
.scene.broken .pod::after{content:"✕";position:absolute;top:-14px;right:-14px;width:28px;height:28px;border-radius:50%;background:var(--red);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700}
.scene.diagnose .pod{border-color:var(--blue);background:rgba(88,166,255,.1)}
.scene.fix .pod{border-color:var(--accent);background:rgba(255,122,69,.1)}
.scene.healthy .pod{border-color:var(--green);background:rgba(63,185,80,.1)}
.scene.healthy .pod .s{color:var(--green)}
.scene.healthy .pod::after{content:"✓";position:absolute;top:-14px;right:-14px;width:28px;height:28px;border-radius:50%;background:var(--green);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700}
.statusline{position:absolute;bottom:6px;left:50%;transform:translateX(-50%);font-family:var(--mono);font-size:11px;color:var(--muted)}
.scene.broken .statusline{color:var(--red)}
.scene.healthy .statusline{color:var(--green)}
.terminal{background:#0d1117;border:1px solid var(--border);border-radius:8px;font-family:var(--mono);font-size:12.5px;overflow:hidden}
.terminal .bar{background:#161b22;padding:8px 12px;display:flex;gap:6px;align-items:center;border-bottom:1px solid var(--border)}
.dot{width:10px;height:10px;border-radius:50%;background:#30363d}
.dot.r{background:#f85149}.dot.y{background:#d29922}.dot.g{background:#3fb950}
.terminal .body{padding:12px;min-height:220px;max-height:320px;overflow:auto;line-height:1.6}
.tline{opacity:0;animation:typeline .5s steps(30,end) forwards}
.tline.cmd{color:var(--blue)}
.tline.cmd::before{content:"$ ";color:var(--accent)}
.tline.out{color:#c9d1d9}
.tline.err{color:var(--red)}
.tnote{font-family:var(--sans);font-size:11px;color:var(--muted);padding:0 0 6px 14px;font-style:italic;opacity:0;animation:fadeIn .35s ease forwards}
@keyframes typeline{from{clip-path:inset(0 100% 0 0);opacity:1}to{clip-path:inset(0 0 0 0);opacity:1}}
@keyframes fadeIn{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
.controls{display:flex;gap:8px;align-items:center;margin-bottom:12px;flex-wrap:wrap}
.btn{background:var(--panel2);border:1px solid var(--border);color:var(--ink);padding:7px 14px;border-radius:7px;font-family:var(--mono);font-size:12px;cursor:pointer}
.btn.primary{background:var(--accent);border-color:var(--accent);color:#fff}
.btn:hover{filter:brightness(1.15)}
.speed{margin-left:auto;display:flex;gap:6px;align-items:center;font-family:var(--mono);font-size:11px;color:var(--muted)}
.voicepick{display:flex;gap:6px;align-items:center;font-family:var(--mono);font-size:11px;color:var(--muted)}
.voicepick select,.speed select{background:var(--panel2);color:var(--ink);border:1px solid var(--border);border-radius:6px;padding:2px 6px;font-family:var(--mono);font-size:11px}
.caption{line-height:1.6}
.caption .w{display:inline-block;padding:0 1px;border-radius:3px;transition:background .12s,color .12s}
.caption .w.active{background:rgba(255,122,69,.25);color:var(--accent);font-weight:600}
select{background:var(--panel2);color:var(--ink);border:1px solid var(--border);border-radius:6px;padding:4px 8px;font-family:var(--mono);font-size:11px}
.progress{height:4px;background:var(--border);border-radius:2px;overflow:hidden;margin-bottom:12px}
.progress .bar{height:100%;background:var(--accent);transition:width .4s}
.stepinfo{font-family:var(--mono);font-size:12px;color:var(--muted);margin-bottom:8px}
.stepinfo .title{color:var(--ink);font-weight:600}
.caption{background:var(--panel2);border:1px solid var(--border);border-radius:8px;padding:12px 14px;font-size:13.5px;line-height:1.55;min-height:60px}
.subtitle{margin-top:10px;background:#000;border:1px solid var(--border);border-radius:6px;padding:10px 14px;font-size:14px;line-height:1.5;color:#fff;text-align:center;min-height:44px}
.predict{margin-top:20px;display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:900px){.predict{grid-template-columns:1fr}}
.predict .card h3{color:var(--red)}
.predict .card.fix h3{color:var(--green)}
.predict ul{list-style:none;padding:0}
.predict li{padding:6px 0;border-bottom:1px solid var(--border);font-size:13px;line-height:1.5}
.predict li:last-child{border-bottom:none}
.predict li::before{content:"• ";color:var(--muted)}
.fix li::before{content:"→ ";color:var(--green)}
.content{margin-top:20px;display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:900px){.content{grid-template-columns:1fr}}
.content .card ul{list-style:none;padding:0}
.content .card li{padding:6px 0;border-bottom:1px solid var(--border);font-size:13px;line-height:1.5}
.content .card li:last-child{border-bottom:none}
.cmds{margin-top:20px}
.cmds table{width:100%;border-collapse:collapse;font-size:13px}
.cmds th,.cmds td{padding:8px 10px;border-bottom:1px solid var(--border);text-align:left;vertical-align:top}
.cmds th{font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.cmds code{font-family:var(--mono);font-size:12px;color:var(--blue);background:rgba(88,166,255,.08);padding:2px 6px;border-radius:4px;word-break:break-all}
.cmds .note{color:var(--muted);font-size:12px}
.follow{margin-top:20px}
.follow ul{list-style:none;padding:0;display:flex;flex-wrap:wrap;gap:8px}
.follow li{background:var(--panel2);border:1px solid var(--border);padding:6px 12px;border-radius:999px;font-size:12px;color:var(--muted)}
.diagramlink{margin-top:20px;text-align:center}
.diagramlink a{display:inline-block;background:var(--panel2);border:1px solid var(--border);padding:10px 18px;border-radius:8px;font-family:var(--mono);font-size:12px}
.navrow{margin-top:20px;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
.navrow a{background:var(--panel2);border:1px solid var(--border);padding:10px 16px;border-radius:8px;font-family:var(--mono);font-size:12px;flex:1;min-width:180px;text-align:center}
.selfcheck{margin-top:20px}
.selfcheck details{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:12px 16px}
.selfcheck summary{cursor:pointer;font-family:var(--display);font-size:13px;font-weight:600;color:var(--muted)}
.selfcheck .ans{margin-top:10px;font-size:13px;line-height:1.55;color:var(--ink);border-top:1px solid var(--border);padding-top:10px}
.studiedbtn{margin-top:12px}
@media (prefers-reduced-motion: reduce){
 .tline{animation:none;opacity:1}
 .scene .pod{transition:none}
}
footer{padding:30px 24px;text-align:center;color:var(--muted);font-family:var(--mono);font-size:11px;border-top:1px solid var(--border);margin-top:40px}
.copybtn{background:transparent;border:1px solid var(--border);color:var(--muted);border-radius:4px;padding:2px 6px;font-family:var(--mono);font-size:10px;cursor:pointer;margin-left:6px}
.copybtn:hover{color:var(--ink)}
</style>
</head>
<body>
<div class="top"><div class="wrap"><a class="brand" href="../index.html">Kube<span>Prep</span></a><a class="back" href="../index.html">← back to guide</a></div></div>
<div class="wrap">
  <div class="hero">
    <p class="eyebrow">__EYEBROW__</p>
    <h1>__QUESTION__</h1>
    <div class="meta">
      <span class="badge">__CHAPTER__</span>
      <span class="badge lvl-__LEVEL__">__LEVEL__</span>
      <span class="badge">walkthrough · __N__ steps</span>
    </div>
  </div>

  <div class="sayfirst"><div class="label">Say first</div><p>__SAYFIRST__</p></div>

  <div class="stage">
    <div class="card">
      <h3>Visual state</h3>
      <div class="scene broken" id="scene">
        <div class="cloud"><span class="t" id="cloudlbl">__CLOUD__</span><span class="t" style="font-size:10px;color:var(--muted)">control plane</span></div>
        <div class="pod"><span class="t" id="podlbl">__POD__</span><span class="s" id="podstatus">__BROKEN__</span></div>
        <div class="statusline" id="statusline">state: BROKEN</div>
      </div>
      <div class="diagrambox" id="diagrambox">__DIAGRAM__</div>
    </div>
    <div class="card">
      <h3>Terminal</h3>
      <div class="controls">
        <button class="btn primary" id="playBtn">▶ Play</button>
        <button class="btn" id="prevBtn">◀ Prev</button>
        <button class="btn" id="nextBtn">Next ▶</button>
        <button class="btn" id="resetBtn">↺ Reset</button>
        <button class="btn" id="voiceBtn">🔊 Voice: on</button>
        <button class="btn" id="fsBtn" title="Fullscreen"> ( ) Fullscreen</button>
        <button class="btn" id="copyLinkBtn" title="Copy link to this step">🔗 Link</button>
        <button class="btn" id="themeBtn" title="Toggle theme"> ( ) Theme</button>
        <div class="voicepick">voice <select id="voiceSelect"><option value="edge">Edge · Aria (premium)</option></select></div>
        <div class="speed">speed <select id="speed"><option value="1">1×</option><option value="1.5">1.5×</option><option value="2">2×</option><option value="0.5">0.5×</option></select></div>
      </div>
      <div class="progress"><div class="bar" id="pbar" style="width:0%"></div></div>
      <div class="stepinfo"><span class="title" id="steptitle"></span></div>
      <div class="terminal">
        <div class="bar"><span class="dot r"></span><span class="dot y"></span><span class="dot g"></span><span style="margin-left:8px;font-size:11px;color:var(--muted)">bash</span></div>
        <div class="body" id="termbody"></div>
      </div>
      <div class="caption" id="caption"></div>
      <div class="subtitle" id="subtitle"></div>
      <div class="studiedbtn"><button class="btn" id="studiedBtn">Mark as studied</button></div>
    </div>
  </div>

  <div class="predict">
    <div class="card">
      <h3>⚠ Predicted failure</h3>
      <ul class="bad">
        __PREDICT__
      </ul>
    </div>
    <div class="card fix">
      <h3>✓ Best troubleshooting path</h3>
      <ul class="fix">
        __FIXPATH__
      </ul>
    </div>
  </div>

  <div class="content">
    <div class="card">
      <h3>Explain</h3>
      <ul>__EXPLAIN__</ul>
    </div>
    <div class="card">
      <h3>Key points</h3>
      <ul>__KEYPOINTS__</ul>
    </div>
  </div>

  __CMDS__

  __FOLLOW__

  <div class="selfcheck">
    <details>
      <summary>Self-check: can you answer a follow-up?</summary>
      <div class="ans">__SELFCHECK__</div>
    </details>
  </div>

  __DIAGRAMLINK__

  <div class="navrow">
    <a id="prevLink" href="__PREV__">← Previous</a>
    <a id="nextLink" href="__NEXT__">Next →</a>
  </div>
</div>
<footer>KubePrep · walkthrough · progress stored in your browser</footer>
<script>
const STEPS = __STEPS__;
const NAV = __NAV__;
let idx = 0;
let playing = false;
let timer = null;
const scene = document.getElementById('scene');
const termbody = document.getElementById('termbody');
const caption = document.getElementById('caption');
const steptitle = document.getElementById('steptitle');
const pbar = document.getElementById('pbar');
const podstatus = document.getElementById('podstatus');
const statusline = document.getElementById('statusline');
const voiceSelect = document.getElementById('voiceSelect');

function speed(){ return parseFloat(document.getElementById('speed').value); }

// ---- voice preference ----
function voiceOn(){ return localStorage.getItem('kp_voice')!=='off'; }
function voiceChoice(){ return localStorage.getItem('kp_voice_choice') || 'edge'; }
function setVoiceChoice(v){ localStorage.setItem('kp_voice_choice', v); }

// populate browser voices
function populateVoices(){
  if(!('speechSynthesis' in window)) return;
  const voices = window.speechSynthesis.getVoices();
  // keep existing edge option, add english voices
  const eng = voices.filter(v=>/^en/i.test(v.lang));
  // dedupe by name
  const seen=new Set(['edge']);
  eng.forEach(v=>{
    if(seen.has(v.name)) return;
    seen.add(v.name);
    const opt=document.createElement('option');
    opt.value='browser::'+v.name;
    opt.textContent=v.name + ' ('+v.lang+')';
    voiceSelect.appendChild(opt);
  });
}
if('speechSynthesis' in window){
  populateVoices();
  window.speechSynthesis.onvoiceschanged = populateVoices;
}
// restore selection
(function(){ const v=voiceChoice(); const opt=Array.from(voiceSelect.options).find(o=>o.value===v); if(opt) voiceSelect.value=v; })();

let currentAudio=null;
let currentUtterance=null;
// confetti canvas
let confettiCanvas=null, confettiCtx=null, confettiParts=[];
function ensureConfetti(){
  if(confettiCanvas) return;
  confettiCanvas=document.createElement('canvas');
  confettiCanvas.style.cssText='position:fixed;inset:0;pointer-events:none;z-index:9999';
  document.body.appendChild(confettiCanvas);
  confettiCtx=confettiCanvas.getContext('2d');
  const resize=()=>{confettiCanvas.width=innerWidth;confettiCanvas.height=innerHeight;};
  resize(); addEventListener('resize',resize);
}
function fireConfetti(){
  ensureConfetti();
  const colors=['#ff7a45','#3fb950','#58a6ff','#a371f7','#d29922'];
  for(let i=0;i<90;i++){
    confettiParts.push({x:innerWidth/2,y:innerHeight/3,vx:(Math.random()-0.5)*12,vy:Math.random()*-14-4,r:Math.random()*6+2,c:colors[Math.floor(Math.random()*colors.length)],life:0,max:80+Math.random()*40});
  }
  if(!confettiRaf) confettiRaf=requestAnimationFrame(confettiTick);
}
let confettiRaf=null;
function confettiTick(){
  if(!confettiCtx) return;
  confettiCtx.clearRect(0,0,confettiCanvas.width,confettiCanvas.height);
  confettiParts=confettiParts.filter(p=>p.life<p.max);
  confettiParts.forEach(p=>{
    p.life++; p.x+=p.vx; p.vy+=0.35; p.y+=p.vy; p.vx*=0.99;
    confettiCtx.globalAlpha=Math.max(0,1-p.life/p.max);
    confettiCtx.fillStyle=p.c;
    confettiCtx.beginPath(); confettiCtx.arc(p.x,p.y,p.r,0,Math.PI*2); confettiCtx.fill();
  });
  confettiCtx.globalAlpha=1;
  if(confettiParts.length){ confettiRaf=requestAnimationFrame(confettiTick); }
  else { confettiRaf=null; confettiCtx.clearRect(0,0,confettiCanvas.width,confettiCanvas.height); }
}
function stopAudio(){
  if(currentAudio){ currentAudio.pause(); currentAudio=null; }
  if(currentUtterance){ try{window.speechSynthesis.cancel();}catch(e){} currentUtterance=null; }
}
function clearTimer(){ if(timer){clearTimeout(timer);timer=null;} }
function advance(){ if(!playing) return; if(idx>=STEPS.length-1){ pause(); return; } renderStep(idx+1); }

// ---- word spans for premium subtitles ----
function wordsOf(text){ return (text||'').split(/\s+/).filter(Boolean); }
function renderCaption(text){
  caption.innerHTML='';
  const words=wordsOf(text);
  words.forEach((w,i)=>{
    const span=document.createElement('span');
    span.className='w';
    span.dataset.i=i;
    span.textContent=w+' ';
    caption.appendChild(span);
  });
  document.getElementById('subtitle').textContent=text;
}
function highlightWord(i){
  const spans=caption.querySelectorAll('.w');
  spans.forEach((sp,k)=>{ sp.classList.toggle('active', k===i); });
}

// estimated timing (character-weighted) for mp3 mode
function estimateWordTimes(text, duration){
  const words=wordsOf(text);
  const totalChars=words.reduce((a,w)=>a+w.length,0) || 1;
  const times=[];
  let acc=0;
  words.forEach(w=>{
    const frac=w.length/totalChars;
    const dur=frac*duration;
    times.push({start:acc, end:acc+dur});
    acc+=dur;
  });
  return times;
}

let wordTimes=null;
let rafId=null;
function stopRaf(){ if(rafId){cancelAnimationFrame(rafId);rafId=null;} }
function startKaraokeAudio(audio, text){
  wordTimes=null;
  const onMeta=()=>{
    wordTimes=estimateWordTimes(text, audio.duration||0);
  };
  if(audio.readyState>=1) onMeta();
  else audio.addEventListener('loadedmetadata', onMeta, {once:true});
  stopRaf();
  const tick=()=>{
    if(!playing || !currentAudio) return;
    const a=currentAudio;
    if(wordTimes){
      const t=a.currentTime;
      let i=wordTimes.findIndex(wt=> t>=wt.start && t<wt.end);
      if(i<0 && wordTimes.length) i=wordTimes.length-1;
      if(t>= (wordTimes[wordTimes.length-1].end||0)) i=wordTimes.length-1;
      highlightWord(i);
    }
    rafId=requestAnimationFrame(tick);
  };
  rafId=requestAnimationFrame(tick);
}

function playMp3(s){
  const a=new Audio(s.audio); currentAudio=a;
  a.onended=()=>{ if(playing) advance(); };
  a.onerror=()=>{ clearTimer(); timer=setTimeout(()=>{ if(playing) advance(); }, 4000); };
  startKaraokeAudio(a, s.caption);
  a.play().then(()=>{}).catch(()=>{ timer=setTimeout(()=>{ if(playing) advance(); }, Math.max(3500,(s.caption||'').length*55)); });
}

function playBrowserTTS(s){
  if(!('speechSynthesis' in window)){ // fallback to timer
    timer=setTimeout(()=>{ if(playing) advance(); }, Math.max(3500,(s.caption||'').length*55));
    return;
  }
  const u=new SpeechSynthesisUtterance(s.caption);
  const chosen=voiceChoice();
  if(chosen.startsWith('browser::')){
    const name=chosen.slice('browser::'.length);
    const v=window.speechSynthesis.getVoices().find(x=>x.name===name);
    if(v) u.voice=v;
  }
  u.rate=speed();
  currentUtterance=u;
  u.onboundary=(e)=>{
    if(e.name==='word' || e.charIndex!=null){
      // map charIndex to word index
      const text=s.caption;
      let idx=0, pos=0;
      const words=wordsOf(text);
      // find word containing charIndex
      let ci=e.charIndex;
      let cumulative=0;
      let wi=0;
      for(let k=0;k<words.length;k++){
        const start=text.indexOf(words[k], cumulative);
        const end=start+words[k].length;
        if(ci>=start && ci<end){ wi=k; break; }
        if(ci>=end){ wi=k; }
        cumulative=end;
      }
      highlightWord(wi);
    }
  };
  u.onend=()=>{ if(playing) advance(); };
  u.onerror=()=>{ timer=setTimeout(()=>{ if(playing) advance(); }, 4000); };
  window.speechSynthesis.speak(u);
}

function scheduleAfterRender(){
  stopAudio(); clearTimer(); stopRaf();
  if(!playing) return;
  const s=STEPS[idx];
  // reset highlight
  highlightWord(-1);
  if(!voiceOn()){
    timer=setTimeout(()=>{ if(playing) advance(); }, Math.max(3500, (s.caption||'').length*55));
    return;
  }
  const choice=voiceChoice();
  if(choice==='edge' && s.audio){
    playMp3(s);
  } else {
    playBrowserTTS(s);
  }
}

function renderStep(i){
  idx = Math.max(0, Math.min(STEPS.length-1, i));
  const s = STEPS[idx];
  scene.className = 'scene ' + s.visual;
  steptitle.textContent = s.title;
  renderCaption(s.caption);
  termbody.innerHTML = '';
  const lines = s.terminal || [];
  lines.forEach((ln, k) => {
    const d = document.createElement('div');
    d.className = 'tline ' + (ln.type||'out');
    d.textContent = ln.text;
    d.style.animationDelay = (k*0.22/speed()) + 's';
    termbody.appendChild(d);
    if(ln.note){
      const n = document.createElement('div');
      n.className = 'tnote';
      n.textContent = '↳ ' + ln.note;
      n.style.animationDelay = (k*0.22/speed()+0.1) + 's';
      termbody.appendChild(n);
    }
  });
  const statusMap = {broken:'state: BROKEN', diagnose:'state: DIAGNOSING', fix:'state: APPLYING FIX', healthy:'state: HEALTHY'};
  podstatus.textContent = s.visual==='healthy' ? '__HEALTHY__' : (s.visual==='broken' ? '__BROKEN__' : (s.visual==='diagnose' ? 'Investigating' : 'Updating'));
  statusline.textContent = statusMap[s.visual] || '';
  pbar.style.width = ((idx+1)/STEPS.length*100) + '%';
  try{ const u=new URL(location.href); u.searchParams.set('step', idx+1); history.replaceState(null,'',u); }catch(e){}
  if(s.visual==='healthy'){ setTimeout(fireConfetti, 120); }
  document.getElementById('playBtn').textContent = playing ? '⏸ Pause' : '▶ Play';
  termbody.scrollTop = termbody.scrollHeight;
  if(playing) scheduleAfterRender();
}

function play(){ playing=true; document.getElementById('playBtn').textContent='⏸ Pause'; renderStep(idx); }
function pause(){ playing=false; document.getElementById('playBtn').textContent='▶ Play'; stopAudio(); clearTimer(); stopRaf(); }

document.getElementById('playBtn').addEventListener('click',()=>{ playing?pause():play(); });
document.getElementById('prevBtn').addEventListener('click',()=>{ pause(); renderStep(idx-1); });
document.getElementById('nextBtn').addEventListener('click',()=>{ pause(); renderStep(idx+1); });
document.getElementById('resetBtn').addEventListener('click',()=>{ pause(); renderStep(0); });
document.getElementById('fsBtn').addEventListener('click',()=>{ document.body.classList.toggle('fs'); document.getElementById('fsBtn').textContent = document.body.classList.contains('fs') ? ' ( ) Exit' : ' ( ) Fullscreen'; });
document.getElementById('copyLinkBtn').addEventListener('click',()=>{ const u = new URL(location.href); u.searchParams.set('step', idx+1); navigator.clipboard.writeText(u.toString()); const b=document.getElementById('copyLinkBtn'); b.textContent='✓ copied'; setTimeout(()=>b.textContent='🔗 Link',1200); });
const voiceBtn=document.getElementById('voiceBtn');
function paintVoice(){ voiceBtn.textContent = voiceOn()?'🔊 Voice: on':'🔇 Voice: off'; }
voiceBtn.addEventListener('click',()=>{ localStorage.setItem('kp_voice', voiceOn()?'off':'on'); paintVoice(); if(playing){ pause(); play(); } });
paintVoice();

voiceSelect.addEventListener('change',()=>{ setVoiceChoice(voiceSelect.value); if(playing){ pause(); play(); } });
document.getElementById('speed').addEventListener('change',()=>{ if(playing){pause();play();} });
document.addEventListener('keydown',e=>{
  if(e.code==='Space'){e.preventDefault(); playing?pause():play();}
  if(e.code==='ArrowRight'){pause();renderStep(idx+1);}
  if(e.code==='ArrowLeft'){pause();renderStep(idx-1);}
});

// studied toggle
const KEY='kp_walkthroughs_studied';
function studied(){try{return JSON.parse(localStorage.getItem(KEY)||'[]')}catch(e){return []}}
function isStudied(){return studied().includes(NAV.id);}
function paintStudied(){const b=document.getElementById('studiedBtn'); b.textContent=isStudied()?'✓ Studied (toggle)':'Mark as studied'; b.style.borderColor=isStudied()?'#3fb950':'';}
document.getElementById('studiedBtn').addEventListener('click',()=>{
  const s=new Set(studied());
  if(s.has(NAV.id)) s.delete(NAV.id); else s.add(NAV.id);
  localStorage.setItem(KEY, JSON.stringify([...s]));
  paintStudied();
});
paintStudied();

// copy buttons
document.querySelectorAll('.copybtn').forEach(b=>{
  b.addEventListener('click',()=>{ navigator.clipboard.writeText(b.dataset.cmd); b.textContent='copied'; setTimeout(()=>b.textContent='copy',1200); });
});

// nav links
const pl=document.getElementById('prevLink'), nl=document.getElementById('nextLink');
if(!NAV.prev){ pl.style.opacity='.3'; pl.style.pointerEvents='none'; pl.textContent='← (first)'; }
else pl.href=NAV.prev+'.html';
if(!NAV.next){ nl.style.opacity='.3'; nl.style.pointerEvents='none'; nl.textContent='(last) →'; }
else nl.href=NAV.next+'.html';

// restore theme
(function(){ if(localStorage.getItem('kp_theme')==='light') document.body.classList.add('light'); })();
document.getElementById('themeBtn').addEventListener('click',()=>{ document.body.classList.toggle('light'); localStorage.setItem('kp_theme', document.body.classList.contains('light')?'light':'dark'); document.getElementById('themeBtn').textContent = document.body.classList.contains('light') ? ' ( ) Dark' : ' ( ) Theme'; });
if(document.body.classList.contains('light')) document.getElementById('themeBtn').textContent=' ( ) Dark';
(function(){ const p=new URLSearchParams(location.search); const s=parseInt(p.get('step')||'1',10); const start=Math.max(1,Math.min(STEPS.length, isNaN(s)?1:s))-1; renderStep(start); })();
</script>
</body>
</html>
'''

def main():
    os.makedirs(OUT, exist_ok=True)
    # flatten topic order for nav
    all_ids = []
    chapters = []
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "ch*.json"))):
        data = json.load(open(f))
        chapters.append(data)
        for t in data["topics"]:
            all_ids.append(t["id"])
    id_to_pos = {tid: i for i, tid in enumerate(all_ids)}

    entries = []
    count = 0
    for data in chapters:
        chnum = data["number"]
        for topic in data["topics"]:
            tid = topic["id"]
            steps, cloud, pod, broken_status, healthy_status, diag_svg = build_steps(topic, chnum)
            for i, st in enumerate(steps):
                st["audio"] = "audio/%s_%d.mp3" % (tid, i)
            predict_items = []
            pits = topic.get("pitfalls") or []
            if pits:
                for p in pits:
                    predict_items.append("Pitfall: " + p)
            else:
                predict_items.append("Symptom: " + synth_symptom(topic))
            predict_items.append("If ignored, this surfaces as: " + broken_status + ".")
            fix_items = []
            fix_items.append("Reproduce with the diagnostic command (step 1-2).")
            for e in (topic.get("explain") or [])[:3]:
                fix_items.append(e)
            fix_items.append("Apply the fix command (step 3), then verify (step 4).")
            fix_items.append("Confirm status becomes " + healthy_status + ".")
            explain_items = topic.get("explain") or []
            kp = topic.get("key_points") or []
            cmds = topic.get("commands") or []
            if cmds:
                rows = "".join(
                    "<tr><td><code>" + esc(c["cmd"]) + "</code><button class='copybtn' data-cmd='" + esc(c["cmd"]) + "'>copy</button></td><td class='note'>" + esc(c.get("note", "")) + "</td></tr>"
                    for c in cmds
                )
                cmds_html = ("<div class='cmds card'><h3>Commands</h3><table><thead><tr><th>Command</th><th>What it shows</th></tr></thead><tbody>" + rows + "</tbody></table></div>")
            else:
                cmds_html = ""
            fu = topic.get("follow_ups") or []
            if fu:
                follow_html = ("<div class='follow card'><h3>Follow-ups</h3><ul>" + "".join("<li>" + esc(x) + "</li>" for x in fu) + "</ul></div>")
            else:
                follow_html = ""
            diag = topic.get("diagram")
            if diag:
                dfile = diag.get("file", "")
                dtitle = diag.get("title", "diagram")
                diag_html = ("<div class='diagramlink'><a href='../" + esc(dfile) + "'>Open diagram: " + esc(dtitle) + " ↗</a></div>")
            else:
                diag_html = ""
            eyebrow = "Chapter %d · %s · %s" % (chnum, data["title"], topic["level"].upper())
            title = topic["question"]
            selfcheck = (fu[0] if fu else "How would you verify the fix in production?") + " — " + (topic.get("say_first") or "")
            # nav
            pos = id_to_pos[tid]
            prev_id = all_ids[pos-1] if pos > 0 else None
            next_id = all_ids[pos+1] if pos < len(all_ids)-1 else None
            nav = {"id": tid, "prev": prev_id, "next": next_id}

            out_html = (TEMPLATE
                .replace("__TITLE__", esc(title))
                .replace("__EYEBROW__", esc(eyebrow))
                .replace("__QUESTION__", esc(title))
                .replace("__CHAPTER__", "Chapter %d" % chnum)
                .replace("__LEVEL__", topic["level"])
                .replace("__N__", str(len(steps)))
                .replace("__SAYFIRST__", esc(topic.get("say_first", "")))
                .replace("__PREDICT__", li_items(predict_items))
                .replace("__FIXPATH__", li_items(fix_items))
                .replace("__EXPLAIN__", li_items(explain_items))
                .replace("__KEYPOINTS__", li_items(kp))
                .replace("__CMDS__", cmds_html)
                .replace("__FOLLOW__", follow_html)
                .replace("__DIAGRAMLINK__", diag_html)
                .replace("__SELFCHECK__", esc(selfcheck))
                .replace("__CLOUD__", esc(cloud))
                .replace("__POD__", esc(pod))
                .replace("__BROKEN__", esc(broken_status))
                .replace("__HEALTHY__", esc(healthy_status))
                .replace("__DIAGRAM__", diag_svg if diag_svg else "")
                .replace("__PREV__", prev_id or "")
                .replace("__NEXT__", next_id or "")
                .replace("__STEPS__", json.dumps(steps))
                .replace("__NAV__", json.dumps(nav))
            )
            out_html = out_html.replace("lvl-__LEVEL__", "lvl-" + topic["level"])
            out_html = out_html.replace("__LEVEL__", topic["level"])
            out_path = os.path.join(OUT, tid + ".html")
            with open(out_path, "w") as fh:
                fh.write(out_html)
            count += 1
            entries.append((chnum, tid, title, topic["level"]))

    idx_html = build_index(entries, set())
    with open(os.path.join(OUT, "index.html"), "w") as fh:
        fh.write(idx_html)
    print("generated", count, "walkthroughs")

if __name__ == "__main__":
    main()
