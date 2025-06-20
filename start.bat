@echo off
echo 🎥 YouTube 보고서 생성기를 시작합니다...
echo.
echo 📦 필요한 패키지를 설치합니다...
pip install -r requirements.txt
echo.
echo 🚀 서버를 시작합니다...
echo 📱 브라우저에서 http://localhost:8000 으로 접속하세요
echo ⏹️  종료하려면 Ctrl+C를 누르세요
echo.
python run.py
pause