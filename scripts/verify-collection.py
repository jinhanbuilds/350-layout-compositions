#!/usr/bin/env python3
"""Verify both the classic 100-layout set and the classified 350-layout set."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def verify_classic() -> None:
    for number in range(1, 101):
        image = REPO / "images" / f"layout-{number:03d}.png"
        thumbnail = REPO / "thumbnails" / f"layout-{number:03d}.jpg"
        if not image.is_file() or not thumbnail.is_file():
            fail(f"经典版缺少第 {number:03d} 项")


def verify_v2() -> list[dict[str, object]]:
    json_path = REPO / "v2" / "catalog.json"
    csv_path = REPO / "v2" / "catalog.csv"
    catalog = json.loads(json_path.read_text(encoding="utf-8"))
    with csv_path.open(encoding="utf-8-sig", newline="") as source:
        csv_catalog = list(csv.DictReader(source))
    if len(catalog) != 350 or len(csv_catalog) != 350:
        fail(f"新版目录数量异常：JSON={len(catalog)}, CSV={len(csv_catalog)}")
    expected_ids = [f"{number:03d}" for number in range(1, 351)]
    if [item["id"] for item in catalog] != expected_ids:
        fail("新版目录编号不是连续的 001–350")
    if [item["id"] for item in csv_catalog] != expected_ids:
        fail("CSV 目录编号与 JSON 不一致")
    if len({item["name"] for item in catalog}) != 350:
        fail("新版目录中存在重复名称")
    if len({item["image"] for item in catalog}) != 350:
        fail("新版目录中存在重复图片路径")
    categories = {item["category_slug"] for item in catalog}
    if len(categories) != 8:
        fail(f"新版分类应为 8 个，实际为 {len(categories)} 个")

    for item in catalog:
        image_path = REPO / str(item["image"])
        thumb_path = REPO / str(item["thumbnail"])
        if not image_path.is_file() or not thumb_path.is_file():
            fail(f"{item['id']} 缺少高清图或缩略图")
        if not image_path.name.startswith(f"{item['id']}-{item['name']}"):
            fail(f"{item['id']} 名称与图片文件名不一致")
        with Image.open(image_path) as image:
            image.verify()
        with Image.open(image_path) as image:
            if list(image.size) != [int(item["width"]), int(item["height"])]:
                fail(f"{item['id']} 图片尺寸与目录不一致")
        with Image.open(thumb_path) as thumbnail:
            thumbnail.verify()
        if digest(image_path) != item["sha256"]:
            fail(f"{item['id']} SHA-256 与目录不一致")
    return catalog


def verify_markdown_links() -> None:
    pages = [REPO / "README.md", REPO / "v2" / "README.md"]
    pages.extend(sorted((REPO / "docs" / "350").glob("*.md")))
    link_pattern = re.compile(r'(?:href|src)="([^"]+)"|\[[^]]*\]\(([^)]+)\)')
    for page in pages:
        text = page.read_text(encoding="utf-8")
        for match in link_pattern.finditer(text):
            link = match.group(1) or match.group(2)
            if link.startswith(("http://", "https://", "#", "mailto:")):
                continue
            path = (page.parent / link).resolve()
            if not path.exists():
                fail(f"链接不存在：{page.relative_to(REPO)} -> {link}")


def main() -> None:
    verify_classic()
    catalog = verify_v2()
    verify_markdown_links()
    category_counts: dict[str, int] = {}
    for item in catalog:
        category = str(item["category"])
        category_counts[category] = category_counts.get(category, 0) + 1
    summary = "，".join(f"{name} {count}" for name, count in category_counts.items())
    print(f"验证通过：经典版 100 张；新版 350 张 / 8 类（{summary}）；本地链接完整。")


if __name__ == "__main__":
    main()
