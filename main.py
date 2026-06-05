from voice.listen import listen
from voice.tts import prepare_for_speech
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
    
    # Prepare text for clear speech (converts emojis to descriptions)
    speech_text = prepare_for_speech(answer)
    
    # Speak with better rate and pitch for clarity
    os.system(f'say -r 180 "{speech_text}"')
