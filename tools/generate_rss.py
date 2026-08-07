from __future__ import annotations

"""전문수업.com의 핵심 학습·과목 허브만 담은 RSS 2.0 피드를 만든다."""

import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "https://xn--z92bu9jx8cwzc.com"
FEED_PATH = ROOT / "rss.xml"
SEOUL = timezone(timedelta(hours=9), name="KST")

# 상세 7천여 개를 전부 싣지 않고, 검색 로봇과 이용자가 실제로 탐색할 핵심 허브만 제공한다.
ITEM_PATHS = [
    Path("과목별학원/고2영어학원"),
    Path("과목별학원/고2수학학원"),
    Path("과목별학원/고1영어학원"),
    Path("과목별학원/고1수학학원"),
    Path("과목별학원/중3영어학원"),
    Path("과목별학원/중3수학학원"),
    Path("과목별학원/중2영어학원"),
    Path("과목별학원/중2수학학원"),
    Path("과목별학원"),
    Path("전국학원"),
    Path("학습가이드"),
]


def page_url(relative: Path) -> str:
    encoded = "/".join(quote(part, safe="") for part in relative.parts)
    return f"{DOMAIN}/{encoded}/"


def first_match(pattern: str, text: str) -> str:
    match = re.search(pattern, text, flags=re.I | re.S)
    if not match:
        return ""
    return html.unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip()


def main() -> None:
    now = datetime.now(SEOUL).replace(microsecond=0)
    ET.register_namespace("atom", "http://www.w3.org/2005/Atom")
    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "전문수업.com 학습 안내 RSS"
    ET.SubElement(channel, "link").text = f"{DOMAIN}/"
    ET.SubElement(channel, "description").text = (
        "전문수업.com의 학습가이드, 전국학원과 학년·과목별 지역 학습 안내 허브를 제공합니다."
    )
    ET.SubElement(channel, "language").text = "ko-KR"
    ET.SubElement(channel, "lastBuildDate").text = format_datetime(now)
    ET.SubElement(
        channel,
        "{http://www.w3.org/2005/Atom}link",
        {
            "href": f"{DOMAIN}/rss.xml",
            "rel": "self",
            "type": "application/rss+xml",
        },
    )

    seen: set[str] = set()
    entries: list[tuple[datetime, str, str, str]] = []
    for relative in ITEM_PATHS:
        source = ROOT / relative / "index.html"
        if not source.exists():
            raise FileNotFoundError(f"RSS 원본 페이지가 없습니다: {source}")
        text = source.read_text(encoding="utf-8")
        title = first_match(r"<title\b[^>]*>(.*?)</title>", text)
        description = first_match(
            r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']\s*/?>',
            text,
        )
        url = page_url(relative)
        if not title or not description:
            raise ValueError(f"RSS 제목 또는 설명을 읽을 수 없습니다: {source}")
        if url in seen:
            raise ValueError(f"RSS URL이 중복되었습니다: {url}")
        seen.add(url)

        modified = datetime.fromtimestamp(source.stat().st_mtime, SEOUL).replace(microsecond=0)
        if modified > now:
            modified = now
        entries.append((modified, title, description, url))

    for modified, title, description, url in sorted(entries, reverse=True):
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = url
        ET.SubElement(item, "guid", {"isPermaLink": "true"}).text = url
        ET.SubElement(item, "pubDate").text = format_datetime(modified)
        ET.SubElement(item, "description").text = description

    ET.indent(rss, space="  ")
    xml = ET.tostring(rss, encoding="utf-8", xml_declaration=True)
    FEED_PATH.write_bytes(xml + b"\n")
    print(f"rss_items={len(seen)}")
    print(f"target={FEED_PATH}")


if __name__ == "__main__":
    main()
