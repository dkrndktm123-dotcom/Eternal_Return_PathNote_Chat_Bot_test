import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://playeternalreturn.com"
NEWS_URL = "https://playeternalreturn.com/posts/news?categoryPath=patchnote&hl=ko-KR"

ARMOR_SLOTS = {"옷", "머리", "팔", "다리", "장식"}
CHARACTER_NAMES = {
    "가넷","나딘","나타폰","니아","니키","다니엘","다르코","데비&마를렌","띠아","라우라","레녹스","레니","레온",
    "로지","루크","르노어","리 다이린","리오","마르티나","마이","마커스","매그너스","미르카","바냐","바바라",
    "버니스","블레어","비앙카","비형","샬럿","셀린","쇼우","쇼이치","수아","슈린","시셀라","실비아","아델라",
    "아드리아나","아디나","아르다","아비게일","아야","아이솔","아이작","알렉스","알론소","얀","에스텔","에이든",
    "에키온","엘레나","엠마","요환","윌리엄","유민","유스티나","유키","이렘","이바","이슈트반","이안","일레븐",
    "자히르","재키","제니","츠바메","카밀로","카티야","칼라","캐시","케네스","코렐라인","크레이버","클로에",
    "키아라","타지아","테오도르","펜리르","펠릭스","프리야","피오라","피올로","하트","헤이즈","헨리","현우",
    "혜진","히스이"
}

def clean(text: str) -> str:
    text = text or ""
    text = text.replace("\xa0", " ").replace("\u200b", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def get_patch_urls(limit: int = 10):
    res = requests.get(NEWS_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")
    urls, seen = [], set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        full = urljoin(BASE_URL, href)
        if re.match(r"^https://playeternalreturn\.com/posts/news/\d+", full):
            if "hl=" not in full:
                full += "?hl=ko-KR"
            if full not in seen:
                seen.add(full)
                urls.append(full)
        if len(urls) >= limit:
            break
    return urls

def extract_lines(content_root):
    raw = content_root.get_text("\n", strip=True)
    lines = [clean(x) for x in raw.splitlines()]
    lines = [x for x in lines if x]
    dedup = []
    for line in lines:
        if not dedup or dedup[-1] != line:
            dedup.append(line)
    return dedup

def get_major_spans(lines):
    spans = []
    major_keys = [
        ("신규 스킨 및 이모티콘", "skins_emote"),
        ("시스템 개선 사항", "system"),
        ("매치메이킹 개선", "matchmaking"),
        ("무기 스킬", "weapon_skill"),
        ("실험체", "character"),
        ("방어구", "armor"),
        ("코발트 프로토콜", "cobalt_protocol"),
        ("버그 수정 및 개선 사항", "bugfix_general"),
        ("게임 플레이 개선 사항", "bugfix_general"),
        ("실험체 및 무기 개선 사항", "bugfix_character"),
    ]
    indices = []
    for i, line in enumerate(lines):
        for key, tag in major_keys:
            if key in line:
                indices.append((i, tag, line))
                break
    for idx, (start, tag, raw_title) in enumerate(indices):
        end = indices[idx + 1][0] if idx + 1 < len(indices) else len(lines)
        spans.append((tag, raw_title, lines[start:end]))
    return spans

def parse_skin_emote_section(block_lines, image_urls, patch_version, patch_title, url, order_start):
    chunks = []
    order_index = order_start
    current_skin = None
    current_skin_lines = []
    emote_lines = []
    emote_started = False

    for line in block_lines[1:]:
        if "시스템 개선 사항" in line or "매치메이킹 개선" in line:
            break
        if re.search(r"\((영웅|희귀|전설|고급|일반)\)", line) and "스킨" not in line and "이모티콘" not in line:
            if current_skin:
                chunks.append({
                    "patch_version": patch_version,
                    "patch_title": patch_title,
                    "category": "skins",
                    "entity_name": current_skin,
                    "title": current_skin,
                    "content": "\n".join(current_skin_lines).strip(),
                    "url": url,
                    "image_urls": image_urls[:2],  # 10.7 패치 기준 스킨 이미지 2장
                    "order_index": order_index,
                })
                order_index += 1
            current_skin = line
            current_skin_lines = []
            continue

        if "이모티콘이 출시됩니다" in line:
            emote_started = True
            emote_lines = [line]
            continue

        if emote_started:
            # 이모티콘 소개는 출시 문구까지만 저장
            break

        if current_skin:
            current_skin_lines.append(line)

    if current_skin:
        chunks.append({
            "patch_version": patch_version,
            "patch_title": patch_title,
            "category": "skins",
            "entity_name": current_skin,
            "title": current_skin,
            "content": "\n".join(current_skin_lines).strip(),
            "url": url,
            "image_urls": image_urls[:2],
            "order_index": order_index,
        })
        order_index += 1

    if emote_lines:
        chunks.append({
            "patch_version": patch_version,
            "patch_title": patch_title,
            "category": "emote",
            "entity_name": "이모티콘",
            "title": "이모티콘",
            "content": "\n".join(emote_lines).strip(),
            "url": url,
            "image_urls": image_urls[2:3],  # 10.7 패치 기준 이모티콘 이미지 1장
            "order_index": order_index,
        })
        order_index += 1

    return chunks, order_index

def parse_simple_named_list(block_lines, category, patch_version, patch_title, url, order_start):
    chunks = []
    order_index = order_start
    current_entity = None
    current_lines = []

    def flush():
        nonlocal current_entity, current_lines, order_index
        if current_entity and current_lines:
            chunks.append({
                "patch_version": patch_version,
                "patch_title": patch_title,
                "category": category,
                "entity_name": current_entity,
                "title": current_entity,
                "content": "\n".join(current_lines).strip(),
                "url": url,
                "image_urls": [],
                "order_index": order_index,
            })
            order_index += 1
        current_entity = None
        current_lines = []

    for line in block_lines[1:]:
        if category == "character" and line in CHARACTER_NAMES:
            flush()
            current_entity = line
            continue
        if category == "armor" and line in ARMOR_SLOTS:
            flush()
            current_entity = line
            continue
        if category == "weapon_skill":
            if re.search(r"[가-힣A-Za-z ]+\s*-\s*.+\([DQWER]\)$", line):
                flush()
                current_entity = line
                continue
        if current_entity:
            current_lines.append(line)
    flush()
    return chunks, order_index

def parse_free_block(block_lines, category, title, patch_version, patch_title, url, order_start):
    content = "\n".join(block_lines[1:]).strip()
    if not content:
        return [], order_start
    return ([{
        "patch_version": patch_version,
        "patch_title": patch_title,
        "category": category,
        "entity_name": title,
        "title": title,
        "content": content,
        "url": url,
        "image_urls": [],
        "order_index": order_start,
    }], order_start + 1)

def parse_one_patch(url: str):
    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    page_title = clean(soup.title.get_text()) if soup.title else ""
    page_title = page_title.replace(" :: 이터널 리턴", "").replace(" :: Eternal Return", "")
    version_match = re.search(r"(\d+(?:\.\d+)*)", page_title)
    patch_version = version_match.group(1) if version_match else ""

    content_root = None
    for sel in [".fr-view", ".board-view__content", ".post-view__content", ".news-view__content", ".article-content", "article", "main", "body"]:
        node = soup.select_one(sel)
        if node:
            content_root = node
            break
    if content_root is None:
        return []

    image_urls = []
    for img in content_root.find_all("img"):
        src = img.get("src")
        if src:
            image_urls.append(urljoin(BASE_URL, src))

    lines = extract_lines(content_root)
    spans = get_major_spans(lines)

    chunks = []
    order_index = 0
    for tag, raw_title, block_lines in spans:
        if tag == "skins_emote":
            new_chunks, order_index = parse_skin_emote_section(
                block_lines, image_urls, patch_version, page_title, url, order_index
            )
            chunks.extend(new_chunks)
        elif tag == "weapon_skill":
            new_chunks, order_index = parse_simple_named_list(
                block_lines, "weapon_skill", patch_version, page_title, url, order_index
            )
            chunks.extend(new_chunks)
        elif tag == "character":
            new_chunks, order_index = parse_simple_named_list(
                block_lines, "character", patch_version, page_title, url, order_index
            )
            chunks.extend(new_chunks)
        elif tag == "armor":
            new_chunks, order_index = parse_simple_named_list(
                block_lines, "armor", patch_version, page_title, url, order_index
            )
            # DB category는 item 으로 저장
            for c in new_chunks:
                c["category"] = "item"
            chunks.extend(new_chunks)
        elif tag == "system":
            new_chunks, order_index = parse_free_block(
                block_lines, "system", "시스템 개선 사항", patch_version, page_title, url, order_index
            )
            chunks.extend(new_chunks)
        elif tag == "matchmaking":
            new_chunks, order_index = parse_free_block(
                block_lines, "matchmaking", "매치메이킹 개선", patch_version, page_title, url, order_index
            )
            chunks.extend(new_chunks)
        elif tag == "cobalt_protocol":
            new_chunks, order_index = parse_free_block(
                block_lines, "cobalt_protocol", "코발트 프로토콜", patch_version, page_title, url, order_index
            )
            chunks.extend(new_chunks)
        elif tag == "bugfix_general":
            new_chunks, order_index = parse_free_block(
                block_lines, "system", raw_title, patch_version, page_title, url, order_index
            )
            chunks.extend(new_chunks)
        elif tag == "bugfix_character":
            new_chunks, order_index = parse_free_block(
                block_lines, "bugfix_character", raw_title, patch_version, page_title, url, order_index
            )
            chunks.extend(new_chunks)

    return chunks

def parse_patch(limit: int = 10):
    urls = get_patch_urls(limit=limit)
    all_chunks = []
    for url in urls:
        try:
            all_chunks.extend(parse_one_patch(url))
        except Exception as e:
            print("PARSE ERROR:", url, e)
    return all_chunks
