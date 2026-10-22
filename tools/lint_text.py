# <wtl> project: watchthelight-labs.github.io | file: tools/lint_text.py | author: watchthelight </wtl>
"""Minimal public-text check for machines without the humanize skill's slop_lint.py.

  python tools/lint_text.py FILE...

Hard hits (exit 1): em dashes, and the AI phrases Bash has banned before. Only the lines changed matter in
practice, so run it on the files you edited. slop_lint.py is stricter; use it when it is installed.
"""
import re
import sys

HARD = [
    (re.compile("—"), "em dash"),
    (re.compile(r"(?i)\b(delve|tapestry|testament to|game[- ]changer|seamless(ly)?|robust solution|"
                r"in today's (fast-paced|digital)|it'?s worth noting|leverag(e|ing) the power|unlock(ing)? the (full )?potential|"
                r"elevate your|cutting-edge|revolutioni[sz]e|embark on|a journey)\b"), "AI phrase"),
    (re.compile(r"(?i)generated with claude|co-authored-by: claude"), "AI attribution"),
]


def main():
    hits = 0
    for path in sys.argv[1:]:
        for n, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
            for rx, what in HARD:
                if rx.search(line):
                    hits += 1
                    print(f"{path}:{n}: {what}: {line.strip()[:100]}")
    print(f"{hits} hard hit(s)")
    sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main()
