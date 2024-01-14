import typer
from rich import print

# from rich.table import Table

from .config import settings
from .core import (
    calcula_saida_edge_black_lay,
    calcula_saida_edge_lay_back,
    calcula_saida_freebet_lay,
)


main = typer.Typer(name="Bet CLI")


@main.command()
def shell():
    """Opens interactive shell"""
    _vars = {
        "settings": settings,
        "calcula_saida_edge_black_lay": calcula_saida_edge_black_lay,
        "calcula_saida_edge_lay_back": calcula_saida_edge_lay_back,
        "calcula_saida_freebet_lay": calcula_saida_freebet_lay,
    }
    typer.echo(f"Auto imports: {list(_vars.keys())}")
    try:
        from IPython import start_ipython

        start_ipython(argv=["--ipython-dir=/tmp", "--no-banner"], user_ns=_vars)
    except ImportError:
        import code

        code.InteractiveConsole(_vars).interact()


@main.command()
def cbl(odd_entrada_back: float, odd_saida_lay: float, stake: float):
    """Calcula o valor da saída em edge, entrando back e saindo em lay"""
    print(calcula_saida_edge_black_lay(odd_entrada_back, odd_saida_lay, stake))

@main.command()
def lbl(odd_entrada_back: float, odd_saida_lay: float, stake: float):
    """Calcula o lucro da saida em edge entrando em back e saindo em lay"""
    print(calcula_saida_edge_black_lay(odd_entrada_back, odd_saida_lay, stake)-stake)


@main.command()
def clb(odd_entrada_lay: float, odd_saida_back: float, responsabilidade: float):
    """Calcula o valor da saída em edge, entrando lay e saindo em back"""
    print(calcula_saida_edge_lay_back(odd_entrada_lay, odd_saida_back, responsabilidade))

@main.command()
def llb(odd_entrada_lay: float, responsabilidade: float):
    """Calcula o lucro da saida em edge entrando em lay e saindo em back"""
    print(round(responsabilidade / (odd_entrada_lay - 1),2))

