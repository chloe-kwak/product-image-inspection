# ⚡ 빠른 시작 가이드

## 🚀 5분 안에 시작하기

### 1단계: 환경 설정 (2분)

⚠️ **중요**: `.env` 파일이 없으면 실행되지 않습니다!

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경 파일 생성 (필수!)
cp .env.example .env

# 3. .env 파일을 열어서 AWS 정보 입력
# 텍스트 에디터로 .env 파일 편집:
```

**`.env` 파일에 입력할 내용:**
```bash
# AWS 자격 증명 (필수)
AWS_ACCESS_KEY_ID=실제_액세스_키_입력
AWS_SECRET_ACCESS_KEY=실제_시크릿_키_입력
AWS_REGION=us-east-1

# AI 모델 선택 (필수)
BEDROCK_MODEL_ID=us.amazon.nova-lite-v1:0

# 기타 설정 (선택)
PROMPT_VERSION=v3.2
DYNAMODB_TABLE_NAME=product-image-inspection
```

**💡 모델 선택 가이드:**
- `nova-lite-v1:0` - 빠르고 경제적 (권장)
- `nova-pro-v1:0` - 더 정확한 분석

### 2단계: 실행 (1분)
```bash
streamlit run two_stage_app.py
```

### 3단계: 테스트 (2분)
1. 브라우저에서 `http://localhost:8502` 접속
2. 테스트 이미지 URL 입력:
   ```
   https://shop-phinf.pstatic.net/20250827_266/1756283702318M5JMo_JPEG/2729632462003176_1558362207.jpg
   ```
3. "검수 실행" 클릭
4. 결과 확인: `false` (파란색 테두리 탐지)

## 🎯 주요 기능 확인

### ✅ 테두리 탐지 테스트
- **파란색 테두리 이미지**: 반드시 `false` 결과
- **깔끔한 이미지**: `true` 결과 (Nova 일반 검수 통과)

### ✅ 일괄 검수 테스트
1. "일괄 검수" 탭 선택
2. 여러 URL 입력 (줄바꿈으로 구분)
3. 결과를 CSV로 다운로드

## 🔧 문제 해결

### ❌ ".env 파일이 없습니다" 에러
```bash
# 해결 방법:
cp .env.example .env
# 그 다음 .env 파일을 열어서 AWS 키 입력
```

### ❌ "Missing required environment variables" 에러
- `.env` 파일에 필수 항목이 누락됨
- 확인 필요: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `BEDROCK_MODEL_ID`

### ❌ AWS 연결 오류
- AWS 키가 올바른지 확인
- Bedrock 서비스 권한 확인
- 리전 설정 확인 (기본: us-east-1)

### ❌ 이미지 로딩 오류
- 이미지 URL이 공개 접근 가능한지 확인
- HTTPS URL 사용 권장

## 📞 즉시 지원
설치나 실행 중 문제가 발생하면 즉시 연락주세요!

---
**준비 완료! 이제 고품질 이미지 검수를 시작하세요! 🎉**