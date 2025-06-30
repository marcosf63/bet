import json
from pathlib import Path
from typing import List, Dict
import typer
from rich import print
from rich.console import Console
from rich.table import Table
from bet.exceptions import NaoExisteMercadoExcecao

from bet.files import load_json_to_dict, save_dict_to_json
from bet.utils import (
        markets_dict, 
        calcula_saida_edge_black_lay,
        calcula_saida_edge_lay_back,
        calcula_saida_freebet_lay,
        add_thirty_minutes_to_time_hm_only,
        is_time_greater_than_now,
        is_time_smaller_than_now_plus30min,
        converter_hora_para_datetime,
        verificar_tempo_passado, 
        print_table,
)  

#from bet.betfair import busca_odds_mercado, get_match_day, get_odds_event_markets, get_1_gol_segundo_tempo, get_trading
from bet.config import settings
from bet.betfair import BetfairCliente, BetfairEventos, BetfairMercados, BetfairMonitor, BetfairResulados
from bet.notification import run_timer, play_sound, send_notification

main = typer.Typer(name="Bet CLI")
console = Console()
#trading = get_trading()
cliente = BetfairCliente(
        username=settings.username, 
        password=settings.password, 
        app_key=settings.app_key,
        certs=settings.certs_dir,
)



def get_lista_jogos(file_path: str, cliente: BetfairCliente) -> List[Dict]:
    if Path(file_path).exists():
        lista_jogos: List[Dict[str, str]] = load_json_to_dict(file_path)
        print("Dados carregados.")
    else:
        print("Buscado dados na Betfair...")
        if not cliente.session_active:
            cliente.login()
        betfair_eventos = BetfairEventos(cliente)
        lista_jogos = betfair_eventos.get_match_day()
        save_dict_to_json(lista_jogos, file_path)
        print("Dados salvos.")
    return lista_jogos

@main.command()
def shell():
    """Opens interactive shell"""
    _vars = {
        "settings": settings,
        "calcula_saida_edge_black_lay": calcula_saida_edge_black_lay,
        "calcula_saida_edge_lay_back": calcula_saida_edge_lay_back,
        "calcula_saida_freebet_lay": calcula_saida_freebet_lay,
        "add_thirty_minutes_to_time_hm_only": add_thirty_minutes_to_time_hm_only,
        "is_time_smaller_than_now_plus30min": is_time_smaller_than_now_plus30min,
        "is_time_greater_than_now": is_time_greater_than_now,
        "verificar_tempo_passado": verificar_tempo_passado,
        "converter_hora_para_datetime": converter_hora_para_datetime,
        "markets_dict": markets_dict,
        "BetfairCliente": BetfairCliente,
        "BetfairEventos": BetfairEventos,
        "BetfairMercados": BetfairMercados,
        "BetfairMonitor": BetfairMonitor,
        "run_timer": run_timer,
        "play_sound": play_sound,
        "send_notification": send_notification
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
    print(calcula_saida_edge_black_lay(odd_entrada_back, odd_saida_lay, stake) - stake)


@main.command()
def clb(odd_entrada_lay: float, odd_saida_back: float, responsabilidade: float):
    """Calcula o valor da saída em edge, entrando lay e saindo em back"""
    print(
        calcula_saida_edge_lay_back(odd_entrada_lay, odd_saida_back, responsabilidade)
    )


@main.command()
def llb(odd_entrada_lay: float, responsabilidade: float):
    """Calcula o lucro da saida em edge entrando em lay e saindo em back"""
    print(round(responsabilidade / (odd_entrada_lay - 1), 2))


@main.command()
def mday(no_print: bool = False, data: str = None ) -> None:
    """Lista as partidas do dia com data/hora e id do evento"""
    dat = datetime.strptime(data, "%d/%m/%Y").date() if data is not None else date.today()
    file_path = f"{settings.data_dir}/jogos/{dat.day}-{dat.month}-{dat.year}.json"
    lista_jogos = get_lista_jogos(file_path, cliente)
    # if Path(file_path).exists():
    #     lista_jogos = load_json_to_dict(file_path)
    #     print("Dados carregados.")
    # else:
    #     print("Buscado dados na Betfair...")
    #     cliente.login()
    #     betfair_eventos = BetfairEventos(cliente)
    #     lista_jogos = betfair_eventos.get_match_day()
    #     save_dict_to_json(lista_jogos, file_path)
    #     print("Dados salvos.")
    if not no_print:
        print_table(lista_jogos)



@main.command()
def godds(
    event_id: str,
    market: str,
    ord: bool = typer.Option(False, help="Ordena CS por da menor para maior odd."),
):
    """
    lista as odds para um evento que seja informado o event_id e o mercado"
    """
    cliente.login()
    betfair_mercados = BetfairMercados(cliente)

    result = betfair_mercados.get_odds_event_markets(event_id, markets_dict[market])
    tabela = Table(
        title=f"Market: {result['market']}",
        show_header=True,
        header_style="bold magenta",
    )
    for chave in result["selections"][0].keys():
        tabela.add_column(chave)

    if ord and market == "CS":
        selections_list = sorted(result["selections"], key=lambda x: x["back_odds"])
    else:
        selections_list = result["selections"]

    for selection in selections_list:
        tabela.add_row(
            selection["name"],
            str(selection["back_odds"]),
            str(selection["lay_odds"]),
        )
    console.print(tabela)


@main.command()
def l2b(odd_lay: str) -> None:
    """Converte a odd do lay para equivalente em back"""
    file_path = Path(f"{settings.data_dir}") / "lay_to_back.json"
    with file_path.open("r") as json_file:
        lay_to_back_dict = json.load(json_file)

    console.print(lay_to_back_dict[odd_lay])


@main.command()
def bom():
    cliente.login()
    betfair_mercados = BetfairMercados(cliente)
    betfair_mercados.busca_odds_mercado()


@main.command()
def all(
    event_id: str,
):
    """
    lista as odds para um evento que seja indormado o event_id e o mercado"
    """
    #cliente.login()
    betfair_mercados = BetfairMercados(cliente)
    for market in ["MO", "BTTS", "O25", "CS"]:
        try:
            result = betfair_mercados.get_odds_event_markets(event_id, markets_dict[market])#, trading)
        except NaoExisteMercadoExcecao as e:
            #print(e)
            continue

        tabela = Table(
            title=f"Market: {result['market']}",
            show_header=True,
            header_style="bold magenta",
        )
        for chave in result["selections"][0].keys():
            tabela.add_column(chave)

        if market == "CS":
            selections_list = sorted(result["selections"], key=lambda x: x["back_odds"])
        else:
            selections_list = result["selections"]

        for selection in selections_list:
            tabela.add_row(
                selection["name"],
                str(selection["back_odds"]),
                str(selection["lay_odds"]),
            )
        console.print(tabela)


@main.command()
def gzebra():
    data = date.today()
    file_path = f"{settings.data_dir}/jogos/{data.day}-{data.month}-{data.year}.json"
    lista_jogos: list = []
    if Path(file_path).exists():
        lista_jogos = load_json_to_dict(file_path)
    print(lista_jogos)

@main.command()
def check_gol():
    """Verifica se em algum jogo 0x0 saiu gol no segundo tempo"""
    cliente.login()
    eventos = BetfairEventos(cliente)
    # Inicializa a classe BetfairMonitor
    monitor = BetfairMonitor(cliente, eventos)
    # # Monitorar eventos ao vivo para detectar o primeiro gol no segundo tempo
    try:
        monitor.monitorar_gols_segundo_tempo(intervalo=60)
    except KeyboardInterrupt:
        print("Saida solicitada pelo usuário.")
        raise typer.Exit()
        
@main.command()        
def over(no_print: bool = False):
    """Lista os jogos com tendencia over e bbts"""
    #tabela = Table(show_header=True, header_style="bold magenta")
    data = date.today()
    file_path = f"{settings.data_dir}/jogos/{data.day}-{data.month}-{data.year}.json"
    lista_jogos = get_lista_jogos(file_path, cliente)
    lista_jogos = [jogo for jogo in lista_jogos if is_time_greater_than_now(jogo.get("hora"))]
    
    file_path = f"{settings.data_dir}/over_btts/{data.day}-{data.month}-{data.year}.json"
    
    if Path(file_path).exists():
        lista_jogos_over_btts = load_json_to_dict(file_path)
        print("Dados Over BTTS carregados")
    else:


        lista_jogos_over_btts = []
        for jogo in lista_jogos:
            is_over, is_btts, is_favorito = False, False, False
            #hora = jogo.get("hora")
            evento_id = jogo.get("evento_id")
            #if not is_time_greater_than_now(hora):
                #print("Fora de hora")
                #continue
                #print(jogo.get("hora"))
            betfair_mercados = BetfairMercados(cliente)
            for market in ["MO", "BTTS", "O25", "O15"]:
                try:
                    result = betfair_mercados.get_odds_event_markets(evento_id, markets_dict[market])#, trading)
                except NaoExisteMercadoExcecao as e:
                    #print(e)
                    continue

                selections_list = result["selections"]

                if market == "O25":
                    for selection in selections_list:
                        if selection.get("name") == "Over 2.5 Goals" and selection.get("back_odds") < 1.8:
                            is_over = True
                            mercado_O25 = selection.get("back_odds")
                
                if market == "BTTS":
                    for selection in selections_list:
                        if selection.get("name") == "Yes" and selection.get("back_odds") < 1.8 and selection.get("back_odds") > 1.5:
                            is_btts = True
                            mercado_btts = selection.get("back_odds")
                
                if market == "MO":
                    #for selection in selections_list:
                    mercado_home = selections_list[0].get("back_odds")
                    mercado_away = selections_list[1].get("back_odds")
                    mercado_draw = selections_list[2].get("back_odds")
                    favorito = mercado_home if mercado_home < mercado_away else mercado_away
                    if favorito > 1.49:
                        is_favorito = True


            
                if market == "O15":
                    for selection in selections_list:
                        if selection.get("name") == "Over 1.5 Goals":
                            mercado_O15 = selection.get("back_odds")
            
            if (is_over and is_btts and is_favorito):
                jogo.update({"home": str(mercado_home)})
                jogo.update({"away": str(mercado_away)})
                jogo.update({"draw": str(mercado_draw)})
                jogo.update({"O15": str(mercado_O15)})
                jogo.update({"O25": str(mercado_O25)})
                jogo.update({"btts": str(mercado_btts)})
                lista_jogos_over_btts.append(jogo)


        if lista_jogos_over_btts == []:
            print("Dados não encontrados")
            exit()

        save_dict_to_json(lista_jogos_over_btts, file_path)


    lista_odds_O25 = [float(jogo.get("O25")) for jogo in lista_jogos_over_btts]
    lista_odds_btts = [float(jogo.get("btts")) for jogo in lista_jogos_over_btts]

    media_O25 = sum(lista_odds_O25) / len(lista_odds_O25)
    media_btts = sum(lista_odds_btts) / len(lista_odds_btts)

    print_table(lista_jogos_over_btts)

@main.command()
def lp(dt_inicio, dt_fim):
    """
    Busca lucros e perdas
    """
    result =  BetfairResulados(cliente)
    print(result.get_lucros_perdas(dt_inicio, dt_fim))




