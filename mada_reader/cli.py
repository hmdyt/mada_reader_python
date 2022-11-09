from mada_reader.parser import parse_headers, read_file, parse_events
from mada_reader.vis import vis_flush_adc
import typer

app = typer.Typer()


@app.command()
def show(mada_path: str):
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


if __name__ == "__main__":
    app()
