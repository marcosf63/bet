#!/usr/bin/env python3
"""
Script para testar acesso à API SofaScore usando Playwright
"""

import asyncio
import json
from datetime import date
from playwright.async_api import async_playwright

async def test_sofascore_api():
    """Testa acesso à API SofaScore com Playwright"""
    
    target_date = date.today().strftime("%Y-%m-%d")
    api_url = f"https://www.sofascore.com/api/v1/sport/football/scheduled-events/{target_date}"
    
    print(f"🔍 Testando acesso à API: {api_url}")
    
    async with async_playwright() as p:
        # Usar Chromium com configurações que simulam navegador real
        browser = await p.chromium.launch(
            headless=True,  # Pode ser False para debug
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--disable-extensions',
                '--disable-dev-shm-usage',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            extra_http_headers={
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }
        )
        
        page = await context.new_page()
        
        try:
            # Interceptar requisições de rede para capturar APIs
            captured_requests = []
            
            def capture_request(request):
                if 'api' in request.url and 'sofascore' in request.url:
                    captured_requests.append({
                        'url': request.url,
                        'method': request.method,
                        'headers': dict(request.headers)
                    })
                    print(f"🔍 API capturada: {request.method} {request.url}")
            
            # Interceptar respostas para capturar dados JSON
            captured_responses = []
            
            async def capture_response(response):
                if 'api' in response.url and 'sofascore' in response.url:
                    try:
                        if response.status == 200:
                            content_type = response.headers.get('content-type', '')
                            if 'application/json' in content_type:
                                json_data = await response.json()
                                captured_responses.append({
                                    'url': response.url,
                                    'status': response.status,
                                    'data': json_data
                                })
                                print(f"✅ JSON capturado de: {response.url}")
                    except Exception as e:
                        print(f"❌ Erro ao capturar resposta: {e}")
            
            page.on("request", capture_request)
            page.on("response", capture_response)
            
            # Primeiro, visitar a página principal para estabelecer contexto
            print("📄 Visitando página principal do SofaScore...")
            await page.goto("https://www.sofascore.com/", wait_until="networkidle")
            await page.wait_for_timeout(3000)  # Aguardar 3 segundos
            
            print(f"🔗 Requisições API capturadas: {len(captured_requests)}")
            for req in captured_requests[:5]:  # Mostrar primeiras 5
                print(f"   - {req['method']} {req['url']}")
            
            # Tentar usar uma das APIs capturadas se disponível
            if captured_responses:
                print(f"📊 Respostas JSON capturadas: {len(captured_responses)}")
                
                # Salvar todas as respostas capturadas para análise
                all_responses_file = f"/home/marcos/projetos/bet/sofa_all_responses_{target_date}.json"
                with open(all_responses_file, 'w', encoding='utf-8') as f:
                    json.dump(captured_responses, f, indent=2, ensure_ascii=False)
                print(f"📄 Todas as respostas salvas em: {all_responses_file}")
                
                for i, resp in enumerate(captured_responses):
                    print(f"   {i+1}. {resp['url']} - Status: {resp['status']}")
                    
                    # Verificar se contém eventos
                    if 'events' in resp['data']:
                        events = resp['data']['events']
                        print(f"      ✅ Encontrados {len(events)} eventos!")
                        
                        if events:
                            first_event = events[0]
                            print(f"         - Primeiro evento:")
                            print(f"           * ID: {first_event.get('id')}")
                            print(f"           * startTimestamp: {first_event.get('startTimestamp')}")
                            print(f"           * Casa: {first_event.get('homeTeam', {}).get('name')}")
                            print(f"           * Visitante: {first_event.get('awayTeam', {}).get('name')}")
                            print(f"           * Liga: {first_event.get('tournament', {}).get('name')}")
                            
                            # Verificar se startTimestamp está presente
                            if 'startTimestamp' in first_event:
                                from datetime import datetime
                                ts = first_event['startTimestamp']
                                dt = datetime.fromtimestamp(ts)
                                print(f"           * Data/hora: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                            
                            # Salvar dados dos eventos especificamente
                            events_file = f"/home/marcos/projetos/bet/sofa_events_{target_date}.json"
                            with open(events_file, 'w', encoding='utf-8') as f:
                                json.dump(events, f, indent=2, ensure_ascii=False)
                            print(f"         - Eventos salvos em: {events_file}")
                            
                            return True
                    else:
                        # Mostrar chaves disponíveis
                        data_keys = list(resp['data'].keys()) if resp['data'] else []
                        print(f"      - Chaves: {data_keys[:5]}...")  # Primeiras 5 chaves
            
            # Se não capturou APIs, tentar acessar diretamente
            print("🔗 Tentando acessar API diretamente...")
            response = await page.goto(api_url, wait_until="networkidle", timeout=30000)
            
            print(f"📊 Status da resposta: {response.status}")
            
            if response.status == 200:
                # Tentar extrair o conteúdo JSON
                content = await page.content()
                text_content = await page.inner_text('body')
                
                print(f"📄 Tamanho da resposta: {len(text_content)} caracteres")
                print(f"📄 Primeiros 500 caracteres: {text_content[:500]}")
                print(f"📄 Últimos 100 caracteres: {text_content[-100:]}")
                
                # Salvar resposta completa para análise
                response_file = f"/home/marcos/projetos/bet/sofa_response_{target_date}.txt"
                with open(response_file, 'w', encoding='utf-8') as f:
                    f.write(text_content)
                print(f"📁 Resposta completa salva em: {response_file}")
                
                # Verificar se parece ser uma página HTML de erro ou redirecionamento
                if text_content.strip().startswith('<'):
                    print("🌐 Resposta parece ser HTML, não JSON")
                    
                    # Procurar por indicações de bloqueio
                    if 'cloudflare' in text_content.lower():
                        print("☁️  Detectado Cloudflare na resposta")
                    if 'captcha' in text_content.lower():
                        print("🤖 Detectado CAPTCHA na resposta")
                    if 'blocked' in text_content.lower():
                        print("🚫 Detectada mensagem de bloqueio")
                    
                    return False
                
                try:
                    # Verificar se é JSON válido
                    if text_content.strip().startswith('{'):
                        data = json.loads(text_content)
                        
                        print("✅ API acessível! Dados recebidos:")
                        print(f"   - Chaves principais: {list(data.keys())}")
                        
                        if 'events' in data:
                            events = data['events']
                            print(f"   - Total de eventos: {len(events)}")
                            
                            if events:
                                first_event = events[0]
                                print(f"   - Primeiro evento:")
                                print(f"     * ID: {first_event.get('id')}")
                                print(f"     * startTimestamp: {first_event.get('startTimestamp')}")
                                print(f"     * Casa: {first_event.get('homeTeam', {}).get('name')}")
                                print(f"     * Visitante: {first_event.get('awayTeam', {}).get('name')}")
                                print(f"     * Liga: {first_event.get('tournament', {}).get('name')}")
                                
                                # Salvar amostra dos dados
                                sample_file = f"/home/marcos/projetos/bet/sofa_sample_{target_date}.json"
                                with open(sample_file, 'w', encoding='utf-8') as f:
                                    json.dump(events[:5], f, indent=2, ensure_ascii=False)
                                print(f"   - Amostra salva em: {sample_file}")
                                
                                return True
                        else:
                            print("⚠️ Resposta não contém campo 'events'")
                            print(f"   - Dados recebidos: {str(data)[:200]}...")
                    else:
                        print("❌ Resposta não é JSON válido")
                        print(f"   - Primeiro caractere: '{text_content[0] if text_content else 'vazio'}'")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Erro ao decodificar JSON: {e}")
                    print(f"   - Tentando limpar texto...")
                    
                    # Tentar limpar e extrair JSON
                    cleaned_text = text_content.strip()
                    if cleaned_text:
                        print(f"   - Texto limpo começa com: '{cleaned_text[:10]}'")
                        print(f"   - Texto limpo termina com: '{cleaned_text[-10:]}'")
                        
                        # Procurar por JSON dentro do texto
                        json_start = cleaned_text.find('{')
                        json_end = cleaned_text.rfind('}')
                        
                        if json_start != -1 and json_end != -1 and json_end > json_start:
                            potential_json = cleaned_text[json_start:json_end+1]
                            print(f"   - Possível JSON encontrado: {len(potential_json)} chars")
                            try:
                                data = json.loads(potential_json)
                                print("✅ JSON extraído com sucesso!")
                                print(f"   - Chaves: {list(data.keys())}")
                                return True
                            except:
                                print("❌ JSON extraído ainda é inválido")
                    
            elif response.status == 403:
                print("🚫 Acesso negado (403 Forbidden)")
                print("   - API ainda está bloqueada")
                
            elif response.status == 429:
                print("⏱️ Rate limit excedido (429)")
                print("   - Muitas requisições")
                
            else:
                print(f"❌ Status inesperado: {response.status}")
                text_content = await page.inner_text('body')
                print(f"   - Conteúdo: {text_content[:200]}...")
                
        except Exception as e:
            print(f"❌ Erro durante acesso: {e}")
            
        finally:
            await browser.close()
    
    return False

if __name__ == "__main__":
    print("🚀 Iniciando teste da API SofaScore com Playwright...")
    success = asyncio.run(test_sofascore_api())
    
    if success:
        print("\n✅ Teste bem-sucedido! API acessível via Playwright.")
        print("💡 Você pode atualizar a função get_scheduled_events() para usar Playwright.")
    else:
        print("\n❌ API ainda não acessível, mesmo via Playwright.")
        print("💡 Continue usando o modo --demo por enquanto.")