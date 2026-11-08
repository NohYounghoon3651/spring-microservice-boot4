#!/usr/bin/env python3
"""Per-chapter 'what changed since the previous chapter' data, computed from the code.

Used by learning.py; run on its own to print a summary:  python3 tools/wiki/delta.py
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CODE = ["Chapter03/1-spring-init", "Chapter03/2-basic-rest-services"] + [f"Chapter{n:02d}" for n in
        (4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 23)]
SKIP = re.compile(r"(^|/)(MIGRATION-BOOT4\.md|BOOK-GUIDE\.md|gradlew(\.bat)?|gradle/wrapper/.*|\.gitignore)$")


def files(d):
    out = set()
    base = os.path.join(ROOT, d)
    for dp, dn, fn in os.walk(base):
        dn[:] = [x for x in dn if x not in ("build", ".gradle", "1-spring-init", "2-basic-rest-services")]
        for f in fn:
            rel = os.path.relpath(os.path.join(dp, f), base)
            if not SKIP.search(rel):
                out.add(rel)
    return out


def modules(d):
    return sorted(os.path.relpath(dp, os.path.join(ROOT, d)) for dp, dn, fn in os.walk(os.path.join(ROOT, d))
                  if "build.gradle" in fn and dp != os.path.join(ROOT, d) and "/build" not in dp)


DEP = re.compile(r'''^\s*(?:implementation|runtimeOnly|testImplementation|annotationProcessor|developmentOnly|compileOnly)\s+(?:platform\()?['"]([^'":]+:[^'":]+)''', re.M)


def deps(d):
    s = set()
    for m in modules(d):
        t = open(os.path.join(ROOT, d, m, "build.gradle"), encoding="utf-8").read()
        s |= set(DEP.findall(t))
    return s


def changed_lines(a, b, rel):
    r = subprocess.run(["git", "diff", "--no-index", "--numstat", os.path.join(ROOT, a, rel), os.path.join(ROOT, b, rel)],
                       capture_output=True, text=True)
    if not r.stdout.strip():
        return 0
    x = r.stdout.split()[:2]
    return sum(int(v) for v in x if v.isdigit())


def compute(root=None, verbose=False):
    global ROOT
    if root:
        ROOT = os.path.abspath(root)
    res = {}
    for prev, cur in zip(CODE, CODE[1:]):
        fa, fb = files(prev), files(cur)
        added = sorted(fb - fa)
        removed = sorted(fa - fb)
        changed = []
        for rel in sorted(fa & fb):
            n = changed_lines(prev, cur, rel)
            if n:
                changed.append((rel, n))
        changed.sort(key=lambda x: -x[1])
        ma, mb = set(modules(prev)), set(modules(cur))
        da, db = deps(prev), deps(cur)
        res[cur] = dict(prev=prev, added=added, removed=removed, changed=changed,
                        new_modules=sorted(mb - ma), removed_modules=sorted(ma - mb),
                        new_deps=sorted(db - da), removed_deps=sorted(da - db))
        if verbose:
            print(f"{prev} -> {cur}: +{len(added)} -{len(removed)} ~{len(changed)} modules+{sorted(mb-ma)} deps+{len(db-da)}")
    return res


if __name__ == "__main__":
    compute(sys.argv[1] if len(sys.argv) > 1 else None, verbose=True)
