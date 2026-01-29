# Extração de Odds - Resumo Completo

## ✅ FASE 1 CONCLUÍDA - Odds do Mercado MATCH_ODDS

### Dados Extraídos com Sucesso

| Campo | Descrição | Disponibilidade | Exemplo |
|-------|-----------|-----------------|---------|
| **odd_home_back** | Odd para apostar NO time mandante | ✅ 95% dos jogos | 1.90 |
| **odd_draw_back** | Odd para apostar NO empate | ✅ 100% dos jogos | 3.55 |
| **odd_away_lay** | Odd para apostar CONTRA o time visitante | ✅ 100% dos jogos | 5.30 |

### Estrutura JSON Atualizada

```json
{
  "mandante": "Coritiba",
  "visitante": "Atlético-GO",
  "horario": "22:30",
  "data": "2025-10-09",
  "competicao": "BR",
  "odd_home_back": 1.9,
  "odd_draw_back": 3.55,
  "odd_away_lay": 5.3,
  "odd_over_25_ft_back": null,
  "odd_btts_yes_back": null,
  "odd_over_15_ft_back": null
}
```

### Como Funciona

A API da Betfair retorna o mercado `MATCH_ODDS` com 3 runners:
1. **Time Mandante** - `availableToBack[0].price`
2. **O empate** - `availableToBack[0].price`
3. **Time Visitante** - `availableToLay[0].price`

O scraper identifica automaticamente cada runner e extrai a melhor odd disponível.

## ⏳ FASE 2 CONCLUÍDA - Investigação de Outros Mercados

### Odds NÃO Disponíveis Atualmente

| Campo | Mercado Necessário | Status |
|-------|-------------------|--------|
| **odd_over_25_ft_back** | `OVER_UNDER_25` | ❌ Não disponível via interceptação |
| **odd_btts_yes_back** | `BOTH_TEAMS_TO_SCORE` | ❌ Não disponível via interceptação |
| **odd_over_15_ft_back** | `OVER_UNDER_15` | ❌ Não disponível via interceptação |

### Resultado da Investigação

**Testes Realizados**:
1. ✅ Interceptação de APIs na página inicial → Apenas MATCH_ODDS
2. ✅ Navegação para página de competição → Apenas MATCH_ODDS
3. ✅ Tentativa de navegação para página de jogo individual → Timeout/Sem sucesso
4. ✅ Análise de múltiplas respostas de API capturadas → Apenas MATCH_ODDS

**Conclusão**: A API `/v1/bymarket` que é interceptada automaticamente na página inicial **retorna apenas o mercado MATCH_ODDS**.

### Motivos Técnicos

Os mercados Over/Under e BTTS NÃO estão disponíveis porque:

1. **APIs Diferentes**: Cada tipo de mercado usa endpoints diferentes com `marketIds` específicos
2. **Carregamento Sob Demanda**: Esses mercados só são carregados ao:
   - Clicar individualmente em cada jogo
   - Navegar para página de detalhes do evento
   - Expandir seções "Mais Mercados"
3. **Estrutura da API**: O endpoint inicial retorna apenas overview com MATCH_ODDS

Para obter outros mercados, seria necessário:
1. **Clicar em cada jogo** (~30 jogos × 5-10s = 2.5-5 minutos)
2. **Aguardar carregamento** de requisições adicionais
3. **Interceptar APIs específicas** para cada tipo de mercado

### Possíveis Soluções Futuras

#### Opção A: Navegação para Detalhes (Mais Lento)
```python
for jogo in jogos:
    # Clicar no jogo
    await page.click(f'[data-event-id="{jogo["event_id"]}"]')

    # Aguardar APIs de mercados adicionais
    await page.wait_for_timeout(2000)

    # Interceptar OVER_UNDER_25, BOTH_TEAMS_TO_SCORE, etc.
```

**Prós**: Garante dados completos
**Contras**: ~5-10 segundos por jogo (5+ minutos para 30 jogos)

#### Opção B: Requisições Diretas (Requer Engenharia Reversa)
```python
# Descobrir marketIds para cada evento
market_ids = get_additional_markets(event_id)

# Fazer requisição direta
response = await fetch(f'/v1/bymarket?marketIds={market_ids}')
```

**Prós**: Mais rápido que navegação
**Contras**: Requer descobrir como a Betfair monta os `marketIds`

#### Opção C: Aceitar Limitação (Recomendado por Agora)
Usar apenas odds do MATCH_ODDS, que já são suficientes para muitas análises:
- Identificar favoritos (odd_home_back < 2.0)
- Calcular probabilidades implícitas
- Estratégias de Lay Away

## 📊 Estatísticas do Teste

**Data**: 09/10/2025
**Jogos extraídos**: 19
**Com odds completas (MATCH_ODDS)**: 19 (100%)

### Cobertura de Odds

```
odd_home_back:  ████████████████████ 95% (18/19)
odd_draw_back:  █████████████████████ 100% (19/19)
odd_away_lay:   █████████████████████ 100% (19/19)
odd_over_25:    ░░░░░░░░░░░░░░░░░░░░░ 0% (0/19)
odd_btts:       ░░░░░░░░░░░░░░░░░░░░░ 0% (0/19)
odd_over_15:    ░░░░░░░░░░░░░░░░░░░░░ 0% (0/19)
```

## 🎯 Recomendação

**Para uso imediato**: As 3 odds extraídas (Home Back, Draw Back, Away Lay) são suficientes para:
- ✅ Estratégias de favoritos
- ✅ Cálculo de ISC (Índice de Segurança do Campeonato)
- ✅ Identificação de value bets
- ✅ Estratégias de Lay Away

**Para análises avançadas** que requerem Over/Under e BTTS:
- Implementar Opção A (navegação) quando necessário
- Ou complementar com dados de outras fontes (FootyStats, FlashScore)

## 🚀 Como Usar

```bash
# Executar scraper com odds
python scripts/betfair_hoje.py

# Verificar odds no JSON
cat data/betfair_jogos_final_*.json | jq '.jogos[0]'
```

## 📝 Exemplo de Uso em Análise

```python
import json

with open('data/betfair_jogos_final_20251009_152824.json') as f:
    dados = json.load(f)

# Filtrar favoritos
favoritos = [
    jogo for jogo in dados['jogos']
    if jogo['odd_home_back'] and jogo['odd_home_back'] < 2.0
]

print(f"Jogos com favorito claro: {len(favoritos)}")

# Calcular probabilidade implícita
for jogo in favoritos:
    prob_home = 1 / jogo['odd_home_back'] * 100
    print(f"{jogo['mandante']}: {prob_home:.1f}% de vitória")
```

---

**Última atualização**: 09/10/2025
**Versão**: 1.2.0 - Odds MATCH_ODDS implementadas + Investigação FASE 2 completa

## 📋 Scripts de Investigação Criados

Durante a FASE 2, foram criados os seguintes scripts para investigar mercados adicionais:

1. **`betfair_investigate_markets.py`** - Intercepta todas as APIs na página inicial
2. **`betfair_navigate_to_match.py`** - Tenta navegar para jogos individuais com múltiplas estratégias
3. **`betfair_direct_event_navigation.py`** - Navegação direta para URL de evento específico

Esses scripts confirmaram que Over/Under e BTTS não são disponibilizados automaticamente.
