class NaoExisteMercadoExcecao(Exception):
    """Exceção personalizada para erros específicos."""

    def __init__(self, mensagem):
        super().__init__(mensagem)
