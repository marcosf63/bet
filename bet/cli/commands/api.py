"""API command - discover APIs from web pages."""

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import typer
from rich.console import Console

from bet.utils import obter_apis_sofascore, testar_interceptador_sofascore

console = Console()


def api_command(
    url: str = typer.Argument(..., help="URL da página para descobrir APIs"),
    mostrar_detalhes: bool = typer.Option(
        False, "--detalhes", "-d", help="Mostra detalhes adicionais das APIs"
    ),
    salvar: bool = typer.Option(
        False, "--salvar", "-s", help="Salva as APIs encontradas em arquivo JSON"
    ),
):
    """Descobre todas as APIs de uma página web (comando: api)."""
    console.print(f"[cyan]🔍 Descobrindo APIs da URL: {url}[/cyan]\n")

    try:
        # Usar função específica do SofaScore se for uma URL do SofaScore, senão usar genérica
        if "sofascore.com" in url.lower():
            console.print(
                "[dim]🎯 URL do SofaScore detectada, usando interceptador otimizado...[/dim]\n"
            )

            if mostrar_detalhes:
                # Usar função detalhada que mostra tabela
                testar_interceptador_sofascore(url)
                return
            else:
                # Usar função simples que retorna só as URLs
                apis = obter_apis_sofascore(url)
        else:
            # Para outros sites, usar função genérica
            console.print("[dim]🌐 Usando interceptador genérico...[/dim]\n")
            apis = obter_apis_sofascore(url)  # Esta função já funciona para qualquer URL

        if not apis:
            console.print("[yellow]❌ Nenhuma API encontrada na página[/yellow]")
            return

        # Mostrar resultados
        console.print(f"[green]✅ Encontradas {len(apis)} APIs:[/green]\n")

        # Agrupar APIs por tipo/domínio para melhor organização
        apis_agrupadas = {}
        for api_url in apis:
            try:
                parsed_url = urlparse(api_url)
                dominio = parsed_url.netloc

                if dominio not in apis_agrupadas:
                    apis_agrupadas[dominio] = []
                apis_agrupadas[dominio].append(api_url)
            except:
                # Se não conseguir fazer parse, colocar em "outros"
                if "outros" not in apis_agrupadas:
                    apis_agrupadas["outros"] = []
                apis_agrupadas["outros"].append(api_url)

        # Mostrar APIs agrupadas por domínio
        for dominio, urls in apis_agrupadas.items():
            console.print(f"[bold blue]📡 {dominio} ({len(urls)} APIs):[/bold blue]")
            for i, api_url in enumerate(urls, 1):
                # Truncar URLs muito longas para melhor visualização
                url_display = api_url if len(api_url) <= 80 else api_url[:77] + "..."
                console.print(f"   {i:2d}. {url_display}")
            console.print()

        # Salvar em arquivo se solicitado
        if salvar:
            parsed_original = urlparse(url)
            nome_arquivo = (
                f"apis_{parsed_original.netloc}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            arquivo_path = Path(f"data/apis/{nome_arquivo}")
            arquivo_path.parent.mkdir(parents=True, exist_ok=True)

            dados_para_salvar = {
                "url_original": url,
                "timestamp": datetime.now().isoformat(),
                "total_apis": len(apis),
                "apis_por_dominio": apis_agrupadas,
                "todas_apis": apis,
            }

            with open(arquivo_path, "w", encoding="utf-8") as f:
                json.dump(dados_para_salvar, f, ensure_ascii=False, indent=2)

            console.print(f"[green]💾 APIs salvas em: {arquivo_path}[/green]")

        # Mostrar resumo
        console.print("[bold yellow]📊 RESUMO:[/bold yellow]")
        console.print(f"   • Total de APIs: [cyan]{len(apis)}[/cyan]")
        console.print(f"   • Domínios únicos: [green]{len(apis_agrupadas)}[/green]")
        console.print(f"   • URL analisada: [dim]{url}[/dim]")

    except Exception as e:
        console.print(f"[red]❌ Erro ao descobrir APIs: {e}[/red]")
