import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import typer
from rich.console import Console
from rich.progress import track
from rich.table import Table

from mada_reader.files import scan_mada_files_from_path
from mada_reader.models.mada_config import get_mada_config
from mada_reader.parser import parse_events, parse_headers, read_file
from mada_reader.pyroot_lib.clock_hist import clock_hist, save_clock_hist_png
from mada_reader.rootfile_generator import gbkb
from mada_reader.vis import vis_flush_adc

app = typer.Typer(pretty_exceptions_show_locals=True)


@app.command()
def show(mada_path: Path):
    """
    show header info
    """
    b = read_file(mada_path)
    events = parse_headers(b)
    print_string = "trigger\tclock\tinput2\n" + "\n".join(map(lambda e: e.col(), events))
    print(print_string)


@app.command()
def fadc(mada_path: str, event_id: int, im: str = "flush_adc.png"):
    """
    visuallize FADC waveform (single event)
    """
    b = read_file(mada_path)
    events = parse_events(b)
    vis_flush_adc(events[event_id].fadc, save_file_name=im)


@app.command()
def root(
    dir: Path = Path("."),
    config_file: Path = Path("MADA_config.json"),
    period_ini: int = 0,
    period_fin: int = 0,
):
    """
    .madaを.rootに (perXXXX以下のmadaを走査する)
    """
    mada_files = scan_mada_files_from_path(dir, config_file, period_ini, period_fin)
    for mada_file in track(mada_files, description="Processing..."):
        print(mada_file, file=sys.stderr)
        gbkb.mada_to_root(mada_file)


@app.command()
def single(path_to_mada: Path):
    """
    .madaを.rootに (1ファイルのみ)
    """
    gbkb.mada_to_root(path_to_mada)


@app.command("detp2p")
def detect_peak_to_peak(
    dir: Path = Path("."),
    config_file: Path = Path("MADA_config.json"),
    period_ini: int = 0,
    period_fin: int = 0,
    pretty: bool = True
):
    """
    [gain測定用]
    指定したperの全てのFADCから波形のp-pを算出して, ボードごとに平均する
    """
    mada_config = get_mada_config(config_file)
    mada_files = scan_mada_files_from_path(dir, config_file, period_ini, period_fin)
    mada_files_group_by_name: Dict[str, List[Path]] = {board_name: [] for board_name in mada_config.available_boards}
    for mada_file in mada_files:
        board_name = mada_file.name[:7]
        mada_files_group_by_name[board_name].append(mada_file)

    results: Dict[str, Tuple[float, float, float, float]] = \
        {board_name: (0, 0, 0, 0) for board_name in mada_config.available_boards}  # GBKB-XX: (sum, count)

    for board_name, mada_file_list in track(mada_files_group_by_name.items(), description="Processing...", transient=True):
        concatenating_arrays = [
            gbkb.get_fadc_peak2peak_from_mada_file(mada_file)
            for mada_file in mada_file_list
        ]
        concatenating_arrays = list(filter(lambda x: x.size > 0, concatenating_arrays))
        fadc_p2p_list = np.concatenate(concatenating_arrays)
        results[board_name] = tuple(np.average(fadc_p2p_list, axis=0))

    if pretty:
        table = Table(title="p2p average summary")
        console = Console()
        table.add_column("Board Name")
        table.add_column("ch0", justify="right")
        table.add_column("ch1", justify="right")
        table.add_column("ch2", justify="right")
        table.add_column("ch3", justify="right")
        for board_name, fadc_p2p_averages in results.items():
            ch0, ch1, ch2, ch3 = map(lambda x: str(int(x)), fadc_p2p_averages)
            table.add_row(board_name, ch0, ch1, ch2, ch3)
        console.print(table)
    else:
        print("board name, ch0, ch1, ch2, ch3")
        for board_name, fadc_p2p_averages in results.items():
            ch0, ch1, ch2, ch3 = map(lambda x: str(int(x)), fadc_p2p_averages)
            print("{}, {}, {}, {}, {}".format(board_name, ch0, ch1, ch2, ch3))


@app.command("detamps")
def detect_peak_to_peak(
    dir: Path = Path("."),
    config_file: Path = typer.Option(Path("MADA_config.json"), "--config", "-c", help="MADA_configへのパス"),
    period_ini: int = typer.Option(0, "--ini", "-f", help="ファイル番号の最初"),
    period_fin: int = typer.Option(0, "--fin", "-t", help="ファイル番号の最後"),
):
    """
    [gain測定用]
    指定したperの全てのFADCから波形のampを算出して, ボードごとに平均する
    """
    mada_config = get_mada_config(config_file)
    mada_files = scan_mada_files_from_path(dir, config_file, period_ini, period_fin)
    mada_files_group_by_name: Dict[str, List[Path]] = {board_name: [] for board_name in mada_config.available_boards}
    for mada_file in mada_files:
        board_name = mada_file.name[:7]
        mada_files_group_by_name[board_name].append(mada_file)

    results: Dict[str, Tuple[gbkb.FlushADCAmplitude, gbkb.FlushADCAmplitude]] = \
        {board_name: None for board_name in mada_config.available_boards}

    for board_name, mada_file_list in track(mada_files_group_by_name.items(), description="Processing...", transient=True):
        amps_min_list, amps_max_list = [], []
        for mada_file in mada_file_list:
            amps_min, amps_max = gbkb.get_fadc_amplitude_from_mada_file(mada_file)
            amps_min_list.append(amps_min)
            amps_max_list.append(amps_max)

        results[board_name] = (
            gbkb.average_flush_adc_amplitudes(amps_min_list),
            gbkb.average_flush_adc_amplitudes(amps_max_list)
        )

    print("board name, ch0, ch1, ch2, ch3")
    for board_name, (amp_min, amp_max) in results.items():
        print("{}, {}, {}, {}, {}".format(board_name, *map(int, amp_min.value)))
        print("{}, {}, {}, {}, {}".format(board_name, *map(int, amp_max.value)))


@app.command("clock")
def command_clock_hist(target_rootfile_path: Path, imgcat: bool = False):
    """
    mada_reader root で作ったrootファイルを見る
    clockの分布を出力する
    """
    hist = clock_hist(str(target_rootfile_path))
    save_png_path = target_rootfile_path.parent / Path(f"{target_rootfile_path.stem}_clock.png")
    save_clock_hist_png(hist, save_png_path)
    if imgcat:
        subprocess.run(f"imgcat {save_png_path}", shell=True)


if __name__ == "__main__":
    app()
