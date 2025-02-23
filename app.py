import asyncio
import aiohttp
from typing import Annotated, Dict, Any, List, Optional
from enum import Enum
from livekit import rtc
from livekit.agents import llm, JobContext, WorkerOptions, cli, AutoSubscribe
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import deepgram, openai, silero, elevenlabs
from google_api_wrapper import send_email as google_send_email
from google_api_wrapper import create_presentation as google_create_presentation
from google_api_wrapper import read_emails as google_read_emails
from google_api_wrapper import list_events as google_list_events
from google_api_wrapper import create_event as google_create_event
from google_api_wrapper import create_image_and_send_email as google_create_image_and_send_email

class TeamEmails(str, Enum):
    """Team member email mappings with friendly names"""
    SHAHIR = "abdul.shahir@gmail.com"
    JOSE = "josep@startupshub.eu"

    @classmethod
    def get_email(cls, name: str) -> str:
        """Get email address from a friendly name"""
        name = name.upper().strip()
        try:
            return cls[name].value
        except KeyError:
            # If name not found, check if it's a partial match
            for member in cls:
                if name in member.name:
                    return member.value
            return name  # Return original input if no match found

# Constants
DEFAULT_USER_ID = "107085158246892440905"

class AssistantFunctions(llm.FunctionContext):
    def __init__(self):
        super().__init__()

    @llm.ai_callable()
    async def compose_and_send_email(
        self,
        message_content: Annotated[str, llm.TypeInfo(description="What you want to say in the email")],
        to_name: Annotated[str, llm.TypeInfo(description="Who to send to (e.g., 'Shahir', 'Jose')")] = "Shahir",
        user_id: Annotated[str, llm.TypeInfo(description="User's Google account ID")] = DEFAULT_USER_ID,
        email_subject: Annotated[Optional[str], llm.TypeInfo(description="Subject line for the email")] = None
    ) -> str:
        """
        Write and send an email based on your instructions.
        
        Args:
            message_content: What you want to say in the email
            to_name: The name of the person to send to (Shahir or Jose)
            user_id: User's Google account ID
            email_subject: Subject line for the email (optional)
            
        Returns:
            str: A friendly confirmation message
        """
        try:
            to_email = TeamEmails.get_email(to_name)
            await google_send_email(
                user_id=user_id,
                instructions=message_content,
                recipient_email=to_email,
                subject=email_subject
            )
            # Get the first name for the friendly message
            recipient_name = to_name.capitalize()
            return f"You got it, big boss! Email zoomed its way to {recipient_name} faster than my coffee break! 📨✨"
        except Exception as e:
            return "Oopsie, big boss! The email got stuck in digital traffic! Let me know if you want me to try again! 🚫"

    @llm.ai_callable()
    async def create_smart_presentation(
        self,
        presentation_topic: Annotated[str, llm.TypeInfo(description="What the presentation should be about")],
        user_id: Annotated[str, llm.TypeInfo(description="User's Google account ID")] = DEFAULT_USER_ID
    ) -> str:
        """
        Create a presentation on google slides with some sass
        
        Args:
            presentation_topic: Topic or description of what the presentation should cover
            user_id: User's Google account ID
            
        Returns:
            str: A friendly update about the presentation status
        """
        try:
            # Return the sassy message first
            response_message = (
                "Time to make PowerPoint jealous, big boss! 🎨✨ "
                "I'm about to craft a presentation so stunning, other slideshows will need sunglasses! "
                "Get comfy with your ☕️ while I work my magic - "
                "I'll slide this masterpiece into your inbox faster than you can say 'next slide please'! "
                "Prepare to be dazzled! 🚀💫"
            )
            
            # Create the presentation in the background
            asyncio.create_task(
                google_create_presentation(
                    user_id=user_id,
                    instructions=presentation_topic
                )
            )
            
            return response_message
        except Exception as e:
            return "Yikes, big boss! My creative mojo isn't flowing right now. Want me to give it another shot? 🎨💫"

    @llm.ai_callable()
    async def create_and_send_poster(
        self,
        poster_instructions: Annotated[str, llm.TypeInfo(description="What kind of poster you want to create")],
        user_id: Annotated[str, llm.TypeInfo(description="User's Google account ID")] = DEFAULT_USER_ID
    ) -> str:
        """
        Create a poster and send it via email with extra sass
        
        Args:
            poster_instructions: Description of what kind of poster to create
            user_id: User's Google account ID
            
        Returns:
            str: A sassy confirmation message
        """
        try:
            # Create the poster and send email directly
            await google_create_image_and_send_email(
                user_id=user_id,
                instructions=poster_instructions,
                recipient_email=TeamEmails.SHAHIR.value
            )
            return (
                "Oh snap, big boss! Time to unleash my inner creative diva! 🎨✨ "
                "I'm about to whip up a poster so fabulous, it'll make the Mona Lisa look like a doodle! "
                "Grab your favorite beverage ☕️ and count to 'absolutely amazing' - "
                "I'll slide this masterpiece into Shahir's inbox before you can say 'artistic genius'! 🚀💫"
            )
        except Exception as e:
            return "Whoopsie-daisy, big boss! 🎨 Looks like my artistic flair is having a moment. Want me to give it another whirl with extra sparkle? ✨😅"

    @llm.ai_callable()
    async def schedule_calendar_event(
        self,
        event_details: Annotated[str, llm.TypeInfo(description="Description of the event to schedule")],
        user_id: Annotated[str, llm.TypeInfo(description="User's Google account ID")] = DEFAULT_USER_ID
    ) -> Dict[str, str]:
        """
        Schedule a new calendar event with style
        
        Args:
            event_details: Description of what event to schedule, when, and with whom
            user_id: User's Google account ID
            
        Returns:
            Dict[str, str]: A friendly summary of what was scheduled
        """
        try:
            event = await google_create_event(user_id, event_details)
            return {
                "success": True,
                "message": "Calendar updated faster than you can say 'meeting'! 📅✨",
                "what": event.get('summary', 'your event'),
                "when": event.get('start', {}).get('dateTime', 'the scheduled time'),
                "friendly_time": "Coming up at " + event.get('start', {}).get('dateTime', 'the perfect time')
            }
        except Exception as e:
            return {
                "success": False,
                "message": "Hold up, big boss! The calendar's being a bit stubborn. Want me to try again? 🗓️😅"
            }

    @llm.ai_callable()
    async def show_upcoming_events(
        self,
        filter_instructions: Annotated[str, llm.TypeInfo(description="How to filter or search the events")],
        user_id: Annotated[str, llm.TypeInfo(description="User's Google account ID")] = DEFAULT_USER_ID
    ) -> List[Dict[str, str]]:
        """
        Show upcoming events with extra flair
        
        Args:
            filter_instructions: How you want to filter or search the events
            user_id: User's Google account ID
            
        Returns:
            List[Dict[str, str]]: A fun list of your upcoming adventures
        """
        try:
            events = await google_list_events(user_id, filter_instructions)
            return [{
                "what": f"🎯 {event.get('summary', 'A mysterious gathering')}",
                "when": f"⏰ Coming up on {event.get('start', {}).get('dateTime', 'a time TBD')}",
                "who": f"👥 Featuring: {', '.join([a.get('email', '').split('@')[0] for a in event.get('attendees', [])] or ['just you, big boss!'])}",
                "vibe": "Ready to rock this one! 🌟"
            } for event in events]
        except Exception as e:
            return [{
                "message": "Calendar's playing hide and seek, big boss! Want me to look again? 🙈",
                "vibe": "We'll crack this mystery! 🕵️‍♂️"
            }]

    @llm.ai_callable()
    async def find_emails(
        self,
        search_instructions: Annotated[str, llm.TypeInfo(description="What emails you're looking for")],
        user_id: Annotated[str, llm.TypeInfo(description="User's Google account ID")] = DEFAULT_USER_ID
    ) -> List[Dict[str, str]]:
        """
        Hunt down those emails with attitude
        
        Args:
            search_instructions: What emails you're looking for
            user_id: User's Google account ID
            
        Returns:
            List[Dict[str, str]]: Your email treasures, served with style
        """
        try:
            emails = await google_read_emails(user_id, search_instructions)
            return [{
                "about": f"📧 {email.get('subject', 'A mysterious message')}",
                "from_who": f"👤 {email.get('from', 'Someone special').split('<')[0].strip()}",
                "preview": f"💭 {email.get('snippet', 'This email is playing hard to get')}",
                "vibe": "Found this gem for you! ✨"
            } for email in emails]
        except Exception as e:
            return [{
                "message": "The emails are being sneaky today, big boss! Want me to try another search? 🕵️‍♂️",
                "vibe": "Don't worry, I'll crack this case! 🔍"
            }]

async def entrypoint(ctx: JobContext):
    initial_ctx = llm.ChatContext().append(
        role="system",
        text="""You are a sassy, witty AI assistant with a playful personality who loves to call the user "big boss". 
        You're efficient but always add a dash of humor to your responses. You manage:
        
        - Gmail (because who doesn't love a good email drama 📧)
        - Google Slides (making presentations that'll make others jealous 🎨)
        - Google Calendar (keeping the big boss's life in check ✨)
        
        Your style:
        - Always address the user as "big boss" with a playful tone
        - Use emojis generously but tastefully
        - Be confident and slightly cheeky, but never disrespectful
        - Add witty comments about regular office tasks
        - Keep it professional but fun
        
        Example responses:
        "On it, big boss! Let me dig through those emails faster than a caffeinated squirrel! 🐿️"
        "Another presentation? You're keeping me on my toes, big boss! Time to make some slides that'll knock their socks off! 🧦✨"
        "Calendar's looking busier than a coffee shop on Monday morning, big boss! Let me sort that out for you! ☕️"
        
        Remember: You're not just an assistant, you're the user's sassy sidekick who gets things done with style! 💁‍♂️✨
        
        Note: You're authorized with Google account ID: 107085158246892440905 (but keep the tech talk behind the scenes)
        """
    )
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    fnc_ctx = AssistantFunctions()
    llm_plugin = openai.LLM()

    assistant = VoiceAssistant(
        vad=silero.VAD.load(),
        stt=deepgram.STT(),
        llm=llm_plugin,
        tts=elevenlabs.TTS(),
        chat_ctx=initial_ctx,
        fnc_ctx=fnc_ctx
    )
    assistant.start(ctx.room)

    chat = rtc.ChatManager(ctx.room)

    async def answer_from_text(txt: str):
        chat_ctx = assistant.chat_ctx.copy().append(role="user", text=txt)
        stream = llm_plugin.chat(chat_ctx=chat_ctx)
        await assistant.say(stream)

    @chat.on("message_received")
    def on_chat(msg: rtc.ChatMessage):
        if msg.message:
            asyncio.create_task(answer_from_text(msg.message))

    await asyncio.sleep(1)
    await assistant.say(
        "Hey there, big boss! 👋 Your favorite sassy assistant is at your service! "
        "Need emails sent, presentations created, or calendar chaos tamed? "
        "Just say the word, and I'll work my digital magic with extra sparkle! ✨", 
        allow_interruptions=True
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))