from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "content" / "posts"
OUTPUT_FILE = ROOT / "content" / "posts-manifest.json"
VALID_CATEGORIES = {"tech", "galgame", "nongalgame"}


def parse_frontmatter(raw: str) -> tuple[dict[str, str], str]:
    if not raw.startswith("---\n"):
        raise ValueError("missing frontmatter start")

    end_marker = "\n---\n"
    end_index = raw.find(end_marker, 4)
    if end_index == -1:
        raise ValueError("missing frontmatter end")

    frontmatter_block = raw[4:end_index]
    body = raw[end_index + len(end_marker):].strip()
    data: dict[str, str] = {}

    for line in frontmatter_block.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            raise ValueError(f"invalid frontmatter line: {line}")
        key, value = stripped.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")

    return data, body


def summarize_markdown(body: str, limit: int = 180) -> str:
    plain = re.sub(r"```[\s\S]*?```", " ", body)
    plain = re.sub(r"`[^`]*`", " ", plain)
    plain = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", plain)
    plain = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", plain)
    plain = re.sub(r"^[#>\-*+\s]+", "", plain, flags=re.MULTILINE)
    plain = re.sub(r"\s+", " ", plain).strip()
    return plain[:limit].rstrip() + ("..." if len(plain) > limit else "")


def estimate_word_count(body: str) -> int:
    plain = re.sub(r"```[\s\S]*?```", " ", body)
    plain = re.sub(r"`[^`]*`", " ", plain)
    plain = re.sub(r"!\[[^\]]*\]\([^)]+\)", " ", plain)
    plain = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", plain)
    plain = re.sub(r"[#>*_\-\[\]\(\)!]", " ", plain)
    chinese_chars = re.findall(r"[\u4e00-\u9fff]", plain)
    latin_words = re.findall(r"[A-Za-z0-9_]+", plain)
    return len(chinese_chars) + len(latin_words)


def collect_posts() -> list[dict[str, str | int]]:
    posts: list[dict[str, str | int]] = []

    for path in sorted(POSTS_DIR.rglob("*.md")):
        if path.name.startswith("_"):
            continue

        raw = path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(raw)

        required_fields = {"title", "slug", "category", "date", "summary"}
        missing = required_fields - set(meta)
        if missing:
            raise ValueError(f"{path.name} missing fields: {', '.join(sorted(missing))}")

        category = meta["category"]
        if category not in VALID_CATEGORIES:
            raise ValueError(f"{path.name} has invalid category: {category}")

        posts.append(
            {
                "title": meta["title"],
                "slug": meta["slug"],
                "category": category,
                "date": meta["date"],
                "summary": meta["summary"],
                "path": f"./content/posts/{path.relative_to(POSTS_DIR).as_posix()}",
                "content": body,
                "excerpt": summarize_markdown(body),
                "wordCount": estimate_word_count(body),
            }
        )

    posts.sort(key=lambda post: str(post["date"]), reverse=True)
    return posts


def main() -> None:
    payload = {"posts": collect_posts()}
    OUTPUT_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"generated {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
