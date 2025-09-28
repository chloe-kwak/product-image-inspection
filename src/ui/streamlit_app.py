"""
Streamlit UI 애플리케이션 모듈
사용자 인터페이스를 담당합니다.
"""

import streamlit as st
import logging
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
import base64
from io import BytesIO
from dotenv import load_dotenv
import json

# 환경 변수 로드
load_dotenv()

# 필요한 모듈들 import
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.inspection_service import InspectionService
from models.inspection_result import InspectionResult
from models.app_config import AppConfig

logger = logging.getLogger(__name__)


class StreamlitApp:
    """Streamlit 애플리케이션 클래스"""
    
    def __init__(self, inspection_service=None):
        """StreamlitApp 초기화"""
        self.inspection_service = inspection_service  # 외부에서 주입받은 서비스
        self.config = None
        self.is_initialized = False
        
        # 페이지 설정
        st.set_page_config(
            page_title="상품 이미지 검수 서비스",
            page_icon="🔍",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # CSS 스타일 적용
        self._apply_custom_styles()
    
    def initialize_app(self) -> bool:
        """
        애플리케이션 초기화
        
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            if not self.is_initialized:
                if self.inspection_service:
                    # 외부에서 주입받은 서비스 사용 (2단계 검수 등)
                    self.is_initialized = True
                    logger.info("외부 검수 서비스 연결 완료")
                else:
                    # 기본 InspectionService 초기화
                    self.config = AppConfig.from_env()
                    
                    # InspectionService 초기화
                    self.inspection_service = InspectionService(self.config)
                    self.inspection_service.initialize()
                    
                    self.is_initialized = True
                    logger.info("기본 검수 서비스 초기화 완료")
            
            return True
            
        except Exception as e:
            logger.error(f"StreamlitApp 초기화 실패: {str(e)}")
            st.error(f"애플리케이션 초기화 실패: {str(e)}")
            return False
    
    def run(self):
        """메인 애플리케이션 실행"""
        # 헤더 렌더링
        self.render_header()
        
        # 애플리케이션 초기화
        if not self.initialize_app():
            st.stop()
        
        # 메인 UI 렌더링
        self.render_main_ui()
    
    def render_header(self) -> None:
        """헤더 및 제목 섹션 렌더링"""
        st.title("🔍 상품 이미지 검수 서비스")
        st.markdown("---")
        
        # 서비스 설명
        st.markdown("""
        ### 📋 서비스 소개
        AWS Bedrock Nova Pro/Lite 모델과 OpenCV를 활용하여 상품 이미지를 자동으로 검수합니다.
        
        **검수 기준:**
        - 상품 외 배경의 네모 테두리 강조 여부
        - 브랜드명 외의 불필요한 텍스트 포함 여부
        - 기타 상품 이미지 품질 기준
        
        **기술 스택:**
        - 🤖 AI 모델: AWS Bedrock Nova Pro/Lite
        - 🔍 이미지 처리: OpenCV
        - 📊 데이터 저장: DynamoDB
        """)
        
        st.markdown("---")
    
    def render_main_ui(self) -> None:
        """메인 UI 렌더링"""
        # 탭으로 단일/일괄 검수 구분
        tab1, tab2 = st.tabs(["🔍 단일 검수", "📋 일괄 검수"])
        
        with tab1:
            self.render_single_inspection_ui()
        
        with tab2:
            self.render_batch_inspection_ui()
        
        # 하단에 서비스 상태 표시
        self.render_service_status()
    
    def render_single_inspection_ui(self) -> None:
        """단일 검수 UI 렌더링"""
        # 두 개의 컬럼으로 레이아웃 구성
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📤 이미지 입력")
            
            # 이미지 URL 입력
            image_url = self.render_image_url_input()
            
            # 이미지 미리보기
            if image_url:
                self.render_image_preview(image_url)
            
            # 검수 실행 버튼
            if image_url:
                inspection_triggered = self.render_inspection_button()
                
                if inspection_triggered:
                    # 검수 실행
                    with col2:
                        self.execute_inspection(image_url)
        
        with col2:
            st.subheader("📊 검수 결과")
            
            # 세션 상태에서 결과 표시
            if 'inspection_result' in st.session_state:
                self.render_inspection_result(st.session_state.inspection_result)
            else:
                st.info("이미지 URL을 입력하고 검수를 실행해주세요.")
    
    def render_batch_inspection_ui(self) -> None:
        """일괄 검수 UI 렌더링"""
        st.subheader("📋 일괄 이미지 검수")
        
        # 기본 테스트 URL들
        default_urls = [
            "https://shop-phinf.pstatic.net/20250827_266/1756283702318M5JMo_JPEG/2729632462003176_1558362207.jpg",
            "https://shop-phinf.pstatic.net/20250529_29/1748478744962VWp59_JPEG/29574150851206828_232978590.jpg",
            "https://shop-phinf.pstatic.net/20250808_142/1754659885260U6F5r_JPEG/88792677359668411_1295289015.jpg",
            "https://shop-phinf.pstatic.net/20250409_31/1744184048255Udgdz_JPEG/30226391699724663_1975296697.jpg",
            "https://shop-phinf.pstatic.net/20250827_46/1756283687822GciLg_JPEG/35877271140464566_343581514.jpg"
        ]
        
        # URL 입력 방식 선택
        input_method = st.radio(
            "입력 방식 선택:",
            ["기본 테스트 이미지 사용", "직접 URL 입력"],
            horizontal=True
        )
        
        if input_method == "기본 테스트 이미지 사용":
            st.info("💡 미리 준비된 5개의 테스트 이미지를 사용합니다.")
            image_urls = default_urls
            
            # 미리보기 표시
            with st.expander("🖼️ 테스트 이미지 미리보기"):
                cols = st.columns(3)
                for i, url in enumerate(image_urls[:3]):
                    with cols[i]:
                        try:
                            st.image(url, caption=f"이미지 {i+1}", width=150)
                        except:
                            st.error(f"이미지 {i+1} 로드 실패")
        
        else:
            st.markdown("**이미지 URL들을 한 줄에 하나씩 입력하세요:**")
            url_text = st.text_area(
                "URL 목록:",
                height=200,
                placeholder="https://example.com/image1.jpg\nhttps://example.com/image2.jpg\n...",
                help="각 URL을 새 줄에 입력하세요"
            )
            
            if url_text.strip():
                image_urls = [url.strip() for url in url_text.strip().split('\n') if url.strip()]
                st.info(f"📝 입력된 URL 개수: {len(image_urls)}개")
            else:
                image_urls = []
        
        # 일괄 검수 실행 버튼
        if image_urls:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button(
                    f"🚀 일괄 검수 시작 ({len(image_urls)}개 이미지)",
                    type="primary",
                    use_container_width=True,
                    key="batch_inspect_button"
                ):
                    self.execute_batch_inspection(image_urls)
        
        # DynamoDB 연결 테스트 (일괄 검수용)
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔧 DynamoDB 연결 테스트", key="batch_test_db_connection"):
                self._test_dynamodb_connection()
        
        # 일괄 검수 결과 표시
        if 'batch_results' in st.session_state:
            self.render_batch_results(st.session_state.batch_results)
    
    def execute_batch_inspection(self, image_urls: List[str]) -> None:
        """일괄 검수 실행"""
        st.markdown("---")
        st.subheader("📊 일괄 검수 결과")
        
        # 디버깅: 일괄 검수에서 사용하는 프롬프트 버전 표시
        if hasattr(self.inspection_service, 'prompt_manager'):
            active_version = self.inspection_service.prompt_manager.get_active_version_info()
            if active_version:
                st.info(f"🔍 **일괄 검수 디버깅**: 현재 사용 중인 프롬프트 버전: **{active_version.version}** ({active_version.name})")
            else:
                st.warning("⚠️ **일괄 검수 디버깅**: 활성 프롬프트 버전을 찾을 수 없습니다")
        
        # 진행률 표시
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        
        for i, url in enumerate(image_urls):
            # 진행률 업데이트
            progress = (i + 1) / len(image_urls)
            progress_bar.progress(progress)
            status_text.text(f"검수 중... ({i+1}/{len(image_urls)}) {url[:50]}...")
            
            try:
                # 검수 실행
                result = self.inspection_service.inspect_image(url)
                results.append({
                    'url': url,
                    'result': result.result,
                    'reason': result.reason,
                    'processing_time': result.processing_time,
                    'model_id': result.model_id,
                    'prompt_version': result.prompt_version,  # 프롬프트 버전 추가
                    'success': True
                })
                
            except Exception as e:
                results.append({
                    'url': url,
                    'result': False,
                    'reason': f"검수 실패: {str(e)}",
                    'processing_time': 0,
                    'success': False
                })
        
        # 완료 메시지
        progress_bar.progress(1.0)
        status_text.text("✅ 일괄 검수 완료!")
        
        # 결과를 세션 상태에 저장
        st.session_state.batch_results = results
        
        # 페이지 새로고침으로 결과 표시
        st.rerun()
    
    def render_batch_results(self, results: List[Dict]) -> None:
        """일괄 검수 결과 렌더링"""
        if not results:
            return
        
        st.markdown("### 📈 검수 결과 요약")
        
        # 요약 통계
        total_count = len(results)
        success_count = sum(1 for r in results if r['success'])
        pass_count = sum(1 for r in results if r['success'] and r['result'])
        fail_count = sum(1 for r in results if r['success'] and not r['result'])
        error_count = total_count - success_count
        
        # 통계 표시
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("전체", total_count)
        with col2:
            st.metric("합격", pass_count, delta=f"{pass_count/total_count*100:.1f}%")
        with col3:
            st.metric("불합격", fail_count, delta=f"{fail_count/total_count*100:.1f}%")
        with col4:
            st.metric("오류", error_count, delta=f"{error_count/total_count*100:.1f}%")
        
        # 상세 결과 테이블
        st.markdown("### 📋 상세 결과")
        
        for i, result in enumerate(results):
            with st.expander(f"이미지 {i+1}: {'✅ 합격' if result['success'] and result['result'] else '❌ 불합격' if result['success'] else '⚠️ 오류'}"):
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    try:
                        st.image(result['url'], caption=f"이미지 {i+1}", width=200)
                    except:
                        st.error("이미지 로드 실패")
                
                with col2:
                    st.markdown(f"**URL:** {result['url']}")
                    st.markdown(f"**결과:** {'✅ 합격' if result['success'] and result['result'] else '❌ 불합격' if result['success'] else '⚠️ 오류'}")
                    st.markdown(f"**사유:** {result['reason']}")
                    if result['success']:
                        st.markdown(f"**처리 시간:** {result['processing_time']:.2f}초")
                        if 'model_id' in result:
                            st.markdown(f"**사용 모델:** {result['model_id']}")
                        if 'prompt_version' in result:
                            st.markdown(f"**프롬프트 버전:** {result['prompt_version']}")
        
        # 결과 다운로드 - 완전히 고유한 키 생성
        if results:  # 결과가 있을 때만 표시
            col1, col2 = st.columns(2)
            
            with col1:
                json_str = json.dumps(results, ensure_ascii=False, indent=2)
                import time
                unique_key = f"download_results_{int(time.time() * 1000000)}"  # 마이크로초 단위 타임스탬프
                st.download_button(
                    label="📥 결과 JSON 다운로드",
                    data=json_str,
                    file_name=f"batch_inspection_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    key=unique_key
                )
            
            with col2:
                # 세션 기반 안정적인 키 생성
                if 'batch_save_key' not in st.session_state:
                    st.session_state.batch_save_key = f"batch_save_{int(time.time())}"
                
                button_clicked = st.button("💾 DynamoDB에 저장", key=st.session_state.batch_save_key)
                if button_clicked:
                    st.write("🔍 **디버깅:** 버튼이 클릭되었습니다!")
                    self._save_batch_to_dynamodb(results)
    
    def _test_dynamodb_connection(self) -> None:
        """DynamoDB 연결 상태 테스트"""
        try:
            if not hasattr(self.inspection_service, 'dynamodb_service'):
                st.error("❌ DynamoDB 서비스가 초기화되지 않았습니다")
                return
            
            with st.spinner("DynamoDB 연결 테스트 중..."):
                test_result = self.inspection_service.dynamodb_service.test_connection()
            
            if test_result['success']:
                st.success("✅ **DynamoDB 연결 성공!**")
                st.info(f"📋 **테이블명:** {test_result['table_name']}")
                st.info(f"🌍 **리전:** {test_result['region']}")
                st.info(f"📊 **테이블 상태:** {test_result['table_status']}")
                st.info(f"🔢 **저장된 항목 수:** {test_result['item_count']}개")
            else:
                st.error("❌ **DynamoDB 연결 실패!**")
                st.code(f"오류: {test_result['error']}")
                st.warning("💡 AWS 자격 증명, 리전, 권한을 확인해주세요")
                
        except Exception as e:
            st.error("❌ **연결 테스트 오류!**")
            st.code(f"오류: {str(e)}")
    
    def _save_single_to_dynamodb(self, result) -> None:
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
            
            # 진행 상태 제거
            progress_placeholder.empty()
            
            # 결과 표시
            if saved_id:
                with status_placeholder:
                    st.success("✅ **저장 완료!** DynamoDB에 성공적으로 저장되었습니다")
                    st.info(f"📋 **저장된 ID:** `{saved_id}`")
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
    
    def _save_batch_to_dynamodb(self, results: List[Dict]) -> None:
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
    
    def render_image_url_input(self) -> str:
        """이미지 URL 입력 필드 렌더링"""
        image_url = st.text_input(
            "이미지 URL을 입력하세요:",
            placeholder="https://example.com/image.jpg",
            help="검수할 상품 이미지의 URL을 입력해주세요. (JPG, PNG, GIF 등 지원)"
        )
        
        return image_url.strip() if image_url else ""
    
    def render_image_preview(self, image_url: str) -> None:
        """이미지 미리보기 표시"""
        if not image_url:
            return
        
        try:
            st.markdown("#### 🖼️ 이미지 미리보기")
            
            # URL 유효성 간단 체크
            if not (image_url.startswith('http://') or image_url.startswith('https://')):
                st.warning("⚠️ 유효한 URL 형식이 아닙니다. http:// 또는 https://로 시작해야 합니다.")
                return
            
            # Streamlit의 이미지 표시 기능 사용
            try:
                st.image(image_url, caption="검수 대상 이미지", width="stretch")
                st.success("✅ 이미지 로드 성공")
            except Exception as e:
                st.error(f"❌ 이미지 로드 실패: {str(e)}")
                st.info("💡 이미지 URL이 올바른지, 이미지가 공개적으로 접근 가능한지 확인해주세요.")
                
        except Exception as e:
            st.error(f"이미지 미리보기 오류: {str(e)}")
    
    def render_inspection_button(self) -> bool:
        """검수 실행 버튼 렌더링"""
        st.markdown("#### 🚀 검수 실행")
        
        # 버튼 컬럼 레이아웃
        btn_col1, btn_col2 = st.columns([1, 1])
        
        with btn_col1:
            inspect_button = st.button(
                "🔍 검수 시작",
                type="primary",
                use_container_width=True,
                help="이미지 검수를 시작합니다",
                key="single_inspect_button"
            )
            
            # 디버깅: 현재 프롬프트 버전 표시
            if inspect_button and hasattr(self.inspection_service, 'prompt_manager'):
                active_version = self.inspection_service.prompt_manager.get_active_version_info()
                if active_version:
                    st.info(f"🔍 **디버깅**: 현재 사용 중인 프롬프트 버전: **{active_version.version}** ({active_version.name})")
                else:
                    st.warning("⚠️ **디버깅**: 활성 프롬프트 버전을 찾을 수 없습니다")
        
        with btn_col2:
            clear_button = st.button(
                "🗑️ 결과 지우기",
                use_container_width=True,
                help="검수 결과를 지웁니다",
                key="clear_results_button"
            )
        
        # 결과 지우기 버튼 처리
        if clear_button:
            if 'inspection_result' in st.session_state:
                del st.session_state.inspection_result
            st.rerun()
        
        return inspect_button
    
    def render_loading_state(self) -> None:
        """로딩 상태 표시"""
        with st.spinner("🔄 이미지 검수 중..."):
            # 진행률 표시
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            steps = [
                "이미지 다운로드 중...",
                "AI 모델에 요청 중...",
                "결과 분석 중...",
                "검수 완료!"
            ]
            
            for i, step in enumerate(steps):
                status_text.text(step)
                progress_bar.progress((i + 1) / len(steps))
                time.sleep(0.5)  # 시각적 효과를 위한 지연
            
            # 정리
            progress_bar.empty()
            status_text.empty()
    
    def execute_inspection(self, image_url: str) -> None:
        """검수 실행"""
        try:
            # 로딩 상태 표시
            with st.spinner("🔄 이미지 검수 중..."):
                # 진행률 표시
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 단계별 진행
                status_text.text("🔄 이미지 다운로드 중...")
                progress_bar.progress(0.25)
                
                # 실제 검수 실행
                result = self.inspection_service.inspect_image(image_url)
                
                status_text.text("🔄 AI 분석 중...")
                progress_bar.progress(0.75)
                
                status_text.text("✅ 검수 완료!")
                progress_bar.progress(1.0)
                
                # 잠시 대기 후 정리
                time.sleep(0.5)
                progress_bar.empty()
                status_text.empty()
            
            # 결과를 세션 상태에 저장
            st.session_state.inspection_result = result
            
            # 성공 메시지
            if result.result:
                st.success("✅ 검수 완료: 이미지가 기준을 통과했습니다!")
            else:
                st.warning("⚠️ 검수 완료: 이미지가 기준에 부합하지 않습니다.")
            
            # 페이지 새로고침하여 결과 표시
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 검수 실행 중 오류가 발생했습니다: {str(e)}")
            logger.error(f"검수 실행 오류: {str(e)}")
    
    def render_inspection_result(self, result: InspectionResult) -> None:
        """검수 결과 표시"""
        if not result:
            return
        
        # 결과에 따른 스타일 적용
        if result.result:
            st.success("✅ 검수 통과")
            result_color = "green"
            result_icon = "✅"
        else:
            st.error("❌ 검수 실패")
            result_color = "red"
            result_icon = "❌"
        
        # 결과 상세 정보
        st.markdown(f"""
        <div style="padding: 1rem; border-left: 4px solid {result_color}; background-color: #f8f9fa; margin: 1rem 0;">
            <h4 style="color: {result_color}; margin: 0;">{result_icon} 검수 결과: {'통과' if result.result else '실패'}</h4>
        </div>
        """, unsafe_allow_html=True)
        
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
            st.metric("사용 모델", result.model_id.split('.')[-1] if result.model_id else "Unknown")
        
        with col4:
            st.metric("프롬프트 버전", result.prompt_version or "Unknown")
        
        # 이미지 URL 표시
        st.markdown("#### 🔗 검수 대상")
        st.code(result.image_url, language=None)
        
        # 원본 응답 표시 (접을 수 있는 형태)
        with st.expander("🔍 상세 응답 보기"):
            st.text(result.raw_response)
        
        # 결과 다운로드 기능
        st.markdown("#### 💾 결과 저장")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # JSON 형태로 다운로드
            json_data = result.to_json()
            
            st.download_button(
                label="📄 JSON으로 다운로드",
                data=json_data,
                file_name=f"inspection_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                help="검수 결과를 JSON 파일로 다운로드합니다"
            )
        
        with col2:
            if st.button("💾 DynamoDB에 저장", key="save_single_to_db"):
                self._save_single_to_dynamodb(result)
            
            # DynamoDB 연결 테스트 버튼 (디버깅용)
            if st.button("🔧 DynamoDB 연결 테스트", key="test_db_connection"):
                self._test_dynamodb_connection()
    
    def render_service_status(self) -> None:
        """서비스 상태 표시"""
        if not self.is_initialized or not self.inspection_service:
            return
        
        # 사이드바에 서비스 상태 표시
        with st.sidebar:
            st.markdown("### 🔧 서비스 상태")
            
            try:
                health_status = self.inspection_service.validate_service_health()
                overall_status = health_status.get('overall_status', 'unknown')
                
                if overall_status == 'healthy':
                    st.success("✅ 서비스 정상")
                else:
                    st.warning("⚠️ 서비스 이상")
                
                # 컴포넌트별 상태
                components = health_status.get('components', {})
                for component, status in components.items():
                    component_status = status.get('status', 'unknown')
                    if component_status == 'healthy':
                        st.text(f"✅ {component}")
                    else:
                        st.text(f"❌ {component}")
                
                # 서비스 통계
                st.markdown("### 📊 서비스 정보")
                stats = self.inspection_service.get_service_stats()
                
                st.text(f"버전: {stats.get('version', 'N/A')}")
                st.text(f"지원 형식: {len(stats.get('supported_formats', []))}개")
                
            except Exception as e:
                st.error(f"상태 확인 실패: {str(e)}")
    
    def _apply_custom_styles(self) -> None:
        """커스텀 CSS 스타일 적용"""
        st.markdown("""
        <style>
        .main {
            padding-top: 2rem;
        }
        
        .stButton > button {
            width: 100%;
            border-radius: 8px;
            border: none;
            padding: 0.5rem 1rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .success-box {
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #28a745;
            background-color: #d4edda;
            margin: 1rem 0;
        }
        
        .error-box {
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #dc3545;
            background-color: #f8d7da;
            margin: 1rem 0;
        }
        
        .metric-container {
            background-color: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            margin: 0.5rem 0;
        }
        
        .stImage > img {
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        </style>
        """, unsafe_allow_html=True)


def main():
    """메인 함수"""
    app = StreamlitApp()
    app.run()


if __name__ == "__main__":
    main()