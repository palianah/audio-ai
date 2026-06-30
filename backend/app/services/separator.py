"""Demucs-based audio stem separation service."""


class StemSeparator:
    """Separates audio into individual stems using Demucs HTDemucs model.

    Supported stems: vocals, drums, bass, other
    """

    def __init__(self, model_name: str = "htdemucs_ft", device: str = "auto") -> None:
        self.model_name = model_name
        self.device = device
        self._model = None

    async def separate(self, input_path: str, output_dir: str) -> dict[str, str]:
        """Separate audio file into stems.

        Args:
            input_path: Path to input audio file
            output_dir: Directory to save separated stems

        Returns:
            Dict mapping stem name to output file path
        """
        raise NotImplementedError(
            "Stem separation will be implemented in next iteration"
        )
