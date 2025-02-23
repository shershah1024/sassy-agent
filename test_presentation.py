import asyncio
import logging
from google_api_wrapper import create_presentation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test():
    instructions = '''Modern Web Development Best Practices

Create an informative presentation covering:
- Latest frontend frameworks and tools
- Backend architecture patterns
- DevOps and CI/CD practices
- Performance optimization techniques
- Security best practices
- Mobile-first design principles
- Future trends and predictions'''
    
    # Test with explicit TECH theme
    user_id = '107085158246892440905'
    logger.info("Creating presentation with TECH theme...")
    result = await create_presentation(user_id, instructions)
    logger.info(f'Presentation created and accessible at: {result}')

if __name__ == '__main__':
    asyncio.run(test()) 