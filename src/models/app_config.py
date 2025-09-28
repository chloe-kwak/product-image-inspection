"""
Application configuration data model for product image inspection service.
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class AppConfig:
    """
    Application configuration settings loaded from environment variables.
    
    Attributes:
        aws_region: AWS region for Bedrock service
        aws_access_key_id: AWS access key ID
        aws_secret_access_key: AWS secret access key
        bedrock_model_id: Bedrock model identifier
        inspection_prompt: Prompt template for image inspection
    """
    aws_region: str
    aws_access_key_id: str
    aws_secret_access_key: str
    bedrock_model_id: str
    inspection_prompt: str = ""  # 선택적 필드로 변경
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration values."""
        if not self.aws_region or not self.aws_region.strip():
            raise ValueError("aws_region must be a non-empty string")
        
        if not self.aws_access_key_id or not self.aws_access_key_id.strip():
            raise ValueError("aws_access_key_id must be a non-empty string")
        
        if not self.aws_secret_access_key or not self.aws_secret_access_key.strip():
            raise ValueError("aws_secret_access_key must be a non-empty string")
        
        if not self.bedrock_model_id or not self.bedrock_model_id.strip():
            raise ValueError("bedrock_model_id must be a non-empty string")
    
    def get_aws_credentials(self) -> Dict[str, str]:
        """Get AWS credentials for boto3."""
        return {
            "aws_access_key_id": self.aws_access_key_id,
            "aws_secret_access_key": self.aws_secret_access_key,
            "region_name": self.aws_region
        }
    
    def get_bedrock_config(self) -> Dict[str, str]:
        """Get Bedrock-specific configuration."""
        return {
            "model_id": self.bedrock_model_id,
            "region": self.aws_region
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding sensitive data)."""
        return {
            'aws_region': self.aws_region,
            'bedrock_model_id': self.bedrock_model_id,
            'inspection_prompt': self.inspection_prompt,
            # Exclude sensitive credentials from dict representation
            'aws_access_key_id': '***',
            'aws_secret_access_key': '***'
        }
    
    @classmethod
    def from_env(cls) -> 'AppConfig':
        """
        Create AppConfig from environment variables.
        
        Required environment variables:
        - AWS_REGION: AWS region for Bedrock service
        - AWS_ACCESS_KEY_ID: AWS access key ID
        - AWS_SECRET_ACCESS_KEY: AWS secret access key
        - BEDROCK_MODEL_ID: Bedrock model identifier
        - INSPECTION_PROMPT: Prompt template for image inspection
        
        Returns:
            AppConfig: Configuration instance loaded from environment
            
        Raises:
            ValueError: If required environment variables are missing
        """
        # 환경 변수를 다시 로드
        from dotenv import load_dotenv
        load_dotenv()
        
        # Get required environment variables
        aws_region = os.getenv('AWS_REGION')
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        bedrock_model_id = os.getenv('BEDROCK_MODEL_ID')
        inspection_prompt = os.getenv('INSPECTION_PROMPT', '')  # 기본값 빈 문자열
        
        # Check for missing environment variables
        missing_vars = []
        if not aws_region:
            missing_vars.append('AWS_REGION')
        if not aws_access_key_id:
            missing_vars.append('AWS_ACCESS_KEY_ID')
        if not aws_secret_access_key:
            missing_vars.append('AWS_SECRET_ACCESS_KEY')
        if not bedrock_model_id:
            missing_vars.append('BEDROCK_MODEL_ID')
        # INSPECTION_PROMPT는 더 이상 필수가 아님
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return cls(
            aws_region=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            bedrock_model_id=bedrock_model_id,
            inspection_prompt=inspection_prompt
        )
    
    @classmethod
    def from_env_with_defaults(cls) -> 'AppConfig':
        """
        Create AppConfig from environment variables with default values.
        
        Returns:
            AppConfig: Configuration instance with defaults for missing values
        """
        # Default values
        default_region = 'us-east-1'
        default_model_id = 'anthropic.claude-3-7-sonnet-20250219-v1:0'
        default_prompt = """당신은 상품 이미지 검수 전문가입니다. 상품 외 배경만 검수합니다. 아래 기준에 따라 이미지를 객관적으로 평가하세요:
1. 상품 외 배경에 네모 테두리 강조(굵은 라인, 색상 박스, 불필요한 윤곽선)가 포함되어 있으면 false 처리한다.브랜드 로고에 있는 네모 테두리는 true 처리한다.
2. 상품 외 배경에 브랜드명 외의 텍스트가 포함되어 있으면 false 처리한다. '백화점 공식', '공식 판매처' 같은 공식적인 텍스트가 있는 경우는 true로 처리한다.
- 브랜드 로고, 브랜드명만 있으면 true 처리한다.
- 상품에 있는 텍스트는 무시한다.
- 브랜드명은 언어(한글/영문), 대소문자, 철자 변형 등을 포함하여 동일한 의미로 인식한다
3. 위 조건 외에는 true 처리한다.
출력은 반드시 아래 형식을 따른다:
- 결과: true 또는 false
- 사유: 사유를 간단히 설명 (사유에는 true, false 사용 금지)"""
        
        # Get environment variables with defaults
        aws_region = os.getenv('AWS_REGION', default_region)
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID', '')
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY', '')
        bedrock_model_id = os.getenv('BEDROCK_MODEL_ID', default_model_id)
        inspection_prompt = os.getenv('INSPECTION_PROMPT', default_prompt)
        
        # Still require AWS credentials
        if not aws_access_key_id or not aws_secret_access_key:
            raise ValueError("AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) are required")
        
        return cls(
            aws_region=aws_region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            bedrock_model_id=bedrock_model_id,
            inspection_prompt=inspection_prompt
        )