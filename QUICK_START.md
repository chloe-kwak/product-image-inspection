# ⚡ 빠른 시작 가이드

## 🚀 5분 안에 시작하기

### 1단계: 환경 설정 (2분)
```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경 파일 복사
cp .env.example .env

# 3. AWS 정보 입력 (.env 파일 편집)
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
```

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

### AWS 연결 오류 시
- AWS 키가 올바른지 확인
- Bedrock 서비스 권한 확인
- 리전 설정 확인 (기본: us-east-1)

### 이미지 로딩 오류 시
- 이미지 URL이 공개 접근 가능한지 확인
- HTTPS URL 사용 권장

## 📞 즉시 지원
설치나 실행 중 문제가 발생하면 즉시 연락주세요!

---
**준비 완료! 이제 고품질 이미지 검수를 시작하세요! 🎉**