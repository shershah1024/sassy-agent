import asyncio
import json
from datetime import datetime
from typing import Dict, Any
import pytest
from dotenv import load_dotenv
import os
from report_models import Report, ReportMetadata, Section, ImageGenerationPrompt
from document_services import DocumentService
from token_service import TokenService

# Load environment variables
load_dotenv()

def create_long_report_content() -> Dict[str, Any]:
    """Create a comprehensive long report structure for testing"""
    return {
        "sections": [
            {
                "heading": "Executive Summary",
                "content": """
                This comprehensive report examines the evolution and impact of artificial intelligence across multiple sectors,
                with a particular focus on recent developments in 2024. The analysis covers technical advancements,
                practical applications, ethical considerations, and future projections. Our findings indicate significant
                progress in several key areas, while also highlighting important challenges that need to be addressed.
                """
            },
            {
                "heading": "1. Introduction",
                "content": """
                Artificial Intelligence has become an integral part of modern society, transforming how we live, work,
                and interact. This report provides a detailed analysis of current AI technologies, their applications,
                and their implications for various sectors. We examine both the technical and societal aspects of AI
                development, offering insights into current trends and future possibilities.
                
                1.1 Scope of Analysis
                This report covers developments from 2020 to 2024, with a particular emphasis on breakthrough
                technologies and their practical implementations. We analyze data from multiple sources, including
                academic research, industry reports, and real-world case studies.
                
                1.2 Methodology
                Our analysis combines quantitative data analysis with qualitative assessments from industry experts.
                We conducted extensive literature reviews, interviewed key stakeholders, and analyzed market trends
                to provide a comprehensive picture of the AI landscape.
                """
            },
            {
                "heading": "2. Technical Advancements",
                "content": """
                2.1 Large Language Models
                Recent years have seen remarkable progress in large language models, with capabilities extending far
                beyond simple text generation. Key developments include:
                - Improved context understanding and reasoning
                - Enhanced multilingual capabilities
                - Better factual accuracy and reduced hallucinations
                - More efficient training and inference methods
                
                2.2 Computer Vision
                Computer vision technologies have achieved new milestones in:
                - Object detection and recognition
                - Real-time video analysis
                - Medical image processing
                - Autonomous vehicle navigation
                
                2.3 Reinforcement Learning
                Advances in reinforcement learning have led to:
                - More efficient training algorithms
                - Better generalization capabilities
                - Improved real-world application potential
                - Enhanced safety mechanisms
                """
            },
            {
                "heading": "3. Industry Applications",
                "content": """
                3.1 Healthcare
                AI has revolutionized healthcare through:
                - Advanced diagnostic tools
                - Drug discovery acceleration
                - Personalized treatment plans
                - Healthcare workflow optimization
                
                3.2 Finance
                The financial sector has seen significant transformation:
                - Automated trading systems
                - Fraud detection
                - Risk assessment
                - Personal finance management
                
                3.3 Manufacturing
                Industry 4.0 implementations include:
                - Predictive maintenance
                - Quality control automation
                - Supply chain optimization
                - Robot-human collaboration
                """
            },
            {
                "heading": "4. Ethical Considerations",
                "content": """
                4.1 Privacy Concerns
                As AI systems become more sophisticated, privacy considerations include:
                - Data collection and storage
                - User consent mechanisms
                - Information sharing protocols
                - Right to be forgotten
                
                4.2 Bias and Fairness
                Addressing bias in AI systems remains crucial:
                - Dataset representation
                - Algorithm fairness
                - Impact assessment
                - Mitigation strategies
                
                4.3 Transparency
                Ensuring AI transparency through:
                - Explainable AI methods
                - Decision-making visibility
                - Audit trails
                - User awareness
                """
            },
            {
                "heading": "5. Future Projections",
                "content": """
                5.1 Emerging Technologies
                Several promising technologies are on the horizon:
                - Quantum AI integration
                - Neuromorphic computing
                - Edge AI advancement
                - AI-human interfaces
                
                5.2 Market Trends
                Expected market developments include:
                - Industry consolidation
                - New application areas
                - Regulatory framework evolution
                - Investment patterns
                
                5.3 Societal Impact
                Long-term implications for society:
                - Workforce transformation
                - Educational requirements
                - Social interaction changes
                - Economic restructuring
                """
            },
            {
                "heading": "6. Recommendations",
                "content": """
                Based on our comprehensive analysis, we recommend:
                
                6.1 For Organizations
                - Develop clear AI adoption strategies
                - Invest in workforce training
                - Establish ethical guidelines
                - Monitor technological developments
                
                6.2 For Policymakers
                - Create balanced regulatory frameworks
                - Support research and development
                - Protect individual rights
                - Foster international cooperation
                
                6.3 For Individuals
                - Develop AI literacy
                - Stay informed about AI impacts
                - Participate in public discourse
                - Adapt to changing job markets
                """
            },
            {
                "heading": "7. Conclusion",
                "content": """
                The rapid advancement of AI technologies presents both opportunities and challenges. Success in
                navigating this landscape will require careful consideration of technical capabilities, ethical
                implications, and societal impacts. Continued collaboration between stakeholders, along with
                thoughtful governance frameworks, will be essential for realizing AI's potential while
                minimizing associated risks.
                """
            }
        ]
    }

@pytest.mark.asyncio
async def test_long_report_generation():
    """Test generating and creating a long, comprehensive report"""
    try:
        # Initialize token service
        token_service = TokenService()
        
        # Use the provided user ID
        user_id = "103206410753859569109"
        
        # Get valid token for the user
        token = await token_service.get_valid_token(user_id)
        if not token:
            pytest.skip("No valid token found for user")
        
        # Initialize document service with the token
        service = DocumentService(access_token=token)
        
        # Create report content
        content = create_long_report_content()
        title = "Comprehensive Analysis: The State of Artificial Intelligence in 2024"
        
        print("\nGenerating long report...")
        print(f"Title: {title}")
        print(f"Number of sections: {len(content['sections'])}")
        
        # Create the document
        doc_info = await service.create_report(title, content)
        assert doc_info["document_id"], "Document ID should be present"
        assert doc_info["url"], "Document URL should be present"
        
        document_id = doc_info["document_id"]
        print(f"\nDocument created successfully!")
        print(f"Document ID: {document_id}")
        print(f"URL: {doc_info['url']}")
        
        # Export as PDF
        print("\nExporting as PDF...")
        pdf_content = await service.export_document(document_id, "pdf")
        assert pdf_content, "PDF content should not be empty"
        
        # Save PDF for verification
        pdf_filename = "long_report_test.pdf"
        with open(pdf_filename, "wb") as f:
            f.write(pdf_content)
        print(f"PDF saved as '{pdf_filename}'")
        
        # Export as DOCX
        print("\nExporting as DOCX...")
        docx_content = await service.export_document(document_id, "docx")
        assert docx_content, "DOCX content should not be empty"
        
        # Save DOCX for verification
        docx_filename = "long_report_test.docx"
        with open(docx_filename, "wb") as f:
            f.write(docx_content)
        print(f"DOCX saved as '{docx_filename}'")
        
        # Clean up (optional - comment out if you want to keep the document)
        # print("\nCleaning up...")
        # await service.delete_document(document_id)
        # print("Test document deleted")
        
    except Exception as e:
        pytest.fail(f"Test failed with error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_long_report_generation()) 