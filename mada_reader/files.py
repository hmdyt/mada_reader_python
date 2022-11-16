from typing import List
from pathlib import Path
from mada_reader.models.mada_config import MadaConfig


def scan_mada_files(
    dir: Path,
    mada_config: MadaConfig,
    initial_period: int = 0,
    final_period: int = 0
) -> List[Path]:
    target_mada_files: List[Path] = []
    active_gigaiwaki = filter(lambda x: x.is_active, mada_config.giga_iwaki)
    for gigaiwaki_config in active_gigaiwaki:
        for per in range(initial_period, final_period + 1):
            per = str(per).zfill(4)  # 1 -> 0001
            target_mada_files.append(
                dir / Path(f"{gigaiwaki_config.name}_{per}.mada")
            )

    # file existance check
    for target_mada_file in target_mada_files:
        if not target_mada_file.exists():
            raise FileExistsError(f"file {target_mada_file} not exists")

    target_mada_files.sort(key=lambda x: x.name[5:7])
    target_mada_files.sort(key=lambda x: x.name[8:12])

    return target_mada_files
