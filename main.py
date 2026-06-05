from voice.listen import listen
from ai.chat import ask_llm
from memory.store import remember, recall

import os
print("🤖 FRIDAY Ready")
print("💡 Tip: Tell me your name, email, or anything you'd like me to remember!")

while True:
    text = listen()

    print("\nYou said:", text)

    if not text:
        continue

    if text.lower() in ["exit", "quit", "goodbye"]:
        print("👋 FRIDAY shutting down...")
        break

    answer = ask_llm(text)

    print("\nFRIDAY:", answer)
    os.system(f'say "{answer}"')
