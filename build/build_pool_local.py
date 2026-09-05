"""Keyless scene-pool generator: no API key, no model, no network.

Composes each scene by sampling an interval's fact bank in build/beats.json, so
every sentence is a hand-written ground-truth fact and nothing is invented. The
output matches build_pool.py exactly (public/scenes.json as
{ intervalId: [ { ma, text } ] }), it is deterministic, and re-running only
fills each bag up to --per-interval.

    python build/build_pool_local.py --per-interval 80
"""
import argparse
import json
import random
import zlib
from pathlib import Path

BUILD = Path(__file__).resolve().parent
PUBLIC = BUILD.parent / "public"
INTERVALS_PATH = PUBLIC / "intervals.json"
BEATS_PATH = BUILD / "beats.json"
POOL_PATH = PUBLIC / "scenes.json"

ORDER = ["sky", "weather", "air", "smell", "sound", "water", "land", "ground", "life", "moment"]
AMBIANCE = ["sky", "weather", "air", "smell", "sound"]
PLACE = ["water", "land", "ground"]
FILL = ["life", "moment", "water", "land", "ground", "sound", "smell", "air", "weather", "sky"]
OPENERS = [
    "You open your eyes, and you are here.",
    "You are here, and it is real.",
    "You are standing in it.",
    "You have arrived.",
]


def load_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return default


def random_ma(interval, rng):
    span = interval["startMa"] - interval["endMa"]
    return round(interval["endMa"] + rng.random() * span, 4)


def compose(bank, rng):
    by = {}
    for kind, sentence in bank:
        by.setdefault(kind, []).append(sentence)

    chosen = []
    used = set()

    def add(kind, sentence):
        if sentence not in used:
            used.add(sentence)
            chosen.append((kind, sentence))

    def take(kinds, count):
        avail = [k for k in kinds if by.get(k)]
        rng.shuffle(avail)
        for kind in avail[:count]:
            add(kind, rng.choice(by[kind]))

    take(AMBIANCE, rng.choice([2, 3, 3]))
    take(PLACE, rng.choice([1, 2]))
    life = list(by.get("life", []))
    rng.shuffle(life)
    for sentence in life[:2]:
        add("life", sentence)
    if by.get("moment") and rng.random() < 0.65:
        add("moment", rng.choice(by["moment"]))

    def words():
        return sum(len(sentence.split()) for _, sentence in chosen)

    guard = 0
    step = 0
    while words() < 70 and guard < 60:
        guard += 1
        kind = FILL[step % len(FILL)]
        step += 1
        fresh = [s for s in by.get(kind, []) if s not in used]
        if fresh:
            add(kind, rng.choice(fresh))

    chosen.sort(key=lambda pair: ORDER.index(pair[0]))
    text = " ".join(sentence for _, sentence in chosen)
    if rng.random() < 0.3:
        text = rng.choice(OPENERS) + " " + text
    return text


def main():
    parser = argparse.ArgumentParser(description="Generate the Deep Time scene pool with no API key.")
    parser.add_argument("--per-interval", type=int, default=80,
                        help="target number of scenes per interval (default 80)")
    parser.add_argument("--seed", type=int, default=0,
                        help="base seed for a reproducible pool (default 0)")
    args = parser.parse_args()

    intervals = load_json(INTERVALS_PATH, None)
    beats = load_json(BEATS_PATH, None)
    if not intervals:
        raise SystemExit("Could not read %s" % INTERVALS_PATH)
    if not beats:
        raise SystemExit("Could not read %s" % BEATS_PATH)

    pool = load_json(POOL_PATH, {})
    total = 0
    for interval in intervals:
        bank = beats.get(interval["id"])
        if not bank:
            continue
        have = pool.get(interval["id"], [])
        seen = set(scene["text"] for scene in have)
        base = zlib.crc32(interval["id"].encode("utf-8")) ^ (args.seed & 0xFFFFFFFF)
        index = len(have)
        while len(have) < args.per_interval:
            text = None
            for attempt in range(12):
                rng = random.Random(base + index * 2654435761 + attempt * 40503)
                text = compose(bank, rng)
                if text not in seen:
                    break
            seen.add(text)
            marng = random.Random(base + index * 40503 + 7)
            have.append({"ma": random_ma(interval, marng), "text": text})
            index += 1
        pool[interval["id"]] = have
        total += len(have)

    POOL_PATH.write_text(json.dumps(pool, ensure_ascii=False), encoding="utf-8")
    print("Wrote %s (%d scenes across %d intervals)." % (POOL_PATH, total, len(pool)))


if __name__ == "__main__":
    main()
