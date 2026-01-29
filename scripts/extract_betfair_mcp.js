// Script JavaScript para ser executado via MCP Playwright browser_evaluate
// Extrai jogos da Betfair e retorna JSON compacto

(() => {
  const jogos = [];
  const hoje = new Date().toISOString().split('T')[0];

  // Buscar todos os textos da página
  const allText = document.body.innerText;
  const lines = allText.split('\n');

  let currentComp = '';

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();

    // Detectar competição
    if ((line.includes('Série') || line.includes('Europa') || line.includes('Eliminatórias') ||
         line.includes('Premier') || line.includes('La Liga') || line.includes('Amistosos')) &&
        line.length < 100) {
      currentComp = line;
    }

    // Procurar horário
    const horaMatch = line.match(/Hoje às (\d{1,2}:\d{2})/);
    if (horaMatch) {
      const horario = horaMatch[1];

      // Próximas linhas devem ter os times
      let mandante = '';
      let visitante = '';

      for (let j = i + 1; j < Math.min(i + 6, lines.length); j++) {
        const nextLine = lines[j].trim();

        if (nextLine.length > 2 && nextLine.length < 50 &&
            !nextLine.match(/^\d+[,.]?\d*$/) &&
            !nextLine.includes('R$') &&
            !nextLine.includes('Correspondido') &&
            !nextLine.includes('Ver todo')) {

          if (!mandante) {
            mandante = nextLine;
          } else if (!visitante) {
            visitante = nextLine;
            break;
          }
        }
      }

      if (mandante && visitante) {
        jogos.push({
          d: hoje,
          h: horario,
          c: currentComp || 'N/A',
          m: mandante,
          v: visitante
        });
      }
    }
  }

  // Remover duplicatas
  const unique = [];
  const seen = new Set();

  jogos.forEach(jogo => {
    const key = `${jogo.h}|${jogo.m}|${jogo.v}`;
    if (!seen.has(key)) {
      seen.add(key);
      unique.push(jogo);
    }
  });

  // Retornar apenas os campos essenciais
  return {
    total: unique.length,
    jogos: unique.slice(0, 20)  // Limitar a 20 para não exceder limite
  };
})()
