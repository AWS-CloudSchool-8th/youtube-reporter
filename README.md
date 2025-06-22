# 통합 콘텐츠 분석 API

YouTube, 문서 파일, 검색을 통한 통합 AI 분석 및 보고서 생성 API 서버입니다.

## 주요 기능

- YouTube 동영상 자막 추출 및 분석
- 문서 파일(PDF, DOCX, XLSX, CSV, TXT) 분석
- YouTube 검색 결과 분석
- AWS S3를 통한 보고서 자동 저장
- AWS Polly를 통한 음성 변환
- 오디오 스트리밍 재생

## 설치 방법

1. 저장소 클론:
```bash
git clone https://github.com/yourusername/backend-final.git
cd backend-final
```

2. 가상환경 생성 및 활성화:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 의존성 설치:
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정:
`.env` 파일을 생성하고 다음 변수들을 설정합니다:
```
AWS_REGION=us-west-2
S3_BUCKET_NAME=your-bucket-name
POLLY_VOICE_ID=Seoyeon
VIDCAP_API_KEY=your-api-key
```

## 실행 방법

```bash
uvicorn app.main:app --reload
```

서버가 실행되면 `http://localhost:8000`에서 API 문서를 확인할 수 있습니다.

## API 엔드포인트

### 분석 관련
- `GET /analysis` - 모든 분석 작업 목록 조회
- `GET /analysis/{job_id}` - 특정 분석 작업 상태 조회
- `DELETE /analysis/{job_id}` - 분석 작업 삭제
- `GET /analysis/health` - 시스템 상태 확인

### 오디오 관련
- `POST /audio/generate` - 텍스트를 음성으로 변환
- `GET /audio/stream/{audio_id}` - 오디오 파일 스트리밍 재생

## 프로젝트 구조

```
backend-final/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── security.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── analysis.py
│   │   ├── audio.py
│   │   └── document.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── analysis.py
│   │   ├── audio.py
│   │   └── search.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── analysis_service.py
│   │   ├── audio_service.py
│   │   ├── document_service.py
│   │   └── s3_service.py
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── requirements.txt
└── README.md
```

## 라이선스

MIT License 