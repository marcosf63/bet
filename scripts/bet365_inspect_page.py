#!/usr/bin/env python3
"""
Script auxiliar para inspecionar a estrutura da página Bet365.
Salva screenshot e HTML para análise.
"""

import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright


async def inspect_page(url: str):
    """Inspect Bet365 page structure."""
    print(f"🔍 Inspecionando: {url}\n")

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )

        # Create context
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='pt-BR',
            timezone_id='America/Sao_Paulo',
        )

        page = await context.new_page()

        # Remove webdriver flag
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        # Navigate
        print("📡 Carregando página...")
        await page.goto(url, wait_until="load", timeout=30000)
        print("✅ Página carregada!")

        # Wait for page to render
        print("⏳ Aguardando renderização (10s)...")
        await asyncio.sleep(10)

        # Create output directory
        output_dir = Path("data/bet365_inspect")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save screenshot
        screenshot_path = output_dir / "page_screenshot.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"📸 Screenshot salvo: {screenshot_path}")

        # Save HTML
        html_content = await page.content()
        html_path = output_dir / "page_content.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"📄 HTML salvo: {html_path}")

        # Try to find "Under Limite" text in page
        print("\n🔎 Procurando por 'Under Limite' na página...")
        try:
            # Search for elements containing the text
            elements = await page.query_selector_all('*')
            found_count = 0

            for element in elements[:1000]:  # Limit to first 1000 elements
                try:
                    text = await element.text_content()
                    if text and "under" in text.lower() and "limite" in text.lower():
                        found_count += 1
                        # Get outer HTML of parent for context
                        outer_html = await element.evaluate('el => el.outerHTML')
                        print(f"\n✅ Encontrado #{found_count}:")
                        print(f"   Texto: {text[:100]}...")
                        print(f"   HTML: {outer_html[:200]}...")
                except:
                    pass

            if found_count == 0:
                print("❌ Não encontrou 'Under Limite' na página")
            else:
                print(f"\n✅ Total encontrado: {found_count} elementos")

        except Exception as e:
            print(f"❌ Erro ao procurar: {e}")

        # Close browser
        await browser.close()

        print(f"\n✅ Inspeção completa! Arquivos salvos em: {output_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/bet365_inspect_page.py <URL>")
        sys.exit(1)

    url = sys.argv[1]
    asyncio.run(inspect_page(url))
