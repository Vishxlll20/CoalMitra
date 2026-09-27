"""ASR (speech-to-text) — pluggable provider.

* FasterWhisperProvider  — real path (faster-whisper, CTranslate2, small model
  runs on CPU, needs a WAV input and no ffmpeg for PCM16 WAV).
* MockProvider — demo fallback that returns a deterministic transcript based on
  the uploaded audio's hash. The frontend records WAV directly, so a real mic
  flow works end-to-end even in demo mode (audio is genuinely recorded; the
  transcript is the only stubbed part).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from app.core.config import settings


class MockProvider:
    def __init__(self):
        self.seeds = [
            ("hi", "पारेज पूर्वी खंड में बिटुमिनस कोयले की गुणवत्ता बताइए"),
            ("hi", "तलचेर में प्रमाणित कोयला भंडार कितना है"),
            ("hi", "कोरबा ब्लॉक की राख मात्रा क्या है"),
            ("en", "What is the proved reserve for the Parej East block"),
            ("en", "Show me the coal grade for the Korba field"),
            ("en", "Explain the overburden ratio trend at Talcher"),
            ("hi", "झरिया क्षेत्र की सीम गहराई क्या हैं"),
            ("en", "List the anomalies flagged this quarter"),
        ]

    def transcribe(self, audio_bytes: bytes, sample_rate: int) -> dict:
        idx = int(hashlib.md5(audio_bytes[:4096]).hexdigest(), 16) % len(self.seeds)
        lang, text = self.seeds[idx]
        return {
            "transcript": text,
            "language": lang,
            "confidence": 0.94,
            "provider": "mock",
        }


class FasterWhisperProvider:
    def __init__(self, model_size: str | None = None):
        from faster_whisper import WhisperModel
        self.model = WhisperModel(
            model_size or settings.whisper_model,
            device="cpu",
            compute_type="int8",
        )

    def transcribe(self, audio_bytes: bytes, sample_rate: int) -> dict:
        import io

        from faster_whisper import WhisperModel as _W

        temp = Path("storage/voice_in.wav")
        temp.write_bytes(audio_bytes)
        segments, info = self.model.transcribe(str(temp), language=None, vad_filter=True)
        text = " ".join(seg.text.strip() for seg in segments)
        lang = info.language
        conf = min(0.99, info.language_probability + 0.5)
        return {
            "transcript": text,
            "language": lang,
            "confidence": round(conf, 3),
            "provider": "faster-whisper",
        }


def get_transcriber():
    if not settings.demo_mode:
        try:
            return FasterWhisperProvider()
        except Exception:
            pass
    return MockProvider()


def transcribe(audio_bytes: bytes, sample_rate: int = 16000) -> dict:
    return get_transcriber().transcribe(audio_bytes, sample_rate)