from .cliente import ClienteBanco
from .conta import Conta


class Banco:
    def __init__(self):
        self.clientes = {}
        self.contas = {}

    def criar_cliente(self, login, nome, conta):
        if login in self.clientes or conta.numero in self.contas:
            return None
        cliente = ClienteBanco(login, nome, conta)
        self.clientes[login] = cliente
        self.contas[conta.numero] = conta
        return cliente

    def buscar_conta(self, numero):
        return self.contas.get(numero)

    def listar_clientes(self):
        return self.clientes
