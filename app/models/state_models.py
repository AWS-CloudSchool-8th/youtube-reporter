from typing import TypedDict, List, Dict

class ImprovedGraphState(TypedDict):
    youtube_url: str
    caption: str
    report_text: str
    tagged_report: str
    visualization_requests: List[Dict]
    generated_visualizations: List[Dict]
    final_output: Dict