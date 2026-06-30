"""Audio effects processing chain."""


class EffectsChain:
    """Applies audio effects to tracks.

    Supported effects: EQ, compression, reverb, noise reduction, normalization.
    """

    async def apply(self, input_path: str, output_path: str, effects: list[dict]) -> str:
        """Apply a chain of effects to an audio file.

        Args:
            input_path: Path to input audio file
            output_path: Path for processed output
            effects: List of effect configs, e.g. [{"type": "eq", "params": {...}}]

        Returns:
            Path to processed audio file
        """
        raise NotImplementedError("Effects processing will be implemented in next iteration")
