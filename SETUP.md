# 디자인 공고 자동 수집 에이전트 — 설치 및 실행 가이드

> **이 문서는 프로그래밍을 전혀 모르는 분을 기준으로 작성되었습니다.**  
> 명령어를 그대로 복사·붙여넣기 하시면 됩니다.

---

## 전체 순서 한눈에 보기

```
1단계  Python 설치          (처음 한 번만)
2단계  코드 내려받기         (처음 한 번만)
3단계  필요한 패키지 설치    (처음 한 번만)
4단계  Gmail 앱 비밀번호 발급 (처음 한 번만)
5단계  설정 파일 작성        (처음 한 번만)
6단계  동작 테스트           (처음 한 번만)
7단계  매일 자동 실행 등록   (처음 한 번만)
```

---

## 1단계 — Python 설치

> **이미 Python이 설치되어 있다면 건너뛰세요.**  
> 터미널(명령 프롬프트)에서 `python3 --version` 또는 `python --version` 을 입력해서  
> `Python 3.10.x` 처럼 숫자가 나오면 이미 설치된 것입니다.

### Mac

1. [python.org/downloads](https://www.python.org/downloads/) 접속
2. **Download Python 3.x.x** 노란 버튼 클릭
3. 다운받은 `.pkg` 파일 더블클릭 → 안내에 따라 설치
4. 설치 완료 후, **터미널** 앱 열기  
   (Spotlight 검색 `⌘ + Space` → `터미널` 입력 → Enter)
5. 아래 명령어 입력해서 확인:
   ```
   python3 --version
   ```
   `Python 3.x.x` 가 출력되면 성공

### Windows

1. [python.org/downloads](https://www.python.org/downloads/) 접속
2. **Download Python 3.x.x** 노란 버튼 클릭
3. 다운받은 `.exe` 파일 더블클릭
4. ⚠️ **반드시** 설치 화면 맨 아래 **"Add Python to PATH"** 체크박스를 체크한 후 Install Now 클릭
5. 설치 완료 후, **명령 프롬프트** 열기  
   (시작 버튼 → `cmd` 검색 → Enter)
6. 아래 명령어 입력해서 확인:
   ```
   python --version
   ```
   `Python 3.x.x` 가 출력되면 성공

---

## 2단계 — 코드 내려받기

### 방법 A — ZIP 파일로 받기 (Git 모르는 분)

1. GitHub 저장소 페이지 접속
2. 초록색 **Code** 버튼 클릭 → **Download ZIP** 클릭
3. 다운받은 ZIP 파일 압축 해제
4. 압축 해제된 폴더를 원하는 위치로 이동  
   예) Mac: `/Users/홍길동/rfp` / Windows: `C:\rfp`

### 방법 B — Git으로 받기 (Git 아는 분)

```bash
git clone https://github.com/koreanha/rfp.git
cd rfp
```

---

## 3단계 — 필요한 패키지 설치

> 터미널(Mac) 또는 명령 프롬프트(Windows)를 열고,  
> 아래 명령어로 **프로젝트 폴더로 이동**합니다.

### Mac

```bash
cd /Users/홍길동/rfp
```
> ⚠️ `홍길동` 부분을 본인 Mac 사용자 이름으로 바꾸세요.  
> 폴더를 다른 곳에 뒀다면 해당 경로로 변경하세요.

### Windows

```
cd C:\rfp
```

---

이동 후 아래 명령어를 **순서대로** 입력합니다.  
각 명령어 입력 후 완료될 때까지 기다렸다가 다음으로 넘어가세요.

**① 필요한 라이브러리 설치** (1~2분 소요)
```bash
pip install -r requirements.txt
```

설치 중 이런 메시지가 나오면 정상입니다:
```
Successfully installed requests-2.x.x playwright-1.56.0 ...
```

**② 브라우저 설치** (1~3분 소요, 크기가 큽니다)
```bash
playwright install chromium
```

완료되면 아래처럼 출력됩니다:
```
Downloading Chromium ...
Chromium downloaded
```

---

## 4단계 — Gmail 앱 비밀번호 발급

> 이 에이전트는 결과를 이메일로 보내줍니다.  
> Gmail은 보안상 일반 비밀번호 대신 **앱 전용 비밀번호**를 사용해야 합니다.

### 4-1. 2단계 인증 활성화 (이미 켜져 있으면 건너뜀)

1. [myaccount.google.com/security](https://myaccount.google.com/security) 접속 (Gmail 로그인 필요)
2. **"2단계 인증"** 항목 클릭
3. **시작하기** → 안내에 따라 설정 완료

### 4-2. 앱 비밀번호 발급

1. [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) 접속
2. **앱 이름** 입력란에 `RFP크롤러` 입력
3. **만들기** 버튼 클릭
4. 화면에 표시되는 **16자리 비밀번호**(예: `abcd efgh ijkl mnop`)를 메모 또는 복사
   > ⚠️ 이 창을 닫으면 다시 볼 수 없습니다. 꼭 복사해두세요.

---

## 5단계 — 설정 파일 작성

프로젝트 폴더 안에 있는 **`.env.example`** 파일을 복사해서 **`.env`** 파일을 만듭니다.

### Mac

터미널에서 (프로젝트 폴더 안에 있어야 함):
```bash
cp .env.example .env
```

### Windows

명령 프롬프트에서:
```
copy .env.example .env
```

---

이제 `.env` 파일을 텍스트 편집기로 열어서 수정합니다.

### Mac — 텍스트 편집기로 열기

```bash
open -a TextEdit .env
```

### Windows — 메모장으로 열기

```
notepad .env
```

---

파일이 열리면 아래 두 줄을 찾아서 수정합니다:

**수정 전:**
```
GMAIL_ADDRESS=koreanha@gmail.com
GMAIL_APP_PW=xxxx xxxx xxxx xxxx
```

**수정 후 (본인 정보로 변경):**
```
GMAIL_ADDRESS=본인Gmail주소@gmail.com
GMAIL_APP_PW=4단계에서받은16자리비밀번호
```

> 예시:
> ```
> GMAIL_ADDRESS=koreanha@gmail.com
> GMAIL_APP_PW=abcdefghijklmnop
> ```
> 앱 비밀번호의 공백은 있어도 없어도 됩니다.

수정 후 **저장** (Mac: `⌘+S` / Windows: `Ctrl+S`) 하고 파일을 닫습니다.

---

## 6단계 — 동작 테스트

터미널(명령 프롬프트)에서 프로젝트 폴더로 이동 후 테스트합니다.

### 테스트 1 — 크롤링만 확인 (이메일 발송 없음, 빠름)

```bash
python main.py --dry-run
```

실행하면 아래처럼 수집된 공고 목록이 화면에 출력됩니다:
```
[bizinfo] 기업마당 크롤링 시작...
  [bizinfo] '제품디자인' → 3건 관련
[3점] 2025년 중소기업 제품디자인 지원사업 공고  마감:2025-06-30
      키워드: 제품디자인, 시제품 제작
...
```

> 아무 공고도 안 나오는 경우: 해당 사이트에 현재 등록된 공고가 없거나,  
> 크롤러가 아직 해당 페이지 구조를 못 잡는 경우입니다. 오류 없이 완료되면 정상입니다.

### 테스트 2 — 이메일 발송까지 확인

```bash
python main.py
```

1~2분 후 받은 편지함을 확인합니다.  
**`[디자인 공고] 2025년 XX월 XX일 신규 N건`** 제목의 메일이 오면 성공입니다.

> 📌 이메일이 **스팸함**으로 갔을 수 있습니다. 스팸함도 확인해주세요.

---

## 7단계 — 매일 오전 10시 자동 실행 등록

### Mac

터미널에서 아래 명령어로 프로젝트 경로를 확인합니다:

```bash
pwd
```

출력 예시: `/Users/홍길동/rfp`

이 경로를 기억해두고, 아래 명령어로 자동 실행을 등록합니다:

```bash
crontab -e
```

> 편집기가 열립니다. 처음 열리면 **vi 편집기**가 뜰 수 있습니다.  
> 키보드에서 `i` 를 눌러 입력 모드로 전환하세요.

아래 한 줄을 입력합니다 (경로를 `pwd`에서 확인한 경로로 변경):

```
0 10 * * * /Users/홍길동/rfp/run.sh >> /Users/홍길동/rfp/logs/cron.log 2>&1
```

입력 후:
- `Esc` 키 누르기
- `:wq` 입력 후 Enter (저장하고 닫기)

등록 확인:
```bash
crontab -l
```
방금 입력한 줄이 보이면 성공입니다.

> **Mac 추가 설정 (macOS Ventura 이상)**  
> 시스템 설정 → 개인정보 보호 및 보안 → 전체 디스크 접근 권한  
> → `+` 버튼 → `/usr/sbin/cron` 추가

---

### Windows

1. 시작 버튼 클릭 → **작업 스케줄러** 검색 → 실행
2. 오른쪽 **작업** 패널에서 **기본 작업 만들기...** 클릭
3. **이름**: `RFP 디자인 공고 크롤링` 입력 → **다음**
4. **트리거**: `매일` 선택 → **다음**
5. **시작**: 날짜는 오늘, 시간은 `오전 10:00:00` 입력 → **다음**
6. **동작**: `프로그램 시작` 선택 → **다음**
7. **프로그램/스크립트** 란에 아래 경로 입력 (실제 경로로 변경):
   ```
   C:\rfp\run_windows.bat
   ```
8. **다음** → **마침**

등록 후 테스트: 작업 목록에서 `RFP 디자인 공고 크롤링` 우클릭 → **실행**  
오류 없이 완료되고 이메일이 오면 성공입니다.

---

## 실행 결과 확인 방법

### 로그 파일 확인 (Mac/Linux)

```bash
# 오늘 날짜 로그 보기
cat logs/crawl_$(date +%Y%m%d).log
```

### 수집된 공고 목록 확인

```bash
# Mac/Linux
sqlite3 data/postings.db "SELECT relevance_score, source_id, title, deadline FROM postings ORDER BY relevance_score DESC LIMIT 20;"

# Windows (sqlite3가 설치된 경우)
sqlite3 data\postings.db "SELECT relevance_score, source_id, title, deadline FROM postings ORDER BY relevance_score DESC LIMIT 20;"
```

---

## 자주 묻는 문제 (FAQ)

**Q. `pip` 명령어를 찾을 수 없다는 오류가 납니다.**  
→ `pip` 대신 `pip3` 로 시도해보세요. Mac의 경우 `python3 -m pip install -r requirements.txt`

**Q. 이메일이 오지 않습니다.**  
→ 스팸 메일함을 확인하세요. 그래도 없으면 `.env` 파일에 GMAIL_APP_PW 를 올바르게 입력했는지 확인하세요.

**Q. 앱 비밀번호 페이지가 보이지 않습니다.**  
→ Google 계정에서 2단계 인증이 꺼져 있으면 앱 비밀번호 메뉴가 안 보입니다. 4-1 단계를 먼저 완료하세요.

**Q. `playwright install chromium` 중 오류가 납니다.**  
→ 인터넷 연결을 확인 후 재시도하세요. 또는 `python -m playwright install chromium` 으로 시도해보세요.

**Q. cron 등록은 됐는데 10시에 실행이 안 됩니다. (Mac)**  
→ 컴퓨터가 10시에 켜져 있어야 합니다. 또한 macOS의 경우 크론에 전체 디스크 접근 권한이 없으면 실행이 안 됩니다. "7단계 Mac 추가 설정" 항목을 확인하세요.

---

## 기타 실행 옵션

```bash
# 특정 사이트만 실행
python main.py --sites bizinfo

# 상세 페이지 본문까지 분석 (더 정밀하지만 시간 더 걸림)
python main.py --deep

# 관련도 점수 2점 이상 공고만 저장
python main.py --min-score 2

# 이메일 발송 건너뜀
python main.py --no-email
```
