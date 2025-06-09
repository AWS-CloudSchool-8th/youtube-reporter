def build_analysis_prompt(caption: str) -> str:
    return f"""
다음 자막을 문단별로 나눈 후, 각 문단마다:
- heading: 섹션 제목
- text: 문단 내용
- visual_type: 없는 경우 none, 이미지 image, 차트 chart, 표 table 중 하나
- visual_prompt: 시각자료 제작용 간단 설명

결과를 JSON 리스트로 출력해줘.
자막:
{caption}
"""