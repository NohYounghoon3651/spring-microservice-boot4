#!/usr/bin/env python3
"""Rebuild every chapter from the workbook alone and compare it with the repository.

Starting from an empty folder, the script applies chapter 3's workbook page, then uses that
result as the starting point for chapter 4, and so on - exactly what a student does.
Every file operation comes from the <!-- wb:file ... --> markers in workbook/*.md:
  write  - the code block that follows the marker is the full file content
  cp     - copy another file of the working folder
  copy   - copy the file from the repository (wrapper, binaries, generated files)
  delete - remove the file
Exit code 1 if any rebuilt chapter differs from the repository.
"""
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import build  # noqa: E402

MARK = re.compile(r'<!-- wb:file path="([^"]+)" op="(\w+)"(?: nl="([01])")?(?: src="([^"]+)")? -->')


def ops(md):
    lines = md.split("\n")
    i = 0
    while i < len(lines):
        m = MARK.fullmatch(lines[i].strip())
        if not m:
            i += 1
            continue
        path, op, nl, src = m.groups()
        content = None
        if op == "write":
            j = i + 1
            while not lines[j].startswith("```"):
                j += 1
            fence = re.match(r"`+", lines[j]).group(0)
            k = j + 1
            while lines[k] != fence:
                k += 1
            content = "\n".join(lines[j + 1:k]) + ("\n" if nl == "1" else "")
            i = k
        yield path, op, content, src
        i += 1


def apply(work, n, md):
    target = build.chapter_dir(n)
    for path, op, content, src in ops(md):
        dst = os.path.join(work, path)
        if op == "delete":
            if os.path.exists(dst):
                os.remove(dst)
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if op == "write":
            with open(dst, "w", encoding="utf-8", newline="") as fh:
                fh.write(content)
        elif op == "empty":
            open(dst, "w").close()
        elif op == "cp":
            shutil.copyfile(os.path.join(work, src), dst)
        elif op == "copy":
            origin = os.path.join(build.ROOT, "Chapter03", "1-spring-init", path) if (
                n == 3 and not os.path.exists(os.path.join(target, path))) else os.path.join(target, path)
            shutil.copyfile(origin, dst)
    # remove directories left empty by deletions
    for r, ds, fs in os.walk(work, topdown=False):
        if r != work and not os.listdir(r):
            os.rmdir(r)


def compare(work, n):
    want = build.list_files(build.chapter_dir(n))
    have = build.list_files(work)
    problems = []
    for p in sorted(set(want) | set(have)):
        if p not in have:
            problems.append(f"missing  {p}")
        elif p not in want:
            problems.append(f"extra    {p}")
        elif open(want[p], "rb").read() != open(have[p], "rb").read():
            problems.append(f"differs  {p}")
    return problems


def main():
    work = tempfile.mkdtemp(prefix="workbook-")
    failed = False
    try:
        for n in build.CODE_CHAPTERS:
            md = open(os.path.join(build.OUT, f"Chapter{n:02d}.md"), encoding="utf-8").read()
            apply(work, n, md)
            problems = compare(work, n)
            print(f"Chapter {n:2d}: {'OK' if not problems else f'{len(problems)} problem(s)'}")
            for x in problems[:20]:
                print("   ", x)
            failed |= bool(problems)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
