import asyncio
import json
import time
from datetime import date, datetime

import requests
from rich import print

from bet.config import settings
from bet.core.models import Event, ScheduledEvent

try:
    from playwright.async_api import async_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


def get_live_events() -> list[Event]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }
    resp = requests.get(settings.sofascore_live_url, headers=headers)
    resp.raise_for_status()
    events_list = resp.json()["events"]
    return [Event(**event) for event in events_list]


def get_scheduled_events(target_date: str = None) -> list[ScheduledEvent]:
    """
    Busca eventos agendados para uma data específica.

    Args:
        target_date (str): Data no formato YYYY-MM-DD. Se None, usa a data atual.

    Returns:
        List[ScheduledEvent]: Lista de eventos agendados filtrados por data.
    """
    if target_date is None:
        target_date = date.today().strftime("%Y-%m-%d")

    # Headers mais completos para evitar detecção de bot
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9,pt;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.sofascore.com/",
        "Origin": "https://www.sofascore.com",
        "DNT": "1",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    url = f"https://www.sofascore.com/api/v1/sport/football/scheduled-events/{target_date}"

    try:
        print(f"[dim]Tentando acessar: {url}[/dim]")
        resp = requests.get(url, headers=headers, timeout=15)

        if resp.status_code == 403:
            print("[red]⚠️  API SofaScore retornou 403 (Forbidden)[/red]")
            print("[yellow]🔄 Tentando acessar via Playwright...[/yellow]")

            # Tentar com Playwright como fallback
            if PLAYWRIGHT_AVAILABLE:
                return _get_scheduled_events_playwright(target_date)
            else:
                print(
                    "[red]❌ Playwright não disponível. Instale com: pip install playwright[/red]"
                )
                print("[yellow]💡 Depois execute: playwright install chromium[/yellow]")
                return []
        elif resp.status_code == 429:
            print("[red]⚠️  Rate limit excedido (429)[/red]")
            print("[yellow]💡 Aguarde alguns minutos antes de tentar novamente[/yellow]")
            return []

        resp.raise_for_status()
        events_data = resp.json()

        if "events" not in events_data:
            print(f"[yellow]Nenhum evento encontrado para {target_date}[/yellow]")
            print(f"[dim]Chaves disponíveis: {list(events_data.keys())}[/dim]")
            return []

        events_list = events_data["events"]
        scheduled_events = []

        # Converter target_date para timestamp para comparação
        target_datetime = datetime.strptime(target_date, "%Y-%m-%d")
        target_timestamp_start = int(target_datetime.timestamp())
        target_timestamp_end = int(target_datetime.timestamp() + 24 * 60 * 60)  # Fim do dia

        print(f"[dim]Processando {len(events_list)} eventos...[/dim]")

        for event_data in events_list:
            try:
                # Verificar se o evento tem os campos necessários
                if "startTimestamp" not in event_data:
                    continue

                event = ScheduledEvent(**event_data)
                # Filtrar eventos que estão dentro do dia especificado
                if target_timestamp_start <= event.startTimestamp < target_timestamp_end:
                    scheduled_events.append(event)
            except Exception as e:
                print(
                    f"[red]Erro ao processar evento {event_data.get('id', 'desconhecido')}: {e}[/red]"
                )
                continue

        print(f"[green]✅ Encontrados {len(scheduled_events)} eventos para {target_date}[/green]")
        return scheduled_events

    except requests.exceptions.Timeout:
        print("[red]⏰ Timeout ao acessar API SofaScore[/red]")
        return []
    except requests.exceptions.ConnectionError:
        print("[red]🔌 Erro de conexão com API SofaScore[/red]")
        return []
    except requests.exceptions.RequestException as e:
        print(f"[bold red]Erro ao buscar eventos agendados para {target_date}: {e}[/bold red]")
        return []
    except Exception as e:
        print(f"[red]Erro inesperado: {e}[/red]")
        return []


def get_scheduled_events_demo() -> list[ScheduledEvent]:
    """
    Retorna eventos de exemplo para demonstração quando a API não está disponível.
    """
    from datetime import datetime

    print("[yellow]📋 Usando dados de demonstração (API indisponível)[/yellow]")

    # Criar eventos de exemplo
    demo_events = []
    base_timestamp = int(datetime.now().timestamp())

    demo_data = [
        {
            "id": 12345,
            "startTimestamp": base_timestamp + 3600,  # +1 hora
            "customId": "arsenal-chelsea",
            "slug": "arsenal-vs-chelsea",
            "tournament": {"name": "Premier League", "category": {"country": {"name": "England"}}},
            "status": {"description": "Not started", "type": "notstarted"},
            "homeTeam": {"name": "Arsenal", "slug": "arsenal", "shortName": "ARS"},
            "awayTeam": {"name": "Chelsea", "slug": "chelsea", "shortName": "CHE"},
        },
        {
            "id": 12346,
            "startTimestamp": base_timestamp + 7200,  # +2 horas
            "customId": "real-madrid-barcelona",
            "slug": "real-madrid-vs-barcelona",
            "tournament": {"name": "La Liga", "category": {"country": {"name": "Spain"}}},
            "status": {"description": "Not started", "type": "notstarted"},
            "homeTeam": {"name": "Real Madrid", "slug": "real-madrid", "shortName": "RMA"},
            "awayTeam": {"name": "Barcelona", "slug": "barcelona", "shortName": "BAR"},
        },
    ]

    for event_data in demo_data:
        try:
            demo_events.append(ScheduledEvent(**event_data))
        except Exception as e:
            print(f"[red]Erro ao criar evento demo: {e}[/red]")

    return demo_events


def _get_scheduled_events_playwright(target_date: str) -> list[ScheduledEvent]:
    """
    Função auxiliar para buscar eventos usando Playwright quando requests falhar.
    """
    if not PLAYWRIGHT_AVAILABLE:
        print("[red]❌ Playwright não disponível[/red]")
        return []

    try:
        # Executar função assíncrona em loop síncrono
        return asyncio.run(_fetch_with_playwright(target_date))
    except Exception as e:
        print(f"[red]❌ Erro no Playwright: {e}[/red]")
        return []


async def _fetch_with_playwright(target_date: str) -> list[ScheduledEvent]:
    """
    Função assíncrona que usa Playwright para acessar a API SofaScore.
    """
    url = f"https://www.sofascore.com/api/v1/sport/football/scheduled-events/{target_date}"

    print(f"[cyan]🎭 Acessando via Playwright: {url}[/cyan]")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--disable-extensions",
                "--disable-dev-shm-usage",
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            ],
        )

        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            extra_http_headers={
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
        )

        page = await context.new_page()
        captured_response = None

        # Interceptar resposta da API específica
        async def capture_response(response):
            nonlocal captured_response
            if f"scheduled-events/{target_date}" in response.url and response.status == 200:
                try:
                    content_type = response.headers.get("content-type", "")
                    if "application/json" in content_type:
                        json_data = await response.json()
                        if "events" in json_data:  # Verificar se tem eventos
                            captured_response = json_data
                            print(
                                "[green]✅ JSON com eventos capturado da API via interceptação[/green]"
                            )
                        else:
                            print(
                                f"[yellow]📅 API interceptada mas sem eventos para {target_date}[/yellow]"
                            )
                except Exception as e:
                    print(f"[yellow]⚠️  Erro ao capturar resposta JSON: {e}[/yellow]")

        page.on("response", capture_response)

        try:
            # Primeiro visitar página principal para estabelecer contexto
            print("[dim]🌐 Estabelecendo contexto no SofaScore...[/dim]")
            await page.goto("https://www.sofascore.com/", wait_until="load", timeout=30000)
            await page.wait_for_timeout(3000)

            print("[dim]📊 Aguardando carregamento das APIs...[/dim]")

            # Navegar para página de futebol da data específica para acionar a API
            football_page_url = f"https://www.sofascore.com/pt/futebol/{target_date}"
            try:
                await page.goto(football_page_url, wait_until="load", timeout=20000)
                print(f"[dim]📄 Página carregada: {football_page_url}[/dim]")

                # Aguardar APIs carregarem com timeout mais conservador
                await page.wait_for_timeout(8000)

                # Se ainda não capturou, aguardar mais um pouco
                if not captured_response:
                    print("[dim]⏱️ Aguardando mais tempo para APIs...[/dim]")
                    await page.wait_for_timeout(5000)

            except Exception as e:
                print(f"[yellow]⚠️  Timeout na navegação, mas continuando: {e}[/yellow]")
                # Mesmo com timeout, tentar aguardar as APIs
                await page.wait_for_timeout(3000)

            # Verificar se capturou a resposta através da interceptação
            if captured_response and "events" in captured_response:
                events_data = captured_response
                events_list = events_data["events"]
                scheduled_events = []

                print(f"[dim]📊 Interceptação capturou {len(events_list)} eventos totais[/dim]")

                # Para funcionalidade de busca de jogos de ontem/outras datas,
                # NÃO filtrar por timestamp, pois a API já retorna jogos da data correta
                for event_data in events_list:
                    try:
                        if "startTimestamp" not in event_data:
                            continue

                        event = ScheduledEvent(**event_data)
                        scheduled_events.append(event)
                    except Exception as e:
                        print(
                            f"[red]Erro ao processar evento {event_data.get('id', 'desconhecido')}: {e}[/red]"
                        )
                        continue

                print(
                    f"[green]✅ Playwright: Processados {len(scheduled_events)} eventos para {target_date}[/green]"
                )
                return scheduled_events
            else:
                print("[yellow]⚠️  API não foi interceptada. Tentando acesso direto...[/yellow]")

                # Fallback: tentar acesso direto à API
                response = await page.goto(url, wait_until="load", timeout=30000)

                if response.status == 200:
                    text_content = await page.inner_text("body")

                    if text_content.strip().startswith("{"):
                        try:
                            events_data = json.loads(text_content)

                            if "events" in events_data:
                                events_list = events_data["events"]
                                scheduled_events = []

                                target_datetime = datetime.strptime(target_date, "%Y-%m-%d")
                                target_timestamp_start = int(target_datetime.timestamp())
                                target_timestamp_end = int(
                                    target_datetime.timestamp() + 24 * 60 * 60
                                )

                                print(
                                    f"[dim]Processando {len(events_list)} eventos via acesso direto...[/dim]"
                                )

                                for event_data in events_list:
                                    try:
                                        if "startTimestamp" not in event_data:
                                            continue

                                        event = ScheduledEvent(**event_data)
                                        if (
                                            target_timestamp_start
                                            <= event.startTimestamp
                                            < target_timestamp_end
                                        ):
                                            scheduled_events.append(event)
                                    except Exception as e:
                                        print(
                                            f"[red]Erro ao processar evento {event_data.get('id', 'desconhecido')}: {e}[/red]"
                                        )
                                        continue

                                print(
                                    f"[green]✅ Playwright (direto): Encontrados {len(scheduled_events)} eventos para {target_date}[/green]"
                                )
                                return scheduled_events
                            else:
                                print(
                                    f"[yellow]Nenhum evento encontrado para {target_date}[/yellow]"
                                )
                                return []
                        except json.JSONDecodeError as e:
                            print(f"[red]❌ Erro ao decodificar JSON: {e}[/red]")
                            return []
                    else:
                        print("[red]❌ Resposta não é JSON válido[/red]")
                        return []
                else:
                    print(f"[red]❌ Status {response.status} no acesso direto[/red]")
                    return []

        finally:
            await browser.close()


def get_live_no_gol_events(all_events: list[Event]) -> list[Event]:
    no_gol_events = []
    for event in all_events:
        home_score = event.homeScore.current if event.homeScore.current is not None else 0
        away_score = event.awayScore.current if event.awayScore.current is not None else 0
        if home_score + away_score == 0:
            # print(f'{event.homeTeam.name} {home_score} x {away_score} {event.awayTeam.name}')
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

                    home_score = (
                        event.homeScore.current if event.homeScore.current is not None else 0
                    )
                    away_score = (
                        event.awayScore.current if event.awayScore.current is not None else 0
                    )
                    print(
                        f"[bold green]{event.homeTeam.name} {home_score} x {away_score} {event.awayTeam.name}[/bold green]"
                    )

        else:
            print("Nenhum evento saiu gol.")

        # Atualiza o conjunto de eventos "parados" para a próxima iteração
        previous_no_gol_events = current_no_gol_events

        # Aguarda 60 segundos antes da próxima verificação
        time.sleep(60)


if __name__ == "__main__":
    events = get_live_events()
    print(len(events))
    no_gol = get_live_no_gol_events(events)
    print(len(no_gol))
