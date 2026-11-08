#!/usr/bin/env python3
import json, glob, os, subprocess, tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "walkthroughs", "audio")
os.makedirs(OUT, exist_ok=True)

import build_walkthroughs as bw

VOICE = "Samantha"
RATE = 185

def tts(text, outpath):
    if os.path.exists(outpath):
        return
    # write text to temp file
    fd, txtpath = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(fd, "w") as f:
        f.write(text)
    aiff = outpath.replace(".mp3", ".aiff")
    try:
        subprocess.run(["say", "-v", VOICE, "-r", str(RATE), "-f", txtpath, "-o", aiff],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["ffmpeg", "-y", "-i", aiff, "-q:a", "4", outpath],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        for p in (txtpath, aiff):
            try: os.remove(p)
            except OSError: pass

def main():
    count = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "ch*.json"))):
        data = json.load(open(f))
        chnum = data["number"]
        for topic in data["topics"]:
            tid = topic["id"]
            steps, *_ = bw.build_steps(topic, chnum)
            for i, st in enumerate(steps):
                outpath = os.path.join(OUT, "%s_%d.mp3" % (tid, i))
                text = st["caption"]
                # make TTS-friendly: strip weird
                text = text.replace("\n", " ").strip()
                if not text:
                    text = st["title"]
                tts(text, outpath)
                count += 1
                if count % 25 == 0:
                    print("done", count)
    print("total audio files:", count)

if __name__ == "__main__":
    main()
