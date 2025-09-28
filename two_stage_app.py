"""
2단계 상품 이미지 검수 서비스 - 메인 애플리케이션
1단계: OpenCV를 활용한 테두리 탐지
2단계: AI 모델을 통한 일반 검수 기준 적용
"""

import os
import sys
from dotenv import load_dotenv

# 환경 변수를 가장 먼저 로드
load_dotenv()

import streamlit as st
import asyncio
from src.models.app_config import AppConfig
from src.services.two_stage_inspection_service import TwoStageInspectionService
from src.ui.streamlit_app import StreamlitApp

def main():
    """메인 애플리케이션 실행"""
    try:
        # 페이지 설정 (StreamlitApp 생성 전에)
        st.set_page_config(
            page_title="🔍 2단계 상품 이미지 검수 서비스",
            page_icon="🔍",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # 애플리케이션 설정 로드
        config = AppConfig.from_env()
        
        # 2단계 검수 서비스 초기화
        inspection_service = TwoStageInspectionService(config)
        
        # 비동기 초기화
        async def init_service():
            return await inspection_service.initialize()
        
        # 초기화 실행
        with st.spinner("2단계 검수 서비스 초기화 중..."):
            if not asyncio.run(init_service()):
                st.error("❌ 2단계 검수 서비스 초기화에 실패했습니다.")
                st.stop()
            else:
                st.success("✅ 2단계 검수 서비스 초기화 완료!")
        
        # 2단계 검수 설명
        st.markdown("### 🔄 2단계 검수 시스템")
        st.info("""
        **1단계**: OpenCV를 활용한 컴퓨터 비전 기반 테두리 탐지
        **2단계**: 테두리가 없으면 AWS Bedrock Nova 모델을 통한 AI 검수 적용
        """)
        
        # 기술 스택 정보 추가
        st.markdown("#### 🛠️ 사용 기술")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**1단계 - 테두리 탐지**")
            st.markdown("- 🔍 OpenCV 컴퓨터 비전")
            st.markdown("- 📐 엣지 검출 알고리즘")
            st.markdown("- 🎨 색상 분석")
        with col2:
            st.markdown("**2단계 - AI 검수**")
            st.markdown("- 🤖 AWS Bedrock Nova Pro/Lite")
            st.markdown("- 💾 DynamoDB 결과 저장")
            st.markdown("- 📊 상세 검수 리포트")
        
        # Streamlit 앱 실행 (2단계 서비스 주입)
        app = StreamlitApp(inspection_service=inspection_service)
        app.run()
        
    except Exception as e:
        st.error(f"❌ 애플리케이션 초기화 실패: {str(e)}")
        st.stop()

if __name__ == "__main__":
    main()
