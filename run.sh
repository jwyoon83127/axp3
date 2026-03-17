#!/bin/bash

# Jira AX Dashboard Deployment Script
# Designed by Louis

echo "🚀 Jira AX 대시보드 배포를 시작합니다! 루이가 도와드릴게요~"

# 1. 가상환경 세팅 (선택 사항이지만 권장)
if [ ! -d "venv" ]; then
    echo "📦 가상환경(venv)을 생성 중입니다..."
    python3 -m venv venv
fi

# 가상환경 활성화
source venv/bin/activate

# 2. 필수 라이브러리 설치
echo "🛠 필요한 라이브러리를 설치합니다... (이거 금방 끝나요!)"
pip install -r requirements.txt

# 3. 브라우저 자동 실행 안내 및 서버 가동
echo ""
echo "✨ 준비 완료! 이제 서버가 돌아갑니다."
echo "🌍 브라우저에서 'http://localhost:8100' 접속하시면 감각적인 대시보드를 보실 수 있어요!"
echo ""

# uvicorn 서버 실행
uvicorn main:app --host 0.0.0.0 --port 8100
