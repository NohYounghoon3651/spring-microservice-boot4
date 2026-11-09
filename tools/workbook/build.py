#!/usr/bin/env python3
"""Generate the hand-coding workbook (workbook/*.md) from the chapter folders.

Each chapter page lists, step by step, every file a student has to create, change or
delete to turn the previous chapter's code into this chapter's code. The code shown is
taken from the repository itself, so the workbook always matches the code.

Every file block is preceded by a machine-readable marker
    <!-- wb:file path="..." op="write|delete|copy" nl="0|1" -->
that tools/workbook/verify.py uses to rebuild each chapter from the workbook alone.

Usage: python3 tools/workbook/build.py   (writes workbook/)
"""
import difflib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "wiki"))
import learning as L  # noqa: E402
from notes import NOTES, MODULE_TITLES  # noqa: E402

GH = "https://github.com/NohYounghoon3651/spring-microservice-boot4"
OUT = os.path.join(ROOT, "workbook")
CODE_CHAPTERS = [3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 23]

SKIP_DIRS = {"build", ".gradle", ".idea", "bin", "out"}
SKIP_FILES = {"gradlew", "gradlew.bat", "MIGRATION-BOOT4.md", "BOOK-GUIDE.md", "README.md"}
# Files that are generated or not meant to be typed: students copy or generate them.
COPY_RULES = [
    (r"(^|/)gradle/wrapper/", "Gradle 래퍼 파일입니다. 저장소의 같은 경로에서 복사하세요."),
    (r"\.p12$", None),  # handled by a keytool note in notes.py
    (r"\.ndjson$", "Kibana에서 내보낸 객체입니다. 저장소의 같은 경로에서 복사하세요."),
    (r"Hands-on-Dashboard\.json$", "Grafana에서 내보낸 대시보드입니다. 저장소의 같은 경로에서 복사하세요."),
    (r"(^|/)Chart\.lock$", "`helm dep up`이 만드는 파일입니다. 직접 치지 말고 확인 단계의 `helm dep up` 명령으로 생성하세요."),
    (r"(^|/)\.gitignore$", "Git이 무시할 파일 목록입니다. 저장소의 같은 경로에서 복사하세요(치지 않아도 실습에는 지장이 없습니다)."),
    (r"(^|/)\.helmignore$", "헬름이 무시할 파일 목록입니다. 저장소의 같은 경로에서 복사하세요."),
]

LANG = {".java": "java", ".yml": "yaml", ".yaml": "yaml", ".gradle": "groovy", ".bash": "bash",
        ".sh": "bash", ".properties": "properties", ".xml": "xml", ".json": "json", ".tpl": "yaml",
        ".sql": "sql", ".conf": "text", ".env": "bash"}


def chapter_dir(n):
    return os.path.join(ROOT, "Chapter03", "2-basic-rest-services") if n == 3 else os.path.join(ROOT, f"Chapter{n:02d}")


def rel_dir(n):
    return "Chapter03/2-basic-rest-services" if n == 3 else f"Chapter{n:02d}"


def list_files(d):
    out = {}
    for r, ds, fs in os.walk(d):
        ds[:] = sorted(x for x in ds if x not in SKIP_DIRS)
        for f in fs:
            if f in SKIP_FILES:
                continue
            p = os.path.relpath(os.path.join(r, f), d)
            if p.startswith("gradle/wrapper/") or "/gradle/wrapper/" in p:
                continue  # the wrapper is copied once, see README
            out[p] = os.path.join(r, f)
    return out


def read(path):
    with open(path, "rb") as fh:
        data = fh.read()
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None  # binary


def copy_note(p):
    for rx, msg in COPY_RULES:
        if re.search(rx, p):
            return msg if msg is not None else "바이너리 파일입니다."
    return None


def module_of(p):
    s = p.split("/")
    if s[0] in ("microservices", "spring-cloud") and len(s) > 2:
        return f"{s[0]}/{s[1]}"
    if s[0] == "kubernetes" and len(s) > 2:
        if s[1] == "helm":
            return f"kubernetes/helm/{s[2]}" if len(s) > 3 else "kubernetes/helm"
        return f"kubernetes/{s[1]}"
    if len(s) > 1:
        return s[0]
    return "(root)"


ORDER = ["(root)", "api", "util", "microservices/product-service", "microservices/recommendation-service",
         "microservices/review-service", "microservices/product-composite-service",
         "spring-cloud/eureka-server", "spring-cloud/gateway", "spring-cloud/authorization-server",
         "spring-cloud/config-server", "config-repo", "auth0", "kubernetes",
         "kubernetes/helm/common", "kubernetes/helm/components", "kubernetes/helm/environments"]


def module_rank(m):
    if m in ORDER:
        return (ORDER.index(m), m)
    for i, o in enumerate(ORDER):
        if m.startswith(o + "/"):
            return (i, m)
    return (len(ORDER), m)


def fence_for(text):
    longest = max((len(x) for x in re.findall(r"`+", text)), default=0)
    return "`" * max(3, longest + 1)


def lang_of(p):
    base = os.path.basename(p)
    if base == "Dockerfile":
        return "dockerfile"
    if base == ".env":
        return "bash"
    return LANG.get(os.path.splitext(p)[1], "text")


def code_block(p, text):
    body = text[:-1] if text.endswith("\n") else text
    f = fence_for(body)
    return [f"{f}{lang_of(p)}", body, f]


def marker(p, op, text=None):
    nl = "1" if (text or "").endswith("\n") else "0"
    return f'<!-- wb:file path="{p}" op="{op}" nl="{nl}" -->'


def gradle_project(p):
    s = p.split("/")
    if s[0] in ("microservices", "spring-cloud") and len(s) > 2:
        return f":{s[0]}:{s[1]}"
    if s[0] in ("api", "util"):
        return f":{s[0]}"
    return None


def file_section(p, old, new, n, src=None):
    """Return markdown lines for one file change. src: an existing file with identical content."""
    lines = []
    if new is None:  # deleted
        lines += [f"- 삭제: `{p}`", marker(p, "delete")]
        return lines
    note = copy_note(p)
    special = NOTES.get(n, {}).get("files", {}).get(p)
    if note or read(os.path.join(chapter_dir(n), p)) is None:
        lines += [f"#### `{p}` — 복사/생성", ""]
        lines += [special or note or "바이너리 파일입니다. 저장소의 같은 경로에서 복사하세요.", "",
                  marker(p, "copy"), ""]
        return lines
    if special:
        lines += [special, ""]
    if src:
        what = "새 파일" if old is None else "전체를 바꿉니다"
        lines += [f"#### `{p}` — {what} (`{src}`와 같은 내용)", "",
                  "앞에서 만든 파일과 내용이 똑같으니 복사합니다.", "",
                  "```bash", f"mkdir -p {os.path.dirname(p) or '.'} && cp {src} {p}", "```", "",
                  f'<!-- wb:file path="{p}" op="cp" src="{src}" -->', ""]
        return lines
    if new == "":
        lines += [f"#### `{p}` — 빈 파일", "", "내용이 없는 파일입니다.", "",
                  "```bash", f"mkdir -p {os.path.dirname(p) or '.'} && touch {p}", "```", "",
                  f'<!-- wb:file path="{p}" op="empty" -->', ""]
        return lines
    if old is None:
        lines += [f"#### `{p}` — 새 파일 ({len(new.splitlines())}줄)", "", marker(p, "write", new)]
        lines += code_block(p, new) + [""]
        return lines
    a, b = old.splitlines(), new.splitlines()
    sm = difflib.SequenceMatcher(None, a, b)
    changed = sum(max(i2 - i1, j2 - j1) for t, i1, i2, j1, j2 in sm.get_opcodes() if t != "equal")
    if len(b) <= 25 or changed > 0.5 * max(len(b), 1):
        lines += [f"#### `{p}` — 전체를 다음 내용으로 바꿉니다", "", marker(p, "write", new)]
        lines += code_block(p, new) + [""]
        return lines
    diff = list(difflib.unified_diff(a, b, lineterm="", n=3))[2:]
    lines += [f"#### `{p}` — 수정", "",
              "`-`로 시작하는 줄은 지우고 `+`로 시작하는 줄을 추가합니다. `@@` 줄은 위치 표시입니다.", ""]
    dtext = "\n".join(diff)
    f = fence_for(dtext)
    lines += [f + "diff", dtext, f]
    lines += ["", "<details><summary>완성된 파일 전체 보기</summary>", "", marker(p, "write", new)]
    lines += code_block(p, new) + ["", "</details>", ""]
    return lines


BINARY = "\0binary\0"


def changes(prev_dir, cur_dir):
    a = list_files(prev_dir) if prev_dir else {}
    b = list_files(cur_dir)
    out = []
    for p in sorted(set(a) | set(b)):
        old = (BINARY if read(a[p]) is None else read(a[p])) if p in a else None
        new = (BINARY if read(b[p]) is None else read(b[p])) if p in b else None
        if p in a and p in b:
            if open(a[p], "rb").read() == open(b[p], "rb").read():
                continue
        out.append((p, old if p in a else None, new if p in b else None, p in b))
    return out


def header(n):
    a, b = NOTES[n]["pages"]
    lines = [f"# {n}장 워크북 — {L.C[n]['t']}", "",
             f"> 교재: 『스프링 부트 3와 스프링 클라우드를 활용한 마이크로서비스 구축』 {n}장 · "
             f"영문 3판 p.{a}–{b} ([교재 대응 가이드]({GH}/blob/main/Chapter{n:02d}/BOOK-GUIDE.md))  ",
             f"> 완성 코드: [`{rel_dir(n)}`]({GH}/tree/main/{rel_dir(n)}) · 위키: [{n}장]({GH}/wiki/{L.page_name(n)})", ""]
    return lines


def start_section(n, prev):
    d = f"Chapter{n:02d}"
    if n == 3:
        return []
    p = rel_dir(prev)
    return ["## 시작하기", "",
            f"{prev}장을 끝낸 작업 폴더를 복사해서 시작합니다. {prev}장을 다 하지 못했다면 저장소의 완성 코드를 복사해도 됩니다.", "",
            "```bash", "cd ~/my-work",
            f"cp -r Chapter{prev:02d} {d}          # 내가 만든 {prev}장 결과에서 시작",
            f"# 또는: cp -r <저장소>/{p} {d}        # 저장소의 {prev}장 완성 코드에서 시작",
            f"cd {d} && ./gradlew clean -q", "```", ""]


def check_section(n):
    lines = ["## 확인하기", ""]
    extra = NOTES[n].get("check")
    if extra:
        lines += extra.strip("\n").split("\n") + [""]
    rs = [x.replace(f"cd Chapter{n:02d}", f"cd ~/my-work/Chapter{n:02d}") for x in L.run_section(n)]
    rs = [x.replace("cd Chapter03/2-basic-rest-services", "cd ~/my-work/Chapter03") for x in rs]
    if n == 3:
        rs = rs[rs.index("**3-2. 기본 REST 서비스** (`Chapter03/2-basic-rest-services`): 서비스 4개를 직접 띄우고 테스트합니다."):]
        rs[0] = "서비스 4개를 직접 띄우고 테스트합니다."
    lines += rs + ["",
                   "테스트가 실패하면 저장소의 완성 코드와 비교해 보세요(작업 폴더에서 실행):", "",
                   "```bash", f"diff -r --exclude=build --exclude=.gradle . <저장소>/{rel_dir(n)}", "```", ""]
    return lines


def chapter_page(n, prev):
    nt = NOTES[n]
    lines = header(n)
    lines += ["## 이 장에서 만드는 것", ""] + nt["intro"].strip("\n").split("\n") + [""]
    lines += start_section(n, prev)
    init_lines = []
    if n == 3:
        init_lines = ch3_init_section()
        prev_dir = os.path.join(ROOT, "Chapter03", "1-spring-init")
    else:
        prev_dir = chapter_dir(prev)
    ch = changes(prev_dir, chapter_dir(n))
    groups = {}
    for p, old, new, exists in ch:
        groups.setdefault(module_of(p), []).append((p, old, new))
    step = 1 if n != 3 else 2
    # content -> path of a file the student already has (unchanged from the previous chapter
    # or written earlier on this page), used to tell them to copy instead of retyping
    available = {}
    changed_paths = {p for p, _, _, _ in ch}
    cur_files = list_files(chapter_dir(n))
    for p in sorted(cur_files):
        if p not in changed_paths:
            t = read(cur_files[p])
            if t is not None and t not in available:
                available[t] = p
    toc = ["1. [Spring Initializr로 골격 만들기](#단계-1) — 새 파일 2"] if n == 3 else []
    body = list(init_lines)
    for m in sorted(groups, key=module_rank):
        items = groups[m]
        title = MODULE_TITLES.get(m, f"`{m}`")
        note = nt.get("modules", {}).get(m)
        n_new = sum(1 for _, o, w in items if o is None and w is not None)
        n_mod = sum(1 for _, o, w in items if o is not None and w is not None)
        n_del = sum(1 for _, o, w in items if w is None)
        stat = " · ".join(x for x in [f"새 파일 {n_new}" if n_new else "", f"수정 {n_mod}" if n_mod else "",
                                       f"삭제 {n_del}" if n_del else ""] if x)
        anchor = f"단계-{step}"
        toc.append(f"{step}. [{title}](#{anchor}) — {stat}")
        body += [f'<a id="{anchor}"></a>', "", f"## 단계 {step}. {title}", ""]
        if note:
            body += note.strip("\n").split("\n") + [""]
        dels = [p for p, o, w in items if w is None]
        if dels:
            body += ["**지울 파일**", "", "```bash"] + [f"rm {p}" for p in dels] + ["```", ""]
            for p in dels:
                body.append(marker(p, "delete"))
            body.append("")
        for p, old, new in items:
            if new is None:
                continue
            src = None
            if new != BINARY and not copy_note(p) and len(new.splitlines()) >= 3:
                src = available.get(new)
            body += file_section(p, old, new, n, src)
            if new != BINARY and new not in available:
                available[new] = p
        gp = gradle_project(items[0][0])
        if gp and any(w is not None and p.endswith((".java", ".gradle", ".yml", ".properties"))
                      for p, o, w in items):
            body += ["**중간 확인**", "", "```bash", f"./gradlew {gp}:build -x test   # 컴파일만 먼저 확인",
                     "```", ""]
        step += 1
    lines += ["## 단계 목록", ""] + toc + [""] + body
    lines += check_section(n)
    lines += ["---", "", nav(n, prev), ""]
    return "\n".join(lines)


def ch3_init_section():
    init = os.path.join(ROOT, "Chapter03", "1-spring-init")
    lines = ['<a id="단계-1"></a>', "", "## 단계 1. Spring Initializr로 골격 만들기", "",
             NOTES[3]["init"].strip("\n"), "",
             "```bash", "mkdir -p ~/my-work/Chapter03 && cd ~/my-work/Chapter03", "```", ""]
    for p in ["create-projects.bash", "settings.gradle"]:
        text = read(os.path.join(init, p))
        lines += [f"#### `{p}` — 새 파일", "", marker(p, "write", text)] + code_block(p, text) + [""]
    lines += ["```bash", "chmod +x create-projects.bash && ./create-projects.bash",
              "cp -r <저장소>/Chapter03/2-basic-rest-services/gradle .   # Gradle 래퍼",
              "cp <저장소>/Chapter03/2-basic-rest-services/gradlew* .",
              "./gradlew build", "```", "",
              "`spring init`이 서비스 4개의 골격(`build.gradle`, `settings.gradle`, 애플리케이션 클래스, "
              "테스트 클래스, `application.properties`)을 만듭니다. 생성 결과는 저장소의 "
              "[`Chapter03/1-spring-init`](" + GH + "/tree/main/Chapter03/1-spring-init)과 같아야 합니다. "
              "`spring` 명령이 없다면 그 폴더를 복사해서 이어가도 됩니다.", ""]
    for p in sorted(list_files(init)):
        if p in ("create-projects.bash", "settings.gradle"):
            continue
        lines.append(marker(p, "copy"))
    lines.append("")
    return lines


def nav(n, prev):
    i = CODE_CHAPTERS.index(n)
    parts = []
    if i > 0:
        parts.append(f"← [{prev}장 워크북](Chapter{prev:02d}.md)")
    parts.append("[워크북 목차](README.md)")
    if i + 1 < len(CODE_CHAPTERS):
        nx = CODE_CHAPTERS[i + 1]
        parts.append(f"[{nx}장 워크북](Chapter{nx:02d}.md) →")
    return " · ".join(parts)


def readme():
    from notes import README_TEXT
    rows = []
    for i, n in enumerate(CODE_CHAPTERS):
        prev = CODE_CHAPTERS[i - 1] if i else None
        ch = changes(os.path.join(ROOT, "Chapter03", "1-spring-init") if n == 3 else chapter_dir(prev), chapter_dir(n))
        new_lines = 0
        for p, old, new, _ in ch:
            if new is None or new == BINARY or copy_note(p):
                continue
            if old is None:
                new_lines += len(new.splitlines())
            else:
                sm = difflib.SequenceMatcher(None, old.splitlines(), new.splitlines())
                new_lines += sum(j2 - j1 for t, i1, i2, j1, j2 in sm.get_opcodes() if t in ("replace", "insert"))
        files = sum(1 for p, o, w, _ in ch if w is not None)
        rows.append(f"| [{n}장 {L.C[n]['t']}](Chapter{n:02d}.md) | {files} | 약 {new_lines:,} |")
    no_code = ", ".join(f"[{n}장]({GH}/blob/main/Chapter{n:02d}/BOOK-GUIDE.md)" for n in (1, 2, 8, 21, 22))
    return README_TEXT.format(table="\n".join(rows), no_code=no_code, gh=GH).strip("\n") + "\n"


def main():
    os.makedirs(OUT, exist_ok=True)
    expected = {"README.md"}
    open(os.path.join(OUT, "README.md"), "w", encoding="utf-8").write(readme())
    for i, n in enumerate(CODE_CHAPTERS):
        prev = CODE_CHAPTERS[i - 1] if i else None
        name = f"Chapter{n:02d}.md"
        expected.add(name)
        open(os.path.join(OUT, name), "w", encoding="utf-8").write(chapter_page(n, prev))
    for f in os.listdir(OUT):
        if f.endswith(".md") and f not in expected:
            os.remove(os.path.join(OUT, f))
    print(f"workbook pages: {len(expected)}")


if __name__ == "__main__":
    main()
