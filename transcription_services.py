import os
import fal_client
from typing import Dict, Any, Optional, AsyncGenerator
from dotenv import load_dotenv

load_dotenv()

class TranscriptionService:
    def __init__(self):
        self.fal_key = os.getenv("FAL_KEY")
        if not self.fal_key:
            raise ValueError("FAL_KEY environment variable is not set")
        
        # Set the API key for fal-client
        fal_client.api_key = self.fal_key

    async def transcribe_audio(
        self,
        audio_url: str,
        model: str,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio using FAL AI's Whisper model.
        
        Args:
            audio_url (str): URL of the audio file to transcribe
            model (str): The model to use for transcription
            additional_params (Dict[str, Any], optional): Additional parameters for the model
            
        Returns:
            Dict[str, Any]: The transcription result
        """
        try:
            # Prepare the arguments
            arguments = {"audio_url": audio_url}
            if additional_params:
                arguments.update(additional_params)

            # Submit the transcription request
            handler = await fal_client.submit_async(
                model,
                arguments=arguments
            )

            # Wait for the result
            result = await handler.get()
            return result

        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")

    async def transcribe_audio_with_progress(
        self,
        audio_url: str,
        model: str,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Transcribe audio with progress updates using FAL AI's Whisper model.
        
        Args:
            audio_url (str): URL of the audio file to transcribe
            model (str): The model to use for transcription
            additional_params (Dict[str, Any], optional): Additional parameters for the model
            
        Yields:
            Dict[str, Any]: Progress updates and final transcription result
        """
        try:
            # Prepare the arguments
            arguments = {"audio_url": audio_url}
            if additional_params:
                arguments.update(additional_params)

            # Submit the transcription request
            handler = await fal_client.submit_async(
                model,
                arguments=arguments
            )

            # Stream progress updates
            async for event in handler.iter_events(with_logs=True):
                yield event

            # Get the final result
            result = await handler.get()
            yield result

        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}") 