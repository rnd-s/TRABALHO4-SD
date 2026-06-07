import pika
import json
from models.banco import Banco
from models.conta import Conta, TipoConta

banco_rn = Banco()

def processar_mensagem(ch, method, properties, body):
  
    mensagem = json.loads(body)
    acao = mensagem.get("acao")
    dados = mensagem.get("dados", {})
    
    print(f"\n[>] Requisição recebida: {acao}")
    
    resposta = {"sucesso": False, "mensagem": "Ação desconhecida"}

    try:
        if acao == "criar_cliente":
            tipo = TipoConta.CORRENTE if dados.get('tipo') == "corrente" else TipoConta.POUPANCA
            conta = Conta(
                numero=int(dados.get('numero')),
                login=dados.get('login'),
                nome=dados.get('nome'),
                saldo=float(dados.get('saldo_inicial', 0)),
                tipo=tipo,
                limite_cheque_especial=float(dados.get('limite', 0)),
                taxa_rendimento=float(dados.get('taxa', 0))
            )
            cliente = banco_rn.criar_cliente(dados.get('login'), dados.get('nome'), conta)
            if cliente:
                resposta = {"sucesso": True, "mensagem": "Cliente criado com sucesso", "cliente": cliente.to_dict()}
            else:
                resposta = {"sucesso": False, "mensagem": "Cliente ou conta já existe"}

        elif acao == "depositar":
            conta = banco_rn.buscar_conta(int(dados.get('numero')))
            if conta and conta.depositar(float(dados.get('valor'))):
                resposta = {"sucesso": True, "mensagem": "Depósito realizado", "saldo": conta.saldo}
            else:
                resposta = {"sucesso": False, "mensagem": "Conta não encontrada ou valor inválido"}

        elif acao == "sacar":
            conta = banco_rn.buscar_conta(int(dados.get('numero')))
            if conta and conta.sacar(float(dados.get('valor'))):
                resposta = {"sucesso": True, "mensagem": "Saque realizado", "saldo": conta.saldo}
            else:
                resposta = {"sucesso": False, "mensagem": "Saldo insuficiente ou conta não encontrada"}

        elif acao == "consultar_saldo":
            conta = banco_rn.buscar_conta(int(dados.get('numero')))
            if conta:
                resposta = {"sucesso": True, "saldo": conta.saldo, "tipo": conta.tipo}
            else:
                resposta = {"sucesso": False, "mensagem": "Conta não encontrada"}

        elif acao == "transferir":
            conta_origem = banco_rn.buscar_conta(int(dados.get('origem')))
            conta_destino = banco_rn.buscar_conta(int(dados.get('destino')))
            if conta_origem and conta_destino:
                if conta_origem.transferir(conta_destino, float(dados.get('valor'))):
                    resposta = {"sucesso": True, "mensagem": "Transferência realizada", "saldo_origem": conta_origem.saldo}
                else:
                    resposta = {"sucesso": False, "mensagem": "Saldo insuficiente na origem"}
            else:
                resposta = {"sucesso": False, "mensagem": "Conta origem ou destino não encontrada"}

    except Exception as e:
        resposta = {"sucesso": False, "mensagem": f"Erro interno: {str(e)}"}

    print(f"[<] Respondendo: {resposta.get('mensagem', 'Sucesso')}")

    # Devolve a resposta para a "fila de retorno" exclusiva do cliente que pediu
    if properties.reply_to and properties.correlation_id:
        ch.basic_publish(
            exchange='',
            routing_key=properties.reply_to,
            properties=pika.BasicProperties(correlation_id=properties.correlation_id),
            body=json.dumps(resposta)
        )
    
    # Confirma para o RabbitMQ que a mensagem foi processada e pode ser apagada da fila
    ch.basic_ack(delivery_tag=method.delivery_tag)

def iniciar_worker():
    # Conecta no RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()

    # Cria a fila principal onde os clientes vão jogar as mensagens
    channel.queue_declare(queue='fila_banco', durable=True) # durable=True garante que a fila não some se o RabbitMQ reiniciar

    # Garante que o worker só pegue 1 mensagem por vez (justo e seguro)
    channel.basic_qos(prefetch_count=1)
    
    # Define quem vai processar as mensagens da 'fila_banco'
    channel.basic_consume(queue='fila_banco', on_message_callback=processar_mensagem)

    print(" [*] Servidor Bancário (Worker) aguardando mensagens. Para sair pressione CTRL+C")
    channel.start_consuming()

if __name__ == '__main__':
    iniciar_worker()
