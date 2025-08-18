# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

### Testing
```bash
# Run tests (minimal test suite available)
python -m pytest tests/
```

## Architecture Overview

This is a **betting analysis CLI application** that fetches and analyzes football match data, primarily from Betfair exchange markets.

### Core Components

**bet/cli.py**: Main CLI interface using Typer. Contains commands for analyzing different betting scenarios:
- `mday`: Fetches daily matches from remote CSV data
- `fav`: Filters games with clear favorites (low odds)  
- `ht0x0`: Identifies matches likely to be 0-0 at halftime based on high Over 2.5 and BTTS odds
- `shell`: Interactive IPython shell with betting utilities

**bet/betfair.py**: Betfair API client wrapper using betfairlightweight library. Handles authentication and market data retrieval.

**bet/models.py**: Pydantic models for data validation, including match data structures and SofaScore API responses.

**bet/utils.py**: Utility functions for time conversion, data formatting, and table printing.

**bet/files.py**: File I/O operations, CSV processing, and JSON handling.

**bet/notification.py**: System notifications and sound alerts using plyer and pygame.

**bet/soufascore.py**: SofaScore API integration for live match data.

**bet/analytics.py**: Advanced trading analytics module with statistical analysis, Monte Carlo simulations, and risk metrics.

### Data Sources
- Remote CSV files from futpythontrader/Jogos_do_Dia GitHub repository
- Betfair Exchange API for live odds and market data
- SofaScore API for match events and scores

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
- Dependencies defined in `requirements.in` and compiled to `requirements.txt`
- Entry point configured through setuptools console_scripts: `bet = bet.cli:main`
- Analytics module optional (graceful degradation if scipy/matplotlib not available)
- CSV data auto-saved to `data/mday/` folder when using `--salvar` option