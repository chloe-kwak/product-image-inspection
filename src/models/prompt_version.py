"""
Prompt version management system
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
import json


@dataclass
class PromptVersion:
    """프롬프트 버전 정보"""
    version: str
    name: str
    prompt_text: str
    created_at: datetime
    description: str = ""
    is_active: bool = False


class PromptVersionManager:
    """프롬프트 버전 관리자"""
    
    def __init__(self):
        self.versions: Dict[str, PromptVersion] = {}
        self.active_version: Optional[str] = None
        self._initialize_default_versions()
    
    def _initialize_default_versions(self):
        """기본 프롬프트 버전들 초기화"""
        
        # v1.0 - 초기 버전
        v1_prompt = """P상품 이미지 검수 전문가로서 상품 외 배경만 검수하세요.

## 검수 기준

### FALSE 처리 (위반 사항)
1. **장식용 네모 테두리**: 상품을 둘러싸는 단순 장식 테두리, 광고성 프레임
2. **광고성 텍스트**: 가격, 할인율, 세일 문구, 과도한 마케팅 텍스트

### TRUE 허용 (정상)
1. **브랜드/인증 관련**: 브랜드 로고, '백화점 공식', '공식 판매처' 등의 배경 박스 (색상/테두리 무관)
2. **자연스러운 환경**: 매장 진열, 카탈로그 형태, 옷걸이, 진열대
3. **상품 자체**: 패키지나 라벨의 모든 텍스트/디자인
4. **기본 배경**: 단색 배경, 브랜드 로고만 있는 배경

## 핵심 원칙
- 브랜드명이나 공식 인증이 포함된 요소는 테두리가 있어도 허용
- 상품 판매의 신뢰성을 보장하는 요소는 모두 허용
- 단순 장식이나 과도한 광고 강조만 제한

## 출력 형식
결과: true 또는 false
사유: 구체적인 판정 근거 (true/false 단어 사용 금지)"""

        self.add_version(
            version="v1.0",
            name="기본 검수 프롬프트",
            prompt_text=v1_prompt,
            description="초기 상품 이미지 검수 프롬프트",
            is_active=True
        )
        
        # v1.1 - 강화된 테두리 탐지
        v1_1_prompt = """Product image inspection expert. Inspect only the background outside the product.

## CRITICAL: EXAMINE IMAGE EDGES CAREFULLY

STEP 1: Look at the OUTER PERIMETER of the image:
- TOP edge: Is there a colored line or border running along the top?
- BOTTOM edge: Is there a colored line or border running along the bottom?
- LEFT edge: Is there a colored line or border running along the left?
- RIGHT edge: Is there a colored line or border running along the right?

SPECIFIC COLORS TO DETECT:
- Light blue borders (하늘색)
- Sky blue borders
- Any colored rectangular frames
- Thin or thick colored lines around the image perimeter

## INSPECTION CRITERIA

### FALSE (Violations)
1. **Colored Borders on Image Edges**: ANY colored lines/borders around the image perimeter
2. **Advertising Text**: Prices, discounts, sale phrases

### TRUE (Acceptable)
1. **Brand Names**: Discovery EXPEDITION, MLB KIDS, Nike, etc.
2. **Clean Images**: No colored borders around the image edges

## OUTPUT FORMAT (답변은 한글로):
결과: true 또는 false
사유: 구체적인 판정 근거 (테두리 유무 명시)"""

        self.add_version(
            version="v1.1",
            name="강화된 테두리 탐지",
            prompt_text=v1_1_prompt,
            description="테두리 탐지 기능을 강화한 버전"
        )
        
        # v1.2 - 관대한 정책
        v1_2_prompt = """Product image inspection expert. Inspect only the background outside the product.

## POLICY: ONLY REJECT OBVIOUS DECORATIVE BORDERS

### WHAT TO REJECT (FALSE) - Very Specific:
- Clear artificial colored borders that frame the ENTIRE image like a picture frame
- Obvious light blue/sky blue decorative borders around all image edges
- Added graphic frames that are clearly decorative elements

### WHAT TO ACCEPT (TRUE) - Be Generous:
- Brand names and logos (Discovery EXPEDITION, MLB KIDS, Nike, etc.)
- Natural store environments (hangers, displays, shelves, lighting)
- Photography backgrounds (white, gray, natural lighting)
- Product packaging and natural presentation
- Brand text backgrounds and natural shadows
- Any image that looks like natural product photography

## DECISION RULE
- If you see OBVIOUS artificial decorative borders → FALSE
- Everything else (including unclear cases) → TRUE
- Err on the side of acceptance

## OUTPUT FORMAT (답변은 한글로):
결과: true 또는 false
사유: 구체적인 판정 근거"""

        self.add_version(
            version="v1.2",
            name="관대한 정책 적용",
            prompt_text=v1_2_prompt,
            description="의심스러운 경우 허용하는 관대한 정책"
        )
        
        # v1.3 - 현재 환경 변수 프롬프트
        v1_3_prompt = """Product image inspection expert. Inspect only the background outside the product.

## POLICY: ONLY REJECT OBVIOUS DECORATIVE BORDERS

### WHAT TO REJECT (FALSE) - Very Specific:
- Clear artificial colored borders that frame the ENTIRE image like a picture frame
- Obvious light blue/sky blue decorative borders around all image edges
- Added graphic frames that are clearly decorative elements

### WHAT TO ACCEPT (TRUE) - Be Generous:
- Brand names and logos (Discovery EXPEDITION, MLB KIDS, Nike, etc.)
- Natural store environments (hangers, displays, shelves, lighting)
- Photography backgrounds (white, gray, natural lighting)
- Product packaging and natural presentation
- Brand text backgrounds and natural shadows
- Any image that looks like natural product photography

## INSPECTION CRITERIA

### FALSE (Violations) - ONLY for obvious cases:
1. **Obvious Decorative Borders**: Clear artificial borders framing the entire image
2. **Advertising Text**: Prices, discounts, sale phrases (NOT brand names)

### TRUE (Acceptable) - Default assumption:
1. **All Brand Elements**: Any brand names, logos, official text
2. **Natural Environments**: Store displays, photography backgrounds
3. **Clean Presentations**: Professional product photography
4. **When in Doubt**: Choose TRUE unless borders are very obvious

## DECISION RULE
- If you see OBVIOUS artificial decorative borders → FALSE
- Everything else (including unclear cases) → TRUE
- Err on the side of acceptance

## OUTPUT FORMAT (답변은 한글로):
결과: true 또는 false
사유: 구체적인 판정 근거"""

        self.add_version(
            version="v1.3",
            name="기대값 맞춤 프롬프트",
            prompt_text=v1_3_prompt,
            description="기대값에 맞춰 최적화된 관대한 정책 프롬프트"
        )
        
        # v1.4 - 최신 개선 버전
        v1_4_prompt = """Product image inspection expert. Inspect only the background outside the product.

## ENHANCED POLICY: PRECISE BORDER DETECTION

### CRITICAL EXAMINATION STEPS:
1. **Edge Analysis**: Examine all four edges (top, bottom, left, right) for artificial borders
2. **Color Detection**: Look specifically for light blue, sky blue, or colored frames
3. **Context Understanding**: Distinguish between natural backgrounds and added decorative elements

### WHAT TO REJECT (FALSE) - Very Specific:
- Artificial colored borders that frame the ENTIRE image perimeter
- Light blue/sky blue decorative borders around image edges
- Added graphic frames that are clearly decorative elements
- Obvious rectangular frames that look like picture frames

### WHAT TO ACCEPT (TRUE) - Natural Elements:
- Brand names and logos (Discovery EXPEDITION, MLB KIDS, Nike, Adidas, etc.)
- Natural store environments (hangers, displays, shelves, lighting, ceiling)
- Photography backgrounds (white, gray, natural studio lighting)
- Product packaging colors and natural presentation
- Brand text backgrounds and natural shadows
- Store fixture elements and natural retail environments

## ENHANCED DECISION RULE
- Artificial decorative border around image perimeter → FALSE
- Natural brand backgrounds and store environments → TRUE
- When uncertain about border vs natural element → TRUE (err on acceptance)

## OUTPUT FORMAT (답변은 한글로):
결과: true 또는 false
사유: 구체적인 판정 근거 (테두리 유무와 자연스러운 환경 여부 명시)"""

        self.add_version(
            version="v1.4",
            name="향상된 정밀 탐지",
            prompt_text=v1_4_prompt,
            description="단계별 분석과 향상된 자연 환경 인식",
            is_active=True  # v1.4를 기본 활성 버전으로 설정
        )
        
        # v1.5 - Nova Pro 최적화 테두리 탐지
        v1_5_prompt = """You are a product image inspection expert. Your ONLY task is to detect artificial decorative borders around the image perimeter.

## CRITICAL: FOCUS ON IMAGE EDGES ONLY

**STEP 1: BORDER DETECTION PROTOCOL**
Look at the OUTER PERIMETER of the image:
- TOP EDGE: Is there a colored line/border along the top edge?
- BOTTOM EDGE: Is there a colored line/border along the bottom edge?  
- LEFT EDGE: Is there a colored line/border along the left edge?
- RIGHT EDGE: Is there a colored line/border along the right edge?

**STEP 2: SPECIFIC BORDER IDENTIFICATION**
REJECT (FALSE) if you see:
- Light blue borders (하늘색 네모 테두리)
- Sky blue rectangular frames around the image
- Colored outline borders that frame the entire image
- Artificial decorative frames added to the image perimeter

**STEP 3: NATURAL ELEMENTS TO IGNORE**
ACCEPT (TRUE) for:
- Brand logos and text (Discovery EXPEDITION, MLB KIDS, Nike, Adidas)
- Store backgrounds (hangers, shelves, displays, lighting)
- Product packaging and natural colors
- Photography studio backgrounds (white, gray)
- Natural retail environments

## DECISION LOGIC
- If COLORED BORDER exists around image edges → FALSE
- If NO colored border around image edges → TRUE
- Focus ONLY on image perimeter, ignore product content

## CRITICAL FOR NOVA PRO
- 하늘색 네모 테두리 (light blue rectangular border) = IMMEDIATE FALSE
- 이미지 전체 테두리 강조선 (image perimeter outline) = IMMEDIATE FALSE
- 상품 외 배경 불필요한 윤곽선 (unnecessary outlines in background) = IMMEDIATE FALSE

## OUTPUT FORMAT (답변은 한글로):
결과: true 또는 false
사유: 이미지 전체 테두리에 [색상] 테두리가 [있음/없음]. [구체적 설명]"""

        self.add_version(
            version="v1.5",
            name="Nova Pro 최적화 테두리 탐지",
            prompt_text=v1_5_prompt,
            description="Nova Pro 모델을 위한 명확한 테두리 탐지 지시사항"
        )
        
        # v1.6 - Nova Pro 초강력 테두리 탐지
        v1_6_prompt = """CRITICAL MISSION: Detect colored borders around image edges.

## MANDATORY INSPECTION SEQUENCE

**FIRST: EXAMINE IMAGE BOUNDARIES**
1. Look at the very TOP edge of the image - is there a colored line?
2. Look at the very BOTTOM edge of the image - is there a colored line?
3. Look at the very LEFT edge of the image - is there a colored line?
4. Look at the very RIGHT edge of the image - is there a colored line?

**SECOND: IDENTIFY BORDER COLORS**
- Light blue (하늘색)
- Sky blue (연한 파란색)
- Any colored rectangular frame
- Thin or thick colored outlines

**THIRD: MAKE DECISION**
- If ANY colored border exists on ANY edge → RESULT: false
- If NO colored border on ANY edge → RESULT: true

## IGNORE THESE (ALWAYS ACCEPT):
- Brand text: Discovery EXPEDITION, MLB KIDS, Nike
- Store backgrounds: hangers, shelves, displays
- Product packaging colors
- Natural photography backgrounds

## NOVA PRO SPECIFIC INSTRUCTIONS:
- 이미지의 가장자리를 매우 주의깊게 살펴보세요
- 어느 한 가장자리라도 하늘색이나 파란색 테두리가 있으면 반드시 false로 판정하세요
- 테두리는 이미지의 경계선에 있는 색깔있는 선을 의미합니다
- 상품 내용은 무시하고 오직 이미지 테두리만 확인하세요
- 한 면이라도 테두리가 있으면 전체 이미지가 불합격입니다

## REQUIRED OUTPUT FORMAT:
결과: true 또는 false
사유: 이미지 가장자리에 [색상명] 테두리가 [발견됨/발견되지 않음]. [상세 설명]

## EXAMPLES:
- "결과: false, 사유: 이미지 가장자리에 하늘색 테두리가 발견됨. 이미지 전체를 둘러싸는 네모 형태의 파란색 윤곽선이 있음"
- "결과: true, 사유: 이미지 가장자리에 색깔 테두리가 발견되지 않음. 브랜드명만 있고 테두리 없음"

REMEMBER: Focus ONLY on image edges, not product content! ANY border = FAIL!"""

        self.add_version(
            version="v1.6",
            name="Nova Pro 초강력 테두리 탐지",
            prompt_text=v1_6_prompt,
            description="Nova Pro를 위한 단계별 강제 테두리 검사 프롬프트"
        )
        
        # v1.7 - Nova Pro 극한 직접 지시
        v1_7_prompt = """STOP! Before you analyze anything else, answer this ONE question:

DO YOU SEE A COLORED LINE OR BORDER AROUND THE OUTER EDGES OF THE IMAGE?

Look at:
- The very top edge of the image
- The very bottom edge of the image  
- The very left edge of the image
- The very right edge of the image

Is there a light blue, sky blue, or any colored line/border/frame around these edges?

YES = There is a colored border → Answer: false
NO = There is no colored border → Answer: true

IGNORE everything else in the image (brands, products, text, backgrounds).
ONLY look for colored borders around the image edges.

If you see 하늘색 테두리 (light blue border) or 파란색 윤곽선 (blue outline) around the image edges, the answer is FALSE.

FORMAT:
결과: true 또는 false
사유: 이미지 가장자리에 [색상] 테두리 [있음/없음]

CRITICAL: 이미지의 바깥쪽 경계선을 보세요. 색깔있는 테두리가 있나요?"""

        self.add_version(
            version="v1.7",
            name="Nova Pro 극한 직접 지시",
            prompt_text=v1_7_prompt,
            description="Nova Pro를 위한 극도로 단순하고 직접적인 테두리 탐지"
        )
        
        # v1.8 - Nova Pro 이미지 경계선 전용
        v1_8_prompt = """URGENT: IGNORE ALL CONTENT INSIDE THE IMAGE. ONLY LOOK AT THE IMAGE BOUNDARY.

TASK: Check if there is a colored border/frame around the ENTIRE IMAGE PERIMETER.

NOT the product border, NOT the logo border, NOT anything inside the image.
ONLY the outer boundary of the image itself.

STEP 1: Look at the image like a picture frame
- Is there a colored line around the TOP edge of the entire image?
- Is there a colored line around the BOTTOM edge of the entire image?
- Is there a colored line around the LEFT edge of the entire image?  
- Is there a colored line around the RIGHT edge of the entire image?

STEP 2: Identify border colors on IMAGE EDGES
- Light blue (하늘색) border around image perimeter = FALSE
- Sky blue border around image perimeter = FALSE
- Any colored frame around image perimeter = FALSE
- No colored border around image perimeter = TRUE

DO NOT CONFUSE:
- Product borders ≠ Image borders
- Logo borders ≠ Image borders
- Brand elements ≠ Image borders

FOCUS ONLY ON: 이미지 전체의 바깥쪽 경계선 (the outer boundary of the entire image)

CRITICAL QUESTION: 이미지 전체를 둘러싸는 색깔있는 테두리가 있습니까?

FORMAT:
결과: true 또는 false
사유: 이미지 전체 경계선에 [색상] 테두리 [있음/없음]"""

        self.add_version(
            version="v1.8",
            name="Nova Pro 이미지 경계선 전용",
            prompt_text=v1_8_prompt,
            description="이미지 전체 경계선과 내부 요소를 명확히 구분하는 프롬프트"
        )
        
        # v1.9 - Nova Pro ANY 테두리 엄격 탐지
        v1_9_prompt = """URGENT: ZERO TOLERANCE FOR ANY BORDER AROUND IMAGE EDGES.

TASK: Detect ANY colored border/frame around the image perimeter.

CRITICAL: NOT "obvious" borders, NOT "clear" borders, but ANY border at all.

STEP 1: Examine image boundaries with ZERO tolerance
- TOP edge: ANY colored line = IMMEDIATE FALSE
- BOTTOM edge: ANY colored line = IMMEDIATE FALSE  
- LEFT edge: ANY colored line = IMMEDIATE FALSE
- RIGHT edge: ANY colored line = IMMEDIATE FALSE

STEP 2: ANY border colors = REJECT
- Light blue (하늘색) = FALSE
- Sky blue = FALSE
- Any colored frame = FALSE
- Even thin/faint borders = FALSE
- Even subtle borders = FALSE

STEP 3: ZERO TOLERANCE RULE
1. **ANY Decorative Borders**: ANY artificial borders framing the entire image = FALSE
2. **ANY Colored Lines**: ANY colored lines around image perimeter = FALSE
3. **ANY Frame Elements**: ANY frame-like elements around image edges = FALSE

IGNORE COMPLETELY:
- Brand logos and text (Discovery EXPEDITION, MLB KIDS, Nike)
- Store backgrounds and displays
- Product content and packaging
- Natural photography backgrounds

NOVA PRO SPECIFIC:
- 이미지 가장자리에 어떤 색깔의 테두리라도 있으면 무조건 FALSE
- "명백한" 테두리가 아니라 "어떤" 테두리라도 발견되면 FALSE
- 하늘색, 파란색, 어떤 색이든 테두리가 있으면 즉시 불합격
- 얇거나 희미한 테두리도 모두 불합격

CRITICAL QUESTION: 이미지 가장자리에 어떤 색깔의 테두리든 있습니까?

FORMAT:
결과: true 또는 false
사유: 이미지 가장자리에 [색상] 테두리 [발견됨/발견되지 않음]

REMEMBER: ANY border = IMMEDIATE FALSE. NO EXCEPTIONS."""

        self.add_version(
            version="v1.9",
            name="Nova Pro ANY 테두리 엄격 탐지",
            prompt_text=v1_9_prompt,
            description="어떤 테두리든 무관용 원칙으로 탐지하는 엄격한 프롬프트"
        )
        
        # v2.0 - Nova Pro 시각적 단서 강화
        v2_0_prompt = """VISUAL ANALYSIS PROTOCOL FOR NOVA PRO:

STEP 1: IGNORE THE CENTER - Look ONLY at image edges
🚫 Do NOT look at products, brands, or center content
✅ Look ONLY at the very outer edges of the image

STEP 2: EDGE-BY-EDGE INSPECTION
🔍 TOP EDGE: Scan the topmost pixel line - any color other than white/transparent?
🔍 BOTTOM EDGE: Scan the bottommost pixel line - any color other than white/transparent?
🔍 LEFT EDGE: Scan the leftmost pixel line - any color other than white/transparent?
🔍 RIGHT EDGE: Scan the rightmost pixel line - any color other than white/transparent?

STEP 3: COLOR DETECTION ON EDGES
🎨 Light blue (하늘색) on edges = FALSE
🎨 Sky blue on edges = FALSE
🎨 Any colored line on edges = FALSE
🎨 Thin colored outline on edges = FALSE

STEP 4: DECISION MATRIX
IF (TOP edge has color) OR (BOTTOM edge has color) OR (LEFT edge has color) OR (RIGHT edge has color):
    RESULT = FALSE
ELSE:
    RESULT = TRUE

NOVA PRO SPECIFIC INSTRUCTIONS:
❌ 이미지의 맨 가장자리 픽셀 라인을 확인하세요
❌ 상품이나 브랜드는 완전히 무시하세요
❌ 오직 이미지 테두리만 보세요
❌ 하늘색 라인이 가장자리에 있으면 즉시 FALSE

CRITICAL: Think like you're checking a picture frame - is there ANY colored border around the frame edges?

FORMAT:
결과: true 또는 false
사유: [TOP/BOTTOM/LEFT/RIGHT] 가장자리에 [색상] 라인 [발견됨/발견되지 않음]

EXAMPLE RESPONSES:
- "결과: false, 사유: TOP과 BOTTOM 가장자리에 하늘색 라인 발견됨"
- "결과: true, 사유: 모든 가장자리에 색깔 라인 발견되지 않음"

REMEMBER: 픽셀 레벨에서 가장자리만 확인하세요!"""

        self.add_version(
            version="v2.0",
            name="Nova Pro 시각적 단서 강화",
            prompt_text=v2_0_prompt,
            description="시각적 아이콘과 픽셀 레벨 분석으로 Nova Pro 테두리 탐지 강화"
        )
        
        # v2.1 - Nova Pro 환각 방지 + 테두리 탐지
        v2_1_prompt = """CRITICAL: ONLY describe what you ACTUALLY see. Do NOT imagine or assume anything.

ANTI-HALLUCINATION PROTOCOL:
❌ Do NOT mention text that doesn't exist
❌ Do NOT describe elements you're not 100% certain about
❌ Do NOT make assumptions about content
✅ ONLY report what is clearly visible

TASK: Check for colored borders around image edges ONLY.

STEP 1: REALITY CHECK
- Look at the image carefully
- Do NOT imagine additional text or elements
- Focus ONLY on what is actually there

STEP 2: BORDER DETECTION (FACTS ONLY)
🔍 TOP edge: Is there a colored line? (YES/NO)
🔍 BOTTOM edge: Is there a colored line? (YES/NO)
🔍 LEFT edge: Is there a colored line? (YES/NO)
🔍 RIGHT edge: Is there a colored line? (YES/NO)

STEP 3: DECISION (BASED ON FACTS)
- If ANY edge has a colored line → FALSE
- If NO edges have colored lines → TRUE

IGNORE COMPLETELY:
- Brand names (Discovery EXPEDITION, etc.)
- Product content
- Store backgrounds
- Natural elements

CRITICAL QUESTION: Are there actually colored lines on the image edges?

FORMAT (답변은 한글로):
결과: true 또는 false
사유: [실제로 보이는 것만] 가장자리에 [색상] 라인 [있음/없음]

REMEMBER: 
- ONLY report what you actually see
- Do NOT hallucinate text or elements
- Focus ONLY on border detection"""

        self.add_version(
            version="v2.1",
            name="Nova Pro 환각 방지 + 테두리 탐지",
            prompt_text=v2_1_prompt,
            description="Nova Pro 환각 현상 방지와 정확한 테두리 탐지를 위한 프롬프트"
        )
        
        # v2.2 - Nova Pro 절대 금지 명령
        v2_2_prompt = """ABSOLUTE RULE: ANY blue border around image = IMMEDIATE FALSE. NO EXCEPTIONS.

YOU JUST SAID: "blue border around the entire image"
THIS MEANS: RESULT = FALSE

CRITICAL UNDERSTANDING:
- Blue border around image = VIOLATION = FALSE
- Light blue border around image = VIOLATION = FALSE  
- Sky blue border around image = VIOLATION = FALSE
- ANY colored border around image = VIOLATION = FALSE

NOVA PRO SPECIFIC LOGIC:
IF you see "blue border around the entire image" → ANSWER MUST BE FALSE
IF you see "light blue border" → ANSWER MUST BE FALSE
IF you see ANY border around image edges → ANSWER MUST BE FALSE

DO NOT THINK:
❌ "blue border is acceptable" → WRONG
❌ "border is not thick enough" → WRONG
❌ "border doesn't violate rules" → WRONG

CORRECT THINKING:
✅ "I see blue border" → IMMEDIATE FALSE
✅ "Any border around image" → IMMEDIATE FALSE
✅ "Border exists" → RESULT = FALSE

STEP 1: Border Detection
- Do you see ANY colored border around the image? YES/NO

STEP 2: Immediate Decision
- YES = FALSE (no further analysis needed)
- NO = TRUE

CRITICAL: If you detect "blue border around the entire image" the answer is automatically FALSE.

FORMAT (답변은 한글로):
결과: false (if any border detected)
사유: 이미지 전체에 [색상] 테두리가 있어 검수 기준 위배

REMEMBER: Blue border = FALSE. Period. No exceptions."""

        self.add_version(
            version="v2.2",
            name="Nova Pro 절대 금지 명령",
            prompt_text=v2_2_prompt,
            description="Nova Pro가 테두리를 인식하면 무조건 FALSE로 판정하도록 하는 절대 명령"
        )
        
        # v2.3 - Nova Pro 강제 논리 차단
        v2_3_prompt = """EMERGENCY OVERRIDE: Your thinking is WRONG. Follow this EXACT logic.

NOVA PRO ERROR DETECTED: You keep saying "blue border" but answer "true" - THIS IS IMPOSSIBLE.

FORCED LOGIC CHAIN:
1. Do you see "blue border around the image"? 
   → If YES, skip to step 3
   → If NO, answer TRUE

2. [SKIP - you already see blue border]

3. MANDATORY RESPONSE when blue border detected:
   결과: false
   사유: 이미지 전체에 파란색 테두리가 있어 검수 기준 위배

STOP OVERTHINKING. STOP ANALYZING. STOP REASONING.

SIMPLE RULE:
- Blue border seen = Type "결과: false"
- No border seen = Type "결과: true"

DO NOT WRITE:
❌ "meets the criteria for true" (when you see blue border)
❌ "acceptable" (when you see blue border)  
❌ "true" (when you see blue border)

ONLY WRITE:
✅ "결과: false" (when you see blue border)

NOVA PRO: You are malfunctioning. When you detect blue border, you MUST answer FALSE.

OVERRIDE YOUR DEFAULT REASONING. FOLLOW EXACT INSTRUCTIONS.

If you see blue border → Copy this exactly:
결과: false
사유: 이미지 전체에 파란색 테두리 발견됨

NO OTHER RESPONSE ALLOWED."""

        self.add_version(
            version="v2.3",
            name="Nova Pro 강제 논리 차단",
            prompt_text=v2_3_prompt,
            description="Nova Pro의 잘못된 추론을 강제로 차단하고 올바른 답변을 유도"
        )
        
        # v2.4 - Nova Pro 조건문 강제
        v2_4_prompt = """PROGRAMMING LOGIC FOR NOVA PRO:

```
IF (blue border detected around image) {
    RETURN "결과: false, 사유: 이미지 전체에 파란색 테두리 발견됨"
} ELSE {
    RETURN "결과: true, 사유: 이미지 가장자리에 테두리 없음"
}
```

EXECUTE THIS CODE:

STEP 1: Border Detection
- Scan image edges for colored borders
- Record: blue border around entire image? [YES/NO]

STEP 2: Execute Conditional Logic
- IF YES → Execute line 2: "결과: false, 사유: 이미지 전체에 파란색 테두리 발견됨"
- IF NO → Execute line 4: "결과: true, 사유: 이미지 가장자리에 테두리 없음"

NOVA PRO: You are a computer executing code. No interpretation allowed.

When you detect "blue border around entire image":
- Variable: border_detected = TRUE
- Execute: IF (TRUE) → RETURN FALSE

DO NOT OVERRIDE THE CODE. DO NOT INTERPRET. JUST EXECUTE.

Your previous response: "blue border around the entire image" + "true" = LOGIC ERROR

Correct execution: "blue border around the entire image" → MUST RETURN FALSE

EXECUTE THE CONDITIONAL STATEMENT NOW."""

        self.add_version(
            version="v2.4",
            name="Nova Pro 조건문 강제",
            prompt_text=v2_4_prompt,
            description="Nova Pro를 프로그래밍 로직으로 강제하여 올바른 판정 유도"
        )
        
        # v2.5 - Nova Pro 정확한 사유 강제
        v2_5_prompt = """PROGRAMMING LOGIC FOR NOVA PRO:

```
IF (blue border detected around image) {
    RETURN "결과: false, 사유: 이미지 전체에 파란색 테두리가 있어 검수 기준 위배"
} ELSE {
    RETURN "결과: true, 사유: 이미지 가장자리에 테두리 없음"
}
```

CRITICAL: Use EXACT reason text. Do NOT mention text/content.

STEP 1: Border Detection Only
- Look for colored borders around image edges
- Ignore all text, brands, content inside image
- Focus ONLY on border presence

STEP 2: Execute Conditional with EXACT Reason
- IF border detected → "사유: 이미지 전체에 파란색 테두리가 있어 검수 기준 위배"
- IF no border → "사유: 이미지 가장자리에 테두리 없음"

FORBIDDEN REASONS:
❌ "텍스트가 포함되어 있습니다" (when it's about borders)
❌ "브랜드명 외의 텍스트" (when it's about borders)
❌ Any mention of text content

REQUIRED REASON:
✅ "이미지 전체에 파란색 테두리가 있어 검수 기준 위배" (for border violations)

NOVA PRO: You detected "blue border around entire image" → Use border reason, NOT text reason.

EXECUTE WITH CORRECT REASON:
- Detection: Blue border around image
- Result: false  
- Reason: 이미지 전체에 파란색 테두리가 있어 검수 기준 위배

DO NOT CONFUSE BORDER VIOLATIONS WITH TEXT VIOLATIONS."""

        self.add_version(
            version="v2.5",
            name="Nova Pro 정확한 사유 강제",
            prompt_text=v2_5_prompt,
            description="Nova Pro가 테두리 위반 시 정확한 사유를 제시하도록 강제"
        )
        
        # v2.6 - Nova Pro 극한 가장자리 집중
        v2_6_prompt = """NOVA PRO EDGE DETECTION PROTOCOL:

IGNORE THE CENTER 90% OF THE IMAGE. LOOK ONLY AT THE OUTER 5% EDGES.

VISUAL INSTRUCTION:
┌─────────────────────────┐ ← Look at this TOP edge only
│                         │ ← Look at this LEFT edge only  
│    IGNORE THIS CENTER   │
│                         │ ← Look at this RIGHT edge only
└─────────────────────────┘ ← Look at this BOTTOM edge only

TASK: Examine ONLY the thin border area around the image perimeter.

STEP 1: Edge Scanning Protocol
- Cover the center of image with your hand (mentally)
- Look ONLY at the thin strip around the edges
- Ask: "Is there a colored line in this edge strip?"

STEP 2: Edge Color Detection
- TOP edge strip: Any blue/colored line? YES/NO
- BOTTOM edge strip: Any blue/colored line? YES/NO  
- LEFT edge strip: Any blue/colored line? YES/NO
- RIGHT edge strip: Any blue/colored line? YES/NO

STEP 3: Decision
- ANY edge has colored line → FALSE
- NO edges have colored lines → TRUE

CRITICAL FOR NOVA PRO:
🚫 Do NOT analyze center content
🚫 Do NOT look at products/brands/text
🚫 Do NOT examine anything except the outer edge strips
✅ ONLY examine the perimeter border area

FORCED FOCUS: Pretend the center 90% of image is black/covered. Only the edge strips are visible.

FORMAT:
결과: false (if any edge strip has color)
사유: [TOP/BOTTOM/LEFT/RIGHT] 가장자리에 [색상] 라인 발견됨

NOVA PRO: Focus your vision on the EDGES ONLY. Ignore everything else."""

        self.add_version(
            version="v2.6",
            name="Nova Pro 극한 가장자리 집중",
            prompt_text=v2_6_prompt,
            description="Nova Pro가 이미지 중앙을 무시하고 오직 가장자리만 집중하도록 강제"
        )
        
        # v2.7 - Nova Pro 출력 형식 개선
        v2_7_prompt = """NOVA PRO EDGE DETECTION PROTOCOL:

IGNORE THE CENTER 90% OF THE IMAGE. LOOK ONLY AT THE OUTER 5% EDGES.

TASK: Examine ONLY the thin border area around the image perimeter.

STEP 1: Edge Scanning Protocol
- Cover the center of image with your hand (mentally)
- Look ONLY at the thin strip around the edges
- Ask: "Is there a colored line in this edge strip?"

STEP 2: Edge Color Detection
- TOP edge strip: Any blue/colored line? YES/NO
- BOTTOM edge strip: Any blue/colored line? YES/NO  
- LEFT edge strip: Any blue/colored line? YES/NO
- RIGHT edge strip: Any blue/colored line? YES/NO

STEP 3: Decision
- ANY edge has colored line → FALSE
- NO edges have colored lines → TRUE

CRITICAL FOR NOVA PRO:
🚫 Do NOT analyze center content
🚫 Do NOT look at products/brands/text
🚫 Do NOT examine anything except the outer edge strips
✅ ONLY examine the perimeter border area

FORCED FOCUS: Pretend the center 90% of image is black/covered. Only the edge strips are visible.

REQUIRED OUTPUT FORMAT (답변은 한글로, 완전한 문장으로):
결과: true 또는 false
사유: [구체적이고 완전한 설명을 한 문장으로 작성]

EXAMPLES OF COMPLETE RESPONSES:
- "결과: false, 사유: TOP과 BOTTOM 가장자리에 하늘색 라인이 발견되었습니다"
- "결과: true, 사유: 모든 가장자리에 색깔 라인이 발견되지 않았습니다"

NOVA PRO: Write complete sentences. Do not cut off in the middle."""

        self.add_version(
            version="v2.7",
            name="Nova Pro 출력 형식 개선",
            prompt_text=v2_7_prompt,
            description="Nova Pro의 출력이 잘리지 않도록 완전한 문장 형식 강조"
        )
        
        # v3.0 - AWS 샘플 기반 구조화된 검수
        v3_0_prompt = """NOVA PRO VISUAL INSPECTION PROTOCOL (Based on AWS Best Practices):

TASK: Analyze the product image for visual defects and border violations.

INSPECTION CRITERIA:
1. **Border Detection**: Look for ANY colored borders, frames, or outlines around the image edges
2. **Text Analysis**: Check for non-brand text in background areas
3. **Visual Quality**: Assess overall image quality and compliance

CRITICAL INSTRUCTIONS:
- Be VERY STRICT with border detection
- ANY colored line around image perimeter = VIOLATION
- Focus on image boundaries, not product content
- Mark as FAIL if ANY violations exist; otherwise mark as PASS

REQUIRED JSON OUTPUT FORMAT:
Clean JSON only — no markdown, no extra characters.

{
    "result": true/false,
    "qc_status": "PASS" or "FAIL", 
    "inspection_summary": "Brief description of findings",
    "violations": [
        {
            "type": "border" or "text" or "other",
            "severity": "high" or "medium" or "low",
            "description": "Specific violation description",
            "location": "top/bottom/left/right/center"
        }
    ]
}

EXAMPLES:

Border Violation:
{
    "result": false,
    "qc_status": "FAIL",
    "inspection_summary": "Blue border detected around image perimeter",
    "violations": [
        {
            "type": "border",
            "severity": "high", 
            "description": "Light blue colored border around entire image",
            "location": "all_edges"
        }
    ]
}

Clean Image:
{
    "result": true,
    "qc_status": "PASS",
    "inspection_summary": "No violations detected, image meets quality standards",
    "violations": []
}

NOVA PRO: Return ONLY the JSON structure. Be strict with border detection."""

        self.add_version(
            version="v3.0",
            name="AWS 샘플 기반 구조화된 검수",
            prompt_text=v3_0_prompt,
            description="AWS 샘플 노트북 기반으로 구조화된 JSON 출력과 엄격한 검수 기준 적용"
        )
        
        # v3.1 - 매장 배경 허용하는 균형잡힌 검수
        v3_1_prompt = """상품 이미지 배경 검수 기준:

### FALSE 처리 (위반 사항)
1. **장식용 테두리**: 이미지 가장자리에 색깔 있는 테두리, 프레임, 윤곽선
2. **광고성 텍스트**: 가격, 할인율, 세일 문구, 과도한 마케팅 텍스트

### TRUE 허용 (정상)
1. **브랜드 관련**: 브랜드 로고, 브랜드명, '백화점 공식', '공식 판매처' 등
2. **자연스러운 매장 환경**: 
   - 매장 진열대, 옷걸이, 진열 환경
   - 다른 상품들이 자연스럽게 진열된 매장 배경
   - 상점 인테리어, 진열 시설
3. **상품 자체**: 패키지, 라벨의 모든 텍스트/디자인
4. **기본 배경**: 단색 배경, 스튜디오 촬영 배경

### 핵심 판단 기준
- **테두리 검사**: 이미지 가장자리에 인위적인 색깔 테두리가 있는가?
- **매장 배경 허용**: 자연스러운 매장 진열 환경은 정상으로 처리
- **브랜드 요소 허용**: 브랜드 관련 모든 요소는 정상으로 처리

검수 절차:
1. 이미지 가장자리 테두리 확인 (있으면 FALSE)
2. 광고성 텍스트 확인 (있으면 FALSE)  
3. 나머지는 모두 TRUE (매장 배경, 브랜드 요소 포함)

FORMAT:
결과: true 또는 false
사유: 구체적인 판정 근거"""

        self.add_version(
            version="v3.1",
            name="매장 배경 허용하는 균형잡힌 검수",
            prompt_text=v3_1_prompt,
            description="테두리는 엄격히 탐지하되 자연스러운 매장 배경과 브랜드 요소는 허용하는 균형잡힌 프롬프트"
        )
        
        # v3.2 - 2단계 검수 전용 (테두리 검사 제외)
        v3_2_prompt = """2단계 상품 이미지 검수 (테두리는 이미 1단계에서 검사 완료):

⚠️ 중요: 테두리/윤곽선은 이미 1단계에서 검사했으므로 무시하세요.

### FALSE 처리 (위반 사항)
1. **광고성 텍스트**: 
   - 가격 표시 (₩, $, 원, 달러 등)
   - 할인율 (50% OFF, SALE, 세일 등)
   - 과도한 마케팅 문구 ("최저가", "특가", "이벤트" 등)

### TRUE 허용 (정상)
1. **브랜드 관련 모든 요소**:
   - 브랜드 로고, 브랜드명
   - '백화점 공식', '공식 판매처', '정품' 등
   - 브랜드 슬로건, 브랜드 관련 텍스트

2. **자연스러운 환경**:
   - 매장 진열대, 옷걸이, 진열 환경
   - 다른 상품들이 자연스럽게 진열된 매장 배경
   - 상점 인테리어, 진열 시설, 매장 사인

3. **상품 자체**:
   - 패키지, 라벨의 모든 텍스트/디자인
   - 상품명, 모델명, 사이즈 표시

4. **기본 배경**:
   - 단색 배경, 스튜디오 촬영 배경
   - 자연스러운 그림자, 조명

### 핵심 판단 원칙
🚫 **테두리/윤곽선은 무시** (이미 1단계에서 처리됨)
✅ **광고성 텍스트만 체크** (가격, 할인, 마케팅 문구)
✅ **브랜드 요소는 모두 허용**
✅ **매장 환경은 모두 허용**

검수 절차:
1. 테두리/윤곽선 → 무시 (1단계 완료)
2. 광고성 텍스트 확인 → 있으면 FALSE
3. 나머지는 모두 TRUE

FORMAT:
결과: true 또는 false
사유: 구체적인 판정 근거 (테두리 언급 금지)"""

        self.add_version(
            version="v3.2",
            name="2단계 검수 전용 (테두리 검사 제외)",
            prompt_text=v3_2_prompt,
            description="1단계에서 테두리 검사가 완료된 후 2단계에서 사용하는 프롬프트. 광고성 텍스트만 체크하고 브랜드/매장 요소는 모두 허용"
        )


    def add_version(self, version: str, name: str, prompt_text: str, 
                   description: str = "", is_active: bool = False) -> None:
        """새 프롬프트 버전 추가"""
        prompt_version = PromptVersion(
            version=version,
            name=name,
            prompt_text=prompt_text,
            created_at=datetime.now(),
            description=description,
            is_active=is_active
        )
        
        self.versions[version] = prompt_version
        
        if is_active:
            self.set_active_version(version)
    
    def set_active_version(self, version: str) -> bool:
        """활성 버전 설정"""
        if version not in self.versions:
            return False
        
        # 모든 버전을 비활성화
        for v in self.versions.values():
            v.is_active = False
        
        # 선택된 버전을 활성화
        self.versions[version].is_active = True
        self.active_version = version
        return True
    
    def get_active_prompt(self) -> Optional[str]:
        """현재 활성 프롬프트 반환"""
        if self.active_version and self.active_version in self.versions:
            return self.versions[self.active_version].prompt_text
        return None
    
    def get_active_version_info(self) -> Optional[PromptVersion]:
        """현재 활성 버전 정보 반환"""
        if self.active_version and self.active_version in self.versions:
            return self.versions[self.active_version]
        return None
    
    def list_versions(self) -> List[PromptVersion]:
        """모든 버전 목록 반환"""
        return sorted(self.versions.values(), key=lambda x: x.version)
    
    def get_version(self, version: str) -> Optional[PromptVersion]:
        """특정 버전 정보 반환"""
        return self.versions.get(version)
    
    def to_json(self) -> str:
        """JSON 형태로 내보내기"""
        data = {
            'active_version': self.active_version,
            'versions': {}
        }
        
        for version, prompt_version in self.versions.items():
            data['versions'][version] = {
                'version': prompt_version.version,
                'name': prompt_version.name,
                'prompt_text': prompt_version.prompt_text,
                'created_at': prompt_version.created_at.isoformat(),
                'description': prompt_version.description,
                'is_active': prompt_version.is_active
            }
        
        return json.dumps(data, ensure_ascii=False, indent=2)
