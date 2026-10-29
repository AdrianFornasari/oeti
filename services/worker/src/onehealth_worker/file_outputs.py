"""Reject output paths that alias protected inputs before starting file work."""
from pathlib import Path


def paths_alias(first: Path, second: Path) -> bool:
    return first.resolve() == second.resolve() or (
        first.exists() and second.exists() and first.samefile(second)
    )


def check_input_output(input_file: Path, output: Path | None) -> None:
    if output is not None and paths_alias(input_file, output):
        raise ValueError("El informe de entrada no puede ser el archivo de salida.")
