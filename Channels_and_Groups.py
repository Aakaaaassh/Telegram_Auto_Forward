import os
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()
API_ID = os.getenv('API_ID')  # Your API ID
API_HASH = os.getenv('API_HASH')  # Your API Hash
SESSION_STRING = os.getenv('SESSION_STRING')  # Your session string (optional)

def get_all_channels_and_groups():
    """
    Retrieve all channels and groups from your Telegram account.
    
    Returns:
        tuple: (channels, groups)
        - channels: List of dictionaries with channel names and IDs
        - groups: List of dictionaries with group names and IDs
    """
    # Initialize the Telegram client
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    
    with client:
        # Fetch all dialogs (chats) from your account
        dialogs = client.get_dialogs()
        
        # Initialize empty lists for channels and groups
        channels = []
        groups = []
        
        # Iterate through all dialogs and categorize them
        for dialog in dialogs:
            if dialog.is_channel:
                # Check if it's a broadcast channel
                if dialog.entity.broadcast:
                    channels.append({
                        'name': dialog.name,
                        'id': dialog.id
                    })
                else:
                    # Non-broadcast channels are treated as groups
                    groups.append({
                        'name': dialog.name,
                        'id': dialog.id
                    })
            elif dialog.is_group:
                # Regular groups and supergroups
                groups.append({
                    'name': dialog.name,
                    'id': dialog.id
                })
        
        return channels, groups

# Example usage
if __name__ == "__main__":
    channels, groups = get_all_channels_and_groups()
    
    print("Channels:")
    for channel in channels:
        print(f"Name: {channel['name']} | ID: {channel['id']}")
    
    print("\nGroups:")
    for group in groups:
        print(f"Name: {group['name']} | ID: {group['id']}")
