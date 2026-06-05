import json
import os
from pathlib import Path

MEMORY_FILE = Path(__file__).parent / "memory.json"

def load_memory():
    """Load memory from file"""
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_memory(memory):
    """Save memory to file"""
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def remember(key, value):
    """Store a piece of information"""
    memory = load_memory()
    memory[key] = value
    save_memory(memory)
    print(f"💾 Remembered: {key} = {value}")

def recall(key):
    """Retrieve a piece of information"""
    memory = load_memory()
    return memory.get(key, None)

def get_all_memory():
    """Get all stored memory"""
    return load_memory()

def forget(key):
    """Delete a piece of information"""
    memory = load_memory()
    if key in memory:
        del memory[key]
        save_memory(memory)
        print(f"🗑️ Forgot: {key}")

def get_memory_context():
    """Get memory as a formatted string for AI context"""
    memory = load_memory()
    if not memory:
        return "No memories stored yet."
    
    context = "My memories about the user:\n"
    for key, value in memory.items():
        context += f"- {key}: {value}\n"
    
    return context
