@echo off
REM Windows 작업 스케줄러용 실행 스크립트
REM 등록 방법: 아래 "Windows 작업 스케줄러 설정" 섹션 참고 (SETUP.md)

cd /d "%~dp0"

REM .env 파일 로드
if exist .env (
    for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
        if not "%%A"=="" if not "%%A:~0,1%"=="#" set %%A=%%B
    )
)

echo === RFP 크롤링 시작: %date% %time% ===
python main.py --min-score 1
echo === 완료: %date% %time% ===
