import os
import logging
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from dotenv import load_dotenv
import asyncio
import datetime
import pytz

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
SOURCE_CHANNEL = os.getenv('SOURCE_CHANNEL')
TARGET_CHANNEL = os.getenv('TARGET_CHANNEL')
SESSION_STRING = os.getenv('SESSION_STRING')

# Initialize Telegram client
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

async def get_channel_info():
    """Display information about accessible channels for debugging."""
    logger.info("Retrieving channel information...")
    print("\n=== CHANNELS YOU HAVE ACCESS TO ===")
    async for dialog in client.iter_dialogs():
        if dialog.is_channel:
            print(f"{dialog.name} | {dialog.id}")
    print("=====================================\n")

async def forward_new_messages():
    """Forward messages from source channel to target channel based on the last timestamp."""
    # Convert channel IDs from strings to integers
    source_channel = int(SOURCE_CHANNEL) if SOURCE_CHANNEL else None
    target_channel = int(TARGET_CHANNEL) if TARGET_CHANNEL else None
    
    if not source_channel or not target_channel:
        logger.error("Source or target channel ID is missing.")
        return
    
    # Step 1: Get the last message from the target channel
    messages = await client.get_messages(target_channel, limit=1)
    if messages:
        last_message = messages[0]
        last_timestamp = last_message.date  # UTC datetime
    else:
        # If target channel is empty, use a very old timestamp to forward all messages
        last_timestamp = datetime.datetime.min.replace(tzinfo=pytz.UTC)
    logger.info(f"Last timestamp in target channel: {last_timestamp}")
    
    # Step 2: Collect messages from source channel after last_timestamp
    messages_to_forward = []
    async for msg in client.iter_messages(source_channel):
        if msg.date <= last_timestamp:
            break  # Stop when we reach messages older than or equal to last_timestamp
        messages_to_forward.append(msg)
    
    if not messages_to_forward:
        logger.info("No new messages to forward.")
        return
    
    logger.info(f"Found {len(messages_to_forward)} new messages to forward")
    
    # Step 3: Sort messages by ID to ensure chronological order
    # Note: iter_messages yields newest to oldest, so sorting by ID ascending corrects this
    messages_to_forward.sort(key=lambda x: x.id)
    
    # Step 4: Forward messages to target channel
    for msg in messages_to_forward:
        try:
            await client.forward_messages(target_channel, msg)
            logger.info(f"Forwarded message ID {msg.id} with timestamp {msg.date}")
        except errors.FloodWaitError as e:
            wait_time = e.seconds
            logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds.")
            await asyncio.sleep(wait_time)
            break  # Stop forwarding and wait until next run
        except Exception as e:
            logger.error(f"Error forwarding message ID {msg.id}: {str(e)}")

async def main():
    """Main function to start the client and run the forwarding process."""
    await client.start()
    logger.info("Client started successfully")
    await get_channel_info()  # Optional: keep for debugging
    if SOURCE_CHANNEL and TARGET_CHANNEL:
        await forward_new_messages()
    else:
        logger.info("Channel IDs not configured.")
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
