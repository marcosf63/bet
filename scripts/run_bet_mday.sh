#!/bin/bash

# Ative o ambiente virtual
source /home/marcos/projetos/bet/.venv/bin/activate

# Execute o comando da CLI
bet mday --no-print

# Desative o ambiente virtual (opcional, pois o script será encerrado)
deactivate

