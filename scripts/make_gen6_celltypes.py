"""Write data/gen6_phaseA_celltypes.json: the cell-type lists that define the gen-6 phase A edge cuts.

    python scripts/make_gen6_celltypes.py <explorer_repo>

<explorer_repo> is a clone of github.com/reiserlab/celltype-explorer-drosophila-male-cns. Its types.html is the
public MaleCNS Cell Type Explorer catalogue; each type card carries the MaleCNS `class` as data-class.
data/neurons.parquet has no class column, so phase A defines "AL PN", "AL local neuron" and "Kenyon cell" by type,
from this catalogue (docs/gen6_phaseA_DRAFT.md, B2). The output records the source commit, the sha256 of
types.html and the extraction rule, so the list can be rebuilt and checked. Run once, before registering; the
phase A registration records the JSON's sha256 and the run refuses a different file.
"""
import hashlib
import html
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "gen6_phaseA_celltypes.json"
CLASSES = ("ALPN", "ALLN", "Kenyon_Cell")
CARD = re.compile(r'<div class="neuron-card-wrapper[^"]*"([^>]*)>.*?class=neuron-name-link href=types/[^ >]+\.html>'
                  r'([^<]+)</a>', re.S)
CLASS_ATTR = re.compile(r'data-class=("[^"]*"|[^\s>]*)')


def main(repo):
    repo = Path(repo)
    page = repo / "types.html"
    if not page.exists():
        raise SystemExit(f"[celltypes] {page} not found: pass a clone of the Cell Type Explorer repository")
    raw = page.read_bytes()
    commit = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    when = subprocess.run(["git", "-C", str(repo), "log", "-1", "--format=%cI"], capture_output=True, text=True).stdout.strip()
    lists = {c: set() for c in CLASSES}
    n_cards = 0
    for attrs, name in CARD.findall(raw.decode("utf-8")):
        n_cards += 1
        m = CLASS_ATTR.search(attrs)
        cls = html.unescape(m.group(1).strip('"')) if m else ""
        if cls in lists:
            lists[cls].add(html.unescape(name).strip())
    if not all(lists.values()):
        raise SystemExit(f"[celltypes] a class came out empty: { {c: len(v) for c, v in lists.items()} }")
    rec = dict(
        purpose="gen-6 phase A edge cuts (docs/gen6_phaseA_DRAFT.md, B2): AL PN = type in ALPN; AL local neuron = "
                "type in ALLN; Kenyon cell = type in Kenyon_Cell",
        source=dict(repository="https://github.com/reiserlab/celltype-explorer-drosophila-male-cns", commit=commit,
                    commit_date=when, file="types.html", sha256=hashlib.sha256(raw).hexdigest(), type_cards=n_cards),
        rule=("every type card in types.html whose data-class attribute is exactly the class name; type name = the "
              "card's neuron-name-link text, HTML-unescaped (scripts/make_gen6_celltypes.py)"),
        classes={c: sorted(v) for c, v in lists.items()},
        counts={c: len(v) for c, v in lists.items()})
    OUT.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
    print(f"[celltypes] {OUT.relative_to(ROOT)}: " + ", ".join(f"{c} {len(v)}" for c, v in lists.items())
          + f" (from {n_cards} cards, commit {commit[:10]})")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
