# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Version
**Current Version**: 0.3.0-dev (Refactored Architecture)

### Version History
- **0.3.0-dev** (2025-10-05): Major refactoring - modular architecture
  - Reorganized into core/, services/, cli/, analysis/ packages
  - Created strategy pattern for betting strategies
  - Extracted metrics (ISC, profit calculations)
  - Modularized CLI commands
- **0.2.0** (2025-10-04): Add ISC calculation, home odds filtering (min/max), SofaScore integration, profit/lay analysis
- **0.1.0** (Initial): Base betting analysis CLI with Betfair integration

## Development Commands

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .

# Update dependencies (when requirements.in changes)
pip-compile requirements.in
```

### Running the Application
```bash
# CLI entry point (after installation)
bet --help

# Available commands:
bet mday        # List all matches for today
bet fav         # List games with clear favorites
bet ht0x0       # Find games with 0x0 potential at halftime
bet shell       # Interactive shell with pre-loaded functions
bet analise     # Advanced trading analytics with statistical analysis

# Examples with options:
bet mday --data 2024-12-25 --salvar                    # Save daily data to CSV
bet fav --oddmax 1.5 --liga "Premier League"           # Filter favorites by league
bet ht0x0 --odd_over 3.0 --odd_btts 2.5                # Custom odds thresholds
bet analise --salvar --simulacoes 20000                # Generate analysis with charts
```

### Testing and Code Quality
```bash
# Run tests (minimal test suite available)
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_utils.py

# Lint and type checking commands (if available)
# Check project for linting commands with: grep -r "lint\|flake8\|black\|ruff" .
```

## Architecture Overview

This is a **betting analysis CLI application** with a modular architecture for analyzing football match data from multiple sources.

### Project Structure (Refactored v0.3.0)

```
bet/
├── core/                    # Core business logic
│   ├── models.py           # Pydantic data models
│   ├── exceptions.py       # Custom exceptions
│   └── constants.py        # Application constants
│
├── services/               # External services integration
│   ├── betfair/           # Betfair API client
│   ├── sofascore/         # SofaScore API integration
│   └── data_sources/      # Remote CSV data sources
│
├── cli/                    # Modular CLI structure
│   ├── main.py            # CLI entry point
│   ├── helpers.py         # Shared helper functions
│   ├── validators.py      # Input validators
│   └── commands/          # Individual command modules
│       ├── daily.py       # mday command
│       ├── favorites.py   # fav command
│       └── halftime.py    # ht0x0 command
│
├── analysis/              # Analysis and strategies
│   ├── analytics.py       # Advanced analytics (Monte Carlo, etc.)
│   ├── strategies/        # Betting strategies
│   │   ├── base.py        # BaseStrategy abstract class
│   │   ├── favorites.py   # Favorites strategy
│   │   ├── halftime_zero.py  # 0x0 HT strategy
│   │   └── lay_away.py    # Lay Away strategy (ISC-based)
│   └── metrics/           # Calculation metrics
│       ├── isc.py         # ISC calculator
│       └── profit.py      # Profit/loss calculations
│
└── utils.py               # Utility functions
```

### Core Components

**bet/core/**: Business logic foundation
- `models.py`: Pydantic models for data validation
- `exceptions.py`: Custom exceptions
- `constants.py`: URL templates, column definitions

**bet/services/**: External integrations
- `betfair/client.py`: Betfair API wrapper (betfairlightweight)
- `sofascore/client.py`: SofaScore API for live data
- `data_sources/`: Remote CSV data handling

**bet/cli/**: Modular CLI
- `main.py`: Typer app with command registration
- `commands/`: Individual command modules (daily, favorites, halftime)
- `helpers.py`: Shared functions (get_daily_games, filter_games, ISC calculation)

**bet/analysis/**: Strategies and analytics
- `strategies/`: Pluggable betting strategies (Favorites, Lay Away, HT 0x0)
- `metrics/`: ISC calculator, profit calculations, Kelly Criterion
- `analytics.py`: Statistical analysis, Monte Carlo simulations

### Data Sources
- **Remote CSV files**: Multiple sources from futpythontrader/Jogos_do_Dia GitHub repository:
  - Betfair: `/Betfair/Jogos_do_Dia_Betfair_Back_Lay_{data}.csv`
  - FootyStats: `/FootyStats/Jogos_do_Dia_FootyStats_{data}.csv` 
  - FlashScore: `/FlashScore/Jogos_do_Dia_FlashScore_{data}.csv`
- **Betfair Exchange API**: Live odds and market data via betfairlightweight
- **SofaScore API**: Live match events and scores (`soufascore.py`)

### Configuration
- **settings.toml**: Application configuration using Dynaconf with paths and API URLs
- **requirements.txt**: Dependencies managed with pip-compile from requirements.in
- **setup.py**: Package configuration with console script entry point
- Data stored in `/data/` directory with various betting analysis results

### Key Features
- Historical match data analysis stored in `data/dados_historicos/`
- Jupyter notebooks for strategy backtesting in `notebooks/`
- Certificate-based Betfair API authentication in `certs/`
- Automated betting strategy scripts in `scripts/`
- Advanced analytics with metrics: Sharpe ratio, VaR, Kelly criterion, Monte Carlo simulations

### Development Workflow
- **Dependencies**: Defined in `requirements.in` and compiled to `requirements.txt` using `pip-compile`
- **Entry point**: Configured through setuptools console_scripts: `bet = bet.cli:main`
- **Analytics module**: Optional (graceful degradation if scipy/matplotlib not available)
- **Data persistence**: CSV data auto-saved to `data/mday/` folder when using `--salvar` option
- **Betfair authentication**: Uses certificate-based authentication (certs/ directory)

### Development Notes
- **Multiple data sources**: CLI supports switching between Betfair, FootyStats, and FlashScore data
- **Jupyter integration**: Notebooks in `notebooks/` for strategy analysis and backtesting
- **Historical data**: Stored in `data/dados_historicos/` with event-based organization
- **Configuration**: Uses Dynaconf for settings management via `settings.toml`
- **Modular strategies**: Easy to add new strategies by extending `BaseStrategy`
- **Entry point**: CLI entry point moved to `bet.cli.main:main`

### Using New Features (v0.3.0)

#### Strategy Pattern
```python
from bet.analysis import FavoritesStrategy, LayAwayStrategy

# Create and use strategies
fav_strategy = FavoritesStrategy(max_odd=1.5)
games_filtered = fav_strategy.analyze(games)
recommendation = fav_strategy.get_recommendation(game)
```

#### Metrics Calculators
```python
from bet.analysis.metrics import ISCCalculator, ProfitCalculator

# Calculate ISC
isc = ISCCalculator.calculate(odd_home_back=1.45, odd_away_lay=3.5, odd_draw_back=3.8)

# Calculate profit
profit = ProfitCalculator.calculate_lay_profit(stake=100, odd_lay=2.5, win=True)
kelly_stake = ProfitCalculator.calculate_kelly_criterion(probability=0.65, odd=2.5, bankroll=1000)
```

#### Modular CLI Commands
```bash
# Old cli.py still works for backward compatibility
python -m bet.cli --help

# New modular structure
python -m bet.cli.main --help

# Commands are now in separate modules:
# - bet/cli/commands/daily.py (mday)
# - bet/cli/commands/favorites.py (fav)
# - bet/cli/commands/halftime.py (ht0x0)
```

See `docs/usage_examples.md` for complete examples.