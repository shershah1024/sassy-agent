from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from openai_utils import structured_openai_completion

class ImagePrompt(BaseModel):
    """Model for image generation prompts"""
    description: str = Field(..., description="Description of the image to be generated")
    style: Optional[str] = Field(None, description="Style of the image (e.g., 'realistic', 'cartoon', etc.)")

class ReportSection(BaseModel):
    """Model for a section within the report"""
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Main content of the section")
    image_prompts: Optional[List[ImagePrompt]] = Field(
        default=None,
        description="List of image prompts to generate visuals for this section"
    )
    subsections: Optional[List['ReportSection']] = Field(
        default=None,
        description="Nested subsections within this section"
    )

class Report(BaseModel):
    """Model for the complete report structure"""
    executive_summary: str = Field(..., description="Executive summary of the report")
    sections: List[ReportSection] = Field(..., description="List of report sections")
    references: Optional[List[str]] = Field(
        default=None,
        description="List of references used in the report"
    )

def test_report_generation():
    """Test the structured report generation"""
    try:
        # Test input
        test_topic = "The Impact of Artificial Intelligence on Healthcare"
        test_content = """
        Analyze how AI is transforming healthcare delivery, diagnosis, and treatment. 
        Include current applications, challenges, and future potential. 
        Consider both technical and ethical aspects, as well as impact on healthcare professionals and patients.
        """

        instructions = """You are a professional report writer and analyst. Generate a comprehensive report structure with:
        1. Relevant sections based on the topic
        2. Detailed content for each section
        3. Appropriate subsections where needed
        4. Image suggestions to visualize key points
        5. An executive summary
        6. Relevant references
        Make the report thorough and well-structured."""

        print("Generating report content...")
        print(f"\nTopic: {test_topic}")
        print(f"Content: {test_content}")

        # Generate the report using structured output
        report = structured_openai_completion(
            instructions=instructions,
            original_content=f"Generate a complete report structure for topic: '{test_topic}'. Context: {test_content}",
            response_model=Report,
            max_tokens=5000,
            temperature=0.7
        )

        # Print the results
        print("\nGenerated Report Structure:")
        print("==========================")
        
        print("\nExecutive Summary:")
        print("-----------------")
        print(report.executive_summary)
        
        print("\nSections:")
        print("---------")
        for i, section in enumerate(report.sections, 1):
            print(f"\n{i}. {section.title}")
            print("Content:", section.content[:200] + "..." if len(section.content) > 200 else section.content)
            
            if section.image_prompts:
                print("\nImage Prompts:")
                for prompt in section.image_prompts:
                    print(f"- {prompt.description} (Style: {prompt.style or 'default'})")
            
            if section.subsections:
                print("\nSubsections:")
                for j, subsection in enumerate(section.subsections, 1):
                    print(f"{i}.{j}. {subsection.title}")
                    print(f"Content: {subsection.content[:100]}...")
        
        if report.references:
            print("\nReferences:")
            print("-----------")
            for ref in report.references:
                print(f"- {ref}")

    except Exception as e:
        print(f"Error during testing: {str(e)}")
        raise

if __name__ == "__main__":
    test_report_generation() 