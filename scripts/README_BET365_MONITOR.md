# Bet365 Under Limite Odds Monitor

Script para monitorar as odds do mercado "Under Limite" de jogos na Bet365 em tempo real, com notificações automáticas quando as odds mudarem.

## 🎯 Funcionalidades

- ✅ Monitora odds do mercado "Under Limite" de um jogo específico
- ✅ Captura dados diretamente das requisições API da Bet365 usando Playwright
- ✅ Envia notificações do sistema Linux quando as odds mudam
- ✅ Interface visual no terminal com Rich (tabela atualizada em tempo real)
- ✅ Detecta direção da mudança (↑ subiu / ↓ desceu)
- ✅ Contador de atualizações e requisições API capturadas

## 📋 Pré-requisitos

### 1. Dependências Python

Todas as dependências já estão instaladas no projeto:

```bash
# Já incluídas no requirements.txt:
playwright==1.55.0
plyer==2.1.0
rich==13.7.0
```

### 2. Instalar navegadores Playwright

Após instalar as dependências Python, é necessário instalar os navegadores do Playwright:

```bash
# Ativar ambiente virtual (se estiver usando)
source venv/bin/activate

# Instalar navegadores Playwright
playwright install chromium

# OU instalar todos os navegadores (opcional)
playwright install
```

### 3. Dependências do sistema (para notificações)

Para as notificações do sistema Linux funcionarem, você precisa de:

```bash
# Ubuntu/Debian
sudo apt-get install libdbus-1-dev

# Fedora
sudo dnf install dbus-devel

# Arch Linux
sudo pacman -S dbus
```

**Nota**: A dependência `dbus-python` já está no requirements.txt.

## 🚀 Como Usar

### Uso Básico

```bash
# Monitorar um jogo específico na Bet365
python scripts/bet365_monitor_odds.py "https://www.bet365.bet.br/#/IP/EV151260177742C1"
```

### Opções

O script aceita apenas um argumento: a URL do jogo na Bet365.

```bash
# Exemplo com URL completa
python scripts/bet365_monitor_odds.py "https://www.bet365.bet.br/#/IP/EV151260177742C1"

# Para parar o monitoramento, pressione Ctrl+C
```

### Modo Headless (Background)

Por padrão, o script abre o navegador visível. Para executar em modo background (headless):

1. Abra o arquivo `scripts/bet365_monitor_odds.py`
2. Na linha 138, altere:
   ```python
   browser = await p.chromium.launch(headless=False)  # Use headless=True for background
   ```
   Para:
   ```python
   browser = await p.chromium.launch(headless=True)
   ```

## 📊 Interface do Terminal

O script exibe uma tabela atualizada em tempo real com as seguintes informações:

```
┌─────────────────────── Bet365 Monitor - Under Limite ───────────────────────┐
│ ╭─────────────────────────────┬──────────────────────────────────────────╮  │
│ │ Status                      │ Valor                                    │  │
│ ├─────────────────────────────┼──────────────────────────────────────────┤  │
│ │ URL                         │ https://www.bet365.bet.br/#/IP/EV151...  │  │
│ │ Odd Atual (Under Limite)    │ 3.45                                     │  │
│ │ Última Atualização          │ 14:32:15                                 │  │
│ │ Total de Atualizações       │ 5                                        │  │
│ │ Requisições API Capturadas  │ 127                                      │  │
│ ╰─────────────────────────────┴──────────────────────────────────────────╯  │
└──────────────────────────────────────────────────────────────────────────────┘
```

## 🔔 Notificações do Sistema

O script envia notificações do sistema Linux nos seguintes eventos:

### 1. Primeira detecção de odd
```
Título: Bet365 Monitor
Mensagem: Under Limite detectado: 3.45
```

### 2. Mudança de odd
```
Título: Odd Mudou ↑
Mensagem: De 3.45 para 3.60 (±0.15)
```

ou

```
Título: Odd Mudou ↓
Mensagem: De 3.60 para 3.45 (±0.15)
```

## 🔍 Como Funciona

1. **Playwright**: Abre o navegador e navega até a URL fornecida
2. **Interceptação de API**: Captura todas as requisições JSON da Bet365
3. **Extração de Dados**: Procura pelo mercado "Under Limite" nas respostas da API
4. **Detecção de Mudanças**: Compara odd atual com odd anterior (threshold: ±0.01)
5. **Notificações**: Envia notificação do sistema quando detecta mudança
6. **Display em Tempo Real**: Atualiza tabela no terminal a cada segundo

## ⚠️ Observações

### Estrutura da API Bet365

A Bet365 pode alterar a estrutura da API sem aviso. O script usa heurísticas para encontrar o mercado "Under Limite":

- Procura por nomes de mercado contendo "under" e "limite"
- Suporta múltiplas estruturas de resposta da API
- Extrai odds de diferentes formatos (`price`, `od`, etc.)

### Threshold de Mudança

O script considera uma mudança de odd quando a diferença é maior que **0.01**. Isso evita notificações para mudanças irrelevantes.

### Requisições API

O contador "Requisições API Capturadas" mostra quantas requisições JSON foram interceptadas. Nem todas contêm dados do mercado Under Limite.

### Login na Bet365

Se a Bet365 exigir login, o navegador será aberto visível e você poderá fazer login manualmente. Após o login, o script continuará monitorando automaticamente.

## 🐛 Troubleshooting

### Notificações não aparecem

1. Verifique se `dbus-python` está instalado:
   ```bash
   pip show dbus-python
   ```

2. Verifique se as dependências do sistema estão instaladas:
   ```bash
   dpkg -l | grep libdbus  # Ubuntu/Debian
   ```

3. Teste notificações manualmente:
   ```python
   from plyer import notification
   notification.notify(title="Teste", message="Funcionou!")
   ```

### Navegador não abre

1. Verifique se os navegadores Playwright estão instalados:
   ```bash
   playwright install chromium
   ```

2. Verifique a versão do Playwright:
   ```bash
   pip show playwright
   ```

### Odd não é detectada

1. Acesse a URL fornecida manualmente no navegador
2. Verifique se o mercado "Under Limite" está disponível para o jogo
3. A estrutura da API Bet365 pode ter mudado - verifique os logs no terminal

## 📝 Exemplos de URLs

```bash
# Exemplo 1: Jogo específico
python scripts/bet365_monitor_odds.py "https://www.bet365.bet.br/#/IP/EV151260177742C1"

# Exemplo 2: Outro formato de URL da Bet365
python scripts/bet365_monitor_odds.py "https://www.bet365.bet.br/#/AVS/42/1/151260177742/"
```

## 🔧 Personalização

### Modificar threshold de mudança

No arquivo `bet365_monitor_odds.py`, linha 94:

```python
elif abs(odd - self.current_odd) > 0.01:  # Threshold for change detection
```

Altere `0.01` para o valor desejado.

### Modificar intervalo de atualização

No arquivo `bet365_monitor_odds.py`, linha 153:

```python
await asyncio.sleep(1)  # Wait 1 second
```

Altere `1` para o intervalo desejado em segundos.

### Modificar tempo de notificação

No arquivo `bet365_monitor_odds.py`, linha 76:

```python
timeout=5,  # Notification duration in seconds
```

Altere `5` para o tempo desejado.

## 📚 Referências

- [Playwright Python](https://playwright.dev/python/)
- [Plyer Documentation](https://plyer.readthedocs.io/)
- [Rich Documentation](https://rich.readthedocs.io/)

## ⚖️ Disclaimer

Este script é apenas para fins educacionais e de análise pessoal. Use-o de acordo com os termos de serviço da Bet365.
