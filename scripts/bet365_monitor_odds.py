#!/usr/bin/env python3
"""
Bet365 Under Limite Odds Monitor

Monitora as odds do mercado "Under Limite" de um jogo específico na Bet365.
Envia notificações do sistema quando as odds mudam.

Uso:
    python scripts/bet365_monitor_odds.py "https://www.bet365.bet.br/#/IP/EV151260177742C1"
    python scripts/bet365_monitor_odds.py "URL" --debug  # Modo debug (salva todas requisições)
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright
from plyer import notification
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

console = Console()


class UnderLimiteMonitor:
    """Monitors Under Limite odds for a specific Bet365 game."""

    def __init__(self, url: str, debug: bool = False):
        self.url = url
        self.debug = debug
        self.current_odd: Optional[float] = None
        self.last_update: Optional[datetime] = None
        self.update_count = 0
        self.api_requests_captured = 0

        # Create debug directory if in debug mode
        if self.debug:
            self.debug_dir = Path("data/bet365_debug")
            self.debug_dir.mkdir(parents=True, exist_ok=True)
            console.print(f"[yellow]🐛 Modo DEBUG ativado - salvando requisições em: {self.debug_dir}[/yellow]\n")

    async def _extract_under_limite_odd_from_dom(self, page) -> Optional[float]:
        """
        Extract Under Limite odd directly from the page DOM.

        Searches for elements containing "Under" or "Limite" text and extracts
        the associated odd value.
        """
        try:
            # Strategy 1: Look for text containing "Under" + "Limite" and get nearby odd
            # This is a generic approach that should work even if Bet365 changes class names

            # Try to find all elements that might contain market names
            elements = await page.query_selector_all('[class*="market"], [class*="Market"], [class*="selection"], [class*="Selection"], .gl-Market, .gl-MarketGroup')

            for element in elements:
                try:
                    # Get text content
                    text = await element.text_content()
                    if not text:
                        continue

                    text_lower = text.lower()

                    # Check if this element contains "under" and "limite"
                    if ("under" in text_lower and "limite" in text_lower) or \
                       ("under limite" in text_lower) or \
                       ("u. limite" in text_lower):

                        # Found Under Limite market! Now find the odd value nearby
                        # Look for odd values (format: X.XX or X,XX)
                        import re
                        odd_pattern = r'\b(\d+[.,]\d{1,2})\b'
                        matches = re.findall(odd_pattern, text)

                        for match in matches:
                            try:
                                odd_str = match.replace(',', '.')
                                odd_value = float(odd_str)

                                # Odds usually between 1.01 and 100.0
                                if 1.0 <= odd_value <= 100.0:
                                    return odd_value
                            except ValueError:
                                continue

                except Exception:
                    continue

            # Strategy 2: Try specific Bet365 class patterns (may change)
            # Look for elements with bet365-specific classes
            bet_buttons = await page.query_selector_all('[class*="Participant"], [class*="participant"], [class*="odd"], [class*="Odd"]')

            for button in bet_buttons:
                try:
                    text = await button.text_content()
                    if text and ("under" in text.lower() or "limite" in text.lower()):
                        # Extract numeric value
                        import re
                        numbers = re.findall(r'\d+[.,]\d{2}', text)
                        if numbers:
                            odd_value = float(numbers[0].replace(',', '.'))
                            if 1.0 <= odd_value <= 100.0:
                                return odd_value
                except Exception:
                    continue

        except Exception as e:
            if self.debug:
                console.print(f"[dim red]Erro extraindo odd do DOM: {e}[/dim red]")

        return None

    def _send_notification(self, title: str, message: str):
        """Send system notification."""
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Bet365 Monitor",
                timeout=5,
            )
        except Exception as e:
            console.print(f"[yellow]⚠️  Erro ao enviar notificação: {e}[/yellow]")

    def _create_status_table(self) -> Table:
        """Create status display table."""
        table = Table(show_header=True, header_style="bold magenta", expand=True)
        table.add_column("Status", style="cyan", width=30)
        table.add_column("Valor", style="white", width=50)

        # URL
        table.add_row("URL", self.url[:80] + "..." if len(self.url) > 80 else self.url)

        # Current odd
        if self.current_odd is not None:
            odd_color = "green" if self.current_odd else "white"
            table.add_row("Odd Atual (Under Limite)", f"[{odd_color}]{self.current_odd:.2f}[/{odd_color}]")
        else:
            table.add_row("Odd Atual (Under Limite)", "[dim]Aguardando...[/dim]")

        # Last update
        if self.last_update:
            table.add_row("Última Atualização", self.last_update.strftime("%H:%M:%S"))
        else:
            table.add_row("Última Atualização", "[dim]N/A[/dim]")

        # Update count
        table.add_row("Total de Atualizações", str(self.update_count))
        table.add_row("Requisições API Capturadas", str(self.api_requests_captured))

        return table

    async def _handle_response(self, response):
        """Handle intercepted API responses."""
        try:
            content_type = response.headers.get("content-type", "")

            # Debug mode: Log ALL responses (not just JSON)
            if self.debug:
                self.api_requests_captured += 1
                url = response.url
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

                # Log URL and content type
                log_file = self.debug_dir / "requests_log.txt"
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"{self.api_requests_captured}. {url} | Content-Type: {content_type}\n")

                # Log every 10 requests
                if self.api_requests_captured % 10 == 0:
                    console.print(f"[dim]Debug: {self.api_requests_captured} requisições capturadas[/dim]")

            # Only process JSON responses for odds extraction
            if "application/json" not in content_type:
                return

            # Parse JSON
            data = await response.json()

            # Debug mode: Save JSON responses
            if self.debug:
                url = response.url
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                debug_file = self.debug_dir / f"json_{timestamp}_{self.api_requests_captured}.json"

                try:
                    with open(debug_file, "w", encoding="utf-8") as f:
                        json.dump({"url": url, "data": data}, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    console.print(f"[red]Erro salvando JSON: {e}[/red]")

            # Try to extract Under Limite odd
            odd = self._extract_under_limite_odd(data)

            if odd is not None:
                # Check if odd changed
                if self.current_odd is None:
                    # First odd captured
                    self.current_odd = odd
                    self.last_update = datetime.now()
                    self.update_count += 1

                    self._send_notification(
                        "Bet365 Monitor",
                        f"Under Limite detectado: {odd:.2f}"
                    )

                elif abs(odd - self.current_odd) > 0.01:  # Threshold for change detection
                    # Odd changed
                    old_odd = self.current_odd
                    self.current_odd = odd
                    self.last_update = datetime.now()
                    self.update_count += 1

                    # Determine direction
                    direction = "↑" if odd > old_odd else "↓"
                    change = abs(odd - old_odd)

                    self._send_notification(
                        f"Odd Mudou {direction}",
                        f"De {old_odd:.2f} para {odd:.2f} (±{change:.2f})"
                    )

        except Exception as e:
            # Ignore parsing errors silently
            pass

    async def monitor(self):
        """Start monitoring the Bet365 game page."""
        console.print(f"[bold cyan]🎯 Iniciando monitoramento da Bet365...[/bold cyan]\n")
        console.print(f"[dim]URL: {self.url}[/dim]\n")
        console.print("[yellow]⚠️  Pressione Ctrl+C para parar[/yellow]\n")

        async with async_playwright() as p:
            # Launch browser with anti-detection settings
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ]
            )

            # Create context with realistic browser fingerprint
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='pt-BR',
                timezone_id='America/Sao_Paulo',
                extra_http_headers={
                    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                }
            )

            page = await context.new_page()

            # Remove webdriver flag
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            # Setup response interceptor
            page.on("response", lambda response: asyncio.create_task(self._handle_response(response)))

            # Navigate to URL
            console.print("[cyan]📡 Carregando página...[/cyan]")
            try:
                # Use 'load' instead of 'networkidle' since Bet365 has continuous polling
                await page.goto(self.url, wait_until="load", timeout=30000)
                console.print("[green]✅ Página carregada com sucesso![/green]")
            except Exception as e:
                console.print(f"[yellow]⚠️  Página pode não ter carregado completamente: {e}[/yellow]")
                console.print("[yellow]   Continuando monitoramento mesmo assim...[/yellow]")

            # Keep page alive and update display
            with Live(self._create_status_table(), console=console, refresh_per_second=1) as live:
                try:
                    while True:
                        # Update display
                        live.update(Panel(self._create_status_table(), title="[bold]Bet365 Monitor - Under Limite[/bold]", border_style="cyan"))

                        # Wait before next update
                        await asyncio.sleep(1)

                except KeyboardInterrupt:
                    console.print("\n[yellow]⏹️  Monitoramento interrompido pelo usuário[/yellow]")

            # Cleanup
            await browser.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Monitora odds do Under Limite na Bet365",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python scripts/bet365_monitor_odds.py "https://www.bet365.bet.br/#/IP/EV151260177742C1"
  python scripts/bet365_monitor_odds.py "https://www.bet365.bet.br/#/IP/EV151260177742C1" --debug

Notas:
  - O navegador roda em modo headless (invisível)
  - Notificações do sistema serão enviadas quando a odd mudar
  - Use --debug para salvar todas as requisições JSON em data/bet365_debug/
  - Pressione Ctrl+C para parar o monitoramento
        """
    )
    parser.add_argument("url", help="URL do jogo na Bet365")
    parser.add_argument("--debug", action="store_true", help="Ativa modo debug (salva todas requisições JSON)")

    args = parser.parse_args()

    # Validate URL
    if not args.url.startswith("https://www.bet365"):
        console.print("[bold red]❌ Erro: URL deve ser da Bet365[/bold red]")
        sys.exit(1)

    # Create monitor and run
    monitor = UnderLimiteMonitor(args.url, debug=args.debug)

    try:
        asyncio.run(monitor.monitor())
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Até logo![/yellow]")
    except Exception as e:
        console.print(f"[bold red]❌ Erro: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
