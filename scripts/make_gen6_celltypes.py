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
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "gen6_phaseA_celltypes.json"
CLASSES = ("ALPN", "ALLN", "Kenyon_Cell")


class _Cards(HTMLParser):
    """Every type card: its data-class and its type name. The name is taken from the card's
    neuron-name-link href (types/<name>.html), because the link text truncates long names with an ellipsis
    and some cards quote the href; a card without that href falls back to the link text."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cards, self._cls, self._in_link, self._text = [], None, False, ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "div" and "neuron-card-wrapper" in (a.get("class") or ""):
            self._cls = a.get("data-class") or ""
            self.cards.append(dict(cls=self._cls, name=None, text=None))
        elif tag == "a" and "neuron-name-link" in (a.get("class") or "").split() and self.cards:
            href = a.get("href") or ""
            m = re.match(r"^types/(.+)\.html$", href)
            if m:
                self.cards[-1]["name"] = unquote(m.group(1))
            self._in_link, self._text = True, ""

    def handle_data(self, data):
        if self._in_link:
            self._text += data

    def handle_endtag(self, tag):
        if tag == "a" and self._in_link:
            self._in_link = False
            if self.cards and self.cards[-1]["text"] is None:
                self.cards[-1]["text"] = self._text.strip()


def main(repo):
    repo = Path(repo)
    page = repo / "types.html"
    if not page.exists():
        raise SystemExit(f"[celltypes] {page} not found: pass a clone of the Cell Type Explorer repository")
    raw = page.read_bytes()
    commit = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    when = subprocess.run(["git", "-C", str(repo), "log", "-1", "--format=%cI"], capture_output=True, text=True).stdout.strip()
    parser = _Cards()
    parser.feed(raw.decode("utf-8"))
    lists = {c: set() for c in CLASSES}
    n_cards, from_text, truncated = len(parser.cards), 0, []
    for c in parser.cards:
        name = c["name"]
        if name is None:
            name, from_text = c["text"], from_text + 1
        if not name:
            continue
        if "\u2026" in name:
            truncated.append(name)
        if c["cls"] in lists:
            lists[c["cls"]].add(name.strip())
    if truncated:
        raise SystemExit(f"[celltypes] {len(truncated)} names still truncated: {truncated[:5]}")
    if not all(lists.values()):
        raise SystemExit(f"[celltypes] a class came out empty: { {c: len(v) for c, v in lists.items()} }")
    rec = dict(
        purpose="gen-6 phase A edge cuts (docs/gen6_phaseA_DRAFT.md, B2): AL PN = type in ALPN; AL local neuron = "
                "type in ALLN; Kenyon cell = type in Kenyon_Cell",
        source=dict(repository="https://github.com/reiserlab/celltype-explorer-drosophila-male-cns", commit=commit,
                    commit_date=when, file="types.html", sha256=hashlib.sha256(raw).hexdigest(), type_cards=n_cards,
                    names_from_link_text=from_text),
        rule=("every type card (div.neuron-card-wrapper) in types.html whose data-class attribute is exactly the class "
              "name; type name = the card's neuron-name-link href, types/<name>.html, URL-decoded (the link text "
              "truncates long names); parsed with html.parser (scripts/make_gen6_celltypes.py)"),
        classes={c: sorted(v) for c, v in lists.items()},
        counts={c: len(v) for c, v in lists.items()})
    OUT.write_text(json.dumps(rec, indent=1) + "\n", encoding="utf-8")
    print(f"[celltypes] {OUT.relative_to(ROOT)}: " + ", ".join(f"{c} {len(v)}" for c, v in lists.items())
          + f" (from {n_cards} cards, commit {commit[:10]})")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
