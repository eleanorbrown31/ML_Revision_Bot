"""Validate question YAML and reading Markdown against the curriculum, offline.

Run manually: python scripts/validate_content.py

No database needed: the curriculum tree is imported from seed_curriculum.py,
which is the same source the database is seeded from. Checks every file under
content/questions/ (recursively) and content/readings/:

- area / topic / subtopic names resolve (exact match)
- difficulty and format are in the allowed sets
- payload and answer_key have the shape lib/scoring.py expects
- no duplicate (subtopic, stem) pairs across all files
- readings: '# Area' first line, every '## Topic' resolves

Exit code 1 and a list of problems if anything is wrong.
"""

import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from seed_curriculum import CURRICULUM  # noqa: E402
from lib.constants import DIFFICULTY_BANDS, QUESTION_FORMATS  # noqa: E402

QUESTIONS_DIR = ROOT / "content" / "questions"
READINGS_DIR = ROOT / "content" / "readings"

TREE = {area: {topic: set(subs) for topic, subs in topics} for area, topics in CURRICULUM}


def check_question(q: dict, default_area: str | None, where: str, problems: list[str]) -> tuple | None:
    area = q.get("area", default_area)
    topic, sub = q.get("topic"), q.get("subtopic")
    stem = q.get("stem")
    if not stem:
        problems.append(f"{where}: missing stem")
        return None
    if area not in TREE:
        problems.append(f"{where}: unknown area {area!r}")
        return None
    if topic not in TREE[area]:
        problems.append(f"{where}: unknown topic {topic!r} in area {area!r}")
        return None
    if sub not in TREE[area][topic]:
        problems.append(f"{where}: unknown subtopic {sub!r} in topic {topic!r}")
        return None
    if q.get("difficulty") not in DIFFICULTY_BANDS:
        problems.append(f"{where}: bad difficulty {q.get('difficulty')!r}")
    fmt = q.get("format")
    if fmt not in QUESTION_FORMATS:
        problems.append(f"{where}: bad format {fmt!r}")
        return (area, topic, sub, stem)
    payload, key = q.get("payload") or {}, q.get("answer_key") or {}
    if not q.get("explanation"):
        problems.append(f"{where}: missing explanation")
    if fmt == "mcq":
        opts = payload.get("options")
        if not isinstance(opts, list) or len(opts) < 3:
            problems.append(f"{where}: mcq needs >=3 options")
        elif not isinstance(key.get("correct"), int) or not 0 <= key["correct"] < len(opts):
            problems.append(f"{where}: mcq correct index out of range")
        elif len(set(map(str, opts))) != len(opts):
            problems.append(f"{where}: mcq duplicate options")
    elif fmt == "multi":
        opts = payload.get("options")
        c = key.get("correct")
        if not isinstance(opts, list) or len(opts) < 3:
            problems.append(f"{where}: multi needs >=3 options")
        elif not isinstance(c, list) or not c or any(
            not isinstance(i, int) or not 0 <= i < len(opts) for i in c
        ):
            problems.append(f"{where}: multi correct must be a non-empty list of valid indices")
    elif fmt == "fill":
        tpl = payload.get("template", "")
        n_blanks = tpl.count("___")
        blanks = key.get("blanks")
        if n_blanks == 0:
            problems.append(f"{where}: fill template has no ___")
        if not isinstance(blanks, list) or len(blanks) != n_blanks:
            got = len(blanks) if isinstance(blanks, list) else "no"
            problems.append(f"{where}: fill has {n_blanks} blanks but {got} answer lists")
        elif any(not isinstance(b, list) or not b for b in blanks):
            problems.append(f"{where}: every fill blank needs a non-empty synonym list")
    elif fmt == "match":
        # The renderer offers the full `right` list as dropdown options for every
        # `left` item (app/components/question_render.py) -- it does not require
        # left/right to be the same length or pairs to be a bijection. A shorter
        # `right` list with repeated values is a legitimate "classify N items into
        # K categories" question, not an error.
        left, right, pairs = payload.get("left"), payload.get("right"), key.get("pairs")
        if not isinstance(left, list) or len(left) < 3:
            problems.append(f"{where}: match needs a left list (>=3)")
        elif not isinstance(right, list) or len(right) < 2:
            problems.append(f"{where}: match needs a right list (>=2)")
        elif not isinstance(pairs, dict) or set(pairs) != set(left):
            problems.append(f"{where}: match pairs must cover every left item exactly once")
        elif not set(pairs.values()) <= set(right):
            problems.append(f"{where}: match pairs must only use values from the right list")
        elif len(left) == len(right) and set(pairs.values()) != set(right):
            problems.append(f"{where}: match has equal-length left/right but doesn't use every right value -- check for a typo")
    elif fmt == "order":
        items, seq = payload.get("items"), key.get("sequence")
        if not isinstance(items, list) or len(items) < 3:
            problems.append(f"{where}: order needs >=3 items")
        elif not isinstance(seq, list) or sorted(seq) != list(range(len(items))):
            problems.append(f"{where}: order sequence must be a permutation of item indices")
    elif fmt == "numeric":
        if "prompt" not in payload:
            problems.append(f"{where}: numeric needs payload.prompt")
        if not isinstance(key.get("value"), (int, float)) or not isinstance(key.get("tolerance"), (int, float)):
            problems.append(f"{where}: numeric needs numeric value and tolerance")
    return (area, topic, sub, stem)


def main() -> int:
    problems: list[str] = []
    seen: dict[tuple, str] = {}
    total = 0
    per_area: dict[str, int] = {}
    per_file: list[tuple[str, int]] = []
    for path in sorted(QUESTIONS_DIR.rglob("*.yaml")):
        rel = str(path.relative_to(QUESTIONS_DIR))
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            problems.append(f"{rel}: YAML parse error: {e}")
            continue
        if not isinstance(data, dict) or not isinstance(data.get("questions"), list):
            problems.append(f"{rel}: needs top-level 'questions' list")
            continue
        per_file.append((rel, len(data["questions"])))
        for i, q in enumerate(data["questions"], 1):
            total += 1
            ident = check_question(q, data.get("area"), f"{rel} #{i}", problems)
            if ident:
                per_area[ident[0]] = per_area.get(ident[0], 0) + 1
                k = (ident[2], ident[3])
                if k in seen:
                    problems.append(f"{rel} #{i}: duplicate stem also in {seen[k]}")
                seen[k] = f"{rel} #{i}"

    for path in sorted(READINGS_DIR.glob("*.md")):
        lines = path.read_text(encoding="utf-8").splitlines()
        if not lines or not lines[0].startswith("# "):
            problems.append(f"{path.name}: first line must be '# Area'")
            continue
        area = lines[0][2:].strip()
        if area not in TREE:
            problems.append(f"{path.name}: unknown area {area!r}")
            continue
        for m in re.finditer(r"^## (.+)$", "\n".join(lines[1:]), re.MULTILINE):
            if m.group(1).strip() not in TREE[area]:
                problems.append(f"{path.name}: unknown topic {m.group(1).strip()!r}")

    print(f"{total} questions checked across {len(per_file)} files")
    for a, n in sorted(per_area.items(), key=lambda x: -x[1]):
        print(f"  {n:4d}  {a}")
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print("  -", p)
        return 1
    print("\nOK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
