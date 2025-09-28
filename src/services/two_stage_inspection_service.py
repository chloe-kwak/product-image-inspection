"""
2단계 검수 서비스: 테두리 탐지 + 일반 검수
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
import sys

# 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.strands_agent import StrandsAgent
from handlers.image_handler import ImageHandler
from parsers.result_parser import ResultParser
from models.inspection_result import InspectionResult
from models.app_config import AppConfig
from models.prompt_version import PromptVersionManager

# DynamoDB 서비스 import
from services.dynamodb_service import DynamoDBService

logger = logging.getLogger(__name__)


class TwoStageInspectionService:
    """2단계 검수 서비스: 1단계 테두리 탐지 + 2단계 일반 검수"""
    
    def __init__(self, config: AppConfig):
        """
        TwoStageInspectionService 초기화
        
        Args:
            config: 애플리케이션 설정
        """
        self.config = config
        self.strands_agent = None
        self.image_handler = ImageHandler()
        self.result_parser = ResultParser()
        self.prompt_manager = PromptVersionManager()
        self.dynamodb_service = DynamoDBService(config.aws_region)  # DynamoDB 서비스 추가
        self.is_initialized = False
        
        # 프롬프트 설정
        self._setup_prompts()
    
    def _setup_prompts(self):
        """프롬프트 설정"""
        # 1단계: 하이브리드 테두리 탐지 프롬프트
        self.border_detection_prompt = """이 이미지를 분석하세요.

**확인사항:**
이미지 전체의 가장자리(경계선)에 인위적인 색상 테두리나 프레임이 있나요?

테두리 예시:
- 파란색, 빨간색, 검은색, 흰색, 회색 등의 경계선
- 이미지 전체를 둘러싸는 색상 프레임
- 명확하게 구분되는 테두리 라인

**무시해야 할 것:**
- 제품 내부의 로고, 텍스트, 디자인
- 제품 자체의 색상이나 패턴
- 자연스러운 배경색

**판정:**
- 이미지 경계에 명확한 인위적 테두리가 있으면: false
- 이미지 경계에 인위적 테두리가 없으면: true

답변: true 또는 false"""

        # 2단계: 일반 검수 프롬프트 (.env에서 가져오기, 기본값 v3.2)
        env_prompt_version = os.getenv('PROMPT_VERSION', 'v3.2')
        self.general_inspection_version = env_prompt_version
    
    async def initialize(self) -> bool:
        """서비스 초기화"""
        try:
            # StrandsAgent 초기화
            self.strands_agent = StrandsAgent(
                aws_region=self.config.aws_region,
                model_id=self.config.bedrock_model_id,
                aws_access_key_id=self.config.aws_access_key_id,
                aws_secret_access_key=self.config.aws_secret_access_key,
                temperature=0.0
            )
            
            self.strands_agent.initialize_agent()
            
            # 프롬프트 매니저 초기화
            self.prompt_manager.set_active_version(self.general_inspection_version)
            
            # DynamoDB 서비스 초기화
            self.dynamodb_service.initialize()
            
            self.is_initialized = True
            logger.info("2단계 검수 서비스 초기화 완료")
            return True
            
        except Exception as e:
            logger.error(f"2단계 검수 서비스 초기화 실패: {str(e)}")
            return False
    
    def inspect_image(self, image_url: str) -> InspectionResult:
        """
        2단계 이미지 검수
        
        Args:
            image_url: 검수할 이미지 URL
            
        Returns:
            InspectionResult: 검수 결과
        """
        if not self.is_initialized:
            raise RuntimeError("서비스가 초기화되지 않았습니다")
        
        start_time = time.time()
        
        try:
            # 이미지 다운로드 및 처리
            logger.info(f"2단계 검수 시작: {image_url}")
            image_data = self.image_handler.fetch_and_process_image(image_url)
            original_bytes = image_data['raw_bytes']
            
            # 1단계: 테두리 탐지
            border_result = self._detect_border(original_bytes, image_url)
            
            # 디버깅: 1단계 결과 로그
            logger.info(f"🔍 1단계 테두리 탐지 결과: {border_result.result}")
            logger.info(f"🔍 1단계 사유: {border_result.reason}")
            
            if not border_result.result:
                # 테두리 발견 → 즉시 false 반환
                border_result.processing_time = time.time() - start_time
                border_result.reason = "이미지 경계에 색상 테두리 탐지됨 [1단계 테두리 검수에서 반려]"
                
                # 검수 단계 메타데이터 추가
                border_result.inspection_stage = "stage_1_border_detected"
                border_result.stage_details = {
                    "stage_1_result": "border_detected",
                    "stage_2_executed": False,
                    "detection_method": "resize_comparison"
                }
                
                logger.info(f"✅ 1단계에서 테두리 탐지하여 검수 종료: {image_url}")
                return border_result
            
            # 2단계: 일반 검수
            logger.info(f"➡️ 1단계 통과, 2단계 일반 검수 진행: {image_url}")
            general_result = self._general_inspection(image_data, image_url)
            general_result.processing_time = time.time() - start_time
            general_result.reason += " [2단계 검수: 테두리 없음, 일반 기준 적용]"
            
            # 검수 단계 메타데이터 추가
            general_result.inspection_stage = "stage_2_general_completed"
            general_result.stage_details = {
                "stage_1_result": "no_border_detected",
                "stage_2_executed": True,
                "stage_2_result": general_result.result,
                "detection_method": "resize_comparison + general_inspection"
            }
            
            logger.info(f"2단계 검수 완료: {image_url} -> {general_result.result}")
            return general_result
            
        except Exception as e:
            logger.error(f"2단계 검수 실패: {str(e)}")
            return InspectionResult(
                image_url=image_url,
                result=False,
                reason=f"검수 오류: {str(e)}",
                timestamp=datetime.now(),
                processing_time=time.time() - start_time,
                raw_response="",
                model_id=self.config.bedrock_model_id,
                prompt_version="error"
            )
    
    def _detect_border(self, original_bytes: bytes, image_url: str) -> InspectionResult:
        """1단계: OpenCV 테두리 탐지"""
        try:
            # OpenCV로 테두리 탐지
            has_opencv_border, opencv_analysis, confidence = self.image_handler.detect_border_opencv(original_bytes)

            logger.info(f"🔬 OpenCV 분석: {opencv_analysis}, 신뢰도: {confidence:.2f}")

            # OpenCV가 테두리를 탐지했으면 즉시 false 반환
            if has_opencv_border:
                return InspectionResult(
                    image_url=image_url,
                    result=False,  # 테두리 발견, 즉시 반려
                    reason=f"OpenCV 테두리 탐지: {opencv_analysis} (신뢰도: {confidence:.1%})",
                    timestamp=datetime.now(),
                    processing_time=0,
                    raw_response="",
                    model_id=self.config.bedrock_model_id,
                    prompt_version="opencv_border_detected"
                )

            # OpenCV가 테두리를 탐지하지 못했으면 2단계로 진행하라는 신호
            return InspectionResult(
                image_url=image_url,
                result=True,  # 테두리 없음, 2단계로 진행
                reason=f"OpenCV: 테두리 미탐지 ({opencv_analysis}), 일반 검수 진행",
                timestamp=datetime.now(),
                processing_time=0,
                raw_response="",
                model_id=self.config.bedrock_model_id,
                prompt_version="opencv_no_border_detected"
            )

        except Exception as e:
            logger.error(f"OpenCV 테두리 탐지 실패: {str(e)}")
            # 오류 시 안전하게 일반 검수로 넘어가기
            return InspectionResult(
                image_url=image_url,
                result=True,  # 테두리 없다고 가정하고 2단계로
                reason="테두리 탐지 오류, 일반 검수로 진행",
                timestamp=datetime.now(),
                processing_time=0,
                raw_response="",
                model_id=self.config.bedrock_model_id,
                prompt_version="border_detection_error"
            )
    
    def _general_inspection(self, image_data: Dict, image_url: str) -> InspectionResult:
        """2단계: 일반 검수"""
        try:
            # 일반 검수 프롬프트 가져오기
            general_prompt = self.prompt_manager.get_active_prompt()
            
            # 일반 검수 실행
            ai_response = self.strands_agent.send_inspection_request(
                image_base64=image_data['base64'],
                prompt=general_prompt,
                media_type=f"image/{image_data['info']['format'].lower()}"
            )
            
            # 결과 파싱
            result = self.result_parser.parse_ai_response(
                response=ai_response,
                image_url=image_url,
                processing_time=0,
                model_id=self.config.bedrock_model_id,
                prompt_version=self.general_inspection_version
            )
            
            return result
            
        except Exception as e:
            logger.error(f"일반 검수 실패: {str(e)}")
            raise e
    
    def inspect_batch(self, image_urls: List[str]) -> List[InspectionResult]:
        """
        일괄 이미지 검수 (2단계 방식)
        
        Args:
            image_urls: 검수할 이미지 URL 리스트
            
        Returns:
            List[InspectionResult]: 검수 결과 리스트
        """
        if not self.is_initialized:
            raise RuntimeError("서비스가 초기화되지 않았습니다")
        
        results = []
        
        for i, image_url in enumerate(image_urls):
            try:
                logger.info(f"일괄 검수 진행: {i+1}/{len(image_urls)} - {image_url}")
                result = self.inspect_image(image_url)
                results.append(result)
                
            except Exception as e:
                logger.error(f"일괄 검수 중 오류 ({image_url}): {str(e)}")
                # 오류 발생 시에도 결과 추가 (실패 결과)
                error_result = InspectionResult(
                    image_url=image_url,
                    result=False,
                    reason=f"검수 오류: {str(e)}",
                    timestamp=datetime.now(),
                    processing_time=0,
                    raw_response="",
                    model_id=self.config.bedrock_model_id,
                    prompt_version="error",
                    inspection_stage="error",
                    stage_details={"error": str(e)}
                )
                results.append(error_result)
        
        logger.info(f"일괄 검수 완료: {len(results)}개 결과")
        return results
