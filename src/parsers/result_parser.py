"""
AI 응답 결과 파서 모듈
AI 모델의 응답을 파싱하여 구조화된 데이터로 변환합니다.
"""

import re
import logging
from typing import Tuple, Dict, Any, Optional
from datetime import datetime

# 데이터 모델 import
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from models.inspection_result import InspectionResult

logger = logging.getLogger(__name__)


class ResultParser:
    """AI 응답 파싱 클래스"""
    
    def __init__(self):
        """ResultParser 초기화"""
        # 결과 파싱을 위한 정규식 패턴
        self.result_pattern = re.compile(r'결과\s*:\s*(true|false)', re.IGNORECASE)
        self.reason_pattern = re.compile(r'사유\s*:\s*(.+?)(?=\n|$)', re.IGNORECASE | re.DOTALL)
        
        # 영어 패턴도 지원
        self.result_pattern_en = re.compile(r'result\s*:\s*(true|false)', re.IGNORECASE)
        self.reason_pattern_en = re.compile(r'reason\s*:\s*(.+?)(?=\n|$)', re.IGNORECASE | re.DOTALL)
    
    def parse_ai_response(self, response: Dict[str, Any], image_url: str = "", 
                         processing_time: float = 0.0, model_id: str = "", 
                         prompt_version: str = "") -> InspectionResult:
        """
        AI 모델의 응답을 파싱하여 InspectionResult 객체로 변환합니다.
        
        Args:
            response: AI 모델의 원본 응답
            image_url: 검수한 이미지 URL
            processing_time: 처리 시간 (초)
            
        Returns:
            InspectionResult: 파싱된 검수 결과
            
        Raises:
            ValueError: 응답 파싱에 실패한 경우
        """
        try:
            # 응답에서 텍스트 추출
            response_text = self._extract_text_from_response(response)
            
            if not response_text:
                raise ValueError("응답에서 텍스트를 찾을 수 없습니다")
            
            # 결과와 사유 파싱
            result, reason = self.extract_result_and_reason(response_text)
            
            # InspectionResult 객체 생성
            inspection_result = InspectionResult(
                image_url=image_url,
                result=result,
                reason=reason,
                timestamp=datetime.now(),
                processing_time=processing_time,
                raw_response=response_text,
                model_id=model_id,
                prompt_version=prompt_version
            )
            
            logger.info(f"응답 파싱 완료 - 결과: {result}, 사유: {reason[:50]}...")
            
            return inspection_result
            
        except Exception as e:
            logger.error(f"응답 파싱 실패: {str(e)}")
            raise ValueError(f"응답 파싱 실패: {str(e)}")
    
    def extract_result_and_reason(self, text: str) -> Tuple[bool, str]:
        """
        텍스트에서 결과(true/false)와 사유를 추출합니다.
        
        Args:
            text: 파싱할 텍스트
            
        Returns:
            Tuple[bool, str]: (결과, 사유)
            
        Raises:
            ValueError: 파싱에 실패한 경우
        """
        if not text or not isinstance(text, str):
            raise ValueError("유효하지 않은 텍스트입니다")
        
        # 텍스트 정리 및 Claude 내부 메시지 제거
        cleaned_text = text.strip()
        
        # Claude 내부 메시지 패턴 제거
        internal_messages = [
            r"이미지를 분석하기 위해.*?불러오겠습니다\.?",
            r"먼저 이미지를.*?불러오겠습니다\.?",
            r"이미지 파일을.*?읽겠습니다\.?",
            r"Tool #\d+:.*?\n",
            r"<thinking>.*?</thinking>",
        ]
        
        for pattern in internal_messages:
            cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.IGNORECASE | re.DOTALL)
        
        # 연속된 공백과 줄바꿈 정리
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        # 결과 추출 (한국어 우선, 영어 fallback)
        result_match = self.result_pattern.search(cleaned_text)
        if not result_match:
            result_match = self.result_pattern_en.search(cleaned_text)
        
        if not result_match:
            # 패턴이 없는 경우 대안적 방법 시도
            result = self._extract_result_alternative(cleaned_text)
            if result is None:
                # 스마트 파싱: AI 응답 내용을 분석해서 결과 추정
                result = self._smart_result_inference(cleaned_text)
        else:
            result_str = result_match.group(1).lower()
            result = result_str == 'true'
        
        # 사유 추출 (한국어 우선, 영어 fallback)
        reason_match = self.reason_pattern.search(cleaned_text)
        if not reason_match:
            reason_match = self.reason_pattern_en.search(cleaned_text)
        
        if not reason_match:
            # 패턴이 없는 경우 대안적 방법 시도
            reason = self._extract_reason_alternative(cleaned_text)
            if not reason:
                # 마지막 수단: 전체 텍스트를 사유로 사용
                reason = cleaned_text[:200] if cleaned_text else "AI 응답을 파싱할 수 없습니다"
        else:
            reason = reason_match.group(1).strip()
        
        # 사유에서 불필요한 문자 제거
        reason = self._clean_reason_text(reason)
        
        return result, reason
    
    def validate_response_format(self, text: str) -> bool:
        """
        응답 형식이 올바른지 검증합니다.
        
        Args:
            text: 검증할 텍스트
            
        Returns:
            bool: 형식이 올바르면 True
        """
        if not text or not isinstance(text, str):
            return False
        
        try:
            # 결과와 사유 추출 시도
            self.extract_result_and_reason(text)
            return True
        except ValueError:
            return False
    
    def _extract_text_from_response(self, response: Dict[str, Any]) -> str:
        """
        다양한 응답 형식에서 텍스트를 추출합니다.
        
        Args:
            response: AI 모델의 응답
            
        Returns:
            str: 추출된 텍스트
        """
        # 문자열인 경우
        if isinstance(response, str):
            return response
        
        # Strands Agent 응답 형식
        if isinstance(response, dict):
            # content 배열 형식 (Anthropic Claude 응답)
            if 'content' in response and isinstance(response['content'], list):
                for content_item in response['content']:
                    if isinstance(content_item, dict) and content_item.get('type') == 'text':
                        return content_item.get('text', '')
            
            # 직접 text 필드
            if 'text' in response:
                return response['text']
            
            # message 필드
            if 'message' in response:
                return response['message']
            
            # 전체 응답을 문자열로 변환
            return str(response)
        
        # 기타 타입은 문자열로 변환
        return str(response)
    
    def _extract_result_alternative(self, text: str) -> Optional[bool]:
        """
        대안적 방법으로 결과를 추출합니다.
        
        Args:
            text: 파싱할 텍스트
            
        Returns:
            Optional[bool]: 추출된 결과, 실패시 None
        """
        text_lower = text.lower()
        
        # true/false 단어 직접 검색 (명확한 경우만)
        if 'true' in text_lower and 'false' not in text_lower:
            return True
        elif 'false' in text_lower and 'true' not in text_lower:
            return False
        
        # 명확하지 않은 경우 None 반환하여 스마트 추론으로 넘김
        return None
    
    def _extract_reason_alternative(self, text: str) -> str:
        """
        대안적 방법으로 사유를 추출합니다.
        
        Args:
            text: 파싱할 텍스트
            
        Returns:
            str: 추출된 사유
        """
        # 줄 단위로 분리하여 사유로 보이는 부분 찾기
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('결과:') and not line.startswith('result:'):
                # 사유로 보이는 줄 반환
                if len(line) > 5:  # 최소 길이를 다시 줄임
                    return line
        
        # 전체 텍스트에서 결과 부분 제거 후 나머지 반환
        result_removed = re.sub(r'결과\s*:\s*(true|false)', '', text, flags=re.IGNORECASE)
        result_removed = re.sub(r'result\s*:\s*(true|false)', '', result_removed, flags=re.IGNORECASE)
        
        cleaned = result_removed.strip()
        if cleaned and len(cleaned) > 5:  # 최소 길이 체크 완화
            return cleaned[:200]  # 최대 200자로 제한
        
        # 마지막 수단: 전체 텍스트 반환
        return text[:200] if text else "AI 응답을 파싱할 수 없습니다"
    
    def _smart_result_inference(self, text: str) -> bool:
        """
        AI 응답 내용을 분석해서 결과를 추정합니다.
        
        Args:
            text: 분석할 텍스트
            
        Returns:
            bool: 추정된 결과
        """
        text_lower = text.lower()
        
        # 강한 부정 신호들 (정확한 매칭)
        strong_negative_patterns = [
            '부적합', '실패했', '위반', '테두리가 있', '문제가 있',
            'failed', 'violation', 'inappropriate', 'has border'
        ]
        
        # 강한 긍정 신호들
        strong_positive_patterns = [
            '통과', '문제없', '문제가 없', '기준 충족', '깔끔',
            'clean', 'meets', 'criteria', 'appropriate', 'no border'
        ]
        
        # 강한 부정 신호 체크 (정확한 매칭)
        for neg in strong_negative_patterns:
            if neg in text_lower:
                return False
        
        # 강한 긍정 신호 체크
        for pos in strong_positive_patterns:
            if pos in text_lower:
                return True
        
        # 둘 다 없으면 보수적으로 False
        return False
    
    def _clean_reason_text(self, reason: str) -> str:
        """
        사유 텍스트를 정리합니다.
        
        Args:
            reason: 원본 사유 텍스트
            
        Returns:
            str: 정리된 사유 텍스트
        """
        if not reason:
            return "사유가 제공되지 않았습니다"
        
        # 앞뒤 공백 제거
        cleaned = reason.strip()
        
        # 불필요한 문자 제거
        cleaned = re.sub(r'^[-\s]*', '', cleaned)  # 앞의 대시나 공백
        cleaned = re.sub(r'[.\s]*$', '', cleaned)  # 뒤의 점이나 공백
        
        # 요구사항에 따라 true/false 단어 제거
        cleaned = re.sub(r'\b(true|false)\b', '', cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.strip()
        
        # 빈 문자열인 경우 기본값 반환
        if not cleaned:
            return "사유가 명확하지 않습니다"
        
        # 최대 길이 제한
        if len(cleaned) > 500:
            cleaned = cleaned[:500] + "..."
        
        return cleaned
    
    def parse_batch_responses(self, responses: list, image_urls: list = None, 
                            processing_times: list = None) -> list[InspectionResult]:
        """
        여러 응답을 일괄 파싱합니다.
        
        Args:
            responses: AI 응답 리스트
            image_urls: 이미지 URL 리스트 (선택적)
            processing_times: 처리 시간 리스트 (선택적)
            
        Returns:
            list[InspectionResult]: 파싱된 결과 리스트
        """
        results = []
        
        for i, response in enumerate(responses):
            try:
                image_url = image_urls[i] if image_urls and i < len(image_urls) else ""
                processing_time = processing_times[i] if processing_times and i < len(processing_times) else 0.0
                
                result = self.parse_ai_response(response, image_url, processing_time)
                results.append(result)
                
            except Exception as e:
                logger.error(f"배치 파싱 중 오류 (인덱스 {i}): {str(e)}")
                # 오류 발생시 기본값으로 결과 생성
                error_result = InspectionResult(
                    image_url=image_urls[i] if image_urls and i < len(image_urls) else "",
                    result=False,
                    reason=f"파싱 오류: {str(e)}",
                    timestamp=datetime.now(),
                    processing_time=0.0,
                    raw_response=str(response)
                )
                results.append(error_result)
        
        return results