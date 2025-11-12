"""
OpenCV 테두리 탐지 테스트 스크립트
"""

import sys
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from handlers.image_handler import ImageHandler

def test_single_image(image_url: str, debug: bool = False):
    """단일 이미지 테스트"""
    print(f"\n{'='*80}")
    print(f"테스트 이미지: {image_url}")
    print(f"{'='*80}\n")
    
    try:
        # ImageHandler 초기화
        handler = ImageHandler()
        
        # 이미지 다운로드
        print("📥 이미지 다운로드 중...")
        image_bytes = handler.fetch_image_from_url(image_url)
        
        # 이미지 정보 출력
        image_info = handler.get_image_info(image_bytes)
        print(f"✅ 다운로드 완료: {len(image_bytes)} bytes")
        print(f"   크기: {image_info['width']}x{image_info['height']}px")
        print(f"   포맷: {image_info['format']}")
        
        # OpenCV 테두리 탐지
        print("\n🔍 OpenCV 테두리 탐지 실행 중...")
        has_border, analysis, confidence = handler.detect_border_opencv(image_bytes)
        
        # 결과 출력
        print(f"\n{'='*80}")
        print(f"📊 테스트 결과")
        print(f"{'='*80}")
        print(f"테두리 탐지: {'❌ 있음 (반려)' if has_border else '✅ 없음 (통과)'}")
        print(f"신뢰도: {confidence:.2%}")
        print(f"상세 분석: {analysis}")
        print(f"{'='*80}\n")
        
        # 판정
        if has_border:
            print("⚠️  이 이미지는 테두리가 탐지되어 반려됩니다.")
            if debug:
                print("\n💡 디버깅 팁:")
                print("   - 색상 임계값을 높이거나 (현재 20%)")
                print("   - 엣지 임계값을 높이거나 (현재 15%)")
                print("   - 최종 임계값을 높여보세요 (현재 15%)")
        else:
            print("✅ 이 이미지는 테두리가 없어 통과합니다.")
        
        return has_border, analysis, confidence
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None, None


def test_multiple_images():
    """여러 이미지 테스트"""
    test_images = [
        {
            "url": "https://shop-phinf.pstatic.net/20250827_216/1756283489529JdvK2_JPEG/10956576108406294_746306671.jpg",
            "description": "바지 3개 (화면 꽉 참)",
            "expected": "통과"
        },
        {
            "url": "https://shop-phinf.pstatic.net/20250827_221/1756283494691jdB7U_JPEG/90416349814593519_811122573.jpg",
            "description": "어린이 이미지",
            "expected": "통과"
        },
        {
            "url": "https://shop-phinf.pstatic.net/20250616_126/1750053958558v4Nl5_JPEG/4727045138458689_1370177227.jpg",
            "description": "사본 텍스트",
            "expected": "통과"
        },
        {
            "url": "https://shop-phinf.pstatic.net/20250827_266/1756283702318M5JMo_JPEG/2729632462003176_1558362207.jpg",
            "description": "파란색 테두리",
            "expected": "반려"
        }
    ]
    
    print("\n" + "="*80)
    print("🧪 일괄 테스트 시작")
    print("="*80)
    
    results = []
    
    for i, test_case in enumerate(test_images, 1):
        print(f"\n[{i}/{len(test_images)}] {test_case['description']}")
        print(f"예상 결과: {test_case['expected']}")
        
        has_border, analysis, confidence = test_single_image(test_case['url'])
        
        if has_border is not None:
            actual = "반려" if has_border else "통과"
            is_correct = actual == test_case['expected']
            
            results.append({
                'description': test_case['description'],
                'expected': test_case['expected'],
                'actual': actual,
                'correct': is_correct,
                'confidence': confidence
            })
        
        print("\n" + "-"*80)
    
    # 최종 요약
    print("\n" + "="*80)
    print("📈 테스트 요약")
    print("="*80)
    
    for result in results:
        status = "✅" if result['correct'] else "❌"
        print(f"{status} {result['description']}")
        print(f"   예상: {result['expected']} | 실제: {result['actual']} | 신뢰도: {result['confidence']:.2%}")
    
    correct_count = sum(1 for r in results if r['correct'])
    total_count = len(results)
    accuracy = correct_count / total_count * 100 if total_count > 0 else 0
    
    print(f"\n정확도: {correct_count}/{total_count} ({accuracy:.1f}%)")
    print("="*80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='OpenCV 테두리 탐지 테스트')
    parser.add_argument('--url', type=str, help='테스트할 이미지 URL')
    parser.add_argument('--batch', action='store_true', help='일괄 테스트 실행')
    parser.add_argument('--debug', action='store_true', help='디버깅 모드')
    
    args = parser.parse_args()
    
    if args.batch:
        # 일괄 테스트
        test_multiple_images()
    elif args.url:
        # 단일 이미지 테스트
        test_single_image(args.url, debug=args.debug)
    else:
        # 기본: 바지 3개 이미지 테스트
        print("기본 테스트: 바지 3개 이미지 (화면 꽉 참)")
        test_single_image("https://shop-phinf.pstatic.net/20250827_216/1756283489529JdvK2_JPEG/10956576108406294_746306671.jpg", debug=args.debug)
