"""Audio editing operations service."""


class AudioEditor:
    """Non-destructive audio editing operations.

    Operations: cut, trim, split, merge, fade-in/out, volume adjust.
    All operations are stored as edit lists; originals are never modified.
    """

    async def cut(self, input_path: str, start_ms: int, end_ms: int, output_path: str) -> str:
        """Cut a segment from audio."""
        raise NotImplementedError

    async def merge(self, input_paths: list[str], output_path: str) -> str:
        """Merge multiple audio files into one."""
        raise NotImplementedError

    async def adjust_volume(self, input_path: str, gain_db: float, output_path: str) -> str:
        """Adjust volume by gain in dB."""
        raise NotImplementedError
