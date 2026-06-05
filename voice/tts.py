import emoji
import re

def emoji_to_text(text):
    """Convert emojis to their text descriptions for better speech clarity"""
    result = text
    
    # Use the emoji library to demojize (convert emojis to text descriptions)
    result = emoji.demojize(result, delimiters=(" ", " "))
    
    # Clean up the description format (remove underscores, capitalize)
    # Convert ":robot_face:" style to "robot face"
    result = re.sub(r':([^:]+):', r'\1', result)
    result = result.replace('_', ' ')
    
    return result

def prepare_for_speech(text):
    """Prepare text for clear speech output"""
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Convert emojis to descriptions
    text = emoji_to_text(text)
    
    # Remove any special characters that might cause issues with speech
    # Keep alphanumeric, spaces, and common punctuation
    text = re.sub(r'[^\w\s\.\,\!\?\-\']', '', text)
    
    # Clean up spacing again
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def get_emoji_description(text):
    """Get a list of emojis found in text with their descriptions"""
    emoji_list = []
    for char in text:
        if char in emoji.EMOJI_DATA:
            description = emoji.EMOJI_DATA[char].get('en', char)
            emoji_list.append(f"{char} ({description})")
    return emoji_list
