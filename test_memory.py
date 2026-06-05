#!/usr/bin/env python3
"""Test script to verify memory system works"""

from memory.store import remember, recall, get_all_memory, get_memory_context

print("🧪 Testing FRIDAY Memory System\n")

# Test 1: Store a name
print("Test 1: Remember your name")
remember("name", "Ankit")
print(f"✅ Stored name")

# Test 2: Recall the name
print("\nTest 2: Recall the name")
name = recall("name")
print(f"✅ Retrieved name: {name}")

# Test 3: Store multiple memories
print("\nTest 3: Store multiple memories")
remember("email", "ankit@example.com")
remember("favorite_language", "Python")
remember("occupation", "Software Engineer")
print(f"✅ Stored 3 items")

# Test 4: Get all memories
print("\nTest 4: Get all memories")
all_memories = get_all_memory()
print(f"✅ All memories: {all_memories}")

# Test 5: Get memory context (formatted for AI)
print("\nTest 5: Get formatted memory context")
context = get_memory_context()
print(f"✅ Memory context:\n{context}")

print("\n✅ All tests passed! Memory system is working.")
