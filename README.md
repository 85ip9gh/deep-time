# Deep Time Machine

One button drops you on a random moment across Earth's 4.54 billion years. A
proportional geological timeline shows where you landed, and a short scene,
composed in your browser from a fixed set of real facts for that interval, places
you there. It is an imagined moment, never an invented fact: a scene only ever
recombines the ground truth, so there are no hallucinated statistics or citations
to get wrong.

Runtime is static and keyless. The g7 container serves an HTML page and two JSON
files and calls no model, so there is no API key on the box and nothing to
rate-limit but bandwidth. Scenes are generated in the browser, on demand, one per
button press, so the variety is effectively endless.

## How it works

- `public/intervals.json` is the source of truth: 18 geological intervals, each
  with its date range, a draw weight, an accent colour, and a hand-written seed
  scene.
- `public/beats.json` is the fact base: for each interval, a bag of short
  hand-written ground-truth facts, typed by sense (sky, air, sound, life, and so
  on). About 200 in total.
- `public/index.html` draws a weighted interval, picks a random date inside it,
  then composes a scene on the spot by sampling a varied subset of that interval's
  facts and ordering them from sky to ground to life. Every sentence is a fact
  from `beats.json`, so nothing is invented and no two draws are quite the same.
  If `beats.json` fails to load it falls back to the interval's seed scene.
- Two weightings: **Eventful** (tilted toward the charismatic chapters) and
  **True to duration** (honest, so most draws land in the microbial Precambrian).

## Add or change facts

Edit `public/beats.json`. Each interval maps to a list of `[type, sentence]`
pairs, where `type` is one of sky, weather, air, smell, sound, water, land,
ground, life, moment. Add sentences to widen an interval's variety and the
generator picks them up with no build step. Keep every sentence a real,
present-tense, second-person fragment of ground truth, never an invented figure,
species, or date.

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
`deploy/k8s/ingress.yaml` (currently `deeptime.pesanth.com`). To refresh after a
change, rebuild and re-import the image, then restart the rollout
(`kubectl -n apps rollout restart deploy/deep-time`).

## Layout

```
public/
  index.html         static site, generates scenes in the browser
  intervals.json     source of truth (ranges, weights, accents, seeds)
  beats.json         the fact base the generator samples
deploy/
  nginx.conf         non-root, read-only, listens on 8080
  k8s/               namespace, deployment, service, ingress, middleware, networkpolicy
Dockerfile
```
