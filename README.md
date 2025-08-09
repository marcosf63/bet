# Bet - Análise de Apostas Esportivas

Uma aplicação CLI em Python para análise automatizada de dados de apostas esportivas, com foco em mercados de futebol da Betfair Exchange.

## 🚀 Funcionalidades

- **Análise de Jogos Diários**: Busca e análise automática de partidas com dados de odds
- **Identificação de Favoritos**: Filtra jogos com times favoritos claros baseado em odds baixas
- **Estratégias Especializadas**: 
  - Análise de potencial 0x0 no primeiro tempo
  - Identificação de jogos com alta probabilidade de gols
- **Integração com APIs**: Betfair Exchange e SofaScore para dados em tempo real
- **Notificações**: Alertas sonoros e visuais para oportunidades identificadas
- **Análise Histórica**: Backtesting de estratégias com dados históricos
- **Analytics Avançados**: Métricas financeiras, simulação Monte Carlo e análise de risco

## 📋 Pré-requisitos

- Python 3.8+
- Conta na Betfair Exchange (para acesso à API)
- Certificados SSL para autenticação Betfair

## ⚙️ Instalação

1. Clone o repositório:
```bash
git clone https://github.com/marcosf63/bet.git
cd bet
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Instale o pacote em modo de desenvolvimento:
```bash
pip install -e .
```

4. Configure seus certificados Betfair no diretório `certs/`

## 🎯 Uso

### Comandos Principais

```bash
# Listar todas as partidas do dia
bet mday

# Salvar dados do dia em CSV
bet mday --salvar

# Buscar jogos com favoritos claros (odd <= 1.5)
bet fav --oddmax 1.5

# Filtrar por horário e liga específica
bet fav --horai 18 --horaf 22 --liga "Premier League"

# Identificar jogos com potencial 0x0 no primeiro tempo
bet ht0x0 --odd_over 2.5 --odd_btts 2.0

# Abrir shell interativo com funções pré-carregadas
bet shell

# Analisar estratégia de trading com métricas avançadas
bet analise

# Análise com gráficos e simulações customizadas
bet analise --salvar --simulacoes 20000 --operacoes-futuras 1000
```

### Exemplos de Uso

```bash
# Análise de jogos da Premier League entre 19h e 23h
bet fav --liga "Premier League" --horai 19 --horaf 23

# Buscar jogos com alta probabilidade de poucos gols
bet ht0x0 --odd_over 3.0 --odd_btts 2.5 --horai 15

# Salvar análise completa do dia
bet mday --data 2024-12-25 --salvar

# Análise completa de estratégia com relatório detalhado
bet analise --arquivo data/minha_estrategia.csv --coluna "Retorno" --salvar
```

## 📊 Estrutura de Dados

O projeto trabalha com dados estruturados incluindo:

- **Odds de Back/Lay** para diferentes mercados
- **Dados históricos** de partidas e resultados  
- **Métricas de performance** de estratégias
- **Análises consolidadas** em formatos JSON/CSV

## 🔧 Configuração

O arquivo `settings.toml` permite configurar:

- Diretórios de dados e certificados
- URLs de APIs externas
- Configurações de notificação
- Parâmetros de estratégias

## 📈 Estratégias Implementadas

### Favoritos em Casa
Identifica times favoritos jogando em casa com odds baixas, indicando alta probabilidade de vitória.

### Zebras no Primeiro Tempo  
Busca jogos com odds altas para Over 2.5 e BTTS, sugerindo maior probabilidade de 0x0 no HT.

### Análise Over 1.5
Avalia mercados de gols com foco em estratégias de Under/Over.

### Analytics de Trading
Análise quantitativa completa de estratégias com métricas como:
- **Sharpe Ratio**: Relação risco-retorno ajustada
- **Drawdown**: Máxima perda acumulada
- **Simulação Monte Carlo**: Projeções probabilísticas
- **Value at Risk (VaR)**: Quantificação de risco de cauda
- **Critério de Kelly**: Sizing optimal de posições

## 📁 Estrutura do Projeto

```
bet/
├── bet/                    # Pacote principal
│   ├── betfair.py         # Cliente Betfair API
│   ├── cli.py             # Interface de linha de comando
│   ├── models.py          # Modelos de dados
│   ├── utils.py           # Funções utilitárias
│   └── ...
├── data/                  # Dados históricos e análises
├── notebooks/             # Jupyter notebooks para análise
├── scripts/               # Scripts de automação
└── tests/                 # Testes unitários
```

## 🤝 Desenvolvimento

```bash
# Executar testes
python -m pytest tests/

# Análise interativa
bet shell

# Contribuir com melhorias
# 1. Fork o projeto
# 2. Crie uma branch para sua feature
# 3. Faça commit das mudanças
# 4. Abra um Pull Request
```

## ⚠️ Aviso Legal

Esta ferramenta é destinada exclusivamente para fins educacionais e de análise de dados. O usuário é responsável por:

- Cumprir todas as leis e regulamentos locais sobre apostas
- Gerenciar riscos financeiros adequadamente
- Usar as informações de forma responsável

**Aposte com responsabilidade. Apostas envolvem riscos.**

## 📝 Licença

Este projeto é licenciado sob os termos definidos pelo autor. Consulte o repositório para detalhes sobre uso e distribuição.

## 📞 Suporte

Para dúvidas, sugestões ou problemas:
- Abra uma issue no GitHub
- Consulte a documentação no código
- Verifique os notebooks de exemplo em `/notebooks/`
