#!/usr/bin/env python3
"""Generate meta/loc.csv from git history (elocuent-compatible)."""

import csv
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPACES_PER_LEVEL = 2

TEXT_EXTS = {
    ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx",
    ".html", ".css", ".scss", ".sass", ".less",
    ".json", ".md", ".txt", ".py", ".sh",
    ".yml", ".yaml", ".toml", ".xml", ".svg",
    ".csv",
}
EXT_TO_TYPE = {
    ".js": "JS", ".mjs": "JS", ".cjs": "JS",
    ".ts": "TS", ".tsx": "TSX", ".jsx": "JSX",
    ".html": "HTML", ".css": "CSS",
    ".scss": "SCSS", ".sass": "SASS", ".less": "LESS",
    ".json": "JSON", ".md": "Markdown", ".txt": "Text",
    ".py": "Python", ".sh": "Shell",
    ".yml": "YAML", ".yaml": "YAML", ".toml": "TOML",
    ".xml": "XML", ".svg": "SVG", ".csv": "CSV",
}


def run(cmd, cwd=ROOT):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


def tracked_text_files():
    res = run(["git", "ls-files"])
    files = []
    for line in res.stdout.splitlines():
        p = ROOT / line
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        if ext not in TEXT_EXTS:
            continue
        files.append(line)
    return files


def parse_blame(rel_path):
    """Return list of dicts (one per line) using git blame --line-porcelain."""
    res = run(["git", "blame", "--line-porcelain", "--", rel_path])
    if res.returncode != 0:
        return []
    lines_meta = []
    cur = {}
    for raw in res.stdout.splitlines():
        if not raw:
            continue
        if raw.startswith("\t"):
            cur["content"] = raw[1:]
            lines_meta.append(cur)
            cur = {}
            continue
        parts = raw.split(" ", 1)
        head = parts[0]
        rest = parts[1] if len(parts) > 1 else ""
        if len(head) == 40 and all(c in "0123456789abcdef" for c in head):
            cur["commit"] = head
        elif head == "author":
            cur["author"] = rest
        elif head == "author-time":
            cur["author_time"] = int(rest)
        elif head == "author-tz":
            cur["author_tz"] = rest
    return lines_meta


def depth_for_line(text):
    stripped = text.lstrip(" ")
    spaces = len(text) - len(stripped)
    return spaces // SPACES_PER_LEVEL


def fmt_offset(tz):
    sign = tz[0]
    hh = tz[1:3]
    mm = tz[3:5]
    return f"{sign}{hh}:{mm}"


def main():
    out_path = ROOT / "meta" / "loc.csv"
    out_path.parent.mkdir(exist_ok=True)
    rows = []
    for rel in tracked_text_files():
        meta = parse_blame(rel)
        ext = Path(rel).suffix.lower()
        ftype = EXT_TO_TYPE.get(ext, ext.lstrip(".").upper() or "Other")
        for i, m in enumerate(meta, start=1):
            content = m.get("content", "")
            t = m.get("author_time")
            tz = m.get("author_tz", "+0000")
            if t is None:
                continue
            import datetime as _dt
            sign = 1 if tz[0] == "+" else -1
            offset = _dt.timedelta(hours=int(tz[1:3]), minutes=int(tz[3:5])) * sign
            local = _dt.datetime.fromtimestamp(t, tz=_dt.timezone.utc) + offset
            date_str = local.strftime("%Y-%m-%d")
            time_str = local.strftime("%H:%M:%S")
            tz_str = fmt_offset(tz)
            datetime_str = f"{date_str}T{time_str}{tz_str}"
            rows.append({
                "file": rel,
                "type": ftype,
                "line": i,
                "depth": depth_for_line(content),
                "length": len(content),
                "commit": m.get("commit", ""),
                "author": m.get("author", ""),
                "date": date_str,
                "time": time_str,
                "timezone": tz_str,
                "datetime": datetime_str,
            })
    fieldnames = ["file", "type", "line", "depth", "length",
                  "commit", "author", "date", "time", "timezone", "datetime"]
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
