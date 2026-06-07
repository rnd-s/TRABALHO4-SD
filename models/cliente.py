class ClienteBanco:
    def __init__(self, login, nome, conta):
        self.login = login
        self.nome = nome
        self.conta = conta

    def to_dict(self):
        return {
            "login": self.login,
            "nome": self.nome,
            "conta": self.conta.to_dict()
        }
