#!/usr/bin/env python3
"""
Script para testar acesso à API SofaScore usando requests com sessão
"""

import requests
import json
import time
from datetime import date

def test_sofascore_api_with_session():
    """Testa acesso à API SofaScore com sessão requests"""
    
    target_date = date.today().strftime("%Y-%m-%d")
    api_url = f"https://www.sofascore.com/api/v1/sport/football/scheduled-events/{target_date}"
    
    print(f"🔍 Testando acesso à API: {api_url}")
    
    # Criar sessão para manter cookies e contexto
    session = requests.Session()
    
    # Headers que simulam navegador real
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,pt;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    })
    
    try:
        # Primeiro, visitar a página principal para estabelecer contexto
        print("📄 Visitando página principal do SofaScore...")
        main_response = session.get("https://www.sofascore.com/", timeout=15)
        print(f"   - Status: {main_response.status_code}")
        
        if main_response.status_code == 200:
            print("   - ✅ Página principal acessível")
            
            # Extrair possíveis cookies ou tokens
            cookies = main_response.cookies
            if cookies:
                print(f"   - 🍪 Cookies recebidos: {len(cookies)}")
            
            # Aguardar um pouco para simular comportamento humano
            time.sleep(2)
            
            # Agora tentar acessar a API com headers de requisição AJAX
            print("🔗 Acessando API de eventos agendados...")
            
            session.headers.update({
                'Accept': 'application/json, text/plain, */*',
                'Referer': 'https://www.sofascore.com/',
                'X-Requested-With': 'XMLHttpRequest',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin'
            })
            
            api_response = session.get(api_url, timeout=15)
            print(f"📊 Status da API: {api_response.status_code}")
            
            if api_response.status_code == 200:
                print("✅ API acessível!")
                
                try:
                    data = api_response.json()
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
                            
                            # Verificar se startTimestamp está presente
                            has_timestamp = 'startTimestamp' in first_event
                            print(f"     * Tem startTimestamp: {has_timestamp}")
                            
                            if has_timestamp:
                                from datetime import datetime
                                ts = first_event['startTimestamp']
                                dt = datetime.fromtimestamp(ts)
                                print(f"     * Data/hora: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                            
                            # Salvar amostra dos dados
                            sample_file = f"/home/marcos/projetos/bet/sofa_sample_{target_date}.json"
                            with open(sample_file, 'w', encoding='utf-8') as f:
                                json.dump(events[:5], f, indent=2, ensure_ascii=False)
                            print(f"   - Amostra salva em: {sample_file}")
                            
                            return True, data
                    else:
                        print("⚠️ Resposta não contém campo 'events'")
                        print(f"   - Dados recebidos: {str(data)[:200]}...")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Erro ao decodificar JSON: {e}")
                    print(f"   - Conteúdo: {api_response.text[:200]}...")
                    
            elif api_response.status_code == 403:
                print("🚫 API ainda está bloqueada (403 Forbidden)")
                
            elif api_response.status_code == 429:
                print("⏱️ Rate limit excedido (429)")
                
            else:
                print(f"❌ Status inesperado: {api_response.status_code}")
                print(f"   - Resposta: {api_response.text[:200]}...")
        else:
            print(f"❌ Não foi possível acessar página principal: {main_response.status_code}")
            
    except requests.exceptions.Timeout:
        print("⏰ Timeout na requisição")
        
    except requests.exceptions.ConnectionError:
        print("🔌 Erro de conexão")
        
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        
    finally:
        session.close()
    
    return False, None

def test_different_dates():
    """Testa diferentes datas para ver se alguma funciona"""
    from datetime import timedelta
    
    print("\n🗓️ Testando diferentes datas...")
    
    base_date = date.today()
    dates_to_test = [
        base_date,  # Hoje
        base_date + timedelta(days=1),  # Amanhã
        base_date - timedelta(days=1),  # Ontem
        base_date + timedelta(days=7),  # Próxima semana
    ]
    
    for test_date in dates_to_test:
        date_str = test_date.strftime("%Y-%m-%d")
        print(f"\n📅 Testando {date_str}...")
        
        url = f"https://www.sofascore.com/api/v1/sport/football/scheduled-events/{date_str}"
        
        try:
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }, timeout=10)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'events' in data:
                        print(f"   ✅ {len(data['events'])} eventos encontrados!")
                        return True, date_str
                except:
                    pass
                    
        except:
            pass
        
        time.sleep(1)  # Evitar rate limiting
    
    return False, None

if __name__ == "__main__":
    print("🚀 Iniciando teste da API SofaScore...")
    
    success, data = test_sofascore_api_with_session()
    
    if not success:
        print("\n🔄 Tentando com datas diferentes...")
        success, working_date = test_different_dates()
        
        if success:
            print(f"\n✅ API funcionou com a data: {working_date}")
        else:
            print("\n❌ API ainda não acessível com nenhuma abordagem.")
    
    if success:
        print("\n✅ Teste bem-sucedido! API acessível.")
        print("💡 Você pode atualizar a função get_scheduled_events() com esta abordagem.")
    else:
        print("\n❌ API ainda bloqueada.")
        print("💡 Continue usando o modo --demo por enquanto.")