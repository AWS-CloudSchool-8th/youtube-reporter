# 🎥 YouTube 보고서 생성기

YouTube 영상을 보지 않고도 완전히 이해할 수 있는 포괄적 보고서를 AI가 자동으로 생성해주는 도구입니다.

## ✨ 주요 기능

- **포괄적 보고서**: YouTube 영상의 모든 핵심 내용을 상세하게 분석
- **지능적 시각화**: AI가 꼭 필요한 시각화만 선별해서 생성 (최대 2-3개)
- **한글 완벽 지원**: 한글 폰트 자동 설정으로 깨짐 없는 차트 생성
- **웹 인터페이스**: 사용하기 쉬운 웹 UI 제공

## 🚀 실행 방법

### 1. 환경변수 설정
```bash
# .env.example을 복사하여 .env 파일 생성
copy .env.example .env

# .env 파일을 열어서 실제 API 키들로 수정
```

### 2. 실행
```bash
# 방법 1: 배치 파일 (가장 쉬움)
start.bat

# 방법 2: 직접 실행
python main.py
```

## 📱 사용법

1. 서버 시작 후 브라우저에서 `http://localhost:8001` 접속
2. YouTube URL 입력 (한국어 자막이 있는 영상 권장)
3. "AI 보고서 생성하기" 버튼 클릭
4. 1-2분 후 완성된 보고서 확인

## 📋 필요한 환경변수 (.env 파일)

```env
# YouTube 자막 추출
VIDCAP_API_KEY=your_vidcap_api_key

# AI 모델 (AWS Bedrock)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-west-2
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# 이미지 저장 (S3)
S3_BUCKET_NAME=your_s3_bucket

# 시각화 생성 (선택사항)
OPENAI_API_KEY=your_openai_api_key

# 추적 (선택사항)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=youtube-reporter
LANGCHAIN_API_KEY=your_langsmith_api_key
```

## 🛠️ 기술 스택

- **Backend**: FastAPI, LangGraph, LangChain
- **AI**: AWS Bedrock (Claude), OpenAI (DALL-E)
- **시각화**: Matplotlib, Seaborn, Pandas
- **Frontend**: HTML, CSS, JavaScript
- **Storage**: AWS S3

## 📁 프로젝트 구조

```
youtube-reporter/
├── app/
│   ├── main.py                 # FastAPI 서버
│   └── pipeline/
│       └── youtube_graph_pipeline.py  # AI 파이프라인
├── frontend/
│   └── index.html             # 웹 인터페이스
├── .env                       # 환경변수
├── requirements.txt           # Python 패키지
├── run.py                     # 실행 스크립트
├── start.bat                  # Windows 실행 파일
└── README.md                  # 이 파일
```

## 🔧 문제 해결

### 한글 폰트 깨짐
- 시스템에 한글 폰트가 설치되어 있는지 확인
- Windows: Malgun Gothic, macOS: AppleGothic 자동 사용

### API 키 오류
- `.env` 파일의 API 키들이 올바른지 확인
- AWS 권한 설정 확인

### 패키지 설치 오류
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 📞 지원

문제가 발생하면 다음을 확인해주세요:
1. Python 3.8+ 설치 여부
2. 모든 환경변수 설정 완료
3. 인터넷 연결 상태
4. YouTube URL이 올바른지 확인