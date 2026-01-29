# Betfair Scraper - Extrator de Jogos de Hoje

## 📋 Descrição

Sistema completo para extração de todos os jogos de futebol disponíveis hoje no site da Betfair Exchange.

### ✅ Funcionalidades Implementadas

- ✅ **Interceptação de API**: Captura requisições XHR/Fetch da Betfair
- ✅ **Extração Automática**: Parse da estrutura JSON da API
- ✅ **Dados Completos**: Data, horário, time mandante e visitante
- ✅ **Extração de Odds**: Mercado MATCH_ODDS (Home Back, Draw Back, Away Lay)
- ✅ **Salvamento Progressivo**: JSON com metadados
- ✅ **Tratamento de Cookies**: Aceita automaticamente popup
- ✅ **Múltiplas Páginas**: Captura todos os jogos disponíveis

## 🎯 Estratégia Implementada

### **Abordagem: Interceptação de API (Método Principal)**

O scraper usa Playwright para:

1. Interceptar requisições HTTP da API da Betfair
2. Capturar respostas JSON com dados estruturados
3. Extrair informações dos jogos diretamente da API

**Vantagens**:
- ✅ Mais rápido que parsing HTML
- ✅ Dados estruturados e confiáveis
- ✅ Não afetado por mudanças no CSS/HTML
- ✅ Captura mais jogos (incluindo fora da viewport)

## 📁 Arquivos Criados

```
scripts/
├── betfair_scraper_api.py      # Scraper com interceptação de API
├── betfair_scraper_unified.py  # Script unificado (API + fallback)
├── betfair_hoje.py             # Script simplificado para uso diário
└── README_BETFAIR_SCRAPER.md   # Esta documentação

data/
├── betfair_jogos_final_YYYYMMDD_HHMMSS.json  # Dados finais com metadados
├── betfair_api_responses_*.json              # Respostas brutas da API (debug)
└── betfair_jogos_api_*.json                  # Jogos extraídos da API
```

## 🚀 Como Usar

### Opção 1: Script Simplificado (Recomendado)

```bash
python scripts/betfair_hoje.py
```

### Opção 2: Script Unificado Completo

```bash
python scripts/betfair_scraper_unified.py
```

### Opção 3: Apenas API (Desenvolvimento)

```bash
python scripts/betfair_scraper_api.py
```

## 📊 Estrutura dos Dados Extraídos

### Arquivo JSON de Saída

```json
{
  "metadata": {
    "data_extracao": "2025-10-09T11:42:00.680744",
    "metodo": "API",
    "total_jogos": 27,
    "url": "https://www.betfair.bet.br/exchange/plus/pt/futebol-apostas-1/today"
  },
  "jogos": [
    {
      "mandante": "Ferroviária",
      "visitante": "Chapecoense",
      "horario": "22:00",
      "data": "2025-10-09",
      "competicao": "BR",
      "odd_home_back": 2.52,
      "odd_draw_back": 3.30,
      "odd_away_lay": 3.30,
      "odd_over_25_ft_back": null,
      "odd_btts_yes_back": null,
      "odd_over_15_ft_back": null
    }
  ]
}
```

### Campos Extraídos

| Campo       | Descrição                    | Exemplo          | Disponibilidade |
|-------------|------------------------------|------------------|-----------------|
| `mandante`  | Time da casa                 | "Ferroviária"    | ✅ 100%         |
| `visitante` | Time visitante               | "Chapecoense"    | ✅ 100%         |
| `horario`   | Hora do jogo (HH:MM)         | "22:00"          | ✅ 100%         |
| `data`      | Data do jogo (YYYY-MM-DD)    | "2025-10-09"     | ✅ 100%         |
| `competicao`| Competição (se disponível)   | "N/A"            | ⚠️ Parcial      |
| `odd_home_back` | Odd para apostar NO mandante | 1.90        | ✅ 95%          |
| `odd_draw_back` | Odd para apostar NO empate | 3.55          | ✅ 100%         |
| `odd_away_lay` | Odd para apostar CONTRA visitante | 5.30   | ✅ 100%         |
| `odd_over_25_ft_back` | Odd Over 2.5 gols FT | null        | ❌ 0%           |
| `odd_btts_yes_back` | Odd Ambos marcam (Yes) | null         | ❌ 0%           |
| `odd_over_15_ft_back` | Odd Over 1.5 gols FT | null        | ❌ 0%           |

## 🔧 Detalhes Técnicos

### Tecnologias Utilizadas

- **Playwright**: Automação do navegador
- **Python AsyncIO**: Operações assíncronas
- **JSON**: Serialização de dados

### API da Betfair Interceptada

```
URL: https://ero.betfair.bet.br/www/sports/exchange/readonly/v1/bymarket
Estrutura: eventTypes[].eventNodes[].event
```

### Estrutura da API

```javascript
{
  "eventTypes": [{
    "eventTypeId": 1,
    "eventNodes": [{
      "eventId": 12345,
      "event": {
        "eventName": "Time A x Time B",  // Nome do jogo
        "openDate": "2025-10-09T19:00:00.000Z",  // Data/hora ISO
        "timezone": "GMT"
      }
    }]
  }]
}
```

### Parser Implementado

O scraper identifica automaticamente:

1. **Formato com "x"**: "Ferroviária x Chapecoense"
2. **Formato com "v"**: "Arsenal v Chelsea"
3. **Formato ISO**: Converte timestamps para HH:MM

## 📈 Resultados

### Teste Realizado (09/10/2025)

- ✅ **27 jogos** extraídos com sucesso
- ✅ **10 horários** diferentes capturados
- ✅ Jogos de **múltiplas competições**:
  - Brasileirão Série B
  - Eliminatórias Europeias
  - Amistosos Internacionais
  - Futebol Feminino

### Performance

- ⏱️ **Tempo de execução**: ~15-20 segundos
- 📡 **Requisições capturadas**: 11 APIs
- 💾 **Tamanho dos dados**: ~2-5 KB (JSON compacto)

## 🛠️ Manutenção e Troubleshooting

### Problemas Comuns

#### 1. "Nenhum jogo extraído"

**Possíveis causas**:
- Estrutura da API mudou
- Cookies não foram aceitos
- Timeout muito curto

**Solução**:
```bash
# Aumentar timeout e verificar logs
python scripts/betfair_scraper_api.py
# Verificar: data/betfair_api_responses_*.json
```

#### 2. "Playwright não instalado"

```bash
pip install playwright
playwright install chromium
```

#### 3. Dados incompletos (falta competição)

A API da Betfair não retorna o nome da competição no campo `event`.
Para obter competições, seria necessário mapear `countryCode` ou fazer requisições adicionais.

## 🔮 Melhorias Futuras

### Implementadas ✅
- [x] Interceptação de API
- [x] Parse de eventos
- [x] Salvamento com metadados
- [x] Tratamento de cookies

### Pendentes 📋
- [ ] Extração de odds Over/Under 2.5 e 1.5 (requer navegação ou APIs adicionais)
- [ ] Extração de odds Both Teams To Score (requer navegação ou APIs adicionais)
- [ ] Filtros por competição/horário
- [ ] Integração com banco de dados
- [ ] Agendamento automático (cron)

## 📝 Notas Importantes

1. **Rate Limiting**: Respeite os termos de uso da Betfair
2. **Headless Mode**: Pode ser ativado alterando `headless=False` para `True`
3. **Cookies**: O script aceita cookies automaticamente via `#onetrust-accept-btn-handler`
4. **Timezone**: Horários estão em GMT (considerar conversão para horário local)
5. **Odds Disponíveis**: Apenas mercado MATCH_ODDS é extraído automaticamente. Para Over/Under e BTTS, consulte [ODDS_EXTRACTION_SUMMARY.md](ODDS_EXTRACTION_SUMMARY.md)

## 🤝 Contribuindo

Para adicionar novas funcionalidades:

1. **Parser de HTML**: Implementar em `betfair_scraper_html.py`
2. **Novos campos**: Adicionar em `_parse_betfair_event()`
3. **Filtros**: Adicionar parâmetros no `main()`

## 📄 Licença

Este projeto é parte do sistema de análise de apostas esportivas.
Uso restrito para fins educacionais e de pesquisa.

---

**Desenvolvido em**: 09/10/2025
**Versão**: 1.1.0 - Com extração de odds MATCH_ODDS
**Status**: ✅ Funcional e Testado

## 📚 Documentação Adicional

- [ODDS_EXTRACTION_SUMMARY.md](ODDS_EXTRACTION_SUMMARY.md) - Detalhes sobre extração de odds
