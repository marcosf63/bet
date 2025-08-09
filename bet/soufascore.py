from typing import List
import time
import requests
from rich import print

from bet.config import settings
from bet.models import Event


def get_live_events() -> List[Event]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }
    resp = requests.get(settings.sofascore_live_url)
    resp.raise_for_status()
    events_list = resp.json()["events"]
    return [Event(**event) for event in events_list]


def get_live_no_gol_events(all_events: List[Event]) -> List[Event]:
    no_gol_events = []
    for event in all_events:
        if event.homeScore.current + event.awayScore.current == 0:
            # print(f'{event.homeTeam.name} {event.homeScore.current} x {event.awayScore.current} {event.awayTeam.name}')
            no_gol_events.append(event)
    return no_gol_events


def check_events():
    previous_no_gol_events = (
        set()
    )  # Conjunto vazio para armazenar os eventos "parados" da iteração anterior

    while True:
        all_events = get_live_events()

        # Busca os eventos que estão atualmente com status "parado"
        current_no_gol_events = set(get_live_no_gol_events(all_events))

        # Identifica os eventos que saíram do status "parado" em relação ao minuto anterior
        one_gol_events = previous_no_gol_events - current_no_gol_events

        if one_gol_events:
            for event in one_gol_events:
                if event.status.description == "2nd half":
                    print("Eventos com 1 gol no segundo tempo")
                    if event.tournament.category["country"]:
                        print(
                            f"{event.tournament.name} - {event.tournament.category['country']['name']}"
                        )
                    else:
                        print(f"{event.tournament.name}")

                    print(
                        f"[bold green]{event.homeTeam.name} {event.homeScore.current} x {event.awayScore.current} {event.awayTeam.name}[/bold green]"
                    )

        else:
            print("Nenhum evento saiu gol.")

        # Atualiza o conjunto de eventos "parados" para a próxima iteração
        previous_no_gol_events = current_no_gol_events

        # Aguarda 60 segundos antes da próxima verificação
        time.sleep(60)


if __name__ == "__main__":
    events = get_events_live()
    print(len(events))
    no_gol = get_events_live_no_gol(events)
    print(len(no_gol))
