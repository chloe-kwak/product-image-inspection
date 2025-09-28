"""
AWS Strands Agent 간단한 통합 모듈
예시 패턴을 따라 구현한 버전
"""

import logging
import base64
from typing import Dict, Any, Optional

try:
    from strands import Agent
    STRANDS_AGENT_AVAILABLE = True
except ImportError:
    STRANDS_AGENT_AVAILABLE = False
    Agent = None

logger = logging.getLogger(__name__)


class SimpleStrandsAgent:
    """간단한 Strands Agent 래퍼 클래스"""
    
    def __init__(self, model_id: str, system_prompt: str = ""):
        """
        SimpleStrandsAgent 초기화
        
        Args:
            model_id: Bedrock 모델 ID (예: us.anthropic.claude-3-7-sonnet-20250219-v1:0)
            system_prompt: 시스템 프롬프트
        """
        self.model_id = model_id
        self.system_prompt = system_prompt
        self.agent = None
        self.is_initialized = False
    
    def initialize_agent(self) -> None:
        """
        Strands Agent 초기화
        
        Raises:
            ValueError: Strands SDK를 찾을 수 없는 경우
        """
        if not STRANDS_AGENT_AVAILABLE or Agent is None:
            raise ValueError("Strands SDK를 찾을 수 없습니다. 'pip install strands-agents' 명령으로 설치하세요.")
        
        try:
            # 예시 패턴을 따라 Agent 생성
            self.agent = Agent(
                model=self.model_id,
                system_prompt=self.system_prompt
            )
            
            self.is_initialized = True
            logger.info(f"Simple Strands Agent 초기화 완료 - 모델: {self.model_id}")
            
        except Exception as e:
            raise ValueError(f"Strands Agent 초기화 실패: {str(e)}")
    
    def send_inspection_request(self, image_base64: str, prompt: str) -> str:
        """
        이미지 검수 요청을 보냅니다.
        
        Args:
            image_base64: Base64 인코딩된 이미지 데이터
            prompt: 검수 프롬프트
            
        Returns:
            str: AI 모델의 응답 텍스트
            
        Raises:
            ValueError: 초기화되지 않았거나 입력이 유효하지 않은 경우
        """
        if not self.is_initialized:
            raise ValueError("Strands Agent가 초기화되지 않았습니다. initialize_agent()를 먼저 호출하세요.")
        
        if not image_base64 or not prompt:
            raise ValueError("이미지 데이터와 프롬프트가 모두 필요합니다.")
        
        try:
            # 이미지와 프롬프트를 함께 전송
            # Strands Agent의 멀티모달 지원 방식에 따라 조정 필요
            message = f"{prompt}\n\n[Base64 이미지: {image_base64[:50]}...]"
            
            # 예시 패턴을 따라 호출
            response = self.agent(message)
            
            logger.info(f"Simple Strands Agent 응답 수신 완료")
            
            return response
            
        except Exception as e:
            raise ValueError(f"이미지 검수 요청 실패: {str(e)}")
    
    def test_connection(self) -> Dict[str, Any]:
        """
        연결 테스트를 수행합니다.
        
        Returns:
            Dict: 테스트 결과
        """
        if not self.is_initialized:
            return {"success": False, "error": "Agent가 초기화되지 않았습니다"}
        
        try:
            # 간단한 테스트 메시지
            response = self.agent("안녕하세요. 연결 테스트입니다. '테스트 성공'이라고 답해주세요.")
            
            return {
                "success": True,
                "model_id": self.model_id,
                "response": response
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"연결 테스트 실패: {str(e)}"
            }