from ollama import chat
from memory.store import get_memory_context, remember, recall
from app_control.control import handle_app_command
import json
import sys
from pathlib import Path

def _get_ollama_model() -> str:
    try:
        def get_base_dir():
            if getattr(sys, "frozen", False):
                return Path(sys.executable).parent
            return Path(__file__).resolve().parent.parent

        path = get_base_dir() / "config" / "api_keys.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            return cfg.get("ollama_model", "qwen3-coder:480b-cloud")
    except Exception:
        pass
    return "qwen3-coder:480b-cloud"

def ask_llm(prompt):
    # First, check if this is an app control command
    app_result = handle_app_command(prompt)
    if app_result:
        return app_result
    
    # Get memory context
    memory_context = get_memory_context()
    
    # System message with memory
    system_message = f"""You are FRIDAY, a personal AI assistant for macOS.
You have access to the user's personal information and memories.
You can also control applications and system settings.

APP CONTROL CAPABILITIES:
- Open apps: "open chrome", "open spotify", etc.
- Close apps: "close chrome", "close spotify", etc.
- List running apps: "what apps are running"
- Volume control: "set volume to 50"
- Brightness: "set brightness to 75"
- Lock screen: "lock screen"
- Sleep: "sleep mac"

Current Memories:
{memory_context}

When the user tells you something about themselves (like their name, age, occupation, preferences), 
you should acknowledge it and suggest remembering it. 
For example: "I'll remember that you're interested in Python programming."

When the user asks about something they've told you before, use the memories to answer accurately.

Keep responses concise and natural."""

    response = chat(
        model=_get_ollama_model(),
        messages=[
            {
                "role": "system",
                "content": system_message
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    answer = response["message"]["content"]
    
    # Check if the response mentions remembering something
    if "remember" in answer.lower() or "i'll remember" in answer.lower():
        # Try to extract and store the memory
        extract_and_store_memory(prompt, answer)
    
    return answer

def extract_and_store_memory(prompt, response):
    """Extract and store memories from the conversation"""
    # Common memory patterns
    memory_patterns = [
        ("my name is", "name"),
        ("i'm", "identity"),
        ("my favorite", "preference"),
        ("i like", "preference"),
        ("i work as", "occupation"),
        ("i'm a", "occupation"),
        ("my email", "email"),
        ("my phone", "phone"),
    ]
    
    prompt_lower = prompt.lower()
    
    for pattern, memory_type in memory_patterns:
        if pattern in prompt_lower:
            # Extract the value after the pattern
            start_idx = prompt_lower.find(pattern) + len(pattern)
            value = prompt[start_idx:].strip()
            
            # Clean up the value
            if value.endswith("."):
                value = value[:-1]
            
            # Store the memory
            if value:
                remember(f"{memory_type}", value)
            break