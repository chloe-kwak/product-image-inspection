"""
이미지 검수 서비스 모듈
전체 검수 워크플로우를 관리합니다.
"""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
import os

# 필요한 모듈들 import
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.strands_agent import StrandsAgent
from handlers.image_handler import ImageHandler
from parsers.result_parser import ResultParser
from models.inspection_result import InspectionResult
from models.app_config import AppConfig
from models.prompt_version import PromptVersionManager

# DynamoDB 서비스 import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))
from dynamodb_service import DynamoDBService

logger = logging.getLogger(__name__)


class InspectionService:
    """이미지 검수 서비스 클래스"""
    
    def __init__(self, config: AppConfig):
        """
        InspectionService 초기화
        
        Args:
            config: 애플리케이션 설정
        """
        self.config = config
        self.strands_agent = None
        self.image_handler = ImageHandler()
        self.result_parser = ResultParser()
        self.dynamodb_service = DynamoDBService(config.aws_region)
        self.prompt_manager = PromptVersionManager()
        self.is_initialized = False
        
        # 환경 변수에서 프롬프트 버전 확인
        env_prompt_version = os.getenv('PROMPT_VERSION')
        if env_prompt_version:
            # 지정된 버전으로 활성화
            if self.prompt_manager.set_active_version(env_prompt_version):
                logger.info(f"환경 변수에서 프롬프트 버전 설정: {env_prompt_version}")
            else:
                logger.warning(f"지정된 프롬프트 버전을 찾을 수 없음: {env_prompt_version}, 기본 버전 사용")
        
        # 환경 변수에 INSPECTION_PROMPT가 있으면 커스텀 버전으로 추가 (하위 호환성)
        env_prompt = self._get_inspection_prompt()
        if env_prompt and env_prompt.strip():
            # 기존 PROMPT_VERSION이 있으면 그 버전을 덮어쓰기, 없으면 custom 사용
            custom_version = env_prompt_version if env_prompt_version else "custom"
            self.prompt_manager.add_version(
                version=custom_version,
                name="커스텀 환경 변수 프롬프트",
                prompt_text=env_prompt,
                description="환경 변수 INSPECTION_PROMPT에서 로드된 프롬프트",
                is_active=True
            )
    
    def initialize(self) -> None:
        """
        검수 서비스 초기화
        
        Raises:
            ValueError: 초기화 실패시
        """
        try:
            # StrandsAgent 초기화
            self.strands_agent = StrandsAgent(
                aws_region=self.config.aws_region,
                model_id=self.config.bedrock_model_id,
                aws_access_key_id=self.config.aws_access_key_id,
                aws_secret_access_key=self.config.aws_secret_access_key,
                temperature=0.0  # 명시적으로 0.0 설정
            )
            
            self.strands_agent.initialize_agent()
            
            # DynamoDB 서비스 초기화
            dynamodb_initialized = self.dynamodb_service.initialize()
            if not dynamodb_initialized:
                logger.warning("DynamoDB 초기화 실패 - 저장 기능 비활성화")
            
            self.is_initialized = True
            logger.info("InspectionService 초기화 완료")
            
        except Exception as e:
            logger.error(f"InspectionService 초기화 실패: {str(e)}")
            raise ValueError(f"검수 서비스 초기화 실패: {str(e)}")
    
    def inspect_image(self, image_url: str, save_to_db: bool = False) -> InspectionResult:
        """
        이미지 검수 메인 로직
        이미지 페치 → Agent 호출 → 결과 파싱
        
        Args:
            image_url: 검수할 이미지 URL
            
        Returns:
            InspectionResult: 검수 결과
            
        Raises:
            ValueError: 검수 실패시
        """
        if not self.is_initialized:
            raise ValueError("검수 서비스가 초기화되지 않았습니다. initialize()를 먼저 호출하세요.")
        
        if not image_url or not isinstance(image_url, str):
            raise ValueError("유효한 이미지 URL이 필요합니다.")
        
        start_time = time.time()
        
        try:
            logger.info(f"이미지 검수 시작: {image_url}")
            
            # 1. 이미지 URL 검증
            if not self.image_handler.validate_image_url(image_url):
                raise ValueError(f"유효하지 않은 이미지 URL입니다: {image_url}")
            
            # 2. 이미지 페치
            logger.info("이미지 다운로드 중...")
            image_bytes = self.image_handler.fetch_image_from_url(image_url)
            
            # 3. 이미지를 Base64로 인코딩
            logger.info("이미지 Base64 인코딩 중...")
            image_base64 = self.image_handler.convert_image_to_base64(image_bytes)
            
            # 4. 이미지 정보 추출 (미디어 타입 등)
            image_info = self.image_handler.get_image_info(image_bytes)
            media_type = image_info.get('format', 'png').lower()
            media_type = f"image/{media_type}"
            
            # 현재 활성 프롬프트 사용
            current_prompt = self.prompt_manager.get_active_prompt()
            active_version = self.prompt_manager.get_active_version_info()
            
            # 디버깅: 현재 사용 중인 프롬프트 버전 로그
            logger.info(f"🔍 현재 활성 프롬프트 버전: {active_version.version if active_version else 'None'}")
            logger.info(f"🔍 프롬프트 이름: {active_version.name if active_version else 'None'}")
            logger.info(f"🔍 프롬프트 길이: {len(current_prompt) if current_prompt else 0}자")
            
            if not current_prompt:
                raise ValueError("활성 프롬프트가 설정되지 않았습니다")
            
            # 5. Strands Agent를 통해 검수 요청
            logger.info("AI 모델에 검수 요청 중...")
            ai_response = self.strands_agent.send_inspection_request(
                image_base64=image_base64,
                prompt=current_prompt,
                media_type=media_type
            )
            
            # 6. 응답 파싱
            logger.info("AI 응답 파싱 중...")
            processing_time = time.time() - start_time
            
            # 현재 활성 프롬프트 버전 정보 가져오기
            active_version_info = self.prompt_manager.get_active_version_info()
            prompt_version = active_version_info.version if active_version_info else "unknown"
            
            inspection_result = self.result_parser.parse_ai_response(
                response=ai_response,
                image_url=image_url,
                processing_time=processing_time,
                model_id=self.config.bedrock_model_id,
                prompt_version=prompt_version
            )
            
            logger.info(f"이미지 검수 완료: {image_url} - 결과: {inspection_result.result}")
            
            # DynamoDB에 결과 저장 (선택적)
            if save_to_db:
                try:
                    saved_id = self.dynamodb_service.save_inspection_result(inspection_result)
                    if saved_id:
                        logger.info(f"검수 결과 DynamoDB 저장 완료: {saved_id}")
                    else:
                        logger.warning("DynamoDB 저장 실패")
                except Exception as db_error:
                    logger.error(f"DynamoDB 저장 중 오류: {str(db_error)}")
            
            return inspection_result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_message = f"이미지 검수 실패: {str(e)}"
            logger.error(error_message)
            
            # 오류 발생시에도 InspectionResult 객체 반환
            return InspectionResult(
                image_url=image_url,
                result=False,
                reason=f"검수 중 오류 발생: {str(e)}",
                timestamp=datetime.now(),
                processing_time=processing_time,
                raw_response=f"Error: {str(e)}"
            )
    
    def inspect_multiple_images(self, image_urls: list) -> list[InspectionResult]:
        """
        여러 이미지를 일괄 검수합니다.
        
        Args:
            image_urls: 검수할 이미지 URL 리스트
            
        Returns:
            list[InspectionResult]: 검수 결과 리스트
        """
        if not self.is_initialized:
            raise ValueError("검수 서비스가 초기화되지 않았습니다.")
        
        if not image_urls or not isinstance(image_urls, list):
            raise ValueError("유효한 이미지 URL 리스트가 필요합니다.")
        
        results = []
        
        for i, image_url in enumerate(image_urls):
            try:
                logger.info(f"일괄 검수 진행 중: {i+1}/{len(image_urls)} - {image_url}")
                result = self.inspect_image(image_url)
                results.append(result)
                
            except Exception as e:
                logger.error(f"일괄 검수 중 오류 (URL: {image_url}): {str(e)}")
                # 오류 발생시에도 결과 추가
                error_result = InspectionResult(
                    image_url=image_url,
                    result=False,
                    reason=f"일괄 검수 중 오류: {str(e)}",
                    timestamp=datetime.now(),
                    processing_time=0.0,
                    raw_response=f"Error: {str(e)}"
                )
                results.append(error_result)
        
        logger.info(f"일괄 검수 완료: {len(results)}개 이미지 처리")
        return results
    
    def get_inspection_prompt(self) -> str:
        """
        현재 사용 중인 검수 프롬프트를 반환합니다.
        
        Returns:
            str: 검수 프롬프트
        """
        return self.inspection_prompt
    
    def _get_inspection_prompt(self) -> str:
        """
        미리 정의된 검수 프롬프트를 가져옵니다.
        
        Returns:
            str: 검수 프롬프트
        """
        # 설정에서 프롬프트 가져오기 (있는 경우)
        if hasattr(self.config, 'inspection_prompt') and self.config.inspection_prompt:
            return self.config.inspection_prompt
        
        # 기본 프롬프트 (요구사항에 명시된 프롬프트)
        default_prompt = """당신은 상품 이미지 검수 전문가입니다. 상품 외 배경만 검수합니다. 아래 기준에 따라 이미지를 객관적으로 평가하세요:

1. 상품 외 배경에 네모 테두리 강조(굵은 라인, 색상 박스, 불필요한 윤곽선)가 포함되어 있으면 false 처리한다.
   브랜드 로고에 있는 네모 테두리는 true 처리한다.

2. 상품 외 배경에 브랜드명 외의 텍스트가 포함되어 있으면 false 처리한다. '백화점 공식', '공식 판매처' 같은 공식적인 텍스트가 있는 경우는 true로 처리한다.
   - 브랜드 로고, 브랜드명만 있으면 true 처리한다.
   - 상품에 있는 텍스트는 무시한다.
   - 브랜드명은 언어(한글/영문), 대소문자, 철자 변형 등을 포함하여 동일한 의미로 인식한다

3. 위 조건 외에는 true 처리한다.

출력은 반드시 아래 형식을 따른다:
- 결과: true 또는 false
- 사유: 사유를 간단히 설명 (사유에는 true, false 사용 금지)"""
        
        return default_prompt
    
    def validate_service_health(self) -> Dict[str, Any]:
        """
        서비스 상태를 검증합니다.
        
        Returns:
            Dict: 서비스 상태 정보
        """
        health_status = {
            "service_initialized": self.is_initialized,
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        try:
            # StrandsAgent 상태 확인
            if self.strands_agent:
                agent_test = self.strands_agent.test_connection()
                health_status["components"]["strands_agent"] = {
                    "status": "healthy" if agent_test.get("success") else "unhealthy",
                    "details": agent_test
                }
            else:
                health_status["components"]["strands_agent"] = {
                    "status": "not_initialized",
                    "details": "StrandsAgent가 초기화되지 않았습니다"
                }
            
            # ImageHandler 상태 확인
            health_status["components"]["image_handler"] = {
                "status": "healthy",
                "details": "ImageHandler 정상 작동"
            }
            
            # ResultParser 상태 확인
            test_response = "결과: true\n사유: 테스트"
            try:
                self.result_parser.validate_response_format(test_response)
                health_status["components"]["result_parser"] = {
                    "status": "healthy",
                    "details": "ResultParser 정상 작동"
                }
            except Exception as e:
                health_status["components"]["result_parser"] = {
                    "status": "unhealthy",
                    "details": f"ResultParser 오류: {str(e)}"
                }
            
            # 전체 상태 결정
            all_healthy = all(
                comp.get("status") == "healthy" 
                for comp in health_status["components"].values()
            )
            health_status["overall_status"] = "healthy" if all_healthy and self.is_initialized else "unhealthy"
            
        except Exception as e:
            health_status["overall_status"] = "error"
            health_status["error"] = str(e)
        
        return health_status
    
    def get_service_stats(self) -> Dict[str, Any]:
        """
        서비스 통계 정보를 반환합니다.
        
        Returns:
            Dict: 서비스 통계
        """
        return {
            "service_name": "InspectionService",
            "version": "1.0.0",
            "initialized": self.is_initialized,
            "prompt_length": len(self.inspection_prompt),
            "supported_formats": ["jpg", "jpeg", "png", "gif", "bmp", "webp"],
            "max_image_size": "10MB",  # ImageHandler에서 설정된 값
            "timestamp": datetime.now().isoformat()
        }
    
    def __del__(self):
        """리소스 정리"""
        if hasattr(self, 'strands_agent') and self.strands_agent:
            # StrandsAgent 리소스 정리는 해당 클래스에서 처리
            pass