# 🎬 YouTube Reporter

YouTube 영상을 자동으로 분석하여 시각적 보고서를 생성하는 AI 파이프라인입니다.

## 📋 주요 기능

- **YouTube 자막 추출**: VidCap API를 통한 자동 자막 추출
- **보고서 생성**: Claude를 이용한 구조화된 보고서 작성
- **시각화 생성**: 자동으로 차트, 그래프, 이미지 생성
- **클라우드 저장**: S3를 통한 자동 이미지 저장
- **에러 처리**: 견고한 에러 핸들링 및 로깅

## 🏗️ 아키텍처

```
YouTube URL → 자막 추출 → 보고서 생성 → 시각화 분할 → 이미지 생성 → 최종 보고서
```

### 프로젝트 구조

```
app/
├── core/                   # 핵심 비즈니스 로직
│   ├── agents/            # AI 에이전트들
│   │   ├── youtube.py     # YouTube 자막 추출
│   │   ├── report_agent.py # 보고서 생성
│   │   └── visual_split.py # 시각화 블록 분할
│   ├── tools/             # 도구들
│   │   ├── code_exec.py   # 코드 실행 및 차트 생성
│   │   ├── s3.py          # S3 업로드
│   │   └── visual_gen.py  # 시각화 자산 생성
│   └── workflow/          # 워크플로우 관리
│       └── fsm.py         # LangGraph 기반 FSM
├── config/                # 설정 관리
│   └── settings.py        # 환경 변수 기반 설정
├── utils/                 # 유틸리티
│   ├── env_validator.py   # 환경 변수 검증
│   ├── error_handler.py   # 에러 처리
│   ├── exceptions.py      # 커스텀 예외
│   ├── llm_factory.py     # LLM 팩토리
│   ├── logger.py          # 로깅 시스템
│   └── merge.py           # 결과 병합
└── main.py                # 메인 실행 파일
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone <repository-url>
cd youtube-reporter

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate     # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env.example`을 복사하여 `.env` 파일을 생성하고 실제 값으로 변경:

```bash
cp .env.example .env
```

필수 환경 변수:
```bash
# 필수 설정
VIDCAP_API_KEY=your_vidcap_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
AWS_REGION=us-west-2
S3_BUCKET_NAME=your-s3-bucket-name
AWS_BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
```

### 3. 실행

```bash
cd app
python main.py
```

## 🔧 설정 옵션

### 필수 환경 변수

| 변수명 | 설명 | 예시 |
|--------|------|------|
| `VIDCAP_API_KEY` | VidCap API 키 | `your_api_key` |
| `OPENAI_API_KEY` | OpenAI API 키 | `sk-proj-...` |
| `AWS_REGION` | AWS 리전 | `us-west-2` |
| `S3_BUCKET_NAME` | S3 버킷 이름 | `my-bucket` |
| `AWS_BEDROCK_MODEL_ID` | Bedrock 모델 ID | `anthropic.claude-3-5-sonnet-20241022-v2:0` |

### 선택적 환경 변수

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `LOG_LEVEL` | `INFO` | 로그 레벨 |
| `LLM_TEMPERATURE` | `0.7` | LLM 온도 설정 |
| `LLM_MAX_TOKENS` | `4096` | 최대 토큰 수 |
| `DALLE_MODEL` | `dall-e-3` | DALL-E 모델 |
| `DALLE_IMAGE_SIZE` | `1024x1024` | 이미지 크기 |

## 📊 사용 예시

1. **YouTube URL 입력**:
   ```
   URL: https://www.youtube.com/watch?v=example
   ```

2. **자동 처리**: 
   - 자막 추출 → 보고서 생성 → 시각화 분할 → 이미지 생성

3. **결과 출력**:
   ```json
   {
     "format": "json",
     "sections": [
       {
         "type": "paragraph",
         "content": "영상 요약 내용..."
       },
       {
         "type": "chart",
         "src": "https://s3.amazonaws.com/bucket/chart.png"
       }
     ]
   }
   ```

## 🛠️ 개발

### 코드 스타일
```bash
# 포맷팅
black app/

# 린팅
flake8 app/
```

### 테스트
```bash
pytest
```

## 🔍 모니터링

### LangSmith 추적 (선택사항)
```bash
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=youtube-reporter
```

### 로그 레벨 설정
```bash
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

## ⚠️ 제한사항

- **API 의존성**: 외부 API (VidCap, OpenAI, AWS)에 의존
- **언어 지원**: 현재 한국어 자막만 지원
- **비용**: API 사용에 따른 비용 발생
- **속도**: 긴 영상의 경우 처리 시간이 오래 걸릴 수 있음

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 라이선스

MIT License

## 🆘 문제 해결

### 일반적인 문제들

**환경 변수 오류**:
```bash
# 환경 변수 확인
python -c "import os; print(os.getenv('VIDCAP_API_KEY'))"
```

**AWS 권한 오류**:
- IAM 정책에 S3 및 Bedrock 권한 확인
- AWS CLI 설정 확인: `aws configure`

**의존성 오류**:
```bash
pip install --upgrade -r requirements.txt
```

더 자세한 문제 해결은 [Issues](link-to-issues) 페이지를 참조하세요.
