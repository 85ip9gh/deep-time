# Deep Time Machine

One button drops you on a random moment across Earth's 4.54 billion years. A
proportional geological timeline shows where you landed, and a short scene,
composed ahead of time from a fixed set of real facts for that interval, places
you there. It is an imagined moment, never an invented fact: a scene only ever
recombines the ground truth, so there are no hallucinated statistics or citations
to get wrong.

Runtime is static. The g7 container serves two JSON files and an HTML page and
calls no model, so there is no API key on the box and nothing to rate-limit but
bandwidth.

## How it works

- `public/intervals.json` is the source of truth: 18 geological intervals, each
  with its date range, a draw weight, an accent colour, the ground-truth facts
  used to generate scenes, and a hand-written seed scene.
- `public/scenes.json` is the generated pool: `{ intervalId: [ { ma, text } ] }`.
  Ships empty; the site falls back to each interval's seed until you build it.
- The page draws an interval (weighted), then picks a random scene from that
  interval's bag and shows the scene's own date. Two weightings: **Eventful**
  (tilted toward the charismatic chapters) and **True to duration** (honest, so
  most draws land in the microbial Precambrian).

## Build the pool

`public/scenes.json` ships empty and the site falls back to seed scenes, so
building the pool is optional: it fills each interval's bag with more variety.
Both generators run offline, never ship to g7, and top each bag up to
`--per-interval` rather than starting over.

### Keyless (default, free)

No API key, no model, no network. Each scene is sampled from that interval's
fact bank in `build/beats.json`, so every sentence is a hand-written ground-truth
fact and nothing is invented. Deterministic: the same facts and count rebuild
the same pool.

```
python build/build_pool_local.py --per-interval 80
```

### With Claude (optional)

Writes each scene with Haiku from the same ground truth, a little more varied
than the templates.

```
python -m venv .venv && . .venv/bin/activate     # or .venv\Scripts\activate on Windows
pip install -r build/requirements.txt
ANTHROPIC_API_KEY=sk-... python build/build_pool.py --per-interval 80
```

`--per-interval 80` across 18 intervals is ~1,440 scenes on Haiku, roughly a few
tens of cents once. Either way, commit the resulting `public/scenes.json` so the
image builds and deploys without a key.

## Run locally

`fetch` needs HTTP, not `file://`:

```
python -m http.server 8099 --directory public
```

Then open http://localhost:8099.

## Deploy to g7

Same pattern as the other `apps`-namespace tenants: build on the node, import
into containerd, apply the manifests.

```
docker build -t deep-time:g7 .
docker save deep-time:g7 | sudo k3s ctr images import -
kubectl apply -f deploy/k8s/
```

Point a DNS name at the cloudflared tunnel and set it as the host in
`deploy/k8s/ingress.yaml` (currently `deeptime.pesanth.com`). To refresh the
scenes, rebuild the pool, rebuild and re-import the image, and restart the
rollout (`kubectl -n apps rollout restart deploy/deep-time`).

## Layout

```
public/
  index.html         static site, fetches the two JSON files
  intervals.json     source of truth (facts, weights, accents, seeds)
  scenes.json        generated pool (commit once built)
build/
  build_pool_local.py  keyless generator (default, samples beats.json)
  beats.json           fact banks for the keyless generator
  build_pool.py        offline generator using Claude (needs a key)
  prompt.py            the shared scene prompt and model id
  requirements.txt
deploy/
  nginx.conf         non-root, read-only, listens on 8080
  k8s/               namespace, deployment, service, ingress, middleware, networkpolicy
Dockerfile
```
