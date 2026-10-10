"""
Fetch bulk MaleCNS files from Google Storage (no token needed; CC-BY).

  synapse-nt   per-T-bar neurotransmitter probabilities (2.7 GB) -> per-synapse confidence
               and sign, instead of one aggregate label per presynaptic neuron
  annotations  body annotations (13 MB)
  connectome   connection weights (1.1 GB)

Run:  menu option 23, or  .venv\\Scripts\\python.exe scripts\\fetch_bulk.py synapse-nt   (or annotations,
connectome, all). Files land in data\\bulk\\. Resumable: an interrupted download continues where it stopped.
"""
import sys
import time
import urllib.request
from pathlib import Path

BASE = "https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome"
TARGETS = {
    "synapse-nt": (f"{BASE}/tbar-neurotransmitters-male-cns-v1.0.feather", "tbar-neurotransmitters.feather", "2.7 GB"),
    "annotations": (f"{BASE}/body-annotations-male-cns-v1.0-minconf-0.5.feather", "body-annotations.feather", "13 MB"),
    "connectome": (f"{BASE}/connectome-weights-male-cns-v1.0-minconf-0.5.feather", "connectome-weights.feather", "1.1 GB"),
}


def download(url, dest):
    """Resumable download: an existing partial file is continued with an HTTP Range request."""
    part = dest.with_suffix(dest.suffix + ".part")
    have = part.stat().st_size if part.exists() else 0
    req = urllib.request.Request(url, headers={"Range": f"bytes={have}-"} if have else {})
    with urllib.request.urlopen(req, timeout=60) as r:
        if have and r.status != 206:          # server ignored the range: start again
            have = 0
        total = have + int(r.headers.get("Content-Length") or 0)
        with open(part, "ab" if have else "wb") as f:
            done, t0 = have, time.time()
            while chunk := r.read(1 << 20):
                f.write(chunk)
                done += len(chunk)
                if total:
                    print(f"\r  {done / 2**20:,.0f} / {total / 2**20:,.0f} MB  "
                          f"({done / total:.0%}, {(done - have) / 2**20 / max(time.time() - t0, 1e-6):.1f} MB/s)",
                          end="", flush=True)
    print()
    part.replace(dest)


if __name__ == "__main__":
    out = Path("data/bulk")
    out.mkdir(parents=True, exist_ok=True)
    which = sys.argv[1] if len(sys.argv) > 1 else "synapse-nt"
    keys = list(TARGETS) if which == "all" else [which]
    for k in keys:
        if k not in TARGETS:
            raise SystemExit(f"unknown target {k}; choose from {list(TARGETS)} or 'all'")
        url, name, size = TARGETS[k]
        if (out / name).exists():
            print(f"{k}: already in data\\bulk\\{name}")
            continue
        print(f"fetching {k} ({size}) -> data\\bulk\\{name}")
        download(url, out / name)
    print("""
ROI volumes are neuroglancer-precomputed on gs:// and need cloud-volume (menu option 25 installs it).
See fit/roi_membership.py once downloaded.""")
