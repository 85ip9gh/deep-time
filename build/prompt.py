"""The scene prompt, shared by every generator run.

Kept in its own module so the wording that the whole pool depends on lives in
exactly one place. The model is only ever asked to render facts it is handed,
never to recall them, which is the whole defence against the invented-statistic
problem that sank the site this project reacts to.
"""

MODEL = "claude-haiku-4-5-20251001"

# Order fixes how the ground-truth block reads to the model. Missing keys are
# skipped rather than emitted blank, so an interval that has no sky line simply
# does not mention one.
_FIELDS = [
    ("sky", "Sky"),
    ("air", "Air"),
    ("climate", "Climate"),
    ("sea", "Sea"),
    ("land", "Land"),
    ("life", "Life"),
]


def format_ma(ma):
    """Match the frontend's readout exactly so a built scene and a live draw
    of the same date describe themselves the same way."""
    if ma >= 1000:
        return "%.2f Ga" % (ma / 1000)
    if ma >= 100:
        return "%d Ma" % round(ma)
    if ma >= 1:
        return "%.1f Ma" % ma
    years = ma * 1e6
    step = 1e4 if years >= 1e5 else 1e3 if years >= 1e4 else 100
    years = max(step, round(years / step) * step)
    return "{:,} years ago".format(int(years))


def build_prompt(interval, ma):
    facts = interval.get("facts", {})
    lines = "".join(
        "%s: %s\n" % (label, facts[key]) for key, label in _FIELDS if facts.get(key)
    )
    return (
        "Render one real moment in Earth's deep past as an immersive snapshot, using ONLY "
        "the ground truth below. Invent no species, numbers, place names, or dates that are "
        "not given.\n\n"
        "MOMENT: %s, during the %s (%s).\n"
        "GROUND TRUTH:\n%s\n"
        "Write 70 to 100 words. Present tense, second person, beginning with the reader "
        "already there (for example \"You stand...\"). Sensory, specific, grounded. No title, "
        "no preamble, no dates or figures beyond those given, no modern references unless "
        "they appear above. Do not end on a lesson or moral. This is an imagined but "
        "scientifically plausible scene."
    ) % (format_ma(ma), interval["name"], interval["eon"], lines)
