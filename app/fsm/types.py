from typing import List, TypedDict, Optional, Any

class Paragraph(TypedDict):
    text: str
    visual_type: str
    visual_prompt: Optional[str]
    visual_url: Optional[str]
    visual_data: Optional[List[List[Any]]]

class Section(TypedDict):
    heading: str
    paragraphs: List[Paragraph]

class ReportState(TypedDict):
    video_id: str
    caption: str
    sections: List[Section]
    retry_count: int