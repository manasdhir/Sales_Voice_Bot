from faster_whisper import WhisperModel
import tempfile
# 🔹 Model initialization (do this once, globally)
# Available sizes: "tiny", "base", "small", "medium", "large-v3"
ASR_MODEL_NAME = "base"  # change to "tiny", "small", etc. for speed
USE_GPU = False  # Set to False for CPU

# Use compute_type="int8" or "int8_float16" for lower VRAM
asr_model = WhisperModel(
    ASR_MODEL_NAME,
    device="cuda" if USE_GPU else "cpu",
    compute_type="int8_float16" if USE_GPU else "int8"
)

def faster_whisper_asr_bytes(audio_bytes: bytes) -> str:

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp_file:
        tmp_file.write(audio_bytes)
        tmp_file.flush()

        segments, info = asr_model.transcribe(
            tmp_file.name,
            language=None,       # 👈 auto-detect
            beam_size=5,
            vad_filter=True
        )

        transcript = "".join(segment.text for segment in segments)

    return transcript

if __name__ == "__main__":
    with open("test audio_english.wav", "rb") as f:
        audio_bytes = f.read()

    transcript = faster_whisper_asr_bytes(audio_bytes)
    print("Transcript:\n", transcript)
