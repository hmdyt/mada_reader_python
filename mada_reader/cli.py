from mada_reader.parser import parse_headers, read_file
import typer

app = typer.Typer()


@app.command()
def show(mada_path: str):
    """show header"""
    b = read_file(mada_path)
    events = parse_headers(b)
    print_string = "trigger\tclock\tinput2\n" + "\n".join(map(lambda e: e.col(), events))
    print(print_string)


@app.command()
def greet(msg: str):
    print(msg)


if __name__ == "__main__":
    app()
