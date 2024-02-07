import typer

app = typer.Typer()


@app.command()
def parse(file: str, merge: bool = False) -> None:
    """
    Parse raw hpl files into netCDF files
    """
    print(f"Hello {file}")


@app.command()
def stare() -> None:
    print("stare cmd")


@app.command()
def wind() -> None:
    print("wind cmd")


if __name__ == "__main__":
    app()
