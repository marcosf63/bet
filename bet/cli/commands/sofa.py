"""SofaScore command - fetch scheduled games."""

import json
from datetime import date, datetime
from pathlib import Path

import typer
from rich.console import Console

from bet.services.sofascore.client import get_scheduled_events, get_scheduled_events_demo
from bet.utils import print_table

console = Console()


def sofa_command(
    data: str = typer.Option(
        date.today().strftime("%Y-%m-%d"),
        help="Data dos jogos no formato AAAA-MM-DD.",
    ),
    liga: str = typer.Option(None, help="Filtra jogos por uma liga específica (busca parcial)."),
    status: str = typer.Option(
        None, help="Filtra jogos por status (ex: ended, notstarted, inprogress, postponed)."
    ),
    salvar: bool = typer.Option(False, help="Se verdadeiro, salva o resultado em JSON."),
    demo: bool = typer.Option(False, help="Usar dados de demonstração (quando API não funciona)."),
):
    """Busca jogos agendados do SofaScore (comando: sofa)."""
    if demo:
        console.print("[cyan]Usando dados de demonstracao...[/cyan]")
        eventos = get_scheduled_events_demo()
    else:
        console.print(f"[cyan]Buscando jogos para {data}...[/cyan]")
        eventos = get_scheduled_events(data)

    if not eventos:
        console.print(f"[yellow]Nenhum jogo encontrado para {data}[/yellow]")
        return

    # Filtrar por liga
    if liga:
        eventos_filtrados = [e for e in eventos if liga.lower() in e.tournament.name.lower()]
        if eventos_filtrados:
            eventos = eventos_filtrados
            console.print(f"[green]Filtrado por liga '{liga}': {len(eventos)} jogos[/green]")
        else:
            console.print(f"[yellow]Nenhum jogo para liga '{liga}'[/yellow]")
            return

    # Filtrar por status
    if status:
        eventos_filtrados = [
            e
            for e in eventos
            if status.lower() in e.status.type.lower()
            or status.lower() in e.status.description.lower()
        ]
        if eventos_filtrados:
            eventos = eventos_filtrados
            console.print(f"[green]Filtrado por status '{status}': {len(eventos)} jogos[/green]")
        else:
            console.print(f"[yellow]Nenhum jogo com status '{status}'[/yellow]")
            return

    # Ordenar por horário
    eventos = sorted(eventos, key=lambda e: e.startTimestamp)

    # Preparar dados
    jogos_para_tabela = []
    data_entrada = datetime.strptime(data, "%Y-%m-%d")
    data_entrada_str = data_entrada.strftime("%d/%m")

    for evento in eventos:
        dt = datetime.fromtimestamp(evento.startTimestamp)
        if dt.strftime("%d/%m") != data_entrada_str:
            continue

        pais = ""
        if (
            evento.tournament.category
            and "country" in evento.tournament.category
            and evento.tournament.category["country"]
            and "name" in evento.tournament.category["country"]
        ):
            pais = evento.tournament.category["country"]["name"]

        placar_casa = (
            evento.homeScore.current
            if evento.homeScore and evento.homeScore.current is not None
            else "-"
        )
        placar_visitante = (
            evento.awayScore.current
            if evento.awayScore and evento.awayScore.current is not None
            else "-"
        )

        url_partida = ""
        if evento.slug and evento.customId:
            url_partida = f"https://www.sofascore.com/pt/football/match/{evento.slug}/{evento.customId}#id:{evento.id}"

        jogos_para_tabela.append(
            {
                "Horario": dt.strftime("%H:%M"),
                "Data": dt.strftime("%d/%m"),
                "Liga": evento.tournament.name,
                "Pais": pais,
                "Casa": evento.homeTeam.name,
                "Visitante": evento.awayTeam.name,
                "Gols Casa": str(placar_casa),
                "Gols Visitante": str(placar_visitante),
                "Status": evento.status.description,
                "CustomID": evento.customId or "",
                "Slug": evento.slug or "",
                "URL": url_partida,
                "ID": str(evento.id),
            }
        )

    # Mostrar tabela
    console.print(
        f"\n[bold green]Jogos encontrados para {data}: {len(jogos_para_tabela)}[/bold green]"
    )
    print_table(jogos_para_tabela)

    # Salvar dados
    if salvar:
        data_dir = Path("/home/marcos/projetos/bet/data/sofa")
        data_dir.mkdir(parents=True, exist_ok=True)

        sufixos = []
        if liga:
            sufixos.append(f"liga-{liga.replace(' ', '-').lower()}")
        if status:
            sufixos.append(f"status-{status.replace(' ', '-').lower()}")

        sufixo = "_" + "_".join(sufixos) if sufixos else ""
        arquivo_json = data_dir / f"jogos_agendados_{data}{sufixo}.json"

        dados_para_salvar = {
            "metadata": {
                "data_busca": data,
                "filtro_liga": liga,
                "filtro_status": status,
                "total_jogos": len(jogos_para_tabela),
                "gerado_em": datetime.now().isoformat(),
            },
            "jogos": jogos_para_tabela,
        }

        with open(arquivo_json, "w", encoding="utf-8") as f:
            json.dump(dados_para_salvar, f, ensure_ascii=False, indent=2)

        console.print(f"[green]Dados salvos em: {arquivo_json}[/green]")

    # Estatísticas
    ligas_count = {}
    for evento in eventos:
        liga_nome = evento.tournament.name
        ligas_count[liga_nome] = ligas_count.get(liga_nome, 0) + 1

    console.print("\n[bold yellow]Top 5 Ligas:[/bold yellow]")
    top_ligas = sorted(ligas_count.items(), key=lambda x: x[1], reverse=True)[:5]
    for liga_nome, count in top_ligas:
        console.print(f"  {liga_nome}: {count} jogos")
