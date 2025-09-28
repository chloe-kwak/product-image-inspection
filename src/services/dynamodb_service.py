"""
DynamoDB service for storing inspection results
"""

import boto3
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError
import uuid
import sys
import os
from decimal import Decimal

# 절대 import를 위한 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.inspection_result import InspectionResult

logger = logging.getLogger(__name__)


class DynamoDBService:
    """DynamoDB 서비스 클래스"""
    
    def __init__(self, region: str, table_name: str = "product-image-inspection"):
        """
        DynamoDB 서비스 초기화
        
        Args:
            region: AWS 리전
            table_name: DynamoDB 테이블 이름
        """
        self.region = region
        self.table_name = table_name
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.table = None
        
    def initialize(self) -> bool:
        """DynamoDB 테이블 초기화 및 생성"""
        try:
            # 테이블 존재 확인
            self.table = self.dynamodb.Table(self.table_name)
            self.table.load()
            logger.info(f"DynamoDB 테이블 '{self.table_name}' 연결 성공")
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # 테이블이 없으면 생성
                return self._create_table()
            else:
                logger.error(f"DynamoDB 초기화 실패: {str(e)}")
                return False
                
    def _create_table(self) -> bool:
        """DynamoDB 테이블 생성"""
        try:
            table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {
                        'AttributeName': 'inspection_id',
                        'KeyType': 'HASH'  # Partition key
                    }
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'inspection_id',
                        'AttributeType': 'S'
                    }
                ],
                BillingMode='PAY_PER_REQUEST'  # On-demand 요금제
            )
            
            # 테이블 생성 완료 대기
            table.wait_until_exists()
            self.table = table
            
            logger.info(f"DynamoDB 테이블 '{self.table_name}' 생성 완료")
            return True
            
        except ClientError as e:
            logger.error(f"DynamoDB 테이블 생성 실패: {str(e)}")
            return False
    
    def save_inspection_result(self, result: InspectionResult) -> Optional[str]:
        """
        검수 결과를 DynamoDB에 저장
        
        Args:
            result: 저장할 검수 결과
            
        Returns:
            str: 저장된 항목의 ID, 실패시 None
        """
        try:
            logger.info(f"DynamoDB 저장 시작: {result.image_url}")
            
            # 테이블 상태 확인
            if not self.table:
                logger.error("DynamoDB 테이블이 초기화되지 않았습니다")
                return None
            
            # 고유 ID 생성
            inspection_id = str(uuid.uuid4())
            logger.info(f"생성된 검수 ID: {inspection_id}")
            
            # DynamoDB 항목 생성
            item = {
                'inspection_id': inspection_id,
                'image_url': result.image_url,
                'result': result.result,
                'reason': result.reason,
                'processing_time': Decimal(str(result.processing_time)),  # Float → Decimal 변환
                'model_id': result.model_id,
                'prompt_version': result.prompt_version,  # 프롬프트 버전 추가
                'timestamp': result.timestamp.isoformat(),
                'raw_response': result.raw_response,
                'created_at': datetime.now().isoformat()
            }
            
            logger.info(f"저장할 항목: {item}")
            
            # DynamoDB에 저장
            response = self.table.put_item(Item=item)
            logger.info(f"DynamoDB 응답: {response}")
            
            # 저장 확인
            if response.get('ResponseMetadata', {}).get('HTTPStatusCode') == 200:
                logger.info(f"검수 결과 저장 완료: {inspection_id}")
                return inspection_id
            else:
                logger.error(f"DynamoDB 저장 실패: {response}")
                return None
            
        except ClientError as e:
            logger.error(f"DynamoDB ClientError: {e.response['Error']['Code']} - {e.response['Error']['Message']}")
            return None
        except Exception as e:
            logger.error(f"DynamoDB 저장 실패: {str(e)}")
            return None
    
    def save_batch_results(self, results: List[Dict[str, Any]]) -> List[str]:
        """
        일괄 검수 결과를 DynamoDB에 저장
        
        Args:
            results: 저장할 검수 결과 리스트
            
        Returns:
            List[str]: 저장된 항목들의 ID 리스트
        """
        saved_ids = []
        
        try:
            with self.table.batch_writer() as batch:
                for result in results:
                    if result.get('success', False):
                        inspection_id = str(uuid.uuid4())
                        
                        item = {
                            'inspection_id': inspection_id,
                            'image_url': result['url'],
                            'result': result['result'],
                            'reason': result['reason'],
                            'processing_time': Decimal(str(result['processing_time'])),  # Float → Decimal 변환
                            'model_id': result.get('model_id', ''),
                            'prompt_version': result.get('prompt_version', ''),  # 프롬프트 버전 추가
                            'timestamp': datetime.now().isoformat(),
                            'created_at': datetime.now().isoformat(),
                            'batch_processing': True
                        }
                        
                        batch.put_item(Item=item)
                        saved_ids.append(inspection_id)
            
            logger.info(f"일괄 검수 결과 저장 완료: {len(saved_ids)}개 항목")
            return saved_ids
            
        except ClientError as e:
            logger.error(f"일괄 저장 실패: {str(e)}")
            return saved_ids
    
    def get_inspection_result(self, inspection_id: str) -> Optional[Dict[str, Any]]:
        """
        검수 결과 조회
        
        Args:
            inspection_id: 조회할 검수 ID
            
        Returns:
            Dict: 검수 결과, 없으면 None
        """
        try:
            response = self.table.get_item(
                Key={'inspection_id': inspection_id}
            )
            
            return response.get('Item')
            
        except ClientError as e:
            logger.error(f"검수 결과 조회 실패: {str(e)}")
            return None
    
    def test_connection(self) -> Dict[str, Any]:
        """DynamoDB 연결 및 테이블 상태 테스트"""
        try:
            # 테이블 정보 조회 (올바른 메서드명)
            table_info = self.table.meta.client.describe_table(TableName=self.table_name)
            
            # 간단한 항목 개수 조회
            response = self.table.scan(
                Select='COUNT'
            )
            
            return {
                'success': True,
                'table_name': self.table_name,
                'table_status': table_info['Table']['TableStatus'],
                'item_count': response['Count'],
                'region': self.region
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'table_name': self.table_name,
                'region': self.region
            }
    
    def list_recent_inspections(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        최근 검수 결과 목록 조회
        
        Args:
            limit: 조회할 최대 개수
            
        Returns:
            List[Dict]: 검수 결과 리스트
        """
        try:
            response = self.table.scan(
                Limit=limit,
                ProjectionExpression='inspection_id, image_url, #result, #timestamp, model_id',
                ExpressionAttributeNames={
                    '#result': 'result',
                    '#timestamp': 'timestamp'
                }
            )
            
            # 타임스탬프 기준 정렬
            items = response.get('Items', [])
            items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return items
            
        except ClientError as e:
            logger.error(f"검수 목록 조회 실패: {str(e)}")
            return []
