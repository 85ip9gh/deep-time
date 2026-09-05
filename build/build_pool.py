"""Generate the static scene pool that the site serves.

This is the only part of Deep Time that ever needs an Anthropic API key. It runs
offline, writes public/scenes.json, and then has nothing more to do: the g7
container serves that file and calls no model. Re-running tops each interval's
bag up to the target count rather than starting over, so growing the pool is
cheap and interruptible.

    ANTHROPIC_API_KEY=... python build/build_pool.py --per-interval 80

Every scene is tied to the exact date it was written for, so the site shows a
scene's own date rather than pairing a fresh random date with unrelated prose.
"""

import argparse
import json
import os
import random
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from anthropic import Anthropic

from prompt import MODEL, build_prompt

PUBLIC = Path(__file__).resolve().parent.parent / "public"
INTERVALS_PATH = PUBLIC / "intervals.json"
POOL_PATH = PUBLIC / "scenes.json"


def load_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return default


def random_ma(interval):
    span = interval["startMa"] - interval["endMa"]
    return round(interval["endMa"] + random.random() * span, 4)


def one_scene(client, interval):
    ma = random_ma(interval)
    message = client.messages.create(
        model=MODEL,
        max_tokens=320,
        messages=[{"role": "user", "content": build_prompt(interval, ma)}],
    )
    text = "".join(block.text for block in message.content if block.type == "text").strip()
    return {"ma": ma, "text": text}


def main():
    parser = argparse.ArgumentParser(description="Generate the Deep Time scene pool.")
    parser.add_argument("--per-interval", type=int, default=80,
                        help="target number of scenes per interval (default 80)")
    parser.add_argument("--workers", type=int, default=8,
                        help="concurrent API calls (default 8)")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY is not set. It is read only here and never ships to g7.")

    intervals = load_json(INTERVALS_PATH, None)
    if not intervals:
        sys.exit("Could not read %s" % INTERVALS_PATH)

    pool = load_json(POOL_PATH, {})

    # Each missing slot in an interval's bag becomes one job. Re-running after a
    # partial pool only fills the gaps.
    jobs = []
    for interval in intervals:
        have = len(pool.get(interval["id"], []))
        jobs += [interval] * max(0, args.per_interval - have)

    if not jobs:
        print("Pool already full at %d per interval." % args.per_interval)
        return

    random.shuffle(jobs)
    print("Generating %d scenes with %s ..." % (len(jobs), MODEL))

    client = Anthropic()
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool_ex:
        futures = {pool_ex.submit(one_scene, client, iv): iv for iv in jobs}
        # scenes.json is written only here, on the main thread, so the workers
        # never race on the file.
        for future in as_completed(futures):
            interval = futures[future]
            try:
                scene = future.result()
            except Exception as err:
                print("  skip %s: %s" % (interval["id"], err), file=sys.stderr)
                continue
            pool.setdefault(interval["id"], []).append(scene)
            done += 1
            if done % 25 == 0:
                POOL_PATH.write_text(json.dumps(pool, ensure_ascii=False), encoding="utf-8")
                print("  %d / %d" % (done, len(jobs)))

    POOL_PATH.write_text(json.dumps(pool, ensure_ascii=False), encoding="utf-8")
    total = sum(len(v) for v in pool.values())
    print("Wrote %s (%d scenes across %d intervals)." % (POOL_PATH, total, len(pool)))


if __name__ == "__main__":
    main()
