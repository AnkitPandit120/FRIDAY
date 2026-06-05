import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel

model = WhisperModel("base")

def listen():
    print("🎤 Speak now...")

    duration = 5  # seconds
    sample_rate = 16000

    recording = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16"
    )

    sd.wait()

    write("temp.wav", sample_rate, recording)

    segments, _ = model.transcribe("temp.wav")

    text = ""
    for segment in segments:
        text += segment.text

    return text.strip()