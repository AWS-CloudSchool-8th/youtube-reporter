from pydantic import BaseModel
from typing import List, Optional

class Visual(BaseModel):
    type: str
    url: Optional[str]
    caption: Optional[str]
    data: Optional[List[List[str]]]

class Paragraph(BaseModel):
    text: str
    visual: Optional[Visual]

class Section(BaseModel):
    heading: str
    paragraphs: List[Paragraph]

class ReportResponse(BaseModel):
    title: str
    videoId: str
    sections: List[Section]