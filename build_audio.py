#!/usr/bin/env python3
import json, glob, os, asyncio

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "walkthroughs", "audio")
os.makedirs(OUT, exist_ok=True)

import build_walkthroughs as bw
import edge_tts

VOICE = "en-US-AriaNeural"
RATE = "+0%"
CONCURRENCY = 8

async def gen_one(text, outpath, sem):
    async with sem:
        if os.path.exists(outpath):
            return
        text = text.replace("\n", " ").strip()
        if not text:
            return
        comm = edge_tts.Communicate(text, voice=VOICE, rate=RATE)
        await comm.save(outpath)

async def main_async():
    sem = asyncio.Semaphore(CONCURRENCY)
    tasks = []
    total = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "ch*.json"))):
        data = json.load(open(f))
        chnum = data["number"]
        for topic in data["topics"]:
            tid = topic["id"]
            steps, *_ = bw.build_steps(topic, chnum)
            for i, st in enumerate(steps):
                outpath = os.path.join(OUT, "%s_%d.mp3" % (tid, i))
                text = st["caption"] or st["title"]
                tasks.append(gen_one(text, outpath, sem))
                total += 1
    print("total audio files:", total)
    await asyncio.gather(*tasks)
    print("done")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()