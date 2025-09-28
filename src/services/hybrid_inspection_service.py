"""
Hybrid Inspection Service: Nova Pro + Claude fallback for border detection
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import os

# 필요한 모듈들 import
import sys
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


class HybridInspectionService:
    """Nova Pro + Claude 하이브리드 검수 서비스"""
    
    def __init__(self, config: AppConfig):
        """
        HybridInspectionService 초기화
        
        Args:
            config: 애플리케이션 설정
        """
        self.config = config
        
        # Nova Pro Agent (1차 검수용)
        self.nova_agent = None
        self.nova_model_id = "us.amazon.nova-pro-v1:0"
        
        # Claude Agent (재검수용)
        self.claude_agent = None
        self.claude_model_id = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
        
        # 공통 컴포넌트
        self.image_handler = ImageHandler()
        self.result_parser = ResultParser()
        self.prompt_manager = PromptVersionManager()
        self.dynamodb_service = DynamoDBService(config.aws_region)
        self.is_initialized = False
        
        # 프롬프트 설정
        self._setup_prompts()
    
    def _setup_prompts(self):
        """프롬프트 설정"""
        # 환경 변수에서 프롬프트 버전 확인
        env_prompt_version = os.getenv('PROMPT_VERSION')
        
        if env_prompt_version:
            # 환경 변수가 있으면 Nova Pro도 같은 버전 사용
            self.nova_prompt_version = env_prompt_version
        else:
            # 환경 변수가 없으면 기본값 사용
            self.nova_prompt_version = "v1.3"
        
        # Claude용 엄격한 테두리 탐지 프롬프트 (v1.1)
        self.claude_prompt_version = "v1.1"
    
    async def initialize(self) -> bool:
        """서비스 초기화"""
        try:
            # Nova Pro Agent 초기화
            self.nova_agent = StrandsAgent(
                aws_region=self.config.aws_region,
                model_id=self.nova_model_id,
                aws_access_key_id=self.config.aws_access_key_id,
                aws_secret_access_key=self.config.aws_secret_access_key
            )
            self.nova_agent.initialize_agent()
            
            # Claude Agent 초기화
            self.claude_agent = StrandsAgent(
                aws_region=self.config.aws_region,
                model_id=self.claude_model_id,
                aws_access_key_id=self.config.aws_access_key_id,
                aws_secret_access_key=self.config.aws_secret_access_key
            )
            self.claude_agent.initialize_agent()
            
            # DynamoDB 서비스 초기화
            self.dynamodb_service.initialize()
            
            self.is_initialized = True
            logger.info("하이브리드 검수 서비스 초기화 완료")
            return True
            
        except Exception as e:
            logger.error(f"하이브리드 검수 서비스 초기화 실패: {str(e)}")
            return False
    
    def inspect_image(self, image_url: str) -> InspectionResult:
        """
        하이브리드 이미지 검수
        
        Args:
            image_url: 검수할 이미지 URL
            
        Returns:
            InspectionResult: 검수 결과
        """
        if not self.is_initialized:
            raise RuntimeError("서비스가 초기화되지 않았습니다")
        
        start_time = time.time()
        
        try:
            # 1단계: Nova Pro로 1차 검수
            logger.info(f"1차 검수 시작 (Nova Pro): {image_url}")
            nova_result = self._inspect_with_nova(image_url)
            
            # 2단계: 재검수 필요성 판단
            needs_recheck = self._needs_claude_recheck(nova_result)
            
            if needs_recheck:
                # 3단계: Claude로 재검수
                logger.info(f"재검수 시작 (Claude): {image_url}")
                claude_result = self._inspect_with_claude(image_url)
                
                # 4단계: 최종 결과 결정
                final_result = self._merge_results(nova_result, claude_result)
                final_result.reason += f" [하이브리드: Nova→Claude 재검수]"
                
            else:
                # Nova Pro 결과 그대로 사용
                final_result = nova_result
                final_result.reason += f" [하이브리드: Nova Pro 단독]"
            
            # 처리 시간 업데이트
            final_result.processing_time = time.time() - start_time
            
            logger.info(f"하이브리드 검수 완료: {image_url} -> {final_result.result}")
            return final_result
            
        except Exception as e:
            logger.error(f"하이브리드 검수 실패: {str(e)}")
            # 오류 시 기본 결과 반환
            return InspectionResult(
                image_url=image_url,
                result=False,
                reason=f"검수 오류: {str(e)}",
                timestamp=datetime.now(),
                processing_time=time.time() - start_time,
                raw_response="",
                model_id="hybrid-error",
                prompt_version="error"
            )
    
    def _inspect_with_nova(self, image_url: str) -> InspectionResult:
        """Nova Pro로 검수"""
        # 이미지 다운로드 및 처리
        image_data = self.image_handler.fetch_and_process_image(image_url)
        image_base64 = image_data['base64']
        media_type = image_data['info']['format'].lower()
        
        # Nova Pro 프롬프트 가져오기
        self.prompt_manager.set_active_version(self.nova_prompt_version)
        nova_prompt = self.prompt_manager.get_active_prompt()
        
        # Nova Pro로 검수
        ai_response = self.nova_agent.send_inspection_request(
            image_base64=image_base64,
            prompt=nova_prompt,
            media_type=f"image/{media_type}"
        )
        
        # 결과 파싱
        result = self.result_parser.parse_ai_response(
            response=ai_response,
            image_url=image_url,
            processing_time=0,  # 임시값
            model_id=self.nova_model_id,
            prompt_version=self.nova_prompt_version
        )
        
        return result
    
    def _inspect_with_claude(self, image_url: str) -> InspectionResult:
        """Claude로 검수"""
        # 이미지 다운로드 및 처리
        image_data = self.image_handler.fetch_and_process_image(image_url)
        image_base64 = image_data['base64']
        media_type = image_data['info']['format'].lower()
        
        # Claude 프롬프트 가져오기
        self.prompt_manager.set_active_version(self.claude_prompt_version)
        claude_prompt = self.prompt_manager.get_active_prompt()
        
        # Claude로 검수
        ai_response = self.claude_agent.send_inspection_request(
            image_base64=image_base64,
            prompt=claude_prompt,
            media_type=f"image/{media_type}"
        )
        
        # 결과 파싱
        result = self.result_parser.parse_ai_response(
            response=ai_response,
            image_url=image_url,
            processing_time=0,  # 임시값
            model_id=self.claude_model_id,
            prompt_version=self.claude_prompt_version
        )
        
        return result
    
    def _needs_claude_recheck(self, nova_result: InspectionResult) -> bool:
        """
        Claude 재검수 필요성 판단 (보수적 접근)
        Nova Pro를 신뢰할 수 있는 명확한 경우만 제외하고 모두 Claude로 재검수
        
        Args:
            nova_result: Nova Pro 검수 결과
            
        Returns:
            bool: 재검수 필요 여부
        """
        reason_lower = nova_result.reason.lower()
        
        # Nova Pro를 신뢰할 수 있는 명확한 경우들 (재검수 불필요)
        trust_nova_conditions = [
            # 1. Nova Pro가 명확하게 테두리를 발견하고 false로 판정한 경우
            nova_result.result == False and any(keyword in reason_lower for keyword in [
                # 한글 테두리 키워드
                "테두리", "윤곽선", "경계선", "네모", "라인",
                # 영어 테두리 키워드  
                "border", "frame", "outline", "boundary", "edge", "line"
            ]),
            
            # 2. Nova Pro가 매우 확실한 표현으로 true 판정한 경우 (매우 제한적)
            nova_result.result == True and any(phrase in reason_lower for phrase in [
                # 매우 확실한 표현만
                "테두리가 전혀 없", "border가 전혀 없", "완전히 깨끗한", "전혀 문제없"
            ])
        ]
        
        # Nova Pro를 신뢰할 수 있으면 재검수 불필요
        trust_nova = any(trust_nova_conditions)
        
        if trust_nova:
            logger.info(f"Nova Pro 결과 신뢰: {nova_result.result} - {nova_result.reason[:50]}...")
            return False
        else:
            # 나머지 모든 경우는 Claude 재검수
            logger.info(f"Claude 재검수 필요 (보수적 접근): {nova_result.reason[:50]}...")
            return True
    
    def _merge_results(self, nova_result: InspectionResult, claude_result: InspectionResult) -> InspectionResult:
        """
        Nova Pro와 Claude 결과 병합
        
        Args:
            nova_result: Nova Pro 결과
            claude_result: Claude 결과
            
        Returns:
            InspectionResult: 최종 결과
        """
        # Claude 결과를 우선시 (더 정확한 테두리 탐지)
        final_result = claude_result
        
        # 메타데이터 업데이트
        final_result.model_id = f"hybrid({self.nova_model_id}→{self.claude_model_id})"
        final_result.prompt_version = f"hybrid({self.nova_prompt_version}→{self.claude_prompt_version})"
        
        # 상세 사유 추가
        if nova_result.result != claude_result.result:
            final_result.reason += f" [Nova Pro: {nova_result.result}, Claude: {claude_result.result} - Claude 우선 적용]"
        
        return final_result
