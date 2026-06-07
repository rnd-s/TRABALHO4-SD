class TipoConta:
    CORRENTE = "corrente"
    POUPANCA = "poupanca"


class Conta:
    def __init__(self, numero, login, nome, saldo, tipo, limite_cheque_especial=None, taxa_rendimento=None):
        self.numero = numero
        self.login = login
        self.nome = nome
        self.saldo = saldo
        self.tipo = tipo
        self.limite_cheque_especial = limite_cheque_especial
        self.taxa_rendimento = taxa_rendimento

    def depositar(self, valor):
        if valor <= 0:
            return False
        self.saldo += valor
        return True

    def sacar(self, valor):
        if valor <= 0:
            return False
        if self.tipo == TipoConta.CORRENTE:
            disponivel = self.saldo + (self.limite_cheque_especial or 0)
            if valor > disponivel:
                return False
        else:
            if valor > self.saldo:
                return False
        self.saldo -= valor
        return True

    def transferir(self, conta_destino, valor):
        if self.sacar(valor):
            conta_destino.depositar(valor)
            return True
        return False

    def to_dict(self):
        return {
            "numero": self.numero,
            "login": self.login,
            "nome": self.nome,
            "saldo": self.saldo,
            "tipo": self.tipo,
            "limite_cheque_especial": self.limite_cheque_especial,
            "taxa_rendimento": self.taxa_rendimento
        }
