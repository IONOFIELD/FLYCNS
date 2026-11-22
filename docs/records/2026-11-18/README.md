# Data-check records, 2026-11-18

Read-only checks run on 2026-11-18 at commit `c1e6e6244570b47ad799bca092fda985ced9a6d4` (`gen6/phaseA-decisions`),
Windows 11 (10.0.26200), Python 3.12.10 from `.venv`. They were produced in an untracked `explore\` folder and moved
here unchanged. Nothing here goes into a score; nothing was registered.

| Folder | What | Start with |
|---|---|---|
| `rescore/` | Part 1: Windows re-score of phase A vs the committed `results/gen6_phaseA/phaseA.json`: 5,404 of 5,404 values equal (only line endings differ) | `rescore/report.md` |
| `v7a/` | Part 2: V7a feasibility (DM4, DL5, VM7d, VM7v, DM1) and the size of the STD-in scope | `v7a/summary.md` |
| `status/` | Part 3: tracing-status audit of every benchmark readout / driven cell; L/R input ratios | `status/summary.md` |
| `sugar_mn9_paths/` | Part 4: LB3b/LB3c → MN9 path analysis, observed and with `mirror_mn9` | `sugar_mn9_paths/summary.md` |
| `density/` | Part 5: MaleCNS vs FlyWire v783 synapses per cell on identically named types | `density/summary.md` |

`sugar_mn9_paths/previous_20261018/` and `density/previous_20261019/` hold the outputs of the earlier exploratory
session (18–19 Oct 2026) that were found in `explore\` on 2026-11-18; they were kept, not overwritten, and the
2026-11-18 runs reproduce their numbers.

## Byte-for-byte storage

`.gitattributes` in this folder sets `* -text`: files are committed exactly as written. Several were written with
CRLF line endings on Windows, and `rescore/phaseA_windows.json`'s CRLF bytes are part of the finding. The sha256
values in this README and in the reports are of these exact bytes.

## Running the scripts from here

The scripts were run from `explore\<part>\` and locate the repository as `Path(__file__).resolve().parents[2]`.
They are kept byte-identical to what produced the records (sha256 below), so at this depth that line would need
`parents[4]` to run in place. `density/density_check.py` takes the downloads folder as its argument.

## Downloads (not in the repository)

Moved out of the repository to `C:\Users\III\Desktop\CODE PROJECTS\FLYCNS\CODE\flycns_downloads\2026-11-18\`
(same relative paths under `density\`). No login is needed for any of them.

| File | Bytes | sha256 | Source |
|---|---|---|---|
| `density/downloads_20261118/Supplemental_file1_neuron_annotations.tsv` | 31,720,298 | `b214970b55d2fbe0853bba536fdcb9e28730f4eb7ab06f600491df795da683cd` | https://raw.githubusercontent.com/flyconnectome/flywire_annotations/a83b2776d60d5764cef36b927f5f9679c16c47a2/supplemental_files/Supplemental_file1_neuron_annotations.tsv |
| `density/downloads_20261118/proofread_connections_783.feather` | 852,022,274 | `24f960ae3e7d4f8cd30db3b62e99fb5179cc3d1e76d8c155bfb441e9737d3faf` | https://zenodo.org/records/10676866/files/proofread_connections_783.feather (MD5 `f48f972d262323a102aed49af1396b8a` = Zenodo's) |
| `density/previous_20261019/downloads/Supplemental_file1_neuron_annotations.tsv` | 31,720,298 | `b214970b55d2fbe0853bba536fdcb9e28730f4eb7ab06f600491df795da683cd` | same URL as above (identical bytes) |
| `density/previous_20261019/downloads/proofread_connections_783.feather` | 852,022,274 | `24f960ae3e7d4f8cd30db3b62e99fb5179cc3d1e76d8c155bfb441e9737d3faf` | same URL as above (identical bytes) |
| `density/previous_20261019/downloads/proofread_root_ids_783.npy` | 1,114,168 | `7c7b7e818e9232e5ab64793d52ba20574dbe9da3a6509fbc74193b0f259a01be` | https://zenodo.org/records/10676866/files/proofread_root_ids_783.npy (MD5 `e0e6c19732fd8c7a4e39a2d170105421` = Zenodo's) |

MaleCNS inputs (in the repository, unchanged): `data/edges.parquet` `61f8c2edbb214111073701fa5c4bef835e52925ce742f24e4011ce98d92da958`,
`data/neurons.parquet` `b60448d9e2f26bfc0389cada9bb08a1a4d5f4d2149163da3fdd3e48621ee9e21`,
`data/gen6_phaseA_celltypes.json` `ea8bad7dccde7e714efdb5a882f73fe5391659415130bde57e71f1d7e5585504`.

## Files

sha256 of every file in this folder except this README (unchanged since they were produced, apart from `.gitattributes`, added here):

| File | Bytes | sha256 |
|---|---|---|
| `.gitattributes` | 313 | `6f396b7c70cfd405b994a16bc8e7b0a1e036d2969fc065481acf3ff7f5b0443e` |
| `density/by_type.csv` | 717,927 | `f168a972c9311ebf44043475f4228350f87cd1ae05c5b557a55c304ff5813bdf` |
| `density/density_check.py` | 10,261 | `737bbe7286fdfc2c59ea02aa191d8cf775a96fa1e01cbfaa4551fdb633d56f99` |
| `density/previous_20261019/by_type.csv` | 345,856 | `d47ef16bc4d63e0550e8c3e8251d4119357c12088b336fa096fde3312522c1e0` |
| `density/previous_20261019/density.py` | 7,959 | `3299a7da120953ead0ef6f75e2d32b419f3a3ff5eda9a14e70291c4195f3a059` |
| `density/previous_20261019/results.json` | 12,586 | `c2ad6dd78af4bf0ca58eb2f3c6bbf4701da77b0cdd994c29046a08af3690e54d` |
| `density/previous_20261019/sources.json` | 2,484 | `d7d97440017a14ba8bddda3cd8250fcfab234bde20c0d84da3f7e0b753895e20` |
| `density/previous_20261019/summary.md` | 7,340 | `0899f12d67a3b4dce47a76ae244e3be05ad33493e18c0d58aa99b18eddafd0db` |
| `density/results.json` | 9,020 | `aad6239d05f7e51dbec199b88d287fb04456a20f9f8d715e3a3f91a992bc688e` |
| `density/sources.json` | 1,946 | `35a9ea61ea2a1076f0faf0a36fbbf4b4183d52ca48ffdad72335d4d3028acec3` |
| `density/summary.md` | 3,125 | `0d643eb37509a8577425448585dbd78c8b95a12b9a857c334aa2fb9804dc19f8` |
| `rescore/compare.py` | 1,804 | `f59e5f7cc18cec155eca614d44e2cc63d25e54c16f5353d2ecfe544d5d7cf951` |
| `rescore/diff.json` | 127 | `bdb835429f2bf0ede614dee444a6a7dbc289124c142f9abf54797b0ec7437293` |
| `rescore/phaseA_committed.json` | 236,851 | `c761a7160df08cd5072af2f5c08eca8092bcbd8bfcef56dfdc683c195238e99b` |
| `rescore/phaseA_windows.json` | 246,374 | `5850307263939bdeef2d9b4282ee9bb067272a954da577a4bcb7684b1306e0f8` |
| `rescore/report.md` | 3,619 | `31a3e251011314b6dc25c7524c5e009572980b37976a214ed38414f55787bbd2` |
| `status/cells.csv` | 1,922,832 | `b2a26813d9413f55d337e177c85efa2bf4d53f918a92006ae8a0682981581fd1` |
| `status/non_traced_cells.csv` | 199 | `4a68deeb89a946f60d10429644d16000c14bd5741ca6755582382da9167c2466` |
| `status/pairs.csv` | 3,295 | `781e6fc32e7a27e6895db33573a0b3d6b0b167706799d0a9509f30b65597e76c` |
| `status/status_audit.json` | 989 | `5d96645a245dd79fa45caff6498f86b18b4f51198c9b14bb012e2864290f8f25` |
| `status/status_audit.py` | 9,329 | `4bdf8b4de9e1b9439a4eac96a6b1aec1c772f7ebab4c3b9144ca167733f167f0` |
| `status/status_table.csv` | 81 | `bfe6f4b17e4553af8e133987c0a1ce5bc4397085919d68d81c44214ddc780f5c` |
| `status/summary.md` | 2,190 | `103c7796a103999df17d6ae184a00f44a5efb3efdd2fc595c3251a8b89c6b705` |
| `status/types_by_side.csv` | 11,678 | `cd10734055f5e067751f5f33aeed4e613ba89cf31ca9fd414d228ad2ce3a4f9d` |
| `status/within_type_outliers.csv` | 48,912 | `fe9561b477148fec35cc5d55e68828c38754313d91b0e4436f6c29b1bcaab4f9` |
| `sugar_mn9_paths/paths.json` | 45,149 | `8c4964ef84ec89d2c1fe66dd8c115af7806695830a79c010cccc1364fd9e377d` |
| `sugar_mn9_paths/previous_20261018/paths.json` | 103,450 | `8ae34e7ad0ee1601078af2eaf0ee39a72fcc0833e6b5c6d654163f84b5dbe6d3` |
| `sugar_mn9_paths/previous_20261018/summary.md` | 5,754 | `51111ebb424077fe145a1764b62a3852b937f94f694cc4a09c7be9a42efb3424` |
| `sugar_mn9_paths/sugar_mn9_paths.py` | 11,110 | `4f1b2f948e5ac07ac2dd26a92bbe125ac7ec6e1d58bcd439fe0e9f2c78391d18` |
| `sugar_mn9_paths/summary.md` | 8,179 | `8f167ef8660f9c8150586487c3fab4f96f60dd328b7df8979baee3fc79eb42b1` |
| `v7a/cell_counts.csv` | 331 | `6a4328e305ce94db0e0ca14653b5e41d046b6c7d57e1cdcdb50507a51d4789c3` |
| `v7a/per_pn.csv` | 1,456 | `3160a233cccf1d833a4d97abd80b1b00063daa01497fc7ee4fc3e58953165cc1` |
| `v7a/summary.md` | 3,188 | `63b125ddbc6cb64fd2a8f6a396957e10f80ab2e514ed4c6bb6b89e7df7f32c60` |
| `v7a/v7a.json` | 19,467 | `330048b31d1b0284131ab691093982fd7ee0a2d2636929b97552e3bd86c7d1e5` |
| `v7a/v7a_feasibility.py` | 8,486 | `997e88fce2bfe1964889dc73596c9801329b9d567a5dad46c580d5d110f7a30d` |
