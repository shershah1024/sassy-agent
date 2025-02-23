from typing import List, Dict, Optional, Union, Literal
from pydantic import BaseModel, Field

class TextContent(BaseModel):
    content: str
    style: Optional[Literal['NORMAL', 'EMPHASIS', 'HIGHLIGHT']] = 'NORMAL'

class ImageGenerationPrompt(BaseModel):
    description: str = Field(..., description="Detailed description of the image to generate")
    style: Optional[Literal['REALISTIC', 'ARTISTIC', 'TECHNICAL', 'MINIMALIST']] = None
    size: Optional[Literal['SMALL', 'MEDIUM', 'LARGE']] = None
    placement: Optional[Literal['INLINE', 'FULL_WIDTH', 'SIDE']] = None
    caption: Optional[str] = None

class TableContent(BaseModel):
    headers: List[str]
    rows: List[List[str]]
    caption: Optional[str] = None

class ChartContent(BaseModel):
    type: Literal['LINE', 'BAR', 'PIE', 'SCATTER']
    data: Dict[str, List[float]]
    labels: List[str]
    title: str
    description: Optional[str] = None

class CodeBlockContent(BaseModel):
    code: str
    language: str
    caption: Optional[str] = None

class QuoteContent(BaseModel):
    text: str
    author: str
    source: Optional[str] = None
    year: Optional[str] = None

class Section(BaseModel):
    type: Literal[
        'EXECUTIVE_SUMMARY',
        'INTRODUCTION',
        'METHODOLOGY',
        'FINDINGS',
        'ANALYSIS',
        'CONCLUSION',
        'RECOMMENDATIONS',
        'APPENDIX'
    ]
    title: str
    content: List[Union[
        TextContent,
        ImageGenerationPrompt,
        TableContent,
        ChartContent,
        CodeBlockContent,
        QuoteContent
    ]]
    subsections: Optional[List['Section']] = None

class ReportMetadata(BaseModel):
    author: str
    date: str
    version: Optional[str] = None
    keywords: List[str]
    abstract: str

class InferredDetails(BaseModel):
    audience: str = Field(..., description="The inferred target audience based on the topic")
    purpose: str = Field(..., description="The inferred purpose of the report")
    key_findings: List[str] = Field(..., description="Key findings extracted and expanded from the topic")
    suggested_next_steps: List[str] = Field(..., description="Suggested next steps or actions based on the findings")

class Report(BaseModel):
    title: str
    style: Literal['ACADEMIC', 'BUSINESS', 'TECHNICAL', 'CREATIVE']
    sections: List[Section]
    metadata: ReportMetadata
    style_reasoning: str = Field(..., description="Explanation of why this style was chosen")
    content_flow: List[str] = Field(..., description="Description of how the report flows and why sections are ordered this way")
    inferred_details: InferredDetails

class ReportGenerationInput(BaseModel):
    topic: str 