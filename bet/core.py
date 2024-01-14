def calcula_saida_edge_black_lay(
    odd_entrada_back: float, odd_saida_lay: float, stake: float
):
    """
    Calcula o valor efetivo da aposta para uma estratégia de black edge em apostas.

    Esta função calcula o valor efetivo da aposta a ser usado quando se aplica uma estratégia de black edge
    em apostas. Ela determina a aposta ajustada com base nas odds de entrada para apostar (odd_entrada_back),
    nas odds de saída para encerrar a aposta (odd_saida_lay), e no valor inicial apostado.

    Parâmetros:
    odd_entrada_back (float): As odds nas quais a aposta foi feita inicialmente.
    odd_saida_lay (float): As odds nas quais a aposta será encerrada.
    stake (float): O valor inicial de dinheiro apostado.

    Retorna:
    float: O valor calculado da aposta efetiva considerando as odds fornecidas.

    Exemplo:
    >>> calcula_saida_edge_black_lay(2.0, 1.8, 100)
    111.11
    """
    return round((odd_entrada_back / odd_saida_lay) * stake, 2)

def calcula_saida_edge_lay_back(
    odd_entrada_lay: float, odd_saida_back: float, responsabilidade: float
):
    """
    Calcula o lucro de uma estratégia de apostas do tipo edge lay-back.

    Esta função é usada para calcular o lucro resultante de uma estratégia de apostas onde o usuário
    primeiro faz uma aposta lay (contra) e depois faz uma aposta back (a favor) em um evento. 
    O cálculo leva em conta as odds da aposta lay e back e a responsabilidade assumida na aposta lay.

    Parâmetros:
    odd_entrada_lay (float): As odds nas quais a aposta lay foi feita.
    odd_saida_back (float): As odds nas quais a aposta back é realizada.
    responsabilidade (float): O valor da responsabilidade assumida na aposta lay.

    Retorna:
    float: O lucro calculado, arredondado para duas casas decimais.

    Exemplo:
    >>> calcula_saida_edge_lay_back(2.0, 1.8, 100)
    22.22
    """
    lucro = responsabilidade / (odd_entrada_lay - 1)
    return round((odd_entrada_lay / odd_saida_back) * lucro, 2)

def calcula_saida_freebet_lay(odd_saida_back: float, responsabilidade: float):
    return round(responsabilidade / (odd_saida_back - 1), 2)
