import typer

app = typer.Typer()

@app.command()
def test(
    flag: bool = typer.Option(False, "--flag", help="Test flag"),
    other: str = typer.Option(None, "--other", help="Other option"),
):
    print(f"flag={flag}, other={other}")

if __name__ == "__main__":
    app()
