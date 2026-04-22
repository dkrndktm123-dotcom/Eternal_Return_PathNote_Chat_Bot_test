import re
from db import get_conn

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
ARMOR_SLOT_NAMES = {"옷", "머리", "팔", "다리", "장식"}
CATEGORY_HINTS = {
    "코발트 프로토콜": "cobalt_protocol","코발트": "cobalt_protocol","무기 스킬": "weapon_skill","무기스킬": "weapon_skill",
    "이모티콘": "emote","이모지": "emote","스킨": "skins","캐릭터": "character","실험체": "character","시스템": "system",
    "매치메이킹": "matchmaking","방어구": "item","아이템": "item","무기": "weapon_skill",
}

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())

def ingest_chunks(chunks):
    conn = get_conn(); cur = conn.cursor(); cur.execute("DELETE FROM chunks")
    for c in chunks:
        cur.execute("""
        INSERT INTO chunks (
            patch_version, patch_title, category, entity_name, title, content, url, image_urls, order_index
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            c["patch_version"], c["patch_title"], c["category"], c["entity_name"],
            c["title"], c["content"], c["url"], "|".join(c.get("image_urls", [])), c["order_index"]
        ))
    conn.commit(); conn.close()

def detect_category(query: str):
    q = normalize(query)
    for k, v in CATEGORY_HINTS.items():
        if k in q: return v
    return None

def detect_entity(query: str):
    q = normalize(query)
    for name in sorted(CHARACTER_NAMES, key=len, reverse=True):
        if name in q: return name
    return None

def score_row(row, query, category_hint, entity_hint):
    score = 0
    entity_name = row["entity_name"] or ""
    title = row["title"] or ""
    content = row["content"] or ""
    category = row["category"] or ""
    q = normalize(query)

    if category_hint and category == category_hint: score += 80
    if entity_hint and entity_hint == entity_name: score += 300
    if "→" in content: score += 40
    if category == "skins" and "스킨" in q: score += 30
    if category == "emote" and "이모티콘" in q: score += 30
    if category == "weapon_skill" and ("무기 스킬" in q or q == "무기"): score += 40
    for t in [x for x in re.split(r"\s+", q) if x]:
        if t in entity_name: score += 20
        if t in title: score += 10
        if t in content: score += 3
    return score

def search(query: str, top_k: int = 5):
    query = normalize(query)
    category_hint = detect_category(query)
    entity_hint = detect_entity(query)

    conn = get_conn(); cur = conn.cursor()
    rows = cur.execute("SELECT * FROM chunks ORDER BY order_index ASC").fetchall()
    conn.close()

    if entity_hint:
        exact_rows = [r for r in rows if (r["entity_name"] or "") == entity_hint]
        if exact_rows:
            scored = [(score_row(r, query, category_hint, entity_hint), r) for r in exact_rows]
            scored.sort(key=lambda x: x[0], reverse=True)
            return [r for _, r in scored[:top_k]], category_hint, entity_hint
        return [], category_hint, entity_hint

    candidate_rows = rows
    if category_hint == "skins":
        candidate_rows = [r for r in rows if r["category"] == "skins"]
    elif category_hint == "emote":
        candidate_rows = [r for r in rows if r["category"] == "emote"]
    elif category_hint == "weapon_skill":
        candidate_rows = [r for r in rows if r["category"] == "weapon_skill"]
    elif category_hint == "cobalt_protocol":
        candidate_rows = [r for r in rows if r["category"] == "cobalt_protocol"]
    elif category_hint == "system":
        candidate_rows = [r for r in rows if r["category"] in {"system","matchmaking"}]
    elif category_hint == "character":
        candidate_rows = [r for r in rows if r["category"] in {"character","bugfix_character"}]
    elif category_hint == "item":
        candidate_rows = [r for r in rows if r["category"] == "item"]

    if "방어구" in query:
        candidate_rows = [r for r in candidate_rows if (r["category"] == "item") and ((r["title"] or "") in ARMOR_SLOT_NAMES)]

    if category_hint == "character":
        return candidate_rows, category_hint, entity_hint

    scored = [(score_row(r, query, category_hint, entity_hint), r) for r in candidate_rows]
    scored = [x for x in scored if x[0] > 0]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:top_k]], category_hint, entity_hint

def _extract_change_lines(content: str):
    raw_lines = [normalize(line) for line in content.splitlines() if normalize(line)]
    lines = []
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        if "→" in line:
            if i + 1 < len(raw_lines):
                nxt = raw_lines[i + 1]
                if "→" not in nxt and len(nxt) <= 40:
                    line = f"{line} {nxt}"
                    i += 1
            lines.append(line)
        i += 1
    return lines

def _emit_images(row):
    raw = row["image_urls"] or ""
    return [f"IMAGE: {u}" for u in raw.split("|") if u]

def format_answer(query: str, rows, category_hint, entity_hint):
    q = normalize(query)
    if not rows:
        return "이번 패치에는 적용되지 않은 실험체입니다." if entity_hint else "관련 패치 항목을 찾지 못했습니다."

    if category_hint == "character" and not entity_hint:
        names, seen = [], set()
        for row in rows:
            name = (row["title"] or "").strip()
            if name and name in CHARACTER_NAMES and name not in seen:
                seen.add(name); names.append(name)
        return "이번 패치에서 변경된 캐릭터:\n\n" + ", ".join(names) if names else "이번 패치에서 변경된 캐릭터를 찾지 못했습니다."

    if "방어구" in q:
        grouped = {slot: [] for slot in ["옷","머리","팔","다리","장식"]}
        for row in rows:
            title = row["title"] or ""
            if title in grouped:
                grouped[title].extend(_extract_change_lines(row["content"] or ""))
        out, idx = [], 1
        for slot, slot_lines in grouped.items():
            if not slot_lines: continue
            out.append(f"{idx}. {slot}"); out.append("")
            for line in slot_lines: out.append(f"- {line}")
            out.append(""); idx += 1
        return "\n".join(out).strip() if out else "관련 방어구 변경점을 찾지 못했습니다."

    lines = []
    for row in rows[:5]:
        lines.append(f"[{row['patch_version']} | {row['category']}] {row['title']}")
        if row["category"] in {"skins","emote"}:
            lines.extend(_emit_images(row))
        content = row["content"]
        if row["category"] == "emote":
            lines.append(content)
        elif row["category"] in {"weapon_skill","cobalt_protocol"}:
            change_lines = _extract_change_lines(content)
            lines.extend(change_lines if change_lines else [content])
        else:
            lines.append(content)
        lines.append("")
        lines.append(f"원문: {row['url']}")
        lines.append("")
    return "\n".join(lines).strip()
