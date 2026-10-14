"""
Pull the few numbers phase 1 needs out of Shiu et al.'s 4.2 GB results.zip (Edmond, doi:10.17617/3.CZODIW,
version 3, MIT), without unpacking it. Run it on the computer where the zip was downloaded; upload only the
two small files it writes.

    .venv\\Scripts\\python.exe scripts\\extract_shiu_archive.py <path to results.zip> [out_dir]

Reads, inside the zip:
  Sugar_Bitter_<s>_Hz_<b>_Hz.parquet   the sugar x bitter grid of their Fig 3a
  sugarR_<f>Hz.parquet                 their sugar dose-response of Fig 1d (for the 80%-of-maximum calibration)
and counts, per file and per trial (30 trials of 1 s), the spikes of MN9 720575940660219265 (contralateral to
the stimulated GRNs; the MN9 of their Fig 3a) and 720575940645521262 (ipsilateral).

Writes:
  shiu_archive_mn9.csv            experiment, sugar_hz, bitter_hz, trial, mn9_contra, mn9_ipsi (spikes per trial)
  shiu_archive_manifest.json      the zip's size and MD5 (compare with the MD5 on the Edmond file page), and the
                                  sha256 of every parquet read, so each number traces to its source file
Nothing here is scored: these are the published reference values a separately registered check (S5b) is
compared with.
"""
import hashlib
import io
import json
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd

MN9_CONTRA, MN9_IPSI = 720575940660219265, 720575940645521262
N_RUN = 30
PAT_BITTER = re.compile(r"(^|/)Sugar_Bitter_(\d+)_Hz_(\d+)_Hz\.parquet$")
PAT_SUGAR = re.compile(r"(^|/)sugarR_(\d+)Hz\.parquet$")


def file_md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    zpath = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".")
    out.mkdir(parents=True, exist_ok=True)
    rows, sources = [], {}
    with zipfile.ZipFile(zpath) as z:
        names = z.namelist()
        wanted = [(n, PAT_BITTER.search(n), PAT_SUGAR.search(n)) for n in names]
        wanted = [(n, b, s) for n, b, s in wanted if b or s]
        print(f"{len(names)} files in the zip; {len(wanted)} needed "
              f"({sum(1 for _, b, _ in wanted if b)} sugar x bitter, {sum(1 for _, _, s in wanted if s)} sugar dose)")
        if not wanted:
            raise SystemExit("none of the expected files found; send the first lines of the zip's file list instead")
        for i, (name, b, s) in enumerate(sorted(wanted)):
            data = z.read(name)
            sources[name] = dict(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
            d = pd.read_parquet(io.BytesIO(data), columns=["trial", "flywire_id"])
            sugar, bitter, exp = (int(b.group(2)), int(b.group(3)), "sugar_bitter") if b else (int(s.group(2)), 0, "sugar_dose")
            for t in range(N_RUN):
                dt = d[d.trial == t]
                rows.append(dict(experiment=exp, sugar_hz=sugar, bitter_hz=bitter, trial=t,
                                 mn9_contra=int((dt.flywire_id == MN9_CONTRA).sum()),
                                 mn9_ipsi=int((dt.flywire_id == MN9_IPSI).sum())))
            if (i + 1) % 20 == 0:
                print(f"  {i + 1}/{len(wanted)} read", flush=True)
    pd.DataFrame(rows).to_csv(out / "shiu_archive_mn9.csv", index=False)
    print("computing the zip's MD5 (a minute for 4 GB) ...", flush=True)
    manifest = dict(source="Edmond doi:10.17617/3.CZODIW, version 3, results.zip", zip_bytes=zpath.stat().st_size,
                    zip_md5=file_md5(zpath), n_files_read=len(sources), n_trials_per_file=N_RUN,
                    mn9_contra=MN9_CONTRA, mn9_ipsi=MN9_IPSI, files=sources)
    (out / "shiu_archive_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {out / 'shiu_archive_mn9.csv'} and {out / 'shiu_archive_manifest.json'}; zip MD5 {manifest['zip_md5']}")


if __name__ == "__main__":
    main()
