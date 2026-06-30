"""Whisper-based audio transcription service."""


class Transcriber:
    """Transcribes audio to text using OpenAI Whisper.

    Supports multiple languages and returns timestamped segments.
    """

    def __init__(self, model_name: str = "base", device: str = "auto") -> None:
        self.model_name = model_name
        self.device = device
        self._model = None

    async def transcribe(self, audio_path: str) -> dict:
        """Transcribe audio file to text with timestamps.

        Args:
            audio_path: Path to audio file

        Returns:
            Dict with 'text' and 'segments' (timestamped)
        """
        raise NotImplementedError("Transcription will be implemented in next iteration")
