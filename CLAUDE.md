# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Version
**Current Version**: 0.3.2-dev (Bet365 Under Limite Monitor)

### Version History
- **0.3.2-dev** (2025-11-11): Bet365 Under Limite Monitor
  - ✅ Added `scripts/bet365_monitor_odds.py` for real-time odds monitoring
  - ✅ Playwright-based API interception for Bet365 data capture
  - ✅ Linux system notifications when odds change
  - ✅ Rich table formatting with live updates
  - ✅ Comprehensive documentation in `scripts/README_BET365_MONITOR.md`
- **0.3.1-dev** (2025-11-02): Under Limite odds calculator
  - ✅ Added `bet odds` command for calculating Under Limite odds tables
  - ✅ Implements correction factor formula: Odd(t) = Odd_Initial × [(Odd_Final / Odd_Initial)^0.02]^t
  - ✅ Supports first half (0-35min) and second half (45-80min) calculations
  - ✅ CSV export functionality to data/odds/ directory
  - ✅ Rich table formatting with color-coded intervals
- **0.3.0-dev** (2025-10-05): Major refactoring - modular architecture
  - ✅ Reorganized into core/, services/, cli/, analysis/, storage/, utils/ packages
  - ✅ Created strategy pattern for betting strategies
  - ✅ Extracted metrics (ISC, profit calculations)
  - ✅ Modularized ALL CLI commands (13/13 = 100%)
  - ✅ Removed monolithic cli.py (1,400+ lines → modular structure)
  - ✅ Full backward compatibility maintained
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

# Available commands (all modularized):
bet mday        # List all matches for today
bet fav         # List games with clear favorites
bet ht0x0       # Find games with 0x0 potential at halftime
bet shell       # Interactive shell with pre-loaded functions
bet diff        # Compare MDAY vs SOFA data with match results
bet sofa        # Fetch SofaScore scheduled events
bet relatorio   # Generate consolidated profit reports
bet layaway     # Calculate Lay Away strategy profit/loss
bet analise     # Advanced trading analytics with statistical analysis
bet api         # Discover APIs from web pages
bet add         # Manage betting records (add, list, summary)
bet calendario  # Visual monthly calendar with betting performance
bet graf        # Horizontal bar chart with daily percentage performance
bet odds        # Calculate Under Limite odds table using correction factor formula

# Examples with options:
bet mday --data 2024-12-25 --salvar --isc excelente    # Save daily data filtered by ISC
bet fav --oddmax 1.5 --liga "Premier League"           # Filter favorites by league
bet ht0x0 --odd_over 3.0 --odd_btts 2.5                # Custom odds thresholds
bet analise --salvar --simulacoes 20000                # Generate analysis with charts
bet relatorio --periodo 2025-08 --salvar               # Monthly profit report
bet layaway --odd-home-max 1.6 --isc bom               # Lay Away with filters

# Betting records management:
bet add registro -a "Arsenal vs Chelsea" -l 2.5         # Default strategy: Under Limite
bet add registro -a "Real Madrid vs Barcelona" -l -3.0 -e "Lay Away"  # Custom strategy
bet add listar                                          # List today, week, and month (defaults)
bet add listar --hoje                                   # List only today
bet add listar --estrategia "Under Limite"             # Filter by strategy
bet add listar --ultimos-dias 7                         # Last 7 days
bet add listar --inicio 2025-10-01 --fim 2025-10-15    # Custom range
bet add resumo --mes                                    # Monthly statistics summary

# Visual monthly calendar:
bet calendario                                          # Calendar for current month
bet calendario --mes 2025-09                            # Specific month (YYYY-MM)
bet calendario --estrategia "Under Limite"             # Filter by strategy
bet calendario --stake-inicial 500.0                    # Custom initial stake

# Visual monthly bar chart:
bet graf                                                # Chart for current month
bet graf --mes 2025-10                                  # Specific month (YYYY-MM)
bet graf --estrategia "Under Limite"                    # Filter by strategy

# Under Limite odds calculator:
bet odds --odd-inicial 4.6 --tempo 1                    # First half (0-35min) with initial odd 4.6
bet odds -o 3.2 -t 2                                    # Second half (45-80min) with initial odd 3.2
bet odds -o 4.6 -t 1 --salvar                          # Calculate and save to CSV
```

### Scripts (Non-CLI Tools)
```bash
# Bet365 Under Limite Monitor (real-time odds monitoring)
python scripts/bet365_monitor_odds.py "https://www.bet365.bet.br/#/IP/EV151260177742C1"

# Prerequisites for Bet365 monitor:
playwright install chromium                             # Install Playwright browsers
# See scripts/README_BET365_MONITOR.md for full documentation
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
├── cli/                    # Modular CLI structure (100% migrated)
│   ├── main.py            # CLI entry point - registers all commands
│   ├── helpers.py         # Shared helper functions
│   ├── validators.py      # Input validators
│   └── commands/          # Individual command modules (13 commands)
│       ├── daily.py       # mday - daily matches
│       ├── favorites.py   # fav - clear favorites
│       ├── halftime.py    # ht0x0 - 0x0 HT potential
│       ├── shell.py       # shell - interactive IPython
│       ├── diff.py        # diff - MDAY vs SOFA comparison
│       ├── sofa.py        # sofa - SofaScore events
│       ├── report.py      # relatorio - profit reports
│       ├── layaway.py     # layaway - Lay Away strategy
│       ├── analysis.py    # analise - trading analytics
│       ├── api.py         # api - API discovery
│       ├── add.py         # add - betting records management
│       ├── calendar.py    # calendario - visual monthly calendar
│       └── odds.py        # odds - Under Limite odds calculator
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
├── storage/               # Data persistence
│   ├── files.py          # JSON/CSV file operations
│   └── database.py       # SQLite database for betting records
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
- `commands/`: Individual command modules (daily, favorites, halftime, add)
- `helpers.py`: Shared functions (get_daily_games, filter_games, ISC calculation)

**bet/storage/**: Data persistence
- `files.py`: JSON and CSV file operations
- `database.py`: SQLite database for betting records (data/betting.db)

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
- **Betting records database**: SQLite database (`data/betting.db`) for tracking daily wins/losses with period filters

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

#### Betting Records Database
```python
from bet.storage.database import BettingDatabase

# Create database instance
db = BettingDatabase()

# Add a betting record (default strategy: "Under Limite")
registro_id = db.adicionar_registro(
    aposta="Arsenal vs Chelsea",
    lucro_prejuizo=2.5,
    estrategia="Under Limite"  # Optional, defaults to "Under Limite"
)

# Query records by period
registros_hoje = db.buscar_por_periodo("hoje")
registros_semana = db.buscar_por_periodo("semana")
registros_mes = db.buscar_por_periodo("mes")

# Calculate statistics
stats = db.calcular_estatisticas(registros_mes)
print(f"Total: {stats['total']}")
print(f"Profit: {stats['lucro_total']:.2f}")

# Filter by strategy
registros_under = db.buscar_registros(estrategia="Under Limite")
registros_lay = db.buscar_registros(estrategia="Lay Away")

# Each record includes lucro_acumulado field
for reg in registros_mes[:3]:
    print(f"{reg['data']}: {reg['aposta']} | Acumulado: {reg['lucro_acumulado']:.2f}")
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
# - bet/cli/commands/add.py (add) - NEW in v0.3.0
```

See `docs/usage_examples.md` for complete examples.