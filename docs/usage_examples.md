# Exemplos de Uso - Nova Estrutura

## Importando Estratégias

```python
from bet.analysis import FavoritesStrategy, LayAwayStrategy, HalftimeZeroStrategy

# Criar estratégia de favoritos
fav_strategy = FavoritesStrategy(max_odd=1.5, fonte="betfair")

# Criar estratégia Lay Away
lay_strategy = LayAwayStrategy(min_isc=65.0, max_home_odd=1.6)

# Criar estratégia 0x0 no intervalo
ht_strategy = HalftimeZeroStrategy(min_odd_over=2.0, min_odd_btts=2.0)
```

## Analisando Jogos

```python
from bet.cli.helpers import get_daily_games

# Buscar jogos do dia
games = get_daily_games("2025-10-05", fonte="betfair")

# Aplicar estratégia de favoritos
favorites = fav_strategy.analyze(games)

# Verificar recomendação para um jogo específico
for game in favorites:
    recommendation = fav_strategy.get_recommendation(game)
    print(f"{game['Home']} vs {game['Away']}: {recommendation}")
```

## Usando Métricas

### Calcular ISC

```python
from bet.analysis.metrics import ISCCalculator

# Calcular ISC para um jogo
isc = ISCCalculator.calculate(
    odd_home_back=1.45,
    odd_away_lay=3.50,
    odd_draw_back=3.80
)

print(f"ISC: {isc}")  # Output: ISC: 72.5

# Obter nível de qualidade
level = ISCCalculator.get_level(isc)
print(f"Nível: {level}")  # Output: Nível: bom

# Adicionar ISC a um dicionário de jogo
game_with_isc = ISCCalculator.add_to_game(game)
```

### Calcular Lucro

```python
from bet.analysis.metrics import ProfitCalculator

# Calcular lucro de uma aposta Lay
profit = ProfitCalculator.calculate_lay_profit(
    stake=100,
    odd_lay=2.5,
    commission=0.05,
    win=True
)
print(f"Lucro Lay: R$ {profit}")

# Calcular lucro de uma aposta Back
profit = ProfitCalculator.calculate_back_profit(
    stake=100,
    odd_back=2.5,
    win=True
)
print(f"Lucro Back: R$ {profit}")

# Calcular green up
result = ProfitCalculator.calculate_green_up(
    stake_back=100,
    odd_back=3.0,
    odd_lay=2.0,
    commission=0.05
)
print(f"Stake Lay necessário: R$ {result['stake_lay']}")
print(f"Lucro médio: R$ {result['average_profit']}")

# Calcular Kelly Criterion
stake = ProfitCalculator.calculate_kelly_criterion(
    probability=0.65,
    odd=2.5,
    bankroll=1000
)
print(f"Stake recomendado (Kelly): R$ {stake}")
```

## Combinando Estratégias

```python
from bet.analysis import LayAwayStrategy, ISCCalculator
from bet.cli.helpers import get_daily_games, filter_games

# Buscar jogos
games = get_daily_games("2025-10-05")

# Filtrar e adicionar ISC
filtered_games = filter_games(games, fonte="betfair")

# Aplicar estratégia Lay Away
lay_strategy = LayAwayStrategy(
    min_isc=65.0,
    max_home_odd=1.6,
    min_home_odd=1.3
)

lay_candidates = lay_strategy.analyze(filtered_games)

print(f"Encontrados {len(lay_candidates)} jogos para Lay Away")

for game in lay_candidates:
    print(f"{game['Home']} vs {game['Away']}")
    print(f"  ISC: {game['ISC']}")
    print(f"  Recomendação: {lay_strategy.get_recommendation(game)}")
```

## CLI Modular

### Comandos Disponíveis

```bash
# Jogos do dia com filtros
bet mday --fonte betfair --isc bom --odd-home-max 1.6

# Favoritos
bet fav --oddmax 1.5 --liga "Premier League"

# Jogos com potencial 0x0 no intervalo
bet ht0x0 --odd_over 2.5 --odd_btts 2.5

# Análise estatística
bet analise --salvar
```

## Estendendo com Nova Estratégia

```python
from bet.analysis.strategies.base import BaseStrategy
from typing import List, Dict

class MinhaEstrategia(BaseStrategy):
    """Minha estratégia personalizada."""

    def __init__(self, parametro: float):
        super().__init__(
            name="Minha Estratégia",
            description="Descrição da estratégia"
        )
        self.parametro = parametro

    def validate_game(self, game: Dict) -> bool:
        """Validar se jogo atende critérios."""
        # Sua lógica aqui
        return True

    def analyze(self, games: List[Dict]) -> List[Dict]:
        """Filtrar jogos que atendem critérios."""
        return [g for g in games if self.validate_game(g)]

    def get_recommendation(self, game: Dict) -> str:
        """Retornar recomendação específica."""
        if self.validate_game(game):
            return "Sua recomendação aqui"
        return None
```

## Integrando com Serviços

```python
from bet.services.sofascore import get_scheduled_events
from bet.services.betfair import BetfairCliente
from bet.core.constants import URL_TEMPLATES

# SofaScore
events = get_scheduled_events("2025-10-05")

# Betfair (requer credenciais)
client = BetfairCliente(
    username="seu_usuario",
    password="sua_senha",
    app_key="sua_app_key",
    certs="path/to/certs"
)

# URLs de dados
betfair_url = URL_TEMPLATES["betfair"].format(data="2025-10-05")
```
