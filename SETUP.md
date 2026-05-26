# 설치 및 자동 실행 가이드

---

## 1. 패키지 설치

```bash
pip install -r requirements.txt
playwright install chromium
```

---

## 2. Gmail 앱 비밀번호 발급 (5분)

> 일반 Gmail 비밀번호는 사용 불가 — 앱 비밀번호가 필요합니다.

1. [Google 계정 보안](https://myaccount.google.com/security) → **2단계 인증** 활성화
2. [앱 비밀번호 페이지](https://myaccount.google.com/apppasswords) 접속
3. 앱 이름 입력 (예: `RFP크롤러`) → **만들기**
4. 표시된 **16자리 비밀번호** 복사 (공백 포함해도 됨)

---

## 3. 환경변수 설정

```bash
cp .env.example .env
```

`.env` 파일을 열어서 채우기:

```env
GMAIL_ADDRESS=koreanha@gmail.com
GMAIL_APP_PW=abcd efgh ijkl mnop   # 발급받은 16자리
```

---

## 4. 동작 테스트

```bash
# 이메일 발송 없이 결과만 확인
python main.py --dry-run

# 이메일까지 실제 발송 테스트 (1건도 없으면 "0건" 메일이 옴)
python main.py --no-email=false
```

---

## 5. 매일 오전 10시 자동 실행 설정

### Mac / Linux (cron)

터미널에서:

```bash
# run.sh 경로 확인
pwd  # 예: /Users/yourname/RFP

# cron 편집기 열기
crontab -e
```

아래 한 줄 추가 (경로를 실제 경로로 변경):

```
0 10 * * * /Users/yourname/RFP/run.sh >> /Users/yourname/RFP/logs/cron.log 2>&1
```

저장 후 확인:

```bash
crontab -l   # 등록된 크론 목록 확인
```

> **Mac 주의**: 시스템 환경설정 → 개인 정보 보호 → 전체 디스크 접근 권한에서  
> `cron` 또는 터미널 앱에 권한을 부여해야 할 수 있습니다.

---

### Windows (작업 스케줄러)

1. **작업 스케줄러** 앱 열기 (시작 메뉴 검색)
2. 오른쪽 패널 → **기본 작업 만들기**
3. 이름: `RFP 크롤링`, 다음
4. 트리거: **매일**, 시작 시간: `오전 10:00`, 다음
5. 동작: **프로그램 시작**, 다음
6. 프로그램: `C:\경로\RFP\run_windows.bat`
7. 마침

---

## 6. 실행 결과 확인

```bash
# 오늘 로그 확인
cat logs/crawl_$(date +%Y%m%d).log

# DB에서 최근 공고 조회 (점수 높은 순)
sqlite3 data/postings.db \
  "SELECT relevance_score, source_id, title, deadline FROM postings ORDER BY relevance_score DESC, crawled_at DESC LIMIT 20;"
```

---

## 7. 기타 실행 옵션

```bash
# 특정 사이트만
python main.py --sites g2b bizinfo

# 상세 페이지 본문까지 분석 (시간 더 걸리지만 정밀)
python main.py --deep

# 관련도 점수 2점 이상만 저장
python main.py --min-score 2

# 이메일 발송 건너뜀
python main.py --no-email
```
