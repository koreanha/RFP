"""키워드 기반 2단계 공고 필터.

1단계: 제목(title)에서 TITLE_KEYWORDS 검색
2단계: 본문(description)에서 CONTENT_KEYWORDS 검색
제외 : EXCLUDE_KEYWORDS 에 해당하면 탈락
"""
from dataclasses import dataclass
from typing import Optional


# ── 1단계: 공고 제목 필터 (넓게 잡아 후보 수집) ─────────────────────────────
TITLE_KEYWORDS: list[str] = [
    # 제품디자인
    "제품디자인", "제품 디자인", "산업디자인", "산업 디자인",
    "상품디자인", "제품개발", "제품혁신", "시제품",
    # 디자인 컨설팅
    "디자인컨설팅", "디자인 컨설팅", "디자인전략", "디자인경영",
    "서비스디자인", "디자인씽킹",
    # 디자인 R&D
    "디자인R&D", "디자인 R&D", "디자인연구", "디자인 연구개발", "디자인혁신",
    # 정부 공고 특유 표현
    "디자인 바우처", "디자인바우처",
    "우수디자인", "GD인증", "굿디자인",
    "디자인 고도화", "디자인 역량", "디자인 용역",
    "제품 고도화",
    # 광의 디자인 (2단계에서 정밀 필터)
    "디자인개발", "디자인 개발", "디자인 지원",
]

# ── 2단계: 본문 정밀 필터 (지원범위·과업범위 등 내부 텍스트) ────────────────
CONTENT_KEYWORDS: list[str] = [
    # 제품디자인
    "제품디자인", "산업디자인", "제품 외관", "폼팩터", "CMF",
    "시제품 제작", "목업", "mock-up", "3D 모델링", "렌더링",
    "제품 형태", "제품 컨셉", "제품 개발",
    # 디자인 컨설팅
    "디자인컨설팅", "디자인 전략", "디자인 방향성",
    "디자인 씽킹", "서비스디자인", "사용자 경험", "UX",
    # 디자인 R&D
    "디자인 연구", "디자인 R&D", "디자인 혁신",
    "기술혁신 디자인", "연구개발",
    # 정부 지원사업 과업 표현
    "과업범위", "지원범위", "지원내용", "사업내용",
    "디자인 바우처", "디자인 지원",
]

# ── 제외 키워드 (디자인 단어가 있어도 무관한 분야) ─────────────────────────
EXCLUDE_KEYWORDS: list[str] = [
    "건축디자인", "인테리어", "조경", "패션디자인", "미용",
    "헤어", "네일", "의상", "섬유",
]


@dataclass
class FilterResult:
    matched: bool
    stage: str          # "title" | "content" | "excluded" | "none"
    matched_keywords: list[str]
    score: int          # 매칭된 키워드 수 (우선순위 정렬용)


def filter_by_title(title: str) -> FilterResult:
    """1단계: 제목 키워드 매칭."""
    title_lower = title.lower()

    # 제외 키워드 우선 확인
    excluded = [k for k in EXCLUDE_KEYWORDS if k.lower() in title_lower]
    if excluded:
        return FilterResult(False, "excluded", excluded, 0)

    matched = [k for k in TITLE_KEYWORDS if k.lower() in title_lower]
    if matched:
        return FilterResult(True, "title", matched, len(matched))
    return FilterResult(False, "none", [], 0)


def filter_by_content(content: str) -> FilterResult:
    """2단계: 본문 키워드 매칭."""
    content_lower = content.lower()

    excluded = [k for k in EXCLUDE_KEYWORDS if k.lower() in content_lower]
    if excluded:
        return FilterResult(False, "excluded", excluded, 0)

    matched = [k for k in CONTENT_KEYWORDS if k.lower() in content_lower]
    if matched:
        return FilterResult(True, "content", matched, len(matched))
    return FilterResult(False, "none", [], 0)


def is_relevant(title: str, content: Optional[str] = None) -> FilterResult:
    """제목 → 본문 순서로 관련 공고 판별.

    title 만 있으면 1단계까지,
    content 까지 있으면 2단계 모두 적용.
    """
    title_result = filter_by_title(title)

    # 제목에서 제외 판정되면 즉시 탈락
    if title_result.stage == "excluded":
        return title_result

    # 제목 매칭 성공 → 추가로 본문까지 확인
    if title_result.matched and content:
        content_result = filter_by_content(content)
        if content_result.stage == "excluded":
            return content_result
        # 제목+본문 모두 매칭 시 점수 합산
        all_kw = list(set(title_result.matched_keywords + content_result.matched_keywords))
        return FilterResult(True, "title+content", all_kw, len(all_kw))

    # 제목 미매칭이지만 본문은 있는 경우 → 본문만으로 판별
    if not title_result.matched and content:
        return filter_by_content(content)

    return title_result
