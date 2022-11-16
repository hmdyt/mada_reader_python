import sys
from pathlib import Path

from mada_reader.files import scan_mada_files
from mada_reader.models.mada_config import parse as parse_mada_config
from mada_reader.parser import parse_headers, read_file, parse_events
from mada_reader.rootfile_generator import gbkb
from mada_reader.vis import vis_flush_adc
import typer
from rich.progress import track

app = typer.Typer()


@app.command()
def show(mada_path: Path):
    """
    show header
    """
    b = read_file(mada_path)
    events = parse_headers(b)
    print_string = "trigger\tclock\tinput2\n" + "\n".join(map(lambda e: e.col(), events))
    print(print_string)


@app.command()
def fadc(mada_path: str, event_id: int):
    """
    visuallize FADC waveform
    """
    b = read_file(mada_path)
    events = parse_events(b)
    vis_flush_adc(events[event_id].fadc)


@app.command()
def root(
    dir: Path = Path("."),
    config_file: Path = Path("MADA_config.json"),
    period_ini: int = 0,
    period_fin: int = 0,
):
    """
    convert .mada into .root
    """
    with open(dir / config_file) as f:
        mada_config = parse_mada_config(f.read())
    mada_files = scan_mada_files(dir, mada_config, period_ini, period_fin)
    for mada_file in track(mada_files, description="Processing..."):
        print(mada_file, file=sys.stderr)
        gbkb.mada_to_root(mada_file)


@app.command()
def single(path_to_mada: Path):
    """
    convert .mada to .root (single file)
    """
    gbkb.mada_to_root(path_to_mada)


if __name__ == "__main__":
    app()
