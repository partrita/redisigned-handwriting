# 손글씨 연습지 생성기

PDF 형식의 맞춤형 손글씨 연습지를 생성하는 Flask 기반 웹 애플리케이션입니다. 학생, 교사, 그리고 손글씨 실력을 향상시키고자 하는 모든 분들에게 완벽한 도구입니다.

## 주요 기능

- **맞춤 텍스트 입력**: 원하는 텍스트를 입력하여 개인화된 연습지 생성
- **다양한 폰트 옵션**: 여러 손글씨 스타일 폰트 중 선택 가능
- **사용자 정의 서식**: 
  - 줄 간격 및 여백 조정 가능
  - 다양한 줄 스타일 (줄 있음, 점선, 빈 줄)
  - 색상 서식 옵션
- **PDF 생성**: 인쇄용 고품질 PDF 출력
- **실시간 미리보기**: PDF 생성 전 연습지 미리보기 제공
- **요청 제한**: 남용 방지를 위한 내장 보호 기능
- **반응형 디자인**: 데스크톱 및 모바일 기기에서 모두 작동

## 빠른 시작

### 필수 요구사항

- Python 3.11 이상
- [uv](https://docs.astral.sh/uv/) 패키지 매니저

### 설치

1. 저장소 복제:
```bash
git clone <repository-url>
cd redisigned-handwriting
```

2. uv를 사용하여 의존성 설치:
```bash
uv sync
```

3. 애플리케이션 실행:
```bash
uv run python run.py
```

4. 브라우저를 열고 `http://localhost:5001`로 이동

## 사용법

1. **텍스트 입력**: 연습하고 싶은 텍스트를 입력하거나 붙여넣기
2. **폰트 선택**: 사용 가능한 손글씨 폰트 중 선택
3. **레이아웃 사용자 정의**: 줄 간격, 여백, 줄 스타일 조정
4. **미리보기**: 미리보기 기능으로 연습지 모양 확인
5. **PDF 생성**: "PDF 생성" 버튼을 클릭하여 연습지 생성
6. **인쇄**: 맞춤형 연습지를 다운로드하고 인쇄

## API 엔드포인트

- `GET /` - 메인 애플리케이션 인터페이스
- `POST /api/generate-pdf` - PDF 연습지 생성
- `POST /api/preview` - 미리보기 이미지 생성
- `GET /api/fonts` - 사용 가능한 폰트 목록
- `POST /api/validate` - 입력 매개변수 검증

## 설정

애플리케이션은 설정을 통해 다양한 환경을 지원합니다:

- **개발 환경**: 디버그 모드 활성화, 상세한 오류 메시지
- **운영 환경**: 성능 및 보안 최적화

환경 변수:
- `FLASK_ENV`: 운영 배포 시 `production`으로 설정
- `SECRET_KEY`: 세션 관리를 위한 Flask 비밀 키

## 개발

### 테스트 실행

```bash
# 모든 테스트 실행
uv run pytest

# 커버리지와 함께 실행
uv run pytest --cov=src/handwriting_transcription --cov-report=html

# 특정 테스트 파일 실행
uv run pytest tests/test_pdf_generator.py
```

### 코드 품질

프로젝트는 코드 품질을 위해 여러 도구를 사용합니다:

```bash
# 린팅 실행
uv run ruff check

# 코드 포맷팅
uv run ruff format

# 타입 검사 (mypy가 설치된 경우)
uv run mypy src/
```

### 프로젝트 구조

```
src/handwriting_transcription/
├── app.py              # 메인 Flask 애플리케이션
├── config.py           # 설정
├── text_processor.py   # 텍스트 처리 로직
├── font_manager.py     # 폰트 관리
├── pdf_generator.py    # PDF 생성
├── preview_generator.py # 미리보기 이미지 생성
├── validators.py       # 입력 검증
├── error_handlers.py   # 오류 처리
├── rate_limiter.py     # 요청 제한
└── models.py          # 데이터 모델

tests/                  # 테스트 스위트
templates/             # HTML 템플릿
static/               # 정적 자산 (CSS, JS, 이미지)
```

## 성능

애플리케이션에는 여러 성능 최적화가 포함되어 있습니다:

- **캐싱**: 빠른 생성을 위한 폰트 및 템플릿 캐싱
- **요청 제한**: 남용 방지 및 공정한 사용 보장
- **비동기 처리**: 논블로킹 PDF 생성
- **메모리 관리**: 대용량 텍스트 입력의 효율적 처리

## 기여하기

1. 저장소를 포크합니다
2. 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 만듭니다
4. 새로운 기능에 대한 테스트를 추가합니다
5. 모든 테스트가 통과하는지 확인합니다 (`uv run pytest`)
6. 변경사항을 커밋합니다 (`git commit -m 'Add amazing feature'`)
7. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`)
8. Pull Request를 엽니다

## 라이선스

이 프로젝트는 MIT 라이선스 하에 라이선스가 부여됩니다 - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 배포

### fly.io 배포

이 프로젝트는 [fly.io](https://fly.io)에 배포할 수 있습니다.

#### 사전 요구사항

1. [flyctl](https://fly.io/docs/hands-on/install-flyctl/) 설치
2. fly.io 계정 생성 및 로그인:
```bash
flyctl auth login
```

#### 첫 번째 배포 (수동)

```bash
# fly.io 앱 생성 (fly.toml 이름과 동일하게)
flyctl apps create redisigned-handwriting

# 배포
flyctl deploy
```

#### GitHub Actions를 통한 자동 배포 (CI/CD)

`main` 또는 `master` 브랜치에 푸시하면 자동으로 테스트를 실행하고 fly.io에 배포합니다.

**설정 방법:**

1. fly.io API 토큰 발급:
```bash
flyctl auth token
```

2. GitHub 저장소의 **Settings → Secrets and variables → Actions**에서 다음 시크릿 추가:
   - `FLY_API_TOKEN`: fly.io API 토큰

3. `main` 브랜치에 푸시하면 자동으로 배포됩니다.

#### 환경 변수

fly.io에 환경 변수를 설정하려면:
```bash
# SECRET_KEY 설정 (필수!)
flyctl secrets set SECRET_KEY="your-secure-secret-key"
```

#### 수동 배포

```bash
flyctl deploy --remote-only
```

#### 앱 상태 확인

```bash
flyctl status
flyctl logs
```

## 지원

문제가 발생하거나 질문이 있는 경우:

1. GitHub의 기존 이슈를 확인하세요
2. 문제에 대한 자세한 정보와 함께 새 이슈를 생성하세요
3. 문제 재현 단계와 환경 세부 정보를 포함하세요

## 감사의 말

- [Flask](https://flask.palletsprojects.com/)로 구축
- [ReportLab](https://www.reportlab.com/)으로 PDF 생성
- [FontTools](https://github.com/fonttools/fonttools)를 사용한 폰트 처리
- [Gunicorn](https://gunicorn.org/)을 사용한 WSGI 서버
- [fly.io](https://fly.io)에 호스팅