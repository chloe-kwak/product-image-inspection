"""
하이브리드 Streamlit 애플리케이션
Nova Pro + Claude 하이브리드 검수 서비스용 UI
"""

import streamlit as st
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import asyncio
import sys
import os

# 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.app_config import AppConfig
from services.hybrid_inspection_service import HybridInspectionService


class HybridStreamlitApp:
    """하이브리드 Streamlit 애플리케이션 클래스"""
    
    def __init__(self):
        """HybridStreamlitApp 초기화"""
        self.inspection_service = None
        self.config = None
        self.is_initialized = False
        
        # 페이지 설정
        st.set_page_config(
            page_title="🔍 하이브리드 상품 이미지 검수 서비스",
            page_icon="🔍",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # CSS 스타일 적용
        self._apply_custom_styles()
    
    def _apply_custom_styles(self):
        """커스텀 CSS 스타일 적용"""
        st.markdown("""
        <style>
        .main-header {
            text-align: center;
            color: #1f77b4;
            margin-bottom: 2rem;
        }
        .result-success {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 0.375rem;
            padding: 1rem;
            margin: 1rem 0;
        }
        .result-failure {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 0.375rem;
            padding: 1rem;
            margin: 1rem 0;
        }
        .hybrid-badge {
            background-color: #6f42c1;
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.875rem;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)
    
    async def initialize_service(self):
        """하이브리드 검수 서비스 초기화"""
        if self.is_initialized:
            return True
        
        try:
            # 설정 로드
            self.config = AppConfig.from_env()
            
            # 하이브리드 서비스 초기화
            self.inspection_service = HybridInspectionService(self.config)
            
            # 서비스 초기화
            success = await self.inspection_service.initialize()
            
            if success:
                self.is_initialized = True
                st.success("✅ 하이브리드 검수 서비스 초기화 완료!")
                return True
            else:
                st.error("❌ 하이브리드 검수 서비스 초기화 실패")
                return False
                
        except Exception as e:
            st.error(f"❌ 초기화 오류: {str(e)}")
            return False
    
    def run(self):
        """애플리케이션 실행"""
        # 헤더
        st.markdown('<h1 class="main-header">🔍 하이브리드 상품 이미지 검수 서비스</h1>', unsafe_allow_html=True)
        st.markdown('<div class="hybrid-badge">Nova Pro + Claude Hybrid</div>', unsafe_allow_html=True)
        st.markdown("---")
        
        # 서비스 초기화
        if not self.is_initialized:
            with st.spinner("하이브리드 검수 서비스 초기화 중..."):
                success = asyncio.run(self.initialize_service())
                if not success:
                    st.stop()
        
        # 탭 생성
        tab1, tab2, tab3 = st.tabs(["🔍 단일 검수", "📋 일괄 검수", "📊 검수 이력"])
        
        with tab1:
            self.render_single_inspection_ui()
        
        with tab2:
            self.render_batch_inspection_ui()
        
        with tab3:
            self.render_inspection_history_ui()
    
    def render_single_inspection_ui(self):
        """단일 검수 UI 렌더링"""
        st.markdown("### 🔍 단일 이미지 검수")
        
        # 이미지 URL 입력
        image_url = st.text_input(
            "검수할 이미지 URL을 입력하세요:",
            placeholder="https://example.com/image.jpg",
            key="single_image_url"
        )
        
        # 검수 실행 버튼
        if st.button("🚀 하이브리드 검수 시작", type="primary", key="single_inspect"):
            if image_url:
                self.execute_single_inspection(image_url)
            else:
                st.warning("⚠️ 이미지 URL을 입력해주세요.")
        
        # 검수 결과 표시
        if 'single_result' in st.session_state:
            self.render_single_result(st.session_state.single_result)
    
    def execute_single_inspection(self, image_url: str):
        """단일 검수 실행"""
        try:
            with st.spinner("🔄 하이브리드 검수 진행 중..."):
                # 하이브리드 검수 실행
                result = self.inspection_service.inspect_image(image_url)
                
                # 세션에 결과 저장
                st.session_state.single_result = result
                
                # 성공 메시지
                st.success("✅ 하이브리드 검수 완료!")
                
        except Exception as e:
            st.error(f"❌ 검수 실패: {str(e)}")
    
    def render_single_result(self, result):
        """단일 검수 결과 렌더링"""
        st.markdown("### 📋 검수 결과")
        
        # 결과 표시
        if result.result:
            st.markdown('<div class="result-success">✅ <strong>합격</strong></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="result-failure">❌ <strong>불합격</strong></div>', unsafe_allow_html=True)
        
        # 사유 표시
        st.markdown("#### 📝 검수 사유")
        st.write(result.reason)
        
        # 메타데이터 표시
        st.markdown("#### 📊 검수 정보")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("처리 시간", f"{result.processing_time:.2f}초")
        
        with col2:
            st.metric("검수 시간", result.timestamp.strftime("%H:%M:%S"))
        
        with col3:
            # 하이브리드 모델 표시
            model_display = result.model_id.replace("hybrid(", "").replace(")", "").replace("→", " → ")
            st.metric("사용 모델", model_display)
        
        with col4:
            st.metric("프롬프트 버전", result.prompt_version or "Unknown")
        
        # 이미지 URL 표시
        st.markdown("#### 🔗 검수 대상")
        st.code(result.image_url, language=None)
        
        # 다운로드 및 저장 버튼
        col1, col2 = st.columns(2)
        
        with col1:
            # JSON 다운로드
            result_dict = {
                'url': result.image_url,
                'result': result.result,
                'reason': result.reason,
                'processing_time': result.processing_time,
                'model_id': result.model_id,
                'prompt_version': result.prompt_version,
                'timestamp': result.timestamp.isoformat(),
                'hybrid': True
            }
            
            json_str = json.dumps(result_dict, ensure_ascii=False, indent=2)
            st.download_button(
                label="📥 결과 JSON 다운로드",
                data=json_str,
                file_name=f"hybrid_inspection_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                key="download_single_result"
            )
        
        with col2:
            if st.button("💾 DynamoDB에 저장", key="save_single_to_db"):
                self._save_single_to_dynamodb(result)
    
    def render_batch_inspection_ui(self):
        """일괄 검수 UI 렌더링"""
        st.markdown("### 📋 일괄 이미지 검수")
        
        # 이미지 URL 입력
        urls_text = st.text_area(
            "검수할 이미지 URL들을 한 줄에 하나씩 입력하세요:",
            placeholder="https://example.com/image1.jpg\nhttps://example.com/image2.jpg\nhttps://example.com/image3.jpg",
            height=150,
            key="batch_urls"
        )
        
        # URL 파싱
        image_urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
        
        if image_urls:
            st.info(f"📊 입력된 이미지: {len(image_urls)}개")
        
        # 일괄 검수 실행 버튼
        if image_urls:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button(
                    f"🚀 하이브리드 일괄 검수 시작 ({len(image_urls)}개 이미지)",
                    type="primary",
                    use_container_width=True,
                    key="batch_inspect_button"
                ):
                    self.execute_batch_inspection(image_urls)
        
        # 일괄 검수 결과 표시
        if 'batch_results' in st.session_state:
            self.render_batch_results(st.session_state.batch_results)
    
    def execute_batch_inspection(self, image_urls: List[str]):
        """일괄 검수 실행"""
        results = []
        
        # 진행 상태 표시
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, url in enumerate(image_urls):
            try:
                status_text.text(f"🔄 검수 중... ({i+1}/{len(image_urls)}) {url}")
                
                # 하이브리드 검수 실행
                result = self.inspection_service.inspect_image(url)
                
                results.append({
                    'url': url,
                    'result': result.result,
                    'reason': result.reason,
                    'processing_time': result.processing_time,
                    'model_id': result.model_id,
                    'prompt_version': result.prompt_version,
                    'success': True,
                    'hybrid': True
                })
                
            except Exception as e:
                results.append({
                    'url': url,
                    'result': False,
                    'reason': f"검수 오류: {str(e)}",
                    'processing_time': 0,
                    'model_id': "error",
                    'prompt_version': "error",
                    'success': False,
                    'hybrid': True
                })
            
            # 진행률 업데이트
            progress_bar.progress((i + 1) / len(image_urls))
        
        # 완료 메시지
        progress_bar.progress(1.0)
        status_text.text("✅ 하이브리드 일괄 검수 완료!")
        
        # 결과를 세션 상태에 저장
        st.session_state.batch_results = results
        
        # 페이지 새로고침으로 결과 표시
        st.rerun()
    
    def render_batch_results(self, results: List[Dict]):
        """일괄 검수 결과 렌더링"""
        if not results:
            return
        
        st.markdown("### 📊 일괄 검수 결과")
        
        # 통계 표시
        total = len(results)
        success_count = sum(1 for r in results if r['success'])
        pass_count = sum(1 for r in results if r['success'] and r['result'])
        fail_count = sum(1 for r in results if r['success'] and not r['result'])
        error_count = total - success_count
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("전체", total)
        with col2:
            st.metric("합격", pass_count, delta=f"{pass_count/total*100:.1f}%")
        with col3:
            st.metric("불합격", fail_count, delta=f"{fail_count/total*100:.1f}%")
        with col4:
            st.metric("오류", error_count, delta=f"{error_count/total*100:.1f}%" if error_count > 0 else None)
        
        # 결과 다운로드 및 저장
        if results:
            col1, col2 = st.columns(2)
            
            with col1:
                json_str = json.dumps(results, ensure_ascii=False, indent=2)
                st.download_button(
                    label="📥 결과 JSON 다운로드",
                    data=json_str,
                    file_name=f"hybrid_batch_inspection_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    key="download_batch_results"
                )
            
            with col2:
                # 세션 기반 안정적인 키 생성
                if 'batch_save_key' not in st.session_state:
                    st.session_state.batch_save_key = f"batch_save_{int(time.time())}"
                
                button_clicked = st.button("💾 DynamoDB에 저장", key=st.session_state.batch_save_key)
                if button_clicked:
                    st.write("🔍 **디버깅:** 버튼이 클릭되었습니다!")
                    self._save_batch_to_dynamodb(results)
        
        # 상세 결과 표시
        st.markdown("#### 📋 상세 결과")
        
        for i, result in enumerate(results, 1):
            with st.expander(f"#{i} - {'✅ 합격' if result['success'] and result['result'] else '❌ 불합격' if result['success'] else '⚠️ 오류'}"):
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    if result['success']:
                        if result['result']:
                            st.success("✅ 합격")
                        else:
                            st.error("❌ 불합격")
                    else:
                        st.warning("⚠️ 오류")
                
                with col2:
                    st.markdown(f"**URL:** {result['url']}")
                    st.markdown(f"**사유:** {result['reason']}")
                    if result['success']:
                        st.markdown(f"**처리 시간:** {result['processing_time']:.2f}초")
                        if 'model_id' in result:
                            model_display = result['model_id'].replace("hybrid(", "").replace(")", "").replace("→", " → ")
                            st.markdown(f"**사용 모델:** {model_display}")
                        if 'prompt_version' in result:
                            st.markdown(f"**프롬프트 버전:** {result['prompt_version']}")
                        st.markdown("**🔄 하이브리드 검수**")
    
    def render_inspection_history_ui(self):
        """검수 이력 UI 렌더링"""
        st.markdown("### 📊 검수 이력")
        st.info("🔄 하이브리드 검수 이력 기능은 개발 중입니다.")
    
    def _save_single_to_dynamodb(self, result):
        """단일 검수 결과를 DynamoDB에 저장"""
        try:
            if not hasattr(self.inspection_service, 'dynamodb_service'):
                st.error("❌ DynamoDB 서비스가 초기화되지 않았습니다")
                return
            
            # 진행 상태 표시
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            
            with progress_placeholder:
                with st.spinner("DynamoDB에 저장 중..."):
                    saved_id = self.inspection_service.dynamodb_service.save_inspection_result(result)
            
            progress_placeholder.empty()
            
            if saved_id:
                with status_placeholder:
                    st.success(f"✅ **저장 완료!** DynamoDB에 저장되었습니다")
                    st.info(f"📋 **저장 ID:** {saved_id}")
                    st.caption(f"⏰ 저장 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                with status_placeholder:
                    st.error("❌ **저장 실패!** DynamoDB 저장에 실패했습니다")
                    st.warning("💡 AWS 자격 증명이나 권한을 확인해주세요")
            
        except Exception as e:
            st.error("❌ **저장 오류!** DynamoDB 저장 중 오류가 발생했습니다")
            st.code(f"오류 내용: {str(e)}")
    
    def _save_batch_to_dynamodb(self, results: List[Dict]):
        """일괄 검수 결과를 DynamoDB에 저장"""
        try:
            if not hasattr(self.inspection_service, 'dynamodb_service'):
                st.error("❌ DynamoDB 서비스가 초기화되지 않았습니다")
                return
            
            # 디버깅: 입력 데이터 확인
            st.write(f"🔍 **디버깅:** 저장할 결과 개수: {len(results)}")
            st.write(f"🔍 **디버깅:** 첫 번째 결과 샘플:")
            if results:
                st.json(results[0])
            
            # 진행 상태 표시
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            
            with progress_placeholder:
                with st.spinner(f"DynamoDB에 {len(results)}개 결과 저장 중..."):
                    saved_ids = self.inspection_service.dynamodb_service.save_batch_results(results)
            
            # 진행 상태 제거
            progress_placeholder.empty()
            
            # 디버깅: 저장 결과 확인
            st.write(f"🔍 **디버깅:** 저장된 ID 개수: {len(saved_ids) if saved_ids else 0}")
            if saved_ids:
                st.write(f"🔍 **디버깅:** 첫 번째 저장 ID: {saved_ids[0]}")
            
            # 결과 표시
            if saved_ids:
                with status_placeholder:
                    st.success(f"✅ **저장 완료!** {len(saved_ids)}개 결과를 DynamoDB에 저장했습니다")
                    
                    # 성공률 표시
                    success_rate = len(saved_ids) / len(results) * 100
                    st.info(f"📊 **성공률:** {success_rate:.1f}% ({len(saved_ids)}/{len(results)})")
                    
                    # 저장된 ID들 표시
                    with st.expander("📋 저장된 항목 ID들 보기"):
                        for i, saved_id in enumerate(saved_ids, 1):
                            st.code(f"{i:2d}. {saved_id}")
                    
                    st.caption(f"⏰ 저장 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                with status_placeholder:
                    st.error("❌ **저장 실패!** DynamoDB 저장에 실패했습니다")
                    st.warning("💡 AWS 자격 증명이나 권한을 확인해주세요")
                    
        except Exception as e:
            with status_placeholder:
                st.error("❌ **저장 오류!** DynamoDB 저장 중 오류가 발생했습니다")
                st.code(f"오류 내용: {str(e)}")
                st.warning("💡 네트워크 연결이나 AWS 설정을 확인해주세요")
