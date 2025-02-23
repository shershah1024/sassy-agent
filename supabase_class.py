import os
import json
import base64
import asyncio
import logging
from typing import List, Dict, Optional, Any, NamedTuple
from dotenv import load_dotenv
import httpx
from calculate_cost import calculate_cost  # Assuming this module exists
from pydantic import BaseModel


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Chapter(BaseModel):
    chapter_id: str
    chapter_title: str
    chapterDescription: str
    chapterImageDescription: str
    chapterOutline: Dict
    chapter_image: Optional[str]

class CourseOutline(BaseModel):
    course_title: str
    course_image_description: str
    course_image: Optional[str]
    chapters: List[Chapter]

class TranslatedChapter(BaseModel):
    chapter_id: str
    chapter_title: str
    chapterDescription: str    
    chapterOutline: Dict
    

class TranslatedCourseOutline(BaseModel):
    course_title: str
    chapters: List[TranslatedChapter]

class SourceTerm(NamedTuple):
    term: str
    explanation: str




class SupabaseCourseManager:
    def __init__(self):
        load_dotenv()
        self.supabase_url: Optional[str] = os.getenv("SUPABASE_URL")
        self.supabase_key: Optional[str] = os.getenv("SUPABASE_KEY")
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables.")

        # Ensure the Supabase URL does not have a trailing slash
        self.supabase_url = self.supabase_url.rstrip('/')

        self.headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(
            base_url=self.supabase_url,
            headers=self.headers,
            timeout=120.0  # Increase timeout to 120 seconds
        )

    async def close(self):
        """Close the httpx client session."""
        await self.client.aclose()

    async def fetch_combined_text_content(self, course_id: str) -> str:
        """
        Fetches and combines text_content from the course_files table for a given course_id.
        """
        try:
            logger.info(f"Fetching content for course_id: {course_id}")
            url = f"/rest/v1/course_files"
            params = {
                "course_id": f"eq.{course_id}",
                "select": "text_content",
            }
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                raise Exception("No data returned from Supabase for course_files.")

            combined_text = "\n\n".join(
                row["text_content"] for row in data if row.get("text_content")
            ).strip()

            logger.info(f"Combined text length: {len(combined_text)}")
            return combined_text

        except Exception as e:
            logger.error(f"An error occurred in fetch_combined_text_content: {str(e)}")
            raise

    async def fetch_combined_text_content_quiz(self, quiz_id: str) -> str:
        """
        Fetches and combines extracted_content from the quiz_files table for a given quiz_id.
        """
        try:
            logger.info(f"Fetching content for quiz_id: {quiz_id}")
            url = f"/rest/v1/quiz_file_data"
            params = {
                "quiz_id": f"eq.{quiz_id}",
                "select": "extracted_content",
            }
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                raise Exception("No data returned from Supabase for course_files.")

            combined_text = "\n\n".join(
                row["extracted_content"] for row in data if row.get("extracted_content")
            ).strip()

            logger.info(f"Combined text length: {len(combined_text)}")
            return combined_text

        except Exception as e:
            logger.error(f"An error occurred in fetch_combined_text_content: {str(e)}")
            raise


    async def upload_image_to_supabase_get_public_url(self, image_data: bytes, file_name: str) -> str:
        """
        Uploads an image to Supabase storage and returns the public URL.
        """
        try:
            bucket_name = "chapter_images"
            file_path = f"{bucket_name}/{file_name}"
            url = f"/storage/v1/object/{file_path}"

            # Remove 'Content-Type' from headers for file upload
            headers = self.headers.copy()
            headers.pop("Content-Type", None)
            headers["Content-Type"] = "image/png"  # Set the correct content type for PNG images

            response = await self.client.post(url, content=image_data, headers=headers)
            response.raise_for_status()

            # Construct the public URL
            public_url = f"{self.supabase_url}/storage/v1/object/public/{bucket_name}/{file_name}"

            return public_url

        except Exception as e:
            logger.error(f"An error occurred in upload_image_to_supabase_get_public_url: {str(e)}")
            raise

    async def upload_course_data(self, course_data: Dict, course_id: str) -> None:
        """
        Uploads course data to the courses and chapters tables.
        """
        try:
            # Insert or update course data
            url_courses = "/rest/v1/courses"
            data_courses = {
                "course_id": course_id,
                "course_title": course_data["course_title"],
                "course_image_description": course_data["course_image_description"],
                "course_image": course_data["course_image"]
            }
            params_courses = {"on_conflict": "course_id"}

            response_courses = await self.client.post(
                url_courses,
                json=data_courses,
                params=params_courses
            )
            response_courses.raise_for_status()

            # Insert or update chapter data
            url_chapters = "/rest/v1/chapters"
            chapter_tasks = []
            for chapter in course_data["chapters"]:
                chapter_data = {
                    "course_id": course_id,
                    "chapter_id": chapter["chapter_id"],
                    "chapter_title": chapter["chapter_title"],
                    "chapter_description": chapter["chapterDescription"],
                    "chapter_image_description": chapter["chapterImageDescription"],
                    "chapter_outline": json.dumps(chapter["chapterOutline"]),
                }
                params_chapters = {"on_conflict": "chapter_id"}
                chapter_tasks.append(
                    self.client.post(
                        url_chapters,
                        json=chapter_data,
                        params=params_chapters
                    )
                )

            # Wait for all chapter insertions to complete
            chapter_responses = await asyncio.gather(*chapter_tasks)
            for response in chapter_responses:
                response.raise_for_status()

            logger.info("Course data upload completed.")

        except Exception as e:
            logger.error(f"An error occurred while uploading course data: {str(e)}")
            raise

    async def upload_slide_data_for_chapter(
        self,
        slide_type: str,
        slide_data: Dict,
        chapter_id: str,
        slide_number: int,
        slide_image_description: Optional[str],
        image_source: Optional[str],  # Uncommented parameter
    ) -> None:
        """
        Uploads the slide data to the slides table.
        """
        try:
            url = "/rest/v1/chapter_slides"
            data = {
                "slide_type": slide_type,
                "slide_data": json.dumps(slide_data),
                "chapter_id": chapter_id,
                "slide_number": slide_number,
                "slide_image_description": slide_image_description,
                "image_source": image_source,  # Added field
            }
            response = await self.client.post(url, json=data)
            response.raise_for_status()

        except Exception as e:
            logger.error(f"An error occurred while uploading slide data: {str(e)}")
            raise

    
    async def upload_presentation_outline_for_chapter(self, chapter_id: str, presentation_outline: Dict) -> None:
        """
        Uploads the presentation outline for a given chapter_id.
        """
        try:
            url = "/rest/v1/chapters"
            params = {
                "chapter_id": f"eq.{chapter_id}",
            }
            data = {
                "presentation_outline": json.dumps(presentation_outline),
            }
            response = await self.client.patch(url, json=data, params=params)
            response.raise_for_status()

        except Exception as e:
            logger.error(f"An error occurred while uploading presentation outline: {str(e)}")
            raise

    async def fetch_chapter_ids_for_course(self, course_id: str) -> List[str]:
        """
        Fetch all the chapter_id values from the chapters table that match the given course_id.
        """
        try:
            url = "/rest/v1/chapters"
            params = {
                "course_id": f"eq.{course_id}",
                "select": "chapter_id",
            }
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                raise Exception("No data returned from Supabase for chapters.")

            return [row["chapter_id"] for row in data]

        except Exception as e:
            logger.error(f"An error occurred while fetching chapter IDs: {str(e)}")
            raise

    async def upload_to_supabase(self, base64_image: str, file_name: str) -> str:
        """
        Uploads an image to Supabase storage and returns the public URL.
        """
        logger.info(f"Attempting to upload image {file_name} to Supabase...")
        if not base64_image:
            raise ValueError("Base64 image data is undefined or empty")

        image_data = base64.b64decode(base64_image)
        try:
            bucket_name = "chapter_images"
            file_path = f"{bucket_name}/{file_name}"
            url = f"/storage/v1/object/{file_path}"

            # Remove 'Content-Type' from headers for file upload
            headers = self.headers.copy()
            headers.pop("Content-Type", None)
            headers["Content-Type"] = "image/png"

            response = await self.client.post(url, content=image_data, headers=headers, timeout=30.0)
            response.raise_for_status()

            # Construct the public URL
            public_url = f"{self.supabase_url}/storage/v1/object/public/{bucket_name}/{file_name}"

            logger.info(f"Successfully uploaded image {file_name} to Supabase.")
            return public_url

        except Exception as e:
            logger.error(f"Error uploading to Supabase: {str(e)}")
            raise

    async def upload_cost_calculation(
        self,
        input_tokens: int,
        output_tokens: int,
        chapter_id: Optional[str],
        course_id: Optional[str],
        model: str,
        purpose: str
    ) -> None:
        """
        Uploads cost calculation data to the cost_calculation table.
        """
        try:
            # Fetch user_email from the chapters table based on the chapter_id
            email_id = "default@example.com"
            if chapter_id:
                url = "/rest/v1/chapters"
                params = {
                    "chapter_id": f"eq.{chapter_id}",
                    "select": "user_email",
                }
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                if data:
                    email_id = data[0]["user_email"]

            input_cost, output_cost, total_cost = calculate_cost(
                input_tokens, output_tokens, model)

            # Insert the data into the cost_calculation table
            url_cost = "/rest/v1/cost_calculation"
            cost_data = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "chapter_id": chapter_id,
                "course_id": course_id,
                "user_email": email_id,
                "model": model,
                "input_cost": input_cost,
                "output_cost": output_cost,
                "total_cost": total_cost,
                "purpose": purpose
            }
            response = await self.client.post(url_cost, json=cost_data)
            response.raise_for_status()

        except Exception as e:
            logger.error(f"An error occurred in upload_cost_calculation: {str(e)}")
            raise

    
    async def upload_audio_to_supabase_get_public_url(self, audio_data: bytes, file_name: str) -> str:
        """
        Uploads audio data to Supabase storage and returns the public URL.
        """
        try:
            bucket_name = "course_audio"
            file_path = f"{bucket_name}/{file_name}"
            url = f"/storage/v1/object/{file_path}"

            # Remove 'Content-Type' from headers for file upload
            headers = self.headers.copy()
            headers.pop("Content-Type", None)
            headers["Content-Type"] = "audio/mpeg"  # Adjust content type as needed

            response = await self.client.post(url, content=audio_data, headers=headers, timeout=30.0)
            response.raise_for_status()

            # Construct the public URL
            public_url = f"{self.supabase_url}/storage/v1/object/public/{bucket_name}/{file_name}"

            return public_url

        except Exception as e:
            logger.error(f"An error occurred while uploading audio: {str(e)}")
            raise

    async def save_lesson_text_to_supabase_course(self, lesson_text: str, lesson_text_title: str, course_id: str, terms: Any, chapter_id: Optional[str], user_email: Optional[str]) -> bool:
        """
        Saves the lessonText to the lesson_texts table and vocabulary to the lesson_text_vocabulary table in Supabase with the matching chapter_id.
        """
        try:
            # Save lesson text
            lesson_text_url = "/rest/v1/lesson_texts"
            lesson_text_data = {
                "lesson_text": lesson_text,
                "lesson_text_title": lesson_text_title,
                "user_email": user_email,
                "chapter_id": chapter_id,
                "course_id": course_id,
            }
            
            lesson_text_response = await self.client.post(lesson_text_url, json=lesson_text_data)
            lesson_text_response.raise_for_status()

            # Save vocabulary
            vocabulary_url = "/rest/v1/lesson_text_vocabulary"
            vocabulary_tasks = []

            for term in terms.words:
                vocabulary_data = {
                    "chapter_id": chapter_id,
                    "term": term.term,
                    "definition": term.explanation
                }
                vocabulary_tasks.append(self.client.post(vocabulary_url, json=vocabulary_data))

            # Execute all vocabulary insert tasks concurrently
            vocabulary_responses = await asyncio.gather(*vocabulary_tasks, return_exceptions=True)

            # Check if all inserts were successful
            all_successful = all(not isinstance(response, Exception) for response in vocabulary_responses)

            if all_successful:
                logger.info(f"Successfully saved lesson text and vocabulary for chapter_id: {chapter_id}")
                return True
            else:
                logger.warning(f"Some vocabulary inserts failed for chapter_id: {chapter_id}")
                return False

        except Exception as e:
            logger.error(f"An error occurred in save_lesson_text_to_supabase_course: {str(e)}")
            raise


    async def save_lesson_text_to_supabase_quiz(self, lesson_text: str, lesson_title: str, quiz_id: Optional[str], user_email: Optional[str]) -> bool:
        """
        Saves the lessonText to the lesson_texts table in Supabase with the matching quiz_id.
        """
        try:
            # Save lesson text
            lesson_text_url = "/rest/v1/lesson_texts"
            lesson_text_data = {
                "lesson_text": lesson_text,
                "lesson_title": lesson_title,
                "user_email": user_email,
                "quiz_id": quiz_id,
            }
            
            lesson_text_response = await self.client.post(lesson_text_url, json=lesson_text_data)
            lesson_text_response.raise_for_status()

            logger.info(f"Successfully saved lesson text for quiz_id: {quiz_id}")
            return True

        except Exception as e:
            logger.error(f"An error occurred in save_lesson_text_to_supabase_quiz: {str(e)}")
            raise


    async def save_lesson_text_to_supabase_course_lesson(self, lesson_text: str, lesson_text_title: str, terms: Any, chapter_id: Optional[str], user_email: Optional[str]) -> bool:
            """
            Saves the lessonText to the lesson_texts table and vocabulary to the lesson_text_vocabulary table in Supabase with the matching quiz_id.
            """
            try:
                # Save lesson text
                lesson_text_url = "/rest/v1/lesson_texts"
                lesson_text_data = {
                    "lesson_text": lesson_text,
                    "lesson_text_title": lesson_text_title,
                    "user_email": user_email,
                    "chapter_id": chapter_id,
                }
                
                lesson_text_response = await self.client.post(lesson_text_url, json=lesson_text_data)
                lesson_text_response.raise_for_status()

                # Save vocabulary
                vocabulary_url = "/rest/v1/lesson_text_vocabulary"
                vocabulary_tasks = []

                for term in terms.words:
                    vocabulary_data = {
                        "chapter_id": chapter_id,
                        "term": term.term,
                        "definition": term.explanation
                    }
                    vocabulary_tasks.append(self.client.post(vocabulary_url, json=vocabulary_data))

                # Execute all vocabulary insert tasks concurrently
                vocabulary_responses = await asyncio.gather(*vocabulary_tasks, return_exceptions=True)

                # Check if all inserts were successful
                all_successful = all(not isinstance(response, Exception) for response in vocabulary_responses)

                if all_successful:
                    logger.info(f"Successfully saved lesson text and vocabulary for chapter_id: {chapter_id}")
                    return True
                else:
                    logger.warning(f"Some vocabulary inserts failed for chapter_id: {chapter_id}")
                    return False

            except Exception as e:
                logger.error(f"An error occurred in save_lesson_text_to_supabase_quiz: {str(e)}")
                raise

    async def save_lesson_text_terms_to_supabase_course_lesson(self, chapter_id: str, term_data: dict) -> bool:
        """
        Saves a single vocabulary term to the lesson_text_vocabulary table for a chapter.

        :param chapter_id: The ID of the chapter.
        :param term_data: Dictionary containing 'term' and 'explanation' keys.
        :return: True if the save was successful, False otherwise.
        """
        try:
            url = "/rest/v1/lesson_text_vocabulary"
            data = {
                "chapter_id": chapter_id,
                "term": term_data["term"],
                "definition": term_data["explanation"]
            }
            
            response = await self.client.post(url, json=data)
            response.raise_for_status()

            logger.info(f"Successfully saved term '{term_data['term']}' for chapter_id: {chapter_id}")
            return True

        except Exception as e:
            logger.error(f"An error occurred in save_lesson_text_terms_to_supabase_course_lesson: {str(e)}")
            return False







    async def update_lesson_text_terms_course(self, chapter_id: str, terms: List[SourceTerm]) -> bool:
        """
        Updates the terms in the lesson_texts table for a specific chapter.

        :param chapter_id: The ID of the chapter.
        :param terms: A list of SourceTerm objects.
        :return: True if the update was successful, False otherwise.
        """
        try:
            if not chapter_id:
                raise ValueError("chapter_id must be provided")

            url = "/rest/v1/lesson_texts_vocabulary"
            params = {
                "chapter_id": f"eq.{chapter_id}"
            }
            
            # Convert SourceTerm objects to a dictionary
            terms_dict = {term.term: term.explanation for term in terms}
            
            data = {
                "terms": json.dumps(terms_dict)  # Convert the dictionary to a JSON string
            }
            
            response = await self.client.patch(url, params=params, json=data)
            response.raise_for_status()

            if response.status_code == 204:  # Successful update returns 204 No Content
                logger.info(f"Successfully updated terms for chapter_id: {chapter_id}")
                return True
            else:
                logger.warning(f"Unexpected status code {response.status_code} when updating terms")
                return False

        except Exception as e:
            logger.error(f"An error occurred in update_lesson_text_terms_course: {str(e)}")
            return False





    async def save_question_to_supabase(self, chapter_id: str, question_data: Dict) -> bool:
        """
        Saves the question data to the quiz_questions table.
        """
        try:
            url = "/rest/v1/quiz_questions"
            data = {
                "chapter_id": chapter_id,
                "question": question_data,
            }
            response = await self.client.post(url, json=data)
            response.raise_for_status()

            return True

        except Exception as e:
            logger.error(f"An error occurred while saving the question: {str(e)}")
            raise

    async def save_course_outline_to_supabase(self, course_id: str, course_title: str, course_description: str, course_image_description: str, course_image: str, user: str) -> bool:
        try:
            url_courses = "/rest/v1/courses"
            course_data = {
                "course_id": course_id,
                "course_title": course_title,
                "course_description": course_description,
                "course_image_description": course_image_description,
                "course_image": course_image,
                "user": user
            }

            response_courses = await self.client.post(
                url_courses,
                json=course_data,
                timeout=30.0
            )
            response_courses.raise_for_status()

            logger.info("Successfully saved course data to Supabase.")
            return True
        except Exception as e:
            logger.error(f"An error occurred while saving course outline: {str(e)}")
            raise

    async def save_chapter_outlines_to_supabase(self, course_id: str, course_title: str, chapters: List[Dict]) -> bool:
        try:
            url_chapters = "/rest/v1/chapters"
            chapter_tasks = []
            for idx, chapter in enumerate(chapters, start=1):
                chapter_data = {
                    "course_id": course_id,
                    "chapter_id": f"{course_id}_chapter_{idx}",
                    "course_title": course_title,
                    "chapter_title": chapter['title'],
                    "chapter_description": chapter['description'],
                    "chapter_image_description": chapter['image_description'],
                    "content": chapter['content'],
                    "detailled_context": chapter['detailled_context'],
                    "code_snippet": json.dumps(chapter.get('code_snippets', [])),
                    "data_points": json.dumps(chapter.get('data_points', [])),
                    "chapter_image": chapter.get('chapter_image', ''),
                }
                
                chapter_tasks.append(
                    self.client.post(
                        url_chapters,
                        json=chapter_data,
                    )
                )

            chapter_responses = await asyncio.gather(*chapter_tasks)
            for response in chapter_responses:
                response.raise_for_status()

            logger.info("Successfully saved chapter data to Supabase.")
            return True
        except Exception as e:
            logger.error(f"An error occurred while saving chapter outlines: {str(e)}")
            raise
        
    
    async def save_color_theme_to_chapters_table(self, color_theme: Dict, chapter_id: str) -> bool:
        """
        Updates the color_theme field in the chapters table for the given chapter_id.
        """
        try:
            url = "/rest/v1/chapters"
            params = {
                "chapter_id": f"eq.{chapter_id}",
            }
            data = {
                "theme": json.dumps(color_theme),
            }
            response = await self.client.patch(url, json=data, params=params)
            response.raise_for_status()

            return True

        except Exception as e:
            logger.error(f"An error occurred in save_color_theme_to_chapters_table: {str(e)}")
            raise

    async def add_color_theme_to_chapter_slides(self, color_theme: Dict, chapter_id: str) -> bool:
        """
        Updates the theme field in the chapter_slides table for all slides of a chapter.
        """
        try:
            logger.info(f"Starting to add color theme to chapter slides for chapter_id: {chapter_id}")
            url = "/rest/v1/chapter_slides"
            params = {
                "chapter_id": f"eq.{chapter_id}",
            }
            data = {
                "theme": json.dumps(color_theme),
            }
            response = await self.client.patch(url, json=data, params=params)
            response.raise_for_status()

            logger.info(f"Successfully updated color theme for chapter_id: {chapter_id}")
            return True

        except Exception as e:
            logger.error(f"An error occurred in add_color_theme_to_chapter_slides: {str(e)}")
            raise

    async def fetch_quiz_data_for_quiz_id(self, quiz_id: str) -> str:
        """
        Fetches and combines extracted_content from the quiz_files table for a given quiz_id.
        """
        try:
            url = "/rest/v1/quiz_file_data"
            params = {
                "quiz_id": f"eq.{quiz_id}",
                "select": "extracted_content"
            }
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                raise Exception("No data returned from Supabase for quiz_files.")

            combined_text = "\n\n".join(
                row["extracted_content"] for row in data if row.get("extracted_content")
            ).strip()

            return combined_text

        except Exception as e:
            logger.error(f"An error occurred in fetch_quiz_data_for_quiz_id: {str(e)}")
            raise

    async def save_quiz_questions_quiz_generator(self, quiz_id: str, questions: List[Dict]) -> None:
        """
        Saves quiz questions to the quiz_data table for a specific quiz.
        """
        try:
            url = "/rest/v1/quiz_data"
            question_tasks = []
            for idx, question in enumerate(questions):
                question_record = {
                    "quiz_id": quiz_id,
                    "question": question,
                    "question_number": idx + 1
                }
                question_tasks.append(
                    self.client.post(url, json=question_record)
                )

            # Wait for all insertions to complete
            responses = await asyncio.gather(*question_tasks)
            for response in responses:
                response.raise_for_status()

            logger.info("Questions saved successfully.")

        except Exception as e:
            logger.error(f"An error occurred while saving quiz questions: {str(e)}")
            raise

    
    async def save_audio_cost_to_supabase(self, chapter_id: str, characters: int, model: str) -> bool:
        """
        Saves the audio cost to the audio_costs table for a specific chapter.
        """
        try:
            cost_per_character = 0.000015 if model == 'openai' else 0
            total_cost = characters * cost_per_character

            url = "/rest/v1/audio_costs"
            data = {
                "chapter_id": chapter_id,
                "characters": characters,
                "cost": total_cost,
                "model": model
            }
            response = await self.client.post(url, json=data)
            response.raise_for_status()

            return True

        except Exception as e:
            logger.error(f"An error occurred in save_audio_cost_to_supabase: {str(e)}")
            raise

    async def save_quiz_questions(self, chapter_id: str, questions: List[Dict]) -> bool:
        """
        Saves multiple quiz questions for a chapter to the quiz_questions table.
        """
        try:
            url = "/rest/v1/quiz_questions"
            question_records = [
                {"chapter_id": chapter_id, "question": question}
                for question in questions
            ]
            response = await self.client.post(url, json=question_records)
            response.raise_for_status()

            await self.mark_quiz_questions_status_complete(chapter_id=chapter_id)
            return True

        except Exception as e:
            logger.error(f"An error occurred while saving the questions: {str(e)}")
            raise

    async def mark_quiz_questions_status_complete(self, chapter_id: str) -> bool:
        """
        Marks the quiz_status as complete for a chapter in the chapters table.
        """
        try:
            url = "/rest/v1/chapters"
            params = {
                "chapter_id": f"eq.{chapter_id}",
            }
            data = {
                "quiz_status": "complete",
            }
            response = await self.client.patch(url, json=data, params=params)
            response.raise_for_status()

            logger.info(f"Successfully marked quiz status as complete for chapter {chapter_id}")
            return True

        except Exception as e:
            logger.error(f"An error occurred while updating quiz status: {str(e)}")
            raise

    async def mark_slides_status_complete(self, chapter_id: str) -> bool:
        """
        Marks the slides_status as complete for a chapter in the chapters table.
        """
        try:
            url = "/rest/v1/chapters"
            params = {
                "chapter_id": f"eq.{chapter_id}",
            }
            data = {
                "slides_status": "complete",
            }
            response = await self.client.patch(url, json=data, params=params)
            response.raise_for_status()

            logger.info(f"Successfully marked slides status as complete for chapter {chapter_id}")
            return True

        except Exception as e:
            logger.error(f"An error occurred while updating slides status: {str(e)}")
            raise

    async def mark_slides_as_ready(self, chapter_id: str) -> bool:
        """
        Marks the slides_status as ready for a chapter in the chapters table.
        """
        try:
            url = "/rest/v1/chapters"
            params = {
                "chapter_id": f"eq.{chapter_id}",
            }
            data = {
                "slides_status": "ready",
            }
            response = await self.client.patch(url, json=data, params=params)
            response.raise_for_status()

            logger.info(f"Successfully marked slides status as ready for chapter {chapter_id}")
            return True

        except Exception as e:
            logger.error(f"An error occurred while updating slides status: {str(e)}")
            raise

    async def fetch_course_languages(self, course_id: str) -> List[Dict[str, Any]]:
        try:
            url = "/rest/v1/course_languages"
            params = {
                "course_id": f"eq.{course_id}",
                "select": "language",
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return data
        except Exception as e:
            logging.error(f"An error occurred in fetch_course_languages: {str(e)}")
            return []

    async def fetch_quiz_languages(self, quiz_id: str) -> List[Dict[str, Any]]:
        try:
            url = "/rest/v1/quiz_languages"
            params = {
                "quiz_id": f"eq.{quiz_id}",
                "select": "language,explainer_language",
            }
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            return data
        except Exception as e:
            logging.error(f"An error occurred in fetch_quiz_languages: {str(e)}")
            return []

    

    async def fetch_chapters_for_course(self, course_id: str) -> List[Dict[str, Any]]:
        try:
            url = "/rest/v1/chapters"
            params = {
                "course_id": f"eq.{course_id}",
                "select": "chapter_id,lesson_text",
            }
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching chapters for course {course_id}: {str(e)}")
            raise

    

    async def save_quiz_course(self, chapter_id: str, course_id: str, quiz_data: dict):
        try:
            for question in quiz_data['questions']:
                url = "/rest/v1/quiz_questions"
                
                data = {
                    "chapter_id": chapter_id,
                    "course_id": course_id,
                    "question": json.dumps(question),  # Save as JSON string instead of encoding
                }
                
                response = await self.client.post(url, json=data)
                response.raise_for_status()
            
            logging.info(f"Successfully saved quiz for chapter {chapter_id}")
        except Exception as e:
            print(f"Error in save_quiz: {e}")
            print(f"Attempted to save with: chapter_id={chapter_id}")
            print(f"Quiz data: {quiz_data}")
            raise  # Re-raise the exception for the caller to handle

    async def save_quiz_quiz(self, quiz_id: str, quiz_data: dict):
        try:
            for question in quiz_data['questions']:
                url = "/rest/v1/quiz_questions"
                
                data = {
                    "quiz_id": quiz_id,
                    "question": json.dumps(question),  # Save as JSON string instead of encoding
                }
                
                response = await self.client.post(url, json=data)
                response.raise_for_status()
            
            logging.info(f"Successfully saved quiz for quiz_id {quiz_id}")
        except Exception as e:
            print(f"Error in save_quiz_quiz: {e}")
            print(f"Attempted to save with: chapter_id={quiz_id}")
            print(f"Quiz data: {quiz_data}")
            raise  # Re-raise the exception for the caller to handle


    async def save_quiz_assignment(self, assignment_id: str, quiz_data: dict):
        try:
            for question in quiz_data['questions']:
                url = "/rest/v1/quiz_questions"
                
                data = {
                    "assignment_id": assignment_id,
                    "question": json.dumps(question),  # Save as JSON string instead of encoding
                }
                
                response = await self.client.post(url, json=data)
                response.raise_for_status()
            
            logging.info(f"Successfully saved quiz for assignment_id {assignment_id}")
        except Exception as e:
            print(f"Error in save_quiz_assignment: {e}")
            print(f"Attempted to save with: assignment_id={assignment_id}")
            print(f"Quiz data: {quiz_data}")
            raise  # Re-raise the exception for the caller to handle

    
    
    async def mark_lesson_text_status_complete(self, chapter_id: str):
        try:
            url = "/rest/v1/chapters"
            params = {
                "chapter_id": f"eq.{chapter_id}",
                "select": "lesson_text_status",
            }
            data = {
                "lesson_text_status": "complete"
            }
            response = await self.client.patch(url, json=data, params=params)
            response.raise_for_status()
        except Exception as e:
            logger.error(f"An error occurred in mark_lesson_text_status_complete: {str(e)}")
            raise

    async def fetch_chapter_data_for_chapter_id(self, chapter_id: str) -> Dict[str, Any]:
        try:
            url = "/rest/v1/chapters"
            params = {"chapter_id": f"eq.{chapter_id}", "select": "chapter_title,chapter_description,content,detailled_context"}
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            print(f"response: {response.json()}")
            return response.json()
        except Exception as e:
            logger.error(f"An error occurred in fetch_chapter_data_for_chapter_id: {str(e)}")
            raise

    async def update_image_url_in_chapters_table(self, chapter_id: str, image_url: str) -> bool:
        try:
            url = "/rest/v1/chapters"
            params = {"chapter_id": f"eq.{chapter_id}"}
            data = {"chapter_image": image_url}
            response = await self.client.patch(url, json=data, params=params)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"An error occurred in update_image_url_in_chapters_table: {str(e)}")
            raise

    async def insert_course_data(self, course_outline: CourseOutline, course_id: str) -> None:
        try:
            # Prepare data for courses and chapters
            chapters_data = [
                {
                    "course_id": course_id,
                    "chapter_id": f"{course_id}_chapter_{idx + 1}",
                    "chapter_title": chapter.chapter_title,
                    "chapter_description": chapter.chapter_description,
                    "chapter_image_description": chapter.chapter_image_description,
                    "bullet_points": json.dumps(chapter.bullet_points),
                    "video_script": chapter.video_script,
                    "lesson_text": chapter.lesson_text
                }
                for idx, chapter in enumerate(course_outline.chapters)
            ]

            rpc_data = {
                "p_course_id": course_id,
                "p_course_title": course_outline.course_title,
                "p_course_description": course_outline.course_description,
                "p_course_image_description": course_outline.course_image_description,
                "p_chapters": chapters_data
            }

            # Call the RPC function to insert all data
            url = f"{self.supabase_url}/rest/v1/rpc/insert_course_data_3"
            response = await self.client.post(url, json=rpc_data)
            response.raise_for_status()

            logger.info(f"Successfully inserted course data for course_id: {course_id}")

        except httpx.HTTPStatusError as e:
            error_info = f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
            logger.error(f"An error occurred in insert_course_data for course_id {course_id}: {error_info}")
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred in insert_course_data for course_id {course_id}: {str(e)}")
            raise

    async def download_and_upload_video(self, download_url: str, video_id: str) -> str:
        """
        Downloads a video from the given URL and uploads it to Supabase storage.
        Returns the public URL of the uploaded video.
        """
        try:
            # Download the video
            async with httpx.AsyncClient() as client:
                response = await client.get(download_url)
                response.raise_for_status()
                video_data = response.content

            # Upload to Supabase
            bucket_name = "course_videos"
            file_name = f"{video_id}.mp4"
            file_path = f"{bucket_name}/{file_name}"
            url = f"/storage/v1/object/{file_path}"

            headers = self.headers.copy()
            headers.pop("Content-Type", None)
            headers["Content-Type"] = "video/mp4"

            upload_response = await self.client.post(url, content=video_data, headers=headers)
            upload_response.raise_for_status()

            # Construct the public URL
            public_url = f"{self.supabase_url}/storage/v1/object/public/{file_path}"

            return public_url

        except Exception as e:
            logger.error(f"An error occurred while downloading and uploading video: {str(e)}")
            raise

    async def fetch_course_image_description(self, course_id: str) -> str:
        """
        Fetches the course_image_description from the courses table for a given course_id.
        """
        try:
            url = "/rest/v1/courses"
            params = {
                "course_id": f"eq.{course_id}",
                "select": "course_image_description",
            }
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                raise Exception(f"No data found for course_id: {course_id}")

            return data[0]["course_image_description"]

        except Exception as e:
            logger.error(f"An error occurred in fetch_course_image_description: {str(e)}")
            raise

    async def update_course_image(self, course_id: str, course_image_url: str) -> bool:
        """
        Updates the course_image field in the courses table for a given course_id.
        """
        try:
            url = "/rest/v1/courses"
            params = {
                "course_id": f"eq.{course_id}",
            }
            data = {
                "course_image": course_image_url,
            }
            response = await self.client.patch(url, json=data, params=params)
            response.raise_for_status()

            logger.info(f"Successfully updated course_image for course_id: {course_id}")
            return True

        except Exception as e:
            logger.error(f"An error occurred in update_course_image: {str(e)}")
            raise

    async def fetch_chapter_image_descriptions(self, course_id: str) -> Dict[str, str]:
        """
        Fetches chapter_ids and their corresponding chapter_image_description
        from the chapters table for a given course_id.
        Returns a dictionary with chapter_id as key and chapter_image_description as value.
        """
        try:
            url = "/rest/v1/chapters"
            params = {
                "course_id": f"eq.{course_id}",
                "select": "chapter_id,chapter_image_description",
            }
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                logger.warning(f"No chapters found for course_id: {course_id}")
                return {}

            return {chapter["chapter_id"]: chapter["chapter_image_description"] for chapter in data}

        except Exception as e:
            logger.error(f"An error occurred in fetch_chapter_image_descriptions: {str(e)}")
            raise

    async def update_chapter_images(self, course_id: str, chapter_image_urls: Dict[str, str]) -> bool:
        """
        Updates the chapter_image field for multiple chapters in the chapters table.
        
        :param course_id: The ID of the course.
        :param chapter_image_urls: A dictionary with chapter_id as key and image_url as value.
        :return: True if all updates were successful, False otherwise.
        """
        try:
            url = "/rest/v1/chapters"
            update_tasks = []

            for chapter_id, image_url in chapter_image_urls.items():
                params = {
                    "course_id": f"eq.{course_id}",
                    "chapter_id": f"eq.{chapter_id}",
                }
                data = {
                    "chapter_image": image_url,
                }
                update_tasks.append(self.client.patch(url, json=data, params=params))

            # Execute all update tasks concurrently
            responses = await asyncio.gather(*update_tasks, return_exceptions=True)

            # Check if all updates were successful
            all_successful = all(not isinstance(response, Exception) for response in responses)

            if all_successful:
                logger.info(f"Successfully updated all chapter images for course_id: {course_id}")
            else:
                logger.warning(f"Some chapter image updates failed for course_id: {course_id}")

            return all_successful

        except Exception as e:
            logger.error(f"An error occurred in update_chapter_images: {str(e)}")
            raise

    async def add_tavus_video_id(self, chapter_id: str, tavus_video_id: str) -> bool:
        """
        Adds or updates the tavus_video_id in the videos table for a given chapter_id.
        
        :param chapter_id: The ID of the chapter.
        :param tavus_video_id: The Tavus video ID to be added or updated.
        :return: True if the operation was successful, False otherwise.
        """
        try:
            url = "/rest/v1/videos"
            
            # First, check if a record already exists for this chapter_id
            params = {
                "chapter_id": f"eq.{chapter_id}",
                "select": "id"
            }
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            existing_records = response.json()

            if existing_records:
                # Update existing record
                record_id = existing_records[0]['id']
                update_url = f"{url}?id=eq.{record_id}"
                data = {"tavus_video_id": tavus_video_id}
                response = await self.client.patch(update_url, json=data)
            else:
                # Insert new record
                data = {
                    "chapter_id": chapter_id,
                    "tavus_video_id": tavus_video_id
                }
                response = await self.client.post(url, json=data)

            response.raise_for_status()
            logger.info(f"Successfully added/updated tavus_video_id for chapter_id: {chapter_id}")
            return True

        except Exception as e:
            logger.error(f"An error occurred in add_tavus_video_id: {str(e)}")
            return False

    async def fetch_video_script(self, chapter_id: str) -> Optional[str]:
        """
        Fetches the video_script from the videos table for a given chapter_id.

        :param chapter_id: The ID of the chapter.
        :return: The video script as a string, or None if not found.
        """
        try:
            url = "/rest/v1/videos"
            params = {
                "chapter_id": f"eq.{chapter_id}",
                "select": "video_script",
            }
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                logger.warning(f"No video script found for chapter_id: {chapter_id}")
                return None

            return data[0]["video_script"]

        except Exception as e:
            logger.error(f"An error occurred in fetch_video_script: {str(e)}")
            raise

    async def fetch_chapter_title(self, chapter_id: str) -> Optional[str]:
        """
        Fetches the chapter_title from the chapters table for a given chapter_id.

        :param chapter_id: The ID of the chapter.
        :return: The chapter title as a string, or None if not found.
        """
        try:
            url = "/rest/v1/chapters"
            params = {
                "chapter_id": f"eq.{chapter_id}",
                "select": "chapter_title",
            }
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                logger.warning(f"No chapter title found for chapter_id: {chapter_id}")
                return None

            return data[0]["chapter_title"]

        except Exception as e:
            logger.error(f"An error occurred in fetch_chapter_title: {str(e)}")
            raise

    async def fetch_lesson_text(self, chapter_id: str) -> Optional[str]:
        """
        Fetches the lesson_text from the chapters table for a given chapter_id.

        :param chapter_id: The ID of the chapter.
        :return: The lesson text as a string, or None if not found.
        """
        try:
            url = "/rest/v1/chapters"
            params = {
                "chapter_id": f"eq.{chapter_id}",
                "select": "lesson_text",
            }
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                return None

            return data[0]["lesson_text"]

        except Exception as e:
            logger.error(f"An error occurred in fetch_lesson_text: {str(e)}")
            raise

    async def update_video_url(self, tavus_video_id: str, video_url: str) -> bool:
        """
        Updates the video_url in the videos table for a given tavus_video_id.
        
        :param tavus_video_id: The Tavus video ID.
        :param video_url: The URL of the generated video.
        :return: True if the update was successful, False otherwise.
        """
        try:
            url = "/rest/v1/videos"
            params = {
                "tavus_video_id": f"eq.{tavus_video_id}",
            }
            data = {
                "video_url": video_url,
            }
            response = await self.client.patch(url, json=data, params=params)
            response.raise_for_status()

            if response.status_code == 204:  # Successful update returns 204 No Content
                logger.info(f"Successfully updated video_url for tavus_video_id: {tavus_video_id}")
                return True
            else:
                logger.warning(f"Unexpected status code {response.status_code} when updating video_url")
                return False

        except Exception as e:
            logger.error(f"An error occurred in update_video_url: {str(e)}")
            return False

    async def update_course_and_chapters_user(self, course_id: str, user_email: str) -> bool:
        """
        Updates the user_email in both the courses and chapters tables for a given course_id.
        
        :param course_id: The ID of the course to update.
        :param user_email: The email of the user to associate with the course and its chapters.
        :return: True if the update was successful, False otherwise.
        """
        try:
            # Update the courses table
            courses_url = "/rest/v1/courses"
            courses_params = {
                "course_id": f"eq.{course_id}",
            }
            courses_data = {
                "user_email": user_email,
            }
            courses_response = await self.client.patch(courses_url, json=courses_data, params=courses_params)
            courses_response.raise_for_status()

            # Update the chapters table
            chapters_url = "/rest/v1/chapters"
            chapters_params = {
                "course_id": f"eq.{course_id}",
            }
            chapters_data = {
                "user_email": user_email,
            }
            chapters_response = await self.client.patch(chapters_url, json=chapters_data, params=chapters_params)
            chapters_response.raise_for_status()

            if courses_response.status_code == 204 and chapters_response.status_code == 204:
                logger.info(f"Successfully updated user_email for course_id: {course_id}")
                return True
            else:
                logger.warning(f"Unexpected status codes: courses={courses_response.status_code}, chapters={chapters_response.status_code}")
                return False

        except Exception as e:
            logger.error(f"An error occurred in update_course_and_chapters_user: {str(e)}")
            return False

    async def fetch_lesson_text_from_lesson_texts(self, chapter_id: str) -> Optional[str]:
        """
        Fetches the lesson_text from the lesson_texts table for a given chapter_id.

        :param chapter_id: The ID of the chapter.
        :return: The lesson text as a string, or None if not found.
        """
        try:
            if not chapter_id:
                raise ValueError("chapter_id must be provided")

            url = "/rest/v1/lesson_texts"
            params = {
                "select": "lesson_text",
                "chapter_id": f"eq.{chapter_id}"
            }

            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                logger.warning(f"No lesson text found for chapter_id: {chapter_id}")
                return None

            return data[0]["lesson_text"]

        except Exception as e:
            logger.error(f"An error occurred in fetch_lesson_text_from_lesson_texts: {str(e)}")
            raise

    async def save_terms_to_lesson_texts(self, chapter_id: str, terms: List[Dict[str, str]] = None) -> bool:
        if not terms:
            logger.error("No terms provided to save")
            return False

        if not chapter_id:
            logger.error("chapter_id must be provided")
            return False

        try:
            url = "/rest/v1/lesson_texts"
            params = {"chapter_id": f"eq.{chapter_id}"}

            data = {
                "terms": json.dumps(terms),
            }
            response = await self.client.patch(url, json=data, params=params)
            response.raise_for_status()

            if response.status_code == 204:  # Successful update returns 204 No Content
                logger.info(f"Successfully updated terms for chapter_id: {chapter_id}")
                return True
            else:
                logger.warning(f"Unexpected status code {response.status_code} when updating terms")
                return False

        except Exception as e:
            logger.error(f"An error occurred in save_terms_to_lesson_texts: {str(e)}")
            return False

    async def save_terms_to_lesson_texts_quiz(self, quiz_id: str, terms: Dict[str, str] = None) -> bool:
        if not terms:
            logger.error("No terms provided to save")
            return False

        if not quiz_id:
            logger.error("quiz_id must be provided")
            return False

        try:
            url = "/rest/v1/lesson_texts"
            params = {"quiz_id": f"eq.{quiz_id}"}

            data = {
                "terms": json.dumps(terms),
            }
            response = await self.client.patch(url, json=data, params=params)
            response.raise_for_status()

            if response.status_code == 204:  # Successful update returns 204 No Content
                logger.info(f"Successfully updated terms for chapter_id: {quiz_id}")
                return True
            else:
                logger.warning(f"Unexpected status code {response.status_code} when updating terms")
                return False

        except Exception as e:
            logger.error(f"An error occurred in save_terms_to_lesson_texts: {str(e)}")
            return False

    async def get_lesson_text_for_chapter(self, chapter_id: str) -> Optional[str]:
        try:
            url = "/rest/v1/chapters"
            params = {"chapter_id": f"eq.{chapter_id}", "select": "lesson_text"}
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()[0]["lesson_text"]
        except Exception as e:
            logger.error(f"An error occurred in get_lesson_text_for_chapter: {str(e)}")
            raise

    async def mark_lesson_text_as_ready(self, chapter_id: str) -> bool:
        """
        Marks the lesson_text_status as ready for a chapter in the chapters table.
        """
        try:
            url = "/rest/v1/chapters"
            params = {
                "chapter_id": f"eq.{chapter_id}",
            }
            data = {
                "lesson_text_status": "ready",
            }
            response = await self.client.patch(url, json=data, params=params)
            response.raise_for_status()

            logger.info(f"Successfully marked lesson text status as ready for chapter {chapter_id}")
            return True

        except Exception as e:
            logger.error(f"An error occurred while updating lesson text status: {str(e)}")
            raise

    async def mark_quiz_as_ready(self, chapter_id: str) -> bool:
        """
        Marks the quiz_status as ready for a chapter in the chapters table.
        """
        try:
            url = "/rest/v1/chapters"
            params = {
                "chapter_id": f"eq.{chapter_id}",
            }
            data = {
                "quiz_status": "ready",
            }
            response = await self.client.patch(url, json=data, params=params)
            response.raise_for_status()

            logger.info(f"Successfully marked quiz status as ready for chapter {chapter_id}")
            return True

        except Exception as e:
            logger.error(f"An error occurred while updating quiz status: {str(e)}")
            raise

    async def mark_video_as_ready(self, chapter_id: str) -> bool:
        """
        Marks the video_status as ready for a chapter in the chapters table.
        """
        try:
            url = "/rest/v1/chapters"
            params = {
                "chapter_id": f"eq.{chapter_id}",
            }
            data = {
                "video_status": "ready",
            }
            response = await self.client.patch(url, json=data, params=params)
            response.raise_for_status()

            logger.info(f"Successfully marked video status as ready for chapter {chapter_id}")
            return True

        except Exception as e:
            logger.error(f"An error occurred while updating video status: {str(e)}")
            raise

    async def mark_course_as_ready(self, course_id: str) -> bool:
        """
        Marks the completion_status as ready for a course in the courses table.
        
        :param course_id: The ID of the course to mark as ready.
        :return: True if the update was successful, False otherwise.
        """
        try:
            url = "/rest/v1/courses"
            params = {
                "course_id": f"eq.{course_id}",
            }
            data = {
                "completion_status": "ready",
            }
            response = await self.client.patch(url, json=data, params=params)
            response.raise_for_status()

            if response.status_code == 204:  # Successful update returns 204 No Content
                logger.info(f"Successfully marked completion status as ready for course {course_id}")
                return True
            else:
                logger.warning(f"Unexpected status code {response.status_code} when updating course status")
                return False

        except Exception as e:
            logger.error(f"An error occurred while updating course completion status: {str(e)}")
            return False

    async def fetch_instructions_from_assignments(self, assignment_id: str) -> Optional[str]:
        """
        Fetches the instructions from the assignments table for a given assignment_id.

        :param assignment_id: The ID of the assignment.
        :return: The instructions as a string, or None if not found.
        """
        try:
            if not assignment_id:
                raise ValueError("assignment_id must be provided")

            url = "/rest/v1/assignments"
            params = {
                "select": "instructions",
                "assignment_id": f"eq.{assignment_id}"
            }

            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                logger.warning(f"No instructions found for assignment_id: {assignment_id}")
                return None

            return data[0]["instructions"]

        except Exception as e:
            logger.error(f"An error occurred in fetch_instructions_from_assignments: {str(e)}")
            raise

    async def fetch_instructions_from_course_instruction(self, course_id: str) -> Optional[str]:
        """
        Fetches the instructions from the course_instruction table for a given course_id.

        :param course_id: The ID of the course.
        :return: The instructions as a string, or None if not found.
        """
        try:
            if not course_id:
                raise ValueError("course_id must be provided")

            url = "/rest/v1/course_instruction"
            params = {
                "select": "instructions",
                "course_id": f"eq.{course_id}"
            }

            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                logger.warning(f"No instructions found for course_id: {course_id}")
                return ""

            return data[0]["instructions"]

        except Exception as e:
            logger.error(f"An error occurred in fetch_instructions_from_course_instruction: {str(e)}")
            raise

    async def save_vocabulary_terms_chapter(
        self, 
        terms: List[Dict[str, str]], 
        chapter_id: Optional[str] = None, 
    ) -> bool:
        """
        Saves vocabulary terms to the lesson_text_vocabulary table.
        Either chapter_id or quiz_id must be provided, but not both.

        Args:
            terms: List of dictionaries containing 'term' and 'definition' keys
            chapter_id: Optional chapter ID if the terms are for a chapter
            quiz_id: Optional quiz ID if the terms are for a quiz

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not terms:
                raise ValueError("Terms list cannot be empty")
            if not chapter_id:
                raise ValueError("chapter_id must be provided")

            url = "/rest/v1/lesson_text_vocabulary"
            vocabulary_tasks = []

            for term_data in terms:
                data = {
                    "term": term_data["term"],
                    "definition": term_data["definition"],
                }
                
                # Add either chapter_id or quiz_id to the data
                if chapter_id:
                    data["chapter_id"] = chapter_id

                vocabulary_tasks.append(self.client.post(url, json=data))

            # Execute all insertions concurrently
            responses = await asyncio.gather(*vocabulary_tasks, return_exceptions=True)

            # Check if all inserts were successful
            all_successful = all(not isinstance(response, Exception) for response in responses)

            if all_successful:
                logger.info(f"Successfully saved vocabulary terms for chapter_id: {chapter_id}")
                return True
            else:
                logger.warning(f"Some vocabulary terms failed to save for chapter_id: {chapter_id}")
                return False

        except Exception as e:
            logger.error(f"An error occurred in save_vocabulary_terms: {str(e)}")
            return False

    async def save_vocabulary_terms_quiz(
        self, 
        terms: List[Dict[str, str]], 
        quiz_id: Optional[str] = None,
    ) -> bool:
        """
        Saves vocabulary terms to the lesson_text_vocabulary table for a quiz.

        Args:
            terms: List of dictionaries containing 'term' and 'definition' keys
            quiz_id: Quiz ID for which the terms are being saved

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not terms:
                raise ValueError("Terms list cannot be empty")
            if not quiz_id:
                raise ValueError("quiz_id must be provided")

            url = "/rest/v1/lesson_text_vocabulary"
            vocabulary_tasks = []

            for term_data in terms:
                data = {
                    "term": term_data["term"],
                    "definition": term_data["definition"],
                    "quiz_id": quiz_id
                }

                vocabulary_tasks.append(self.client.post(url, json=data))

            # Execute all insertions concurrently
            responses = await asyncio.gather(*vocabulary_tasks, return_exceptions=True)

            # Check if all inserts were successful
            all_successful = all(not isinstance(response, Exception) for response in responses)

            if all_successful:
                logger.info(f"Successfully saved vocabulary terms for quiz_id: {quiz_id}")
                return True
            else:
                logger.warning(f"Some vocabulary terms failed to save for quiz_id: {quiz_id}")
                return False

        except Exception as e:
            logger.error(f"An error occurred in save_vocabulary_terms_quiz: {str(e)}")
            return False

    async def fetch_course_outline(self, course_id: str) -> CourseOutline:
        """
        Fetches the course outline from the courses and chapters tables.
        
        :param course_id: The ID of the course.
        :return: CourseOutline object containing course and chapter data.
        """
        try:
            # Fetch course data
            course_url = "/rest/v1/courses"
            course_params = {
                "course_id": f"eq.{course_id}",
                "select": "course_title,course_image_description,course_image"
            }
            course_response = await self.client.get(course_url, params=course_params)
            course_response.raise_for_status()
            course_data = course_response.json()

            if not course_data:
                raise ValueError(f"No course found with ID: {course_id}")

            # Fetch chapters data
            chapters_url = "/rest/v1/chapters"
            chapters_params = {
                "course_id": f"eq.{course_id}",
                "select": "chapter_id,chapter_title,chapter_description,chapter_image_description,chapter_outline,chapter_image",
                "order": "chapter_id.asc"
            }
            chapters_response = await self.client.get(chapters_url, params=chapters_params)
            chapters_response.raise_for_status()
            chapters_data = chapters_response.json()

            # Convert to CourseOutline model
            chapters = [
                Chapter(
                    chapter_id=chapter["chapter_id"],
                    chapter_title=chapter["chapter_title"],
                    chapterDescription=chapter["chapter_description"],
                    chapterImageDescription=chapter["chapter_image_description"],
                    chapterOutline=json.loads(chapter["chapter_outline"]) if chapter.get("chapter_outline") else {},
                    chapter_image=chapter.get("chapter_image")
                )
                for chapter in chapters_data
            ]

            return CourseOutline(
                course_title=course_data[0]["course_title"],
                course_image_description=course_data[0]["course_image_description"],
                course_image=course_data[0].get("course_image"),
                chapters=chapters
            )

        except Exception as e:
            logger.error(f"An error occurred in fetch_course_outline: {str(e)}")
            raise

    async def get_video_scripts_chapter_ids_and_chapter_title(self, course_id: str, course_outline: CourseOutline) -> Dict:
        """
        Gets video scripts, chapter IDs, and chapter titles for all chapters in a course.
        
        :param course_id: The ID of the course.
        :param course_outline: The CourseOutline object containing chapter data.
        :return: Dictionary containing chapters with their video scripts, IDs, and titles.
        """
        try:
            # Fetch all chapters data with video scripts
            url = "/rest/v1/chapters"
            params = {
                "course_id": f"eq.{course_id}",
                "select": "chapter_id,chapter_title,video_script",
                "order": "chapter_id.asc"
            }
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            chapters_data = response.json()

            if not chapters_data:
                raise ValueError(f"No chapters found for course ID: {course_id}")

            # Format the response
            return {
                "course_id": course_id,
                "chapters": [
                    {
                        "chapter_id": chapter["chapter_id"],
                        "chapter_title": chapter["chapter_title"],
                        "video_script": chapter["video_script"]
                    }
                    for chapter in chapters_data
                    if chapter.get("video_script")  # Only include chapters with video scripts
                ]
            }

        except Exception as e:
            logger.error(f"An error occurred in get_video_scripts_chapter_ids_and_chapter_title: {str(e)}")
            raise

    async def update_chapter_video_data(self, chapter_id: str, video_data: Dict) -> bool:
        """
        Updates or inserts video data for a chapter in the chapter_videos table.
        
        :param chapter_id: The ID of the chapter.
        :param video_data: Dictionary containing video data from HeyGen API.
        :return: True if successful, False otherwise.
        """
        try:
            url = "/rest/v1/chapter_videos"
            
            # Extract course_id from chapter_id (assuming format: course_id_chapter_X)
            course_id = "_".join(chapter_id.split("_")[:-2])
            
            data = {
                "course_id": course_id,
                "chapter_id": chapter_id,
                "heygen_video_id": video_data.get("video_id"),
                "status": "processing",  # Initial status when video is created
                "error_message": None
            }
            
            # If video_url is present in video_data, add it and update status
            if "video_url" in video_data:
                data["video_url"] = video_data["video_url"]
                data["status"] = "completed"
            
            # Use upsert to either insert new record or update existing one
            params = {"on_conflict": "chapter_id"}
            response = await self.client.post(url, json=data, params=params)
            response.raise_for_status()

            logger.info(f"Successfully updated video data for chapter {chapter_id}")
            return True

        except Exception as e:
            logger.error(f"An error occurred in update_chapter_video_data: {str(e)}")
            return False

    async def save_chapter_audio(self, course_id: str, chapter_id: str, audio_url: str, transcript: str):
        """Save chapter audio data to Supabase."""
        try:
            url = "/rest/v1/course_audio"
            data = {
                'course_id': course_id,
                'chapter_id': chapter_id,
                'audio_url': audio_url,
                'transcript': transcript
            }
            
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error saving chapter audio: {e}")
            raise

    async def fetch_chapter_content(self, chapter_id: str) -> Optional[str]:
        """Fetch chapter content for generating conversation."""
        try:
            logger.info(f"Fetching content for chapter {chapter_id} from database")
            url = "/rest/v1/course_chapters"
            params = {
                "chapter_id": f"eq.{chapter_id}",
                "select": "content,detailled_context,chapter_title"
            }
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data and len(data) > 0:
                content = data[0].get('content', '')
                detailed_context = data[0].get('detailled_context', '')
                chapter_title = data[0].get('chapter_title', '')
                
                logger.info(f"Found data for chapter {chapter_id}: title={chapter_title}")
                logger.info(f"Content length: {len(content)}, Detailed context length: {len(detailed_context)}")
                
                # Combine fields for a richer conversation context
                combined_content = f"Chapter: {chapter_title}\n\n{content}\n\n{detailed_context}".strip()
                if not combined_content:
                    logger.warning(f"No content found for chapter {chapter_id}")
                    return None
                    
                return combined_content
            
            logger.warning(f"No data found for chapter {chapter_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching chapter content: {e}")
            return None

    async def fetch_course_outline_from_outlines(self, course_id: str) -> Optional[str]:
        """
        Fetches the course outline from the course_outlines table for a given course_id.
        
        :param course_id: The ID of the course.
        :return: The course outline as a string, or None if not found.
        """
        try:
            if not course_id:
                raise ValueError("course_id must be provided")

            url = "/rest/v1/course_outlines"
            params = {
                "select": "course_outline",
                "course_id": f"eq.{course_id}",
                "order": "created_at.desc",  # Get the most recent outline
                "limit": 1
            }

            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                logger.warning(f"No course outline found for course_id: {course_id}")
                return None

            return data[0]["course_outline"]

        except Exception as e:
            logger.error(f"An error occurred in fetch_course_outline_from_outlines: {str(e)}")
            raise
