"""Gmail SMTP 이메일 발송 모듈.

환경변수:
  GMAIL_ADDRESS   — 발송자 Gmail 주소 (= 수신자와 같아도 됨)
  GMAIL_APP_PW    — Gmail 앱 비밀번호 (16자리, 공백 없이)
  NOTIFY_TO       — 수신자 이메일 (기본: koreanha@gmail.com)
"""
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

from models.posting import Posting

_RECIPIENT = os.environ.get("NOTIFY_TO", "koreanha@gmail.com")
_SENDER    = os.environ.get("GMAIL_ADDRESS", "")
_APP_PW    = os.environ.get("GMAIL_APP_PW", "")


# ── HTML 이메일 템플릿 ──────────────────────────────────────────────────────

def _score_color(score: int) -> str:
    if score >= 5:
        return "#1a7f37"   # 초록 — 매우 관련
    if score >= 3:
        return "#0969da"   # 파랑 — 관련
    return "#6e7781"       # 회색 — 낮음


def _posting_html(p: Posting) -> str:
    color   = _score_color(p.relevance_score)
    kw_tags = "".join(
        f'<span style="background:#f0f6ff;border:1px solid #cce0ff;'
        f'border-radius:4px;padding:1px 6px;margin:2px;font-size:12px;">{k}</span>'
        for k in p.matched_keywords[:5]
    )
    deadline_str = f"마감 {p.deadline}" if p.deadline else "마감일 미확인"
    return f"""
    <div style="border:1px solid #e1e4e8;border-radius:8px;padding:14px 16px;
                margin-bottom:10px;background:#fff;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <a href="{p.url}" style="font-size:15px;font-weight:600;color:#0969da;
                                  text-decoration:none;line-height:1.4;">
          {p.title}
        </a>
        <span style="white-space:nowrap;margin-left:12px;font-size:13px;
                     font-weight:700;color:{color};">
          ★ {p.relevance_score}점
        </span>
      </div>
      <div style="margin-top:6px;font-size:12px;color:#6e7781;">
        <span style="margin-right:12px;">📌 {p.source_id.upper()}</span>
        <span style="margin-right:12px;">⏰ {deadline_str}</span>
        {'<span>🏢 ' + p.organization + '</span>' if p.organization else ''}
      </div>
      <div style="margin-top:8px;">{kw_tags}</div>
    </div>"""


def _build_html(postings: List[Posting], date_str: str) -> str:
    if not postings:
        body = '<p style="color:#6e7781;text-align:center;padding:40px 0;">오늘 새로운 관련 공고가 없습니다.</p>'
    else:
        # 사이트별 그룹핑
        groups: dict[str, List[Posting]] = {}
        for p in sorted(postings, key=lambda x: -x.relevance_score):
            groups.setdefault(p.source_id, []).append(p)

        site_names = {"g2b": "나라장터", "bizinfo": "기업마당",
                      "ripc": "RIPC", "seouldesign": "서울디자인재단", "egbiz": "이지비즈"}
        body = ""
        for sid, items in groups.items():
            name = site_names.get(sid, sid)
            body += f"""
            <h3 style="margin:20px 0 8px;font-size:14px;color:#24292f;
                       border-bottom:2px solid #e1e4e8;padding-bottom:6px;">
              {name} — {len(items)}건
            </h3>"""
            body += "".join(_posting_html(p) for p in items)

    return f"""
<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f6f8fa;font-family:-apple-system,
             BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <div style="max-width:680px;margin:30px auto;background:#fff;
              border:1px solid #e1e4e8;border-radius:12px;overflow:hidden;">

    <!-- 헤더 -->
    <div style="background:#0969da;padding:24px 28px;">
      <h1 style="margin:0;color:#fff;font-size:20px;">📋 디자인 공고 알림</h1>
      <p  style="margin:6px 0 0;color:#cce0ff;font-size:13px;">{date_str} 기준 신규 관련 공고</p>
    </div>

    <!-- 요약 -->
    <div style="background:#f0f6ff;padding:14px 28px;border-bottom:1px solid #e1e4e8;">
      <span style="font-size:15px;font-weight:600;color:#0969da;">
        총 {len(postings)}건
      </span>
      <span style="font-size:13px;color:#6e7781;margin-left:8px;">
        의 새 공고가 수집됐습니다 (관련도 점수 높은 순 정렬)
      </span>
    </div>

    <!-- 공고 목록 -->
    <div style="padding:20px 28px;">
      {body}
    </div>

    <!-- 푸터 -->
    <div style="background:#f6f8fa;padding:16px 28px;border-top:1px solid #e1e4e8;
                font-size:12px;color:#6e7781;text-align:center;">
      자동 발송 — RFP 크롤링 에이전트
    </div>
  </div>
</body>
</html>"""


# ── 발송 함수 ───────────────────────────────────────────────────────────────

def send(postings: List[Posting]) -> bool:
    """공고 목록을 HTML 이메일로 발송. 성공 시 True 반환."""
    if not _SENDER or not _APP_PW:
        print("[email] GMAIL_ADDRESS 또는 GMAIL_APP_PW 미설정 — 발송 건너뜀")
        return False

    date_str  = datetime.now().strftime("%Y년 %m월 %d일")
    subject   = f"[디자인 공고] {date_str} 신규 {len(postings)}건"
    html_body = _build_html(postings, date_str)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = _SENDER
    msg["To"]      = _RECIPIENT
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(_SENDER, _APP_PW)
            smtp.sendmail(_SENDER, _RECIPIENT, msg.as_string())
        print(f"[email] 발송 완료 → {_RECIPIENT} ({len(postings)}건)")
        return True
    except Exception as e:
        print(f"[email] 발송 실패: {e}")
        return False
