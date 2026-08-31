#!/usr/bin/env python3
"""Import the 350-layout collection and build its GitHub Markdown galleries."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class Category:
    source_name: str
    slug: str
    title: str
    description: str


CATEGORIES = (
    Category("构图逻辑名称", "01-composition-logic", "构图逻辑", "从经典比例、几何形态、空间层次到视点组织，建立画面的基础骨架。"),
    Category("视觉原则与阅读模式名称", "02-visual-principles", "视觉原则与阅读模式", "用格式塔原则、视觉层级和阅读路径解释信息如何被看见与理解。"),
    Category("平面出版广告排版名称", "03-editorial-advertising", "平面、出版与广告", "覆盖海报、书刊、包装、广告等常见平面媒介的版式结构。"),
    Category("字体网格与东亚文字排版名称", "04-type-grid-cjk", "字体、网格与东亚文字", "聚焦字体编排、网格系统，以及横排、直排和中西文混排。"),
    Category("网页与UI布局名称", "05-web-ui", "网页与 UI", "收录网站和产品界面的导航、内容、表单与响应式布局模式。"),
    Category("影视画面构图名称", "06-film-frame", "影视画面构图", "以镜头、景别、机位和画幅关系组织动态影像中的单个画面。"),
    Category("中国传统构图名称", "07-chinese-composition", "中国传统构图", "整理中国绘画与传统视觉中的空间经营、散点透视和章法。"),
    Category("演示文稿页面布局名称", "08-presentation", "演示文稿页面", "覆盖封面、目录、内容、比较、数据、流程和全图等幻灯片版式。"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_mapping(mapping_path: Path) -> list[dict[str, str]]:
    with mapping_path.open(encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source, delimiter="\t"))
    if len(rows) != 350:
        raise ValueError(f"映射表应有 350 项，实际为 {len(rows)} 项")
    expected = [f"{number:03d}" for number in range(1, 351)]
    actual = [row["序号"] for row in rows]
    if actual != expected:
        raise ValueError("映射表序号不是连续的 001–350")
    return rows


def image_name(row: dict[str, str]) -> str:
    return Path(row["新文件名"]).name


def layout_name(row: dict[str, str]) -> str:
    return Path(image_name(row)).stem.split("-", 1)[1]


def build_gallery_page(repo: Path, category: Category, items: list[dict[str, object]]) -> None:
    page = repo / "docs" / "350" / f"{category.slug}.md"
    lines = [
        f"# {category.title} · {len(items)} 种",
        "",
        category.description,
        "",
        "[← 返回 350 种排版总目录](README.md)",
        "",
    ]
    for offset in range(0, len(items), 4):
        group = items[offset : offset + 4]
        cells = []
        labels = []
        for item in group:
            full = Path(str(item["image"]))
            thumb = Path(str(item["thumbnail"]))
            cells.append(
                f'<a href="../../{full.as_posix()}"><img src="../../{thumb.as_posix()}" width="180" alt="{item["id"]} {item["name"]}"></a>'
            )
            labels.append(f'**{item["id"]}**<br>{item["name"]}')
        while len(cells) < 4:
            cells.append("")
            labels.append("")
        lines.extend(
            [
                "| " + " | ".join(cells) + " |",
                "| :---: | :---: | :---: | :---: |",
                "| " + " | ".join(labels) + " |",
                "",
            ]
        )
    page.write_text("\n".join(lines), encoding="utf-8")


def build_index(repo: Path, grouped: dict[str, list[dict[str, object]]]) -> None:
    lines = [
        "# 350 种排版 · 分类图鉴",
        "",
        "这是一套从构图基础到具体媒介的排版知识图鉴。350 个版式按 8 个应用与知识板块组织；点击分类浏览全部缩略图，再点击任意缩略图查看高清 PNG。",
        "",
        "[← 返回项目首页](../../README.md)",
        "",
        "## 分类目录",
        "",
        "| 分类 | 数量 | 范围 | 内容 |",
        "| --- | ---: | --- | --- |",
    ]
    for category in CATEGORIES:
        items = grouped[category.source_name]
        first, last = items[0]["id"], items[-1]["id"]
        lines.append(
            f"| [{category.title}]({category.slug}.md) | {len(items)} | {first}–{last} | {category.description} |"
        )
    lines.extend(
        [
            "",
            "## 浏览方式",
            "",
            "- 想系统学习：按 01–08 的顺序浏览。",
            "- 想解决具体设计问题：直接进入对应媒介分类。",
            "- 想查某个名称：在 GitHub 页面使用浏览器查找，或下载 [`catalog.csv`](../../v2/catalog.csv)。",
            "",
            "## 数据说明",
            "",
            "- 高清图：[`v2/images/`](../../v2/images/)",
            "- 轻量预览：[`v2/thumbnails/`](../../v2/thumbnails/)",
            "- 机器可读目录：[`catalog.json`](../../v2/catalog.json) / [`catalog.csv`](../../v2/catalog.csv)",
            "- 每项均保留全局连续编号，分类不会改变编号与名称之间的对应关系。",
            "",
        ]
    )
    (repo / "docs" / "350" / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="350 张瑞士平面图片目录")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--skip-images", action="store_true", help="只重建目录和 Markdown")
    args = parser.parse_args()

    repo = args.repo.resolve()
    source = args.source.resolve()
    mapping_path = source / "整理结果" / "图片对应关系.tsv"
    source_images = source / "整理结果" / "按主题分组"
    rows = parse_mapping(mapping_path)
    category_by_source = {category.source_name: category for category in CATEGORIES}
    unknown = sorted({row["主题"] for row in rows} - set(category_by_source))
    if unknown:
        raise ValueError(f"发现未知分类：{', '.join(unknown)}")

    (repo / "docs" / "350").mkdir(parents=True, exist_ok=True)
    (repo / "v2" / "images").mkdir(parents=True, exist_ok=True)
    (repo / "v2" / "thumbnails").mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[dict[str, object]]] = {category.source_name: [] for category in CATEGORIES}
    catalog: list[dict[str, object]] = []

    for row in rows:
        category = category_by_source[row["主题"]]
        filename = image_name(row)
        source_image = source_images / row["主题"] / filename
        if not source_image.is_file():
            raise FileNotFoundError(source_image)
        image_path = Path("v2") / "images" / category.slug / filename
        thumb_path = Path("v2") / "thumbnails" / category.slug / f"{Path(filename).stem}.jpg"
        target_image = repo / image_path
        target_thumb = repo / thumb_path
        target_image.parent.mkdir(parents=True, exist_ok=True)
        target_thumb.parent.mkdir(parents=True, exist_ok=True)
        if not args.skip_images:
            if not target_image.exists() or source_image.stat().st_size != target_image.stat().st_size:
                shutil.copy2(source_image, target_image)
            if not target_thumb.exists() or target_thumb.stat().st_mtime < source_image.stat().st_mtime:
                with Image.open(source_image) as image:
                    image.thumbnail((480, 640), Image.Resampling.LANCZOS)
                    image.convert("RGB").save(target_thumb, "JPEG", quality=82, optimize=True, progressive=True)
        if not target_image.is_file() or not target_thumb.is_file():
            raise FileNotFoundError(f"缺少输出图片：{target_image} / {target_thumb}")
        with Image.open(target_image) as imported_image:
            width, height = imported_image.size
        item: dict[str, object] = {
            "id": row["序号"],
            "name": layout_name(row),
            "category": category.title,
            "category_slug": category.slug,
            "image": image_path.as_posix(),
            "thumbnail": thumb_path.as_posix(),
            "width": width,
            "height": height,
            "sha256": sha256(target_image),
        }
        catalog.append(item)
        grouped[row["主题"]].append(item)

    with (repo / "v2" / "catalog.json").open("w", encoding="utf-8") as target:
        json.dump(catalog, target, ensure_ascii=False, indent=2)
        target.write("\n")
    with (repo / "v2" / "catalog.csv").open("w", encoding="utf-8-sig", newline="") as target:
        fields = ["id", "name", "category", "category_slug", "image", "thumbnail", "width", "height", "sha256"]
        writer = csv.DictWriter(target, fieldnames=fields)
        writer.writeheader()
        writer.writerows(catalog)

    for category in CATEGORIES:
        build_gallery_page(repo, category, grouped[category.source_name])
    build_index(repo, grouped)
    print(f"已导入 {len(catalog)} 张图片，生成 {len(CATEGORIES)} 个分类页面。")


if __name__ == "__main__":
    main()
