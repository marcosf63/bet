# Análise de Arquivos Legacy

## Arquivos na Raiz de `bet/`

### ✅ **DEVEM SER MANTIDOS** (em uso ativo)

#### 1. **config.py**
**Status:** ✅ **NECESSÁRIO**
**Usado por:** 3 arquivos
- `bet/cli.py`
- `bet/evolution.py`
- `bet/services/sofascore/client.py`

**Função:** Configuração do Dynaconf (settings.toml, .secrets.toml)

**Recomendação:**
- **MANTER** mas pode ser movido para `bet/config/`
- Criar `bet/config/__init__.py` que exporta `settings`

```python
# Proposta futura:
bet/config/
├── __init__.py       # from .settings import settings
└── settings.py       # Código atual do config.py
```

---

#### 2. **files.py**
**Status:** ✅ **NECESSÁRIO**
**Usado por:** 3 arquivos
- `bet/cli/helpers.py`
- `bet/cli.py`
- `bet/services/betfair/client.py`

**Funções:**
- `save_dict_to_json()` - Salvar dict em JSON
- `load_json_to_dict()` - Carregar JSON para dict
- `csv_string_to_json_list()` - Converter CSV string para lista

**Recomendação:**
- **Mover** para `bet/storage/files.py` ou `bet/utils/io.py`
- Faz parte da Fase 4 (Storage Layer)

```python
# Proposta futura:
bet/storage/
├── __init__.py
├── files.py          # Funções de file I/O
└── database.py       # Funções de DB (quando implementar)
```

---

#### 3. **notification.py**
**Status:** ✅ **NECESSÁRIO**
**Usado por:** 2 arquivos
- `bet/cli.py`
- `bet/services/betfair/client.py`

**Funções:**
- `send_notification()` - Notificações desktop (plyer)
- `play_sound()` - Tocar sons (pygame)
- `run_timer()` / `start_timer()` - Timer com notificação

**Recomendação:**
- **Mover** para `bet/utils/notifications.py`
- Renomear para plural (notifications)

```python
# Proposta futura:
bet/utils/
├── __init__.py
├── notifications.py  # notification.py renomeado
├── datetime.py       # Extrair funções de tempo do utils.py
└── formatters.py     # Extrair formatters do utils.py
```

---

#### 4. **utils.py**
**Status:** ✅ **NECESSÁRIO** (40KB!)
**Usado por:** 5 arquivos
- `bet/cli/commands/daily.py`
- `bet/cli/commands/favorites.py`
- `bet/cli/commands/halftime.py`
- `bet/cli.py`
- `bet/services/betfair/client.py`

**Funções:** MUITAS (arquivo grande - 40KB)
- Conversão de datas/horas
- Formatação de tabelas (print_table)
- Cálculos de odds
- Busca de resultados
- Country codes
- E muito mais...

**Recomendação:**
- **DIVIDIR** em módulos menores em `bet/utils/`
- Criar submódulos temáticos

```python
# Proposta futura:
bet/utils/
├── __init__.py
├── datetime.py       # converter_hora_para_datetime, verificar_tempo_passado
├── formatters.py     # print_table, formatações
├── calculations.py   # Cálculos de odds, lucros
├── search.py         # buscar_resultado_partida
└── constants.py      # country_codes, markets_dict
```

---

#### 5. **cli.py** (62KB!)
**Status:** ⚠️ **LEGACY** mas **AINDA USADO**
**Usado por:** `bet/cli/main.py` (importação dinâmica)

**Função:** CLI antigo com todos os comandos

**Situação atual:**
- Comandos `mday`, `fav`, `ht0x0` já migrados para `bet/cli/commands/`
- Comandos restantes: `shell`, `diff`, `relatorio`, `layaway`, `analise`, `sofa`, `api`
- `bet/cli/main.py` importa dinamicamente para backward compatibility

**Recomendação:**
- **MANTER** temporariamente
- **MIGRAR** comandos restantes para `bet/cli/commands/`
- **DEPRECAR** após migração completa

```python
# Comandos a migrar:
bet/cli/commands/
├── shell.py      # shell command
├── diff.py       # diff command
├── report.py     # relatorio command
├── layaway.py    # layaway command
├── analysis.py   # analise command
├── sofa.py       # sofa command
└── api.py        # api command
```

---

### ❌ **PODEM SER REMOVIDOS** (não usados ou vazios)

#### 6. **db.py**
**Status:** ❌ **VAZIO** (1 linha)
**Usado por:** Ninguém

**Recomendação:**
- **REMOVER** agora
- Recriar em `bet/storage/database.py` quando implementar Fase 4

---

#### 7. **evolution.py**
**Status:** ⚠️ **POUCO USADO**
**Usado por:** Apenas comentado em `bet/services/betfair/client.py`

**Função:** `send_message()` - Enviar mensagem WhatsApp (Evolution API)

**Recomendação:**
- **Mover** para `bet/services/messaging/` ou `bet/utils/messaging.py`
- OU **REMOVER** se não for mais usado

---

## 📊 Resumo

| Arquivo | Status | Ação Recomendada | Prioridade |
|---------|--------|------------------|------------|
| `config.py` | ✅ Necessário | Mover para `bet/config/` | Baixa |
| `files.py` | ✅ Necessário | Mover para `bet/storage/` | Média |
| `notification.py` | ✅ Necessário | Mover para `bet/utils/` | Média |
| `utils.py` | ✅ Necessário | Dividir em módulos | Alta |
| `cli.py` | ⚠️ Legacy | Migrar comandos restantes | Alta |
| `db.py` | ❌ Vazio | Remover | Alta |
| `evolution.py` | ⚠️ Pouco usado | Mover ou remover | Baixa |

---

## 🎯 Plano de Ação Sugerido

### **Fase 4: Storage & Utils** (Próxima)

1. **Criar `bet/storage/`**
   ```
   bet/storage/
   ├── __init__.py
   ├── files.py      # Mover bet/files.py
   └── database.py   # Criar (vazio por enquanto)
   ```

2. **Reorganizar `bet/utils/`**
   ```
   bet/utils/
   ├── __init__.py
   ├── datetime.py
   ├── formatters.py
   ├── calculations.py
   ├── notifications.py  # Mover bet/notification.py
   └── constants.py
   ```

3. **Migrar comandos restantes do cli.py**
   - Criar módulos em `bet/cli/commands/`
   - Atualizar `bet/cli/main.py`
   - Deprecar `bet/cli.py`

4. **Limpar arquivos desnecessários**
   - Remover `bet/db.py`
   - Decidir sobre `bet/evolution.py`

### **Benefícios esperados:**
- ✅ Código mais organizado
- ✅ Módulos menores e mais focados
- ✅ Fácil localizar funcionalidades
- ✅ Melhor testabilidade
- ✅ Menos imports desnecessários
