"""Value-by-value comparison of two phaseA.json files. Usage: python compare.py A.json B.json out.json"""
import json, sys, re, math

# a path is provenance if any key segment names a timestamp, git/machine stamp or environment field
PROV = re.compile(r"(^|[/_])(time|timestamp|date|stamp|stamps|commit|git|git_commit|sha|sha256|hash|host|hostname|machine|platform|python|version|user|cwd|elapsed|duration|wall|os|env|registered_at)($|[/_\[])", re.I)


def leaves(x, p=""):
    if isinstance(x, dict):
        if not x:
            yield p, {}
        for k, v in x.items():
            yield from leaves(v, f"{p}/{k}")
    elif isinstance(x, list):
        if not x:
            yield p, []
        for i, v in enumerate(x):
            yield from leaves(v, f"{p}[{i}]")
    else:
        yield p, x


def same(a, b):
    if isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b):
        return True
    return type(a) == type(b) and a == b


a = dict(leaves(json.load(open(sys.argv[1], encoding="utf-8"))))
b = dict(leaves(json.load(open(sys.argv[2], encoding="utf-8"))))
keys = sorted(set(a) | set(b))
diffs = []
for k in keys:
    if k not in a or k not in b or not same(a[k], b[k]):
        kind = "provenance" if PROV.search(k) else "results"
        diffs.append({"path": k, "kind": kind, "committed": a.get(k, "<absent>"), "rerun": b.get(k, "<absent>")})
out = {"n_paths_union": len(keys), "n_committed": len(a), "n_rerun": len(b),
       "n_compared_both": len(set(a) & set(b)), "n_diff": len(diffs), "diffs": diffs}
json.dump(out, open(sys.argv[3], "w", encoding="utf-8"), indent=1, default=str)
print(json.dumps({k: v for k, v in out.items() if k != "diffs"}))
for d in diffs:
    print(d["kind"], d["path"], repr(d["committed"])[:90], "->", repr(d["rerun"])[:90])
