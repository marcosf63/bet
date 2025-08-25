# QUEN - Project Context

## Project Overview
This is a Python CLI application for automated analysis of sports betting data, focused on football markets from Betfair Exchange. The project is designed to identify profitable betting opportunities through data analysis and statistical modeling.

## Key Features
- Daily match analysis with odds data
- Identification of clear favorites based on low odds
- Specialized strategies for 0x0 halftime results
- Integration with Betfair Exchange and SofaScore APIs
- Advanced analytics including Monte Carlo simulations
- Trading performance metrics (Sharpe Ratio, VaR, Kelly Criterion)

## Project Structure
```
bet/
├── bet/                    # Main package
│   ├── cli.py             # Command-line interface
│   ├── analytics.py       # Statistical analysis tools
│   ├── betfair.py         # Betfair API client
│   └── ...                # Other modules
├── data/                  # Historical data and analyses
├── notebooks/             # Jupyter notebooks for analysis
├── scripts/               # Automation scripts
└── tests/                 # Unit tests
```

## Main Commands
- `bet mday` - List all matches of the day
- `bet fav` - Find matches with clear favorites (low odds)
- `bet ht0x0` - Identify matches with potential 0x0 halftime scores
- `bet analise` - Complete statistical analysis of trading strategies

## Data Sources
- Betfair Exchange (primary source for odds data)
- SofaScore (match statistics)
- FootyStats and FlashScore (alternative data sources)

## Analytics Capabilities
The project includes a comprehensive TradingAnalyzer class that provides:
- Performance metrics (win rate, profit factor, expectancy)
- Risk metrics (Sharpe ratio, Sortino ratio, maximum drawdown)
- Statistical analysis (VaR, Kelly criterion)
- Monte Carlo simulations for future performance projections

## Configuration
- Settings are managed in `settings.toml`
- SSL certificates for Betfair API authentication are stored in `certs/`
- Data is stored in the `data/` directory

## Dependencies
Key dependencies include:
- betfairlightweight (Betfair API client)
- pandas, numpy (data analysis)
- matplotlib, seaborn (data visualization)
- scipy (statistical analysis)
- typer, rich (CLI interface)