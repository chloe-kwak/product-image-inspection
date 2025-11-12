"""
이미지 핸들러 모듈
URL에서 이미지를 페치하고 처리하는 기능을 제공합니다.
"""

import base64
import io
import re
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse

import requests
from PIL import Image
import cv2
import numpy as np


class ImageHandler:
    """이미지 URL에서 이미지를 페치하고 처리하는 핸들러 클래스"""
    
    def __init__(self, timeout: int = 30):
        """
        ImageHandler 초기화
        
        Args:
            timeout: HTTP 요청 타임아웃 (초)
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def validate_image_url(self, url: str) -> bool:
        """
        이미지 URL의 유효성을 검증합니다.
        
        Args:
            url: 검증할 이미지 URL
            
        Returns:
            bool: URL이 유효하면 True, 그렇지 않으면 False
        """
        if not url or not isinstance(url, str):
            return False
        
        # URL 형식 검증
        try:
            parsed = urlparse(url.strip())
            if not all([parsed.scheme, parsed.netloc]):
                return False
            
            # HTTP/HTTPS 스키마만 허용
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # 일반적인 이미지 확장자 확인 (선택적)
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            path_lower = parsed.path.lower()
            
            # 확장자가 있는 경우 이미지 확장자인지 확인
            if '.' in path_lower:
                if not any(path_lower.endswith(ext) for ext in image_extensions):
                    # 확장자가 있지만 이미지 확장자가 아닌 경우에도 허용 (동적 이미지 URL 고려)
                    pass
            
            return True
            
        except Exception:
            return False
    
    def fetch_image_from_url(self, url: str) -> bytes:
        """
        URL에서 이미지를 페치합니다.
        
        Args:
            url: 이미지 URL
            
        Returns:
            bytes: 이미지 바이트 데이터
            
        Raises:
            ValueError: URL이 유효하지 않은 경우
            requests.RequestException: HTTP 요청 실패
            Exception: 기타 이미지 페치 오류
        """
        if not self.validate_image_url(url):
            raise ValueError(f"유효하지 않은 이미지 URL입니다: {url}")
        
        try:
            response = self.session.get(url, timeout=self.timeout, stream=True)
            response.raise_for_status()
            
            # Content-Type 확인
            content_type = response.headers.get('content-type', '').lower()
            if content_type and not content_type.startswith('image/'):
                raise ValueError(f"응답이 이미지가 아닙니다. Content-Type: {content_type}")
            
            # 이미지 데이터 읽기
            image_data = response.content
            
            # 이미지 데이터가 비어있는지 확인
            if not image_data:
                raise ValueError("이미지 데이터가 비어있습니다")
            
            # PIL로 이미지 유효성 검증
            try:
                with Image.open(io.BytesIO(image_data)) as img:
                    img.verify()
            except Exception as e:
                raise ValueError(f"유효하지 않은 이미지 데이터입니다: {str(e)}")
            
            return image_data
            
        except requests.exceptions.Timeout:
            raise requests.RequestException(f"이미지 다운로드 시간 초과: {url}")
        except requests.exceptions.ConnectionError:
            raise requests.RequestException(f"이미지 다운로드 연결 오류: {url}")
        except requests.exceptions.HTTPError as e:
            status_code = getattr(e.response, 'status_code', 'Unknown') if e.response else 'Unknown'
            raise requests.RequestException(f"HTTP 오류 ({status_code}): {url}")
        except requests.exceptions.RequestException as e:
            raise requests.RequestException(f"이미지 다운로드 실패: {str(e)}")
    
    def convert_image_to_base64(self, image_bytes: bytes) -> str:
        """
        이미지 바이트 데이터를 Base64 문자열로 변환합니다.
        
        Args:
            image_bytes: 이미지 바이트 데이터
            
        Returns:
            str: Base64 인코딩된 이미지 문자열
            
        Raises:
            ValueError: 이미지 데이터가 유효하지 않은 경우
        """
        if not image_bytes:
            raise ValueError("이미지 데이터가 비어있습니다")
        
        try:
            # 이미지 유효성 재검증
            with Image.open(io.BytesIO(image_bytes)) as img:
                img.verify()
            
            # Base64 인코딩
            base64_string = base64.b64encode(image_bytes).decode('utf-8')
            return base64_string
            
        except Exception as e:
            raise ValueError(f"이미지를 Base64로 변환하는 중 오류 발생: {str(e)}")
    
    def get_image_info(self, image_bytes: bytes) -> Dict[str, any]:
        """
        이미지 바이트 데이터에서 정보를 추출합니다.
        
        Args:
            image_bytes: 이미지 바이트 데이터
            
        Returns:
            Dict: 이미지 정보 (크기, 형식, 모드 등)
            
        Raises:
            ValueError: 이미지 데이터가 유효하지 않은 경우
        """
        if not image_bytes:
            raise ValueError("이미지 데이터가 비어있습니다")
        
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                info = {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'size_bytes': len(image_bytes),
                    'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                }
                
                # EXIF 데이터가 있는 경우 추가
                if hasattr(img, '_getexif') and img._getexif():
                    info['has_exif'] = True
                else:
                    info['has_exif'] = False
                
                return info
                
        except Exception as e:
            raise ValueError(f"이미지 정보 추출 중 오류 발생: {str(e)}")
    
    def fetch_and_process_image(self, url: str) -> Dict[str, any]:
        """
        URL에서 이미지를 페치하고 모든 처리를 수행하는 편의 메서드
        
        Args:
            url: 이미지 URL
            
        Returns:
            Dict: 처리된 이미지 데이터와 정보
            
        Raises:
            ValueError: URL이나 이미지가 유효하지 않은 경우
            requests.RequestException: HTTP 요청 실패
        """
        # 이미지 페치
        image_bytes = self.fetch_image_from_url(url)
        
        # Base64 변환
        base64_string = self.convert_image_to_base64(image_bytes)
        
        # 이미지 정보 추출
        image_info = self.get_image_info(image_bytes)
        
        return {
            'url': url,
            'base64': base64_string,
            'info': image_info,
            'raw_bytes': image_bytes
        }

    def detect_border_opencv(self, image_bytes: bytes, center_mask_ratio: float = 0.95) -> Tuple[bool, str, float]:
        """
        OpenCV를 사용한 테두리 탐지 (극단적 마스킹 적용)

        Args:
            image_bytes: 이미지 바이트 데이터
            center_mask_ratio: 중앙 제외 비율 (기본값: 0.95 = 중앙 95% 제외)
                              제품이 화면을 거의 꽉 채우는 경우 대비

        Returns:
            Tuple[bool, str, float]: (테두리 존재 여부, 상세 분석, 신뢰도)
        """
        if not image_bytes:
            raise ValueError("이미지 데이터가 비어있습니다")

        try:
            # PIL Image를 OpenCV 형식으로 변환
            pil_image = Image.open(io.BytesIO(image_bytes))
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # PIL을 numpy 배열로 변환 후 BGR로 변환 (OpenCV 형식)
            img_array = np.array(pil_image)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

            height, width = img_bgr.shape[:2]

            # 1. 가장자리 영역 정의 (극단적으로 좁게 - 최외곽 2-3%만)
            # 제품이 화면을 꽉 채워도 순수 배경 테두리만 분석
            border_thickness = max(3, min(width, height) // 40)  # 약 2.5%

            # 가장자리 마스크 생성 (최외곽만)
            border_mask = np.zeros((height, width), dtype=np.uint8)
            border_mask[:border_thickness, :] = 255  # 상단
            border_mask[-border_thickness:, :] = 255  # 하단
            border_mask[:, :border_thickness] = 255  # 좌측
            border_mask[:, -border_thickness:] = 255  # 우측
            
            # 2. 중앙 영역 마스킹 (제품 영역 제외 - 거의 전체)
            # 제품이 화면 꽉 차는 경우 대비하여 중앙 거의 전체 제외
            center_width = int(width * center_mask_ratio)
            center_height = int(height * center_mask_ratio)
            center_x = (width - center_width) // 2
            center_y = (height - center_height) // 2
            
            # 중앙 영역을 마스크에서 제거 (0으로 설정)
            border_mask[center_y:center_y+center_height, center_x:center_x+center_width] = 0

            # 2. HSV 색공간에서 색상 분석
            hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

            # 모든 색상 범위 정의 (유채색 + 무채색)
            color_ranges = {
                'blue1': [(90, 30, 30), (130, 255, 255)],  # 파란색 범위 확장
                'blue2': [(100, 50, 50), (140, 255, 255)], # 진한 파란색
                'cyan': [(75, 30, 30), (105, 255, 255)],   # 청록색 범위 확장
                'red1': [(0, 50, 50), (10, 255, 255)],     # 빨간색
                'red2': [(170, 50, 50), (180, 255, 255)],  # 빨간색2
                'green': [(35, 50, 50), (85, 255, 255)],   # 녹색
                'yellow': [(15, 50, 50), (45, 255, 255)],  # 노란색
                'magenta': [(125, 50, 50), (175, 255, 255)], # 보라색
                'orange': [(5, 50, 50), (25, 255, 255)]    # 주황색
            }

            # 총 테두리 픽셀 수 계산 (먼저 계산해야 함!)
            total_border_pixels = np.sum(border_mask > 0)

            # 무채색 (흰색, 검은색, 회색) 별도 처리
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

            # 밝은 테두리 (흰색, 밝은 회색) 탐지
            white_mask = cv2.inRange(gray, 200, 255)
            white_border_pixels = np.sum(cv2.bitwise_and(white_mask, border_mask) > 0)
            white_ratio = white_border_pixels / total_border_pixels if total_border_pixels > 0 else 0

            # 어두운 테두리 (검은색, 어두운 회색) 탐지
            black_mask = cv2.inRange(gray, 0, 50)
            black_border_pixels = np.sum(cv2.bitwise_and(black_mask, border_mask) > 0)
            black_ratio = black_border_pixels / total_border_pixels if total_border_pixels > 0 else 0

            detected_colors = []

            # 유채색 탐지 (더 엄격한 기준)
            for color_name, (lower, upper) in color_ranges.items():
                mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                border_color_pixels = np.sum(cv2.bitwise_and(mask, border_mask) > 0)

                if total_border_pixels > 0:
                    ratio = border_color_pixels / total_border_pixels
                    # 20% ~ 95% 범위만 테두리로 판단
                    # - 20% 미만: 너무 적음 (노이즈)
                    # - 95% 이상: 제품 자체 색상 (테두리 아님)
                    if 0.20 < ratio < 0.95:
                        detected_colors.append((color_name, ratio))

            # 무채색 탐지 비활성화 (너무 민감해서 자연 배경도 잡음)
            # 유채색 테두리만 탐지하도록 함
            # if white_ratio > 0.95:  # 비활성화
            #     detected_colors.append(('white', white_ratio))
            # if black_ratio > 0.95:  # 비활성화
            #     detected_colors.append(('black', black_ratio))

            # 3. 엣지 검출로 강한 경계선 찾기
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            border_edges = cv2.bitwise_and(edges, border_mask)
            edge_ratio = np.sum(border_edges > 0) / total_border_pixels if total_border_pixels > 0 else 0

            # 4. 판정 로직 (색상 + 엣지 조합)
            has_border = False
            confidence = 0.0
            analysis_details = []

            # 색상 기반 판정 (20% 이상만 탐지)
            if detected_colors:
                color_confidence = sum(ratio for _, ratio in detected_colors)
                analysis_details.append(f"색상 탐지: {', '.join([f'{name}({ratio:.1%})' for name, ratio in detected_colors])}")
                confidence += color_confidence * 0.5  # 가중치 낮춤

            # 엣지 기반 판정 (더 중요하게)
            if edge_ratio > 0.15:  # 15% 이상 강한 엣지
                analysis_details.append(f"강한 경계선: {edge_ratio:.1%}")
                confidence += edge_ratio * 0.5  # 가중치 높임

            # 최종 판정: 색상 + 엣지 조합으로 판단
            # 색상만으로는 부족, 강한 경계선도 있어야 테두리로 판정
            has_border = confidence > 0.15  # 15% 임계값 (더 엄격하게)

            analysis = "; ".join(analysis_details) if analysis_details else "특별한 테두리 패턴 없음"
            
            # 디버깅 정보 추가
            if detected_colors or edge_ratio > 0.1:
                analysis += f" [중앙 {int(center_mask_ratio*100)}% 제외, 최외곽 {border_thickness}px만 분석]"

            return has_border, analysis, confidence

        except Exception as e:
            raise ValueError(f"OpenCV 테두리 탐지 중 오류: {str(e)}")

    def __del__(self):
        """세션 정리"""
        if hasattr(self, 'session'):
            self.session.close()