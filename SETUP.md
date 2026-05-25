# 로컬 설치 및 실행 가이드

## 1. 의존성 설치

```bash
pip install -r requirements.txt
playwright install chromium
```

## 2. 환경변수 설정 (선택)

```bash
cp .env.example .env
# .env 파일에서 필요한 항목만 채우면 됨
# - G2B_API_KEY: 현재 사용 안 함 (playwright 방식으로 전환됨)
# - RIPC_USERNAME / RIPC_PASSWORD: RIPC 사이트 사용 시만
```

## 3. 실행

```bash
# 전체 사이트 실행
python main.py

# 특정 사이트만
python main.py --sites g2b bizinfo

# DB 저장 없이 결과 미리보기
python main.py --dry-run

# 브라우저 창 띄워서 실행 (디버깅용)
# utils/browser.py 에서 headless=True → False 로 변경
```

## 4. 결과 확인

```bash
# SQLite DB 위치: data/postings.db
sqlite3 data/postings.db "SELECT source_id, title, deadline FROM postings ORDER BY crawled_at DESC LIMIT 20;"
```

## 주의

- 나라장터(g2b), 기업마당(bizinfo) 등 정부 사이트는
  **반드시 로컬에서 실행**해야 합니다.
  GitHub Actions 등 클라우드 환경은 해당 사이트 접근이 차단됩니다.
- 크롤링 간격은 하루 1~2회를 권장합니다 (과도한 요청 방지).
