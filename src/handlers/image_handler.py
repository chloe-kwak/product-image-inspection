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
    
    def create_center_canvas_transparent(self, image_bytes: bytes, resize_ratio: float = 0.3) -> bytes:
        """
        원본 크기의 투명 캔버스 중앙에 축소된 이미지를 배치합니다.
        투명 배경으로 자연스러운 효과를 만들어 Nova가 더 정확히 인식하도록 합니다.
        
        Args:
            image_bytes: 원본 이미지 바이트 데이터
            resize_ratio: 축소 비율 (기본값: 0.3 = 30%)
            
        Returns:
            bytes: 투명 배경 중앙 배치된 캔버스 이미지 바이트 데이터
            
        Raises:
            ValueError: 이미지 처리 중 오류 발생
        """
        if not image_bytes:
            raise ValueError("이미지 데이터가 비어있습니다")
        
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                original_format = img.format or 'JPEG'
                original_width, original_height = img.size
                
                # 축소된 이미지 크기 계산
                new_width = int(original_width * resize_ratio)
                new_height = int(original_height * resize_ratio)
                
                # 이미지 축소
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # 투명도 지원 여부에 따라 캔버스 생성
                if original_format.upper() == 'PNG':
                    # PNG는 투명도 지원
                    canvas = Image.new('RGBA', (original_width, original_height), (0, 0, 0, 0))
                    if resized_img.mode != 'RGBA':
                        resized_img = resized_img.convert('RGBA')
                    canvas.paste(resized_img, ((original_width - new_width) // 2, (original_height - new_height) // 2), resized_img)
                else:
                    # JPEG는 흰 배경 사용 (투명도 미지원)
                    canvas = Image.new('RGB', (original_width, original_height), 'white')
                    canvas.paste(resized_img, ((original_width - new_width) // 2, (original_height - new_height) // 2))
                
                # 원본 형식으로 저장
                with io.BytesIO() as output:
                    canvas.save(output, format=original_format)
                    return output.getvalue()
                    
        except Exception as e:
            raise ValueError(f"투명 배경 중앙 배치 캔버스 생성 중 오류 발생: {str(e)}")
    
    def create_center_canvas_black(self, image_bytes: bytes, resize_ratio: float = 0.3) -> bytes:
        """
        원본 크기의 검은 캔버스 중앙에 축소된 이미지를 배치합니다.
        검은 배경으로 더 강한 대비를 만들어 Nova가 테두리를 더 잘 인식하도록 합니다.
        
        Args:
            image_bytes: 원본 이미지 바이트 데이터
            resize_ratio: 축소 비율 (기본값: 0.3 = 30%)
            
        Returns:
            bytes: 검은 배경 중앙 배치된 캔버스 이미지 바이트 데이터
            
        Raises:
            ValueError: 이미지 처리 중 오류 발생
        """
        if not image_bytes:
            raise ValueError("이미지 데이터가 비어있습니다")
        
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                original_width, original_height = img.size
                
                # 축소된 이미지 크기 계산
                new_width = int(original_width * resize_ratio)
                new_height = int(original_height * resize_ratio)
                
                # 이미지 축소
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # 원본 크기의 검은 캔버스 생성
                canvas = Image.new('RGB', (original_width, original_height), 'black')
                
                # 중앙 위치 계산
                x_offset = (original_width - new_width) // 2
                y_offset = (original_height - new_height) // 2
                
                # 축소된 이미지를 캔버스 중앙에 배치
                canvas.paste(resized_img, (x_offset, y_offset))
                
                # 바이트로 변환
                with io.BytesIO() as output:
                    canvas.save(output, format=img.format or 'PNG')
                    return output.getvalue()
                    
        except Exception as e:
            raise ValueError(f"검은 배경 중앙 배치 캔버스 생성 중 오류 발생: {str(e)}")
    
    def create_center_canvas(self, image_bytes: bytes, resize_ratio: float = 0.3) -> bytes:
        """
        원본 크기의 흰 캔버스 중앙에 축소된 이미지를 배치합니다.
        테두리가 있다면 중앙으로 이동하여 Nova가 더 잘 인식하도록 합니다.
        
        Args:
            image_bytes: 원본 이미지 바이트 데이터
            resize_ratio: 축소 비율 (기본값: 0.3 = 30%)
            
        Returns:
            bytes: 중앙 배치된 캔버스 이미지 바이트 데이터
            
        Raises:
            ValueError: 이미지 처리 중 오류 발생
        """
        if not image_bytes:
            raise ValueError("이미지 데이터가 비어있습니다")
        
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                original_width, original_height = img.size
                
                # 축소된 이미지 크기 계산
                new_width = int(original_width * resize_ratio)
                new_height = int(original_height * resize_ratio)
                
                # 이미지 축소
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # 원본 크기의 흰 캔버스 생성
                canvas = Image.new('RGB', (original_width, original_height), 'white')
                
                # 중앙 위치 계산
                x_offset = (original_width - new_width) // 2
                y_offset = (original_height - new_height) // 2
                
                # 축소된 이미지를 캔버스 중앙에 배치
                canvas.paste(resized_img, (x_offset, y_offset))
                
                # 바이트로 변환
                with io.BytesIO() as output:
                    canvas.save(output, format=img.format or 'PNG')
                    return output.getvalue()
                    
        except Exception as e:
            raise ValueError(f"중앙 배치 캔버스 생성 중 오류 발생: {str(e)}")
    
    def resize_30_percent(self, image_bytes: bytes) -> bytes:
        """
        이미지를 30% 크기로 축소합니다. (테두리를 더 중앙으로 이동시켜 Nova가 확실히 인식하도록)
        
        Args:
            image_bytes: 원본 이미지 바이트 데이터
            
        Returns:
            bytes: 30% 축소된 이미지 바이트 데이터
            
        Raises:
            ValueError: 이미지 처리 중 오류 발생
        """
        if not image_bytes:
            raise ValueError("이미지 데이터가 비어있습니다")
        
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                width, height = img.size
                
                # 30% 크기로 축소 (더 극단적인 변화)
                new_width = int(width * 0.3)
                new_height = int(height * 0.3)
                
                # 리샘플링으로 축소 (고품질 유지)
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # 바이트로 변환
                with io.BytesIO() as output:
                    resized_img.save(output, format=img.format or 'PNG')
                    return output.getvalue()
                    
        except Exception as e:
            raise ValueError(f"이미지 리사이즈 중 오류 발생: {str(e)}")
    
    def resize_50_percent(self, image_bytes: bytes) -> bytes:
        """
        이미지를 50% 크기로 축소합니다. (테두리를 중앙으로 이동시켜 Nova가 더 잘 인식하도록)
        
        Args:
            image_bytes: 원본 이미지 바이트 데이터
            
        Returns:
            bytes: 50% 축소된 이미지 바이트 데이터
            
        Raises:
            ValueError: 이미지 처리 중 오류 발생
        """
        if not image_bytes:
            raise ValueError("이미지 데이터가 비어있습니다")
        
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                width, height = img.size
                
                # 50% 크기로 축소
                new_width = width // 2
                new_height = height // 2
                
                # 리샘플링으로 축소 (고품질 유지)
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # 바이트로 변환
                with io.BytesIO() as output:
                    resized_img.save(output, format=img.format or 'PNG')
                    return output.getvalue()
                    
        except Exception as e:
            raise ValueError(f"이미지 리사이즈 중 오류 발생: {str(e)}")
    
    def crop_center_50_percent(self, image_bytes: bytes) -> bytes:
        """
        이미지 중앙 50% 영역을 크롭합니다.
        
        Args:
            image_bytes: 원본 이미지 바이트 데이터
            
        Returns:
            bytes: 크롭된 이미지 바이트 데이터
            
        Raises:
            ValueError: 이미지 처리 중 오류 발생
        """
        if not image_bytes:
            raise ValueError("이미지 데이터가 비어있습니다")
        
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                width, height = img.size
                
                # 중앙 50% 영역 계산
                crop_width = width // 2
                crop_height = height // 2
                
                left = (width - crop_width) // 2
                top = (height - crop_height) // 2
                right = left + crop_width
                bottom = top + crop_height
                
                # 크롭 실행
                cropped_img = img.crop((left, top, right, bottom))
                
                # 바이트로 변환
                with io.BytesIO() as output:
                    cropped_img.save(output, format=img.format or 'PNG')
                    return output.getvalue()
                    
        except Exception as e:
            raise ValueError(f"이미지 크롭 중 오류 발생: {str(e)}")
    
    def add_black_padding(self, image_bytes: bytes, padding_ratio: float = 0.2) -> bytes:
        """
        원본 이미지 주변에 검은 패딩을 추가합니다.
        테두리 탐지를 위해 명확한 검은 배경과 대비를 만듭니다.

        Args:
            image_bytes: 원본 이미지 바이트 데이터
            padding_ratio: 패딩 비율 (기본값: 0.2 = 20%)

        Returns:
            bytes: 검은 패딩이 추가된 이미지 바이트 데이터

        Raises:
            ValueError: 이미지 처리 중 오류 발생
        """
        if not image_bytes:
            raise ValueError("이미지 데이터가 비어있습니다")

        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                original_format = img.format or 'JPEG'
                original_width, original_height = img.size

                # 패딩 크기 계산
                padding_width = int(original_width * padding_ratio)
                padding_height = int(original_height * padding_ratio)

                # 새 캔버스 크기 (원본 + 양쪽 패딩)
                new_width = original_width + (padding_width * 2)
                new_height = original_height + (padding_height * 2)

                # 검은 캔버스 생성
                canvas = Image.new('RGB', (new_width, new_height), 'black')

                # 원본 이미지를 캔버스 중앙에 배치
                canvas.paste(img, (padding_width, padding_height))

                # 바이트로 변환
                with io.BytesIO() as output:
                    canvas.save(output, format=original_format)
                    return output.getvalue()

        except Exception as e:
            raise ValueError(f"검은 패딩 추가 중 오류 발생: {str(e)}")

    def detect_border_opencv(self, image_bytes: bytes) -> Tuple[bool, str, float]:
        """
        OpenCV를 사용한 테두리 탐지

        Args:
            image_bytes: 이미지 바이트 데이터

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

            # 1. 가장자리 영역 정의 (전체의 5%)
            border_thickness = max(5, min(width, height) // 20)

            # 가장자리 마스크 생성
            border_mask = np.zeros((height, width), dtype=np.uint8)
            border_mask[:border_thickness, :] = 255  # 상단
            border_mask[-border_thickness:, :] = 255  # 하단
            border_mask[:, :border_thickness] = 255  # 좌측
            border_mask[:, -border_thickness:] = 255  # 우측

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

            # 유채색 탐지
            for color_name, (lower, upper) in color_ranges.items():
                mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
                border_color_pixels = np.sum(cv2.bitwise_and(mask, border_mask) > 0)

                if total_border_pixels > 0:
                    ratio = border_color_pixels / total_border_pixels
                    if ratio > 0.03:  # 3% 이상이면 의미있는 색상
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

            # 4. 판정 로직
            has_border = False
            confidence = 0.0
            analysis_details = []

            # 색상 기반 판정
            if detected_colors:
                color_confidence = sum(ratio for _, ratio in detected_colors)
                analysis_details.append(f"색상 탐지: {', '.join([f'{name}({ratio:.1%})' for name, ratio in detected_colors])}")
                confidence += color_confidence * 0.7

            # 엣지 기반 판정
            if edge_ratio > 0.1:  # 10% 이상 강한 엣지
                analysis_details.append(f"강한 경계선: {edge_ratio:.1%}")
                confidence += edge_ratio * 0.3

            # 최종 판정 (더 민감하게)
            has_border = confidence > 0.08  # 8% 임계값으로 낮춤

            analysis = "; ".join(analysis_details) if analysis_details else "특별한 테두리 패턴 없음"

            return has_border, analysis, confidence

        except Exception as e:
            raise ValueError(f"OpenCV 테두리 탐지 중 오류: {str(e)}")

    def __del__(self):
        """세션 정리"""
        if hasattr(self, 'session'):
            self.session.close()