import os
import logging
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
import datetime
import pytz

load_dotenv()

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables directly (no .env file needed on Render)
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
SOURCE_CHANNEL = os.getenv('SOURCE_CHANNEL')
TARGET_CHANNEL = os.getenv('TARGET_CHANNEL')
SESSION_STRING = os.getenv('SESSION_STRING')

# Initialize Telegram client
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

async def forward_new_messages():
    """Forward messages from source to target channel based on last timestamp."""
    source_channel = int(SOURCE_CHANNEL) if SOURCE_CHANNEL else None
    target_channel = int(TARGET_CHANNEL) if TARGET_CHANNEL else None
    
    if not source_channel or not target_channel:
        logger.error("Source or target channel ID is missing.")
        return
    
    # Get the last message from the target channel
    messages = await client.get_messages(target_channel, limit=1)
    last_timestamp = messages[0].date if messages else datetime.datetime.min.replace(tzinfo=pytz.UTC)
    logger.info(f"Last timestamp in target channel: {last_timestamp}")
    
    # Collect messages from source channel after last_timestamp
    messages_to_forward = []
    async for msg in client.iter_messages(source_channel):
        if msg.date <= last_timestamp:
            break
        messages_to_forward.append(msg)
    
    if not messages_to_forward:
        logger.info("No new messages to forward.")
        return
    
    logger.info(f"Found {len(messages_to_forward)} new messages to forward")
    messages_to_forward.sort(key=lambda x: x.id)
    
    # Forward messages
    for msg in messages_to_forward:
        try:
            await client.forward_messages(target_channel, msg)
            logger.info(f"Forwarded message ID {msg.id} with timestamp {msg.date}")
        except errors.FloodWaitError as e:
            logger.warning(f"Rate limit hit. Waiting {e.seconds} seconds.")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f"Error forwarding message ID {msg.id}: {str(e)}")

async def main():
    """Run the forwarding logic every minute."""
    await client.start()
    logger.info("Client started successfully")
    
    while True:
        try:
            await forward_new_messages()
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
        await asyncio.sleep(60)  # Wait 1 minute before next run

if __name__ == "__main__":
    asyncio.run(main())
