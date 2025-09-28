"""
AWS Strands Agent 통합 모듈
AWS Bedrock Claude 3.5 Haiku 모델과의 통신을 담당합니다.
"""

import json
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError

try:
    from strands import Agent
    from strands.models import BedrockModel
    from strands_tools import image_reader
    STRANDS_AVAILABLE = True
except ImportError:
    # Fallback to direct boto3 implementation if strands is not available
    Agent = None
    BedrockModel = None
    image_reader = None
    STRANDS_AVAILABLE = False

logger = logging.getLogger(__name__)


class StrandsAgent:
    """AWS Strands Agent를 사용한 Bedrock 통합 클래스"""
    
    def __init__(self, aws_region: str, model_id: str, aws_access_key_id: Optional[str] = None, 
                 aws_secret_access_key: Optional[str] = None, temperature: float = 0.0):
        """
        StrandsAgent 초기화
        
        Args:
            aws_region: AWS 리전
            model_id: Bedrock 모델 ID (예: anthropic.claude-3-5-haiku-20241022-v1:0)
            aws_access_key_id: AWS Access Key ID (선택적)
            aws_secret_access_key: AWS Secret Access Key (선택적)
            temperature: 모델 온도 설정 (기본값: 0.0 - 일관된 검수 결과)
        """
        self.aws_region = aws_region
        self.model_id = model_id
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.temperature = temperature
        self.agent = None
        self.bedrock_model = None
        self.bedrock_client = None  # Fallback용
        self.is_initialized = False
    
    def initialize_agent(self) -> None:
        """
        Strands Agent 초기화 및 Bedrock 모델 설정
        
        Raises:
            ValueError: 설정이 올바르지 않은 경우
            NoCredentialsError: AWS 자격 증명이 없는 경우
            ClientError: AWS 서비스 오류
        """
        try:
            if not STRANDS_AVAILABLE or Agent is None or BedrockModel is None or image_reader is None:
                raise ImportError("Strands SDK 또는 strands_tools를 찾을 수 없습니다.")
            
            # AWS 자격 증명 설정 (환경 변수 또는 명시적 설정)
            if self.aws_access_key_id and self.aws_secret_access_key:
                import os
                os.environ['AWS_ACCESS_KEY_ID'] = self.aws_access_key_id
                os.environ['AWS_SECRET_ACCESS_KEY'] = self.aws_secret_access_key
                os.environ['AWS_DEFAULT_REGION'] = self.aws_region
            
            # Bedrock Runtime 클라이언트 초기화 (dual image request용)
            import boto3
            self.bedrock_runtime = boto3.client(
                'bedrock-runtime',
                region_name=self.aws_region,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key
            )
            
            # BedrockModel 생성
            self.bedrock_model = BedrockModel(
                model_id=self.model_id,
                temperature=self.temperature
            )
            
            # 검수 전용 시스템 프롬프트
            inspection_system_prompt = """당신은 상품 이미지 검수 전문가입니다. 
image_reader 도구를 사용하여 이미지를 분석하고, 제공된 검수 기준에 따라 정확한 판정을 내리세요.
반드시 지정된 출력 형식을 준수해야 합니다."""
            
            # Strands Agent 생성 (image_reader 도구 포함)
            self.agent = Agent(
                system_prompt=inspection_system_prompt,
                tools=[image_reader],
                model=self.bedrock_model
            )
            
            # Fallback용 Bedrock 클라이언트도 생성
            session_kwargs = {'region_name': self.aws_region}
            if self.aws_access_key_id and self.aws_secret_access_key:
                session_kwargs.update({
                    'aws_access_key_id': self.aws_access_key_id,
                    'aws_secret_access_key': self.aws_secret_access_key
                })
            
            session = boto3.Session(**session_kwargs)
            self.bedrock_client = session.client('bedrock-runtime')
            
            # 자격 증명 검증
            if not self.validate_credentials():
                raise ValueError("AWS 자격 증명 검증에 실패했습니다")
            
            self.is_initialized = True
            logger.info(f"Strands Agent 초기화 완료 - 리전: {self.aws_region}, 모델: {self.model_id}")
            
        except ImportError as e:
            raise ValueError(f"Strands SDK 가져오기 실패: {str(e)}")
        except NoCredentialsError as e:
            raise ValueError("AWS 자격 증명을 찾을 수 없습니다. 환경 변수나 AWS 프로필을 확인하세요.")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            raise ClientError(
                error_response={'Error': {'Code': error_code, 'Message': f"AWS 서비스 오류: {error_message}"}},
                operation_name='initialize_agent'
            )
        except Exception as e:
            raise ValueError(f"Strands Agent 초기화 실패: {str(e)}")
    
    def validate_credentials(self) -> bool:
        """
        AWS 자격 증명 유효성 검증
        
        Returns:
            bool: 자격 증명이 유효하면 True
        """
        try:
            if not self.bedrock_client:
                return False
            
            # Bedrock Runtime 클라이언트는 list_foundation_models가 없으므로
            # 대신 STS를 사용하여 자격 증명 검증
            import boto3
            sts_client = boto3.client('sts', region_name=self.aws_region)
            
            # 현재 자격 증명으로 caller identity 확인
            response = sts_client.get_caller_identity()
            return 'Account' in response
            
        except Exception as e:
            logger.error(f"자격 증명 검증 실패: {str(e)}")
            return False
    
    def send_inspection_request(self, image_base64: str, prompt: str, media_type: str = "image/png") -> Dict[str, Any]:
        """
        Strands Agent를 사용하여 이미지 검수 요청을 보냅니다.
        
        Args:
            image_base64: Base64 인코딩된 이미지 데이터
            prompt: 검수 프롬프트
            media_type: 이미지 미디어 타입 (기본값: image/png)
            
        Returns:
            Dict: AI 모델의 응답
            
        Raises:
            ValueError: 초기화되지 않았거나 입력이 유효하지 않은 경우
            ClientError: AWS Bedrock 서비스 오류
        """
        if not self.is_initialized:
            raise ValueError("Strands Agent가 초기화되지 않았습니다. initialize_agent()를 먼저 호출하세요.")
        
        if not image_base64 or not prompt:
            raise ValueError("이미지 데이터와 프롬프트가 모두 필요합니다.")
        
        try:
            # Strands Agent를 사용한 멀티모달 요청
            if STRANDS_AVAILABLE and self.agent and image_reader:
                # 임시 이미지 파일 생성
                import tempfile
                import base64
                
                # Base64를 바이트로 디코딩
                image_bytes = base64.b64decode(image_base64)
                
                # 임시 파일에 이미지 저장
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                    temp_file.write(image_bytes)
                    temp_image_path = temp_file.name
                
                try:
                    # Strands Agent로 이미지 분석 요청
                    message = f"이미지 파일: {temp_image_path}\n\n{prompt}"
                    response = self.agent(message)
                    
                    # 응답을 표준 형식으로 변환
                    result = {
                        "content": [
                            {
                                "type": "text",
                                "text": response if isinstance(response, str) else str(response)
                            }
                        ],
                        "usage": {
                            "input_tokens": 0,
                            "output_tokens": 0
                        }
                    }
                    
                    logger.info(f"Strands Agent 이미지 분석 완료")
                    return result
                    
                finally:
                    # 임시 파일 정리
                    import os
                    try:
                        os.unlink(temp_image_path)
                    except:
                        pass
            else:
                # Strands Agent 사용 불가시 fallback
                logger.info("Strands Agent 사용 불가, Bedrock 직접 호출로 fallback")
                return self._fallback_bedrock_request(image_base64, prompt, media_type)
            
        except Exception as e:
            logger.warning(f"Strands Agent 호출 실패, Bedrock 직접 호출로 fallback: {str(e)}")
            return self._fallback_bedrock_request(image_base64, prompt, media_type)
    
    def _fallback_bedrock_request(self, image_base64: str, prompt: str, media_type: str) -> Dict[str, Any]:
        """
        Strands Agent 실패 시 직접 Bedrock API를 호출하는 fallback 메서드
        """
        try:
            # Claude 3.5 Haiku용 메시지 구성
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
            
            # Bedrock 요청 본문 구성
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "temperature": self.temperature,
                "messages": messages
            }
            
            # Bedrock API 호출
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            # 응답 파싱
            response_body = json.loads(response['body'].read())
            
            logger.info(f"Bedrock 직접 호출 응답 수신 완료 - 토큰 사용량: {response_body.get('usage', {})}")
            
            return response_body
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'ValidationException':
                raise ValueError(f"요청 데이터가 유효하지 않습니다: {error_message}")
            elif error_code == 'AccessDeniedException':
                raise ClientError(
                    error_response={'Error': {'Code': error_code, 'Message': "Bedrock 모델에 대한 접근 권한이 없습니다"}},
                    operation_name='invoke_model'
                )
            elif error_code == 'ThrottlingException':
                raise ClientError(
                    error_response={'Error': {'Code': error_code, 'Message': "요청이 너무 많습니다. 잠시 후 다시 시도하세요"}},
                    operation_name='invoke_model'
                )
            else:
                raise ClientError(
                    error_response={'Error': {'Code': error_code, 'Message': f"Bedrock 서비스 오류: {error_message}"}},
                    operation_name='invoke_model'
                )
        except json.JSONDecodeError as e:
            raise ValueError(f"응답 파싱 오류: {str(e)}")
        except Exception as e:
            raise ValueError(f"이미지 검수 요청 실패: {str(e)}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        현재 사용 중인 모델 정보를 반환합니다.
        
        Returns:
            Dict: 모델 정보
        """
        if not self.is_initialized:
            return {"error": "Agent가 초기화되지 않았습니다"}
        
        # Bedrock Runtime 클라이언트는 모델 정보 조회 기능이 없으므로
        # 설정된 모델 정보를 반환
        return {
            "model_id": self.model_id,
            "region": self.aws_region,
            "provider": "Anthropic",
            "model_name": "Claude 3.7 Sonnet",
            "status": "initialized"
        }
    
    def send_dual_image_request(self, image1_base64: str, image2_base64: str, prompt: str, media_type: str = "image/png") -> str:
        """
        2개 이미지를 포함한 검수 요청을 Bedrock에 전송합니다.
        
        Args:
            image1_base64: 첫 번째 이미지의 Base64 인코딩 문자열
            image2_base64: 두 번째 이미지의 Base64 인코딩 문자열
            prompt: 검수 프롬프트
            media_type: 이미지 미디어 타입 (기본값: "image/png")
            
        Returns:
            str: AI 모델의 응답
            
        Raises:
            RuntimeError: Agent가 초기화되지 않은 경우
            Exception: Bedrock 호출 실패
        """
        if not self.agent:
            raise RuntimeError("Agent가 초기화되지 않았습니다. initialize_agent()를 먼저 호출하세요.")
        
        try:
            # Claude 모델인지 확인
            if "claude" in self.model_id.lower():
                return self._send_dual_image_claude_request(image1_base64, image2_base64, prompt, media_type)
            else:
                return self._send_dual_image_nova_request(image1_base64, image2_base64, prompt, media_type)
                
        except Exception as e:
            logger.error(f"Dual image request 실패: {str(e)}")
            raise e
    
    def _send_dual_image_claude_request(self, image1_base64: str, image2_base64: str, prompt: str, media_type: str) -> str:
        """Claude 모델용 2개 이미지 요청"""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "첫 번째 이미지 (원본):"},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image1_base64
                        }
                    },
                    {"type": "text", "text": "두 번째 이미지 (중앙 50% 크롭):"},
                    {
                        "type": "image", 
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image2_base64
                        }
                    },
                    {"type": "text", "text": prompt}
                ]
            }
        ]
        
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "temperature": self.temperature,
            "messages": messages
        }
        
        response = self.bedrock_runtime.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body)
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
    
    def _send_dual_image_nova_request(self, image1_base64: str, image2_base64: str, prompt: str, media_type: str) -> str:
        """Nova 모델용 2개 이미지 요청"""
        messages = [
            {
                "role": "user",
                "content": [
                    {"text": "첫 번째 이미지 (원본):"},
                    {
                        "image": {
                            "format": media_type.split("/")[1],
                            "source": {"bytes": image1_base64}
                        }
                    },
                    {"text": "두 번째 이미지 (중앙 50% 크롭):"},
                    {
                        "image": {
                            "format": media_type.split("/")[1], 
                            "source": {"bytes": image2_base64}
                        }
                    },
                    {"text": prompt}
                ]
            }
        ]
        
        body = {
            "schemaVersion": "messages-v1",
            "messages": messages,
            "inferenceConfig": {
                "max_new_tokens": 1000,
                "temperature": self.temperature
            }
        }
        
        response = self.bedrock_runtime.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body)
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['output']['message']['content'][0]['text']
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Bedrock 연결 테스트를 수행합니다.
        
        Returns:
            Dict: 테스트 결과
        """
        if not self.is_initialized:
            return {"success": False, "error": "Agent가 초기화되지 않았습니다"}
        
        try:
            # 간단한 텍스트 요청으로 연결 테스트
            test_messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "안녕하세요. 연결 테스트입니다. '테스트 성공'이라고 답해주세요."
                        }
                    ]
                }
            ]
            
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 50,
                "temperature": 0.0,
                "messages": test_messages
            }
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType='application/json',
                accept='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            
            return {
                "success": True,
                "model_id": self.model_id,
                "region": self.aws_region,
                "response": response_body.get('content', [{}])[0].get('text', ''),
                "usage": response_body.get('usage', {})
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"연결 테스트 실패: {str(e)}"
            }
    
    def __del__(self):
        """리소스 정리"""
        if hasattr(self, 'bedrock_client') and self.bedrock_client:
            # Boto3 클라이언트는 자동으로 정리되므로 특별한 작업 불필요
            pass