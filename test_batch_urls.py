"""
일괄 URL 테스트 스크립트
"""

import sys
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# 환경 변수 로드
load_dotenv()

# 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from handlers.image_handler import ImageHandler


def test_urls():
    """URL 리스트 테스트"""
    
    # 테스트할 URL 리스트
    test_urls = [
        "https://shop-phinf.pstatic.net/20250827_140/1756283709244MLmy6_JPEG/61424597425515825_2106381066.jpg",
        "https://shop-phinf.pstatic.net/20250827_216/1756283489529JdvK2_JPEG/10956576108406294_746306671.jpg",
        "https://shop-phinf.pstatic.net/20250616_126/1750053958558v4Nl5_JPEG/4727045138458689_1370177227.jpg",
        "https://shop-phinf.pstatic.net/20250827_221/1756283494691jdB7U_JPEG/90416349814593519_811122573.jpg",
        "https://shop-phinf.pstatic.net/20250702_51/1751438720970FLwNE_JPEG/6153218682847289_1744730206.jpg"
    ]
    
    print("="*80)
    print("🧪 OpenCV 테두리 탐지 일괄 테스트")
    print("="*80)
    print(f"테스트 이미지 수: {len(test_urls)}개")
    print(f"테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    handler = ImageHandler()
    results = []
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n[{i}/{len(test_urls)}] 테스트 중...")
        print(f"URL: {url}")
        
        try:
            # 이미지 다운로드
            image_bytes = handler.fetch_image_from_url(url)
            image_info = handler.get_image_info(image_bytes)
            
            print(f"  ✅ 다운로드 완료: {len(image_bytes)} bytes")
            print(f"  📐 크기: {image_info['width']}x{image_info['height']}px")
            
            # OpenCV 테두리 탐지
            has_border, analysis, confidence = handler.detect_border_opencv(image_bytes)
            
            # 결과 저장
            result = {
                "index": i,
                "url": url,
                "image_size": f"{image_info['width']}x{image_info['height']}",
                "image_format": image_info['format'],
                "file_size_bytes": len(image_bytes),
                "has_border": has_border,
                "confidence": round(confidence * 100, 2),
                "analysis": analysis,
                "judgment": "반려 (테두리 있음)" if has_border else "통과 (테두리 없음)",
                "status": "✅ 통과" if not has_border else "❌ 반려"
            }
            
            results.append(result)
            
            # 콘솔 출력
            print(f"  🔍 테두리 탐지: {result['status']}")
            print(f"  📊 신뢰도: {result['confidence']}%")
            print(f"  📝 분석: {analysis}")
            
        except Exception as e:
            print(f"  ❌ 오류: {str(e)}")
            results.append({
                "index": i,
                "url": url,
                "error": str(e),
                "status": "⚠️ 오류"
            })
        
        print("-"*80)
    
    # 결과 요약
    print("\n" + "="*80)
    print("📈 테스트 결과 요약")
    print("="*80)
    
    success_results = [r for r in results if "error" not in r]
    pass_count = sum(1 for r in success_results if not r['has_border'])
    fail_count = sum(1 for r in success_results if r['has_border'])
    error_count = len(results) - len(success_results)
    
    print(f"총 테스트: {len(results)}개")
    print(f"✅ 통과: {pass_count}개")
    print(f"❌ 반려: {fail_count}개")
    print(f"⚠️  오류: {error_count}개")
    print("="*80)
    
    # 상세 결과 테이블
    print("\n📋 상세 결과:")
    print("-"*80)
    for result in results:
        if "error" in result:
            print(f"{result['index']}. {result['status']} - 오류 발생")
        else:
            print(f"{result['index']}. {result['status']} - 신뢰도: {result['confidence']}%")
            print(f"   {result['analysis']}")
    print("-"*80)
    
    # JSON 파일로 저장
    output_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "total_count": len(results),
            "pass_count": pass_count,
            "fail_count": fail_count,
            "error_count": error_count,
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 결과 저장 완료: {output_file}")
    
    # 마크다운 리포트 생성
    markdown_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    generate_markdown_report(results, pass_count, fail_count, error_count, markdown_file)
    print(f"📄 리포트 생성 완료: {markdown_file}")
    
    return results


def generate_markdown_report(results, pass_count, fail_count, error_count, filename):
    """마크다운 리포트 생성"""
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# 🔍 OpenCV 테두리 탐지 테스트 리포트\n\n")
        f.write(f"**테스트 일시**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 요약
        f.write("## 📊 테스트 요약\n\n")
        f.write(f"- **총 테스트**: {len(results)}개\n")
        f.write(f"- **✅ 통과**: {pass_count}개\n")
        f.write(f"- **❌ 반려**: {fail_count}개\n")
        f.write(f"- **⚠️ 오류**: {error_count}개\n\n")
        
        # 통과율
        if len(results) > 0:
            pass_rate = (pass_count / len(results)) * 100
            f.write(f"**통과율**: {pass_rate:.1f}%\n\n")
        
        # 상세 결과
        f.write("## 📋 상세 결과\n\n")
        
        for result in results:
            f.write(f"### {result['index']}. {result['status']}\n\n")
            
            if "error" in result:
                f.write(f"**URL**: {result['url']}\n\n")
                f.write(f"**오류**: {result['error']}\n\n")
            else:
                f.write(f"**URL**: {result['url']}\n\n")
                f.write(f"**이미지 크기**: {result['image_size']}\n\n")
                f.write(f"**파일 크기**: {result['file_size_bytes']:,} bytes\n\n")
                f.write(f"**판정**: {result['judgment']}\n\n")
                f.write(f"**신뢰도**: {result['confidence']}%\n\n")
                f.write(f"**분석 내용**:\n```\n{result['analysis']}\n```\n\n")
            
            f.write("---\n\n")
        
        # 설정 정보
        f.write("## ⚙️ 테스트 설정\n\n")
        f.write("- **중앙 마스킹**: 95%\n")
        f.write("- **가장자리 영역**: 2.5%\n")
        f.write("- **색상 범위**: 20% ~ 95%\n")
        f.write("- **신뢰도 임계값**: 15%\n\n")
        
        f.write("---\n\n")
        f.write("*Generated by OpenCV Border Detection Test*\n")


if __name__ == "__main__":
    test_urls()
