# Trabalho 4 – Comunicação Indireta com Filas de Mensagens

## Disciplina

Sistemas Distribuídos – QXD0043

## Integrantes

* Nome 1
* Nome 2
* Nome 3

## Objetivo

Este trabalho tem como objetivo evoluir a arquitetura do sistema bancário distribuído desenvolvido na disciplina, substituindo a comunicação direta entre cliente e servidor por uma arquitetura baseada em Filas de Mensagens (Message Queues), utilizando RabbitMQ como intermediário.

A solução busca reduzir o acoplamento entre os componentes do sistema e demonstrar as propriedades de comunicação indireta estudadas na disciplina.

---

# Arquitetura

A comunicação ocorre através de uma fila denominada `fila_banco`.

```text
+-------------+
| Cliente Go  |
+-------------+
       |
       | Publica Mensagens
       v
+------------------+
|    RabbitMQ      |
|   fila_banco     |
+------------------+
       |
       | Consome Mensagens
       v
+------------------+
| Worker Python    |
| Servidor Bancário|
+------------------+
```

O cliente não se comunica diretamente com o servidor bancário. Todas as requisições passam pelo RabbitMQ, que atua como intermediário.

---

# Tecnologias Utilizadas

* Go
* Python
* RabbitMQ
* Docker
* AMQP 0-9-1

---

# Funcionalidades Implementadas

* Criar cliente
* Consultar saldo
* Depositar
* Sacar
* Transferir valores

As operações são enviadas pelo cliente para a fila `fila_banco` e processadas pelo worker Python.

---

# Comunicação Indireta

## Desacoplamento Espacial

O cliente não conhece o endereço IP nem a porta do servidor bancário.

Ele apenas publica mensagens na fila do RabbitMQ.

Dessa forma, o servidor pode ser substituído, reiniciado ou escalado sem alterações no cliente.

## Desacoplamento Temporal

O cliente consegue enviar mensagens mesmo quando o servidor bancário está desligado.

Durante os testes realizados:

1. O Worker foi interrompido.
2. O cliente enviou uma requisição de criação de conta.
3. A mensagem permaneceu armazenada na fila `fila_banco`.
4. Após a reinicialização do Worker, a mensagem foi consumida e processada normalmente.

Esse comportamento demonstra que produtor e consumidor possuem tempos de vida independentes.

---

# Robustez e Tratamento de Falhas

A fila principal foi criada utilizando:

```python
channel.queue_declare(
    queue='fila_banco',
    durable=True
)
```

O parâmetro `durable=True` garante que a fila continue existindo após reinicializações do RabbitMQ.

Além disso, o Worker utiliza confirmações explícitas (ACK):

```python
ch.basic_ack(
    delivery_tag=method.delivery_tag
)
```

A mensagem somente é removida da fila após o processamento bem-sucedido.

Também foi utilizado:

```python
channel.basic_qos(
    prefetch_count=1
)
```

permitindo que cada Worker processe apenas uma mensagem por vez.

---

# Justificativa da Escolha

A utilização de Filas de Mensagens foi escolhida por se adequar ao cenário do sistema bancário distribuído.

As operações bancárias podem ser executadas de forma assíncrona e não exigem que cliente e servidor estejam ativos simultaneamente.

O RabbitMQ atua como intermediário entre produtor e consumidor, eliminando o acoplamento direto e aumentando a flexibilidade da arquitetura.

---

# Impacto no Desempenho

A introdução do RabbitMQ adiciona uma etapa extra na comunicação:

```text
Cliente -> RabbitMQ -> Worker
```

Isso aumenta ligeiramente a latência em comparação com uma comunicação direta.

Por outro lado, a solução oferece vantagens importantes:

* Desacoplamento entre componentes;
* Maior tolerância a falhas;
* Possibilidade de escalabilidade;
* Processamento assíncrono;
* Melhor gerenciamento de carga.

O pequeno overhead introduzido é compensado pelos ganhos de flexibilidade e confiabilidade.

---

# Como Executar

## 1. Iniciar RabbitMQ

```bash
docker compose up -d
```

ou

```bash
docker run -d \
  --hostname rabbit \
  --name rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  rabbitmq:management
```

Painel:

```text
http://localhost:15672
```

Usuário:

```text
guest
```

Senha:

```text
guest
```

---

## 2. Iniciar o Worker

```bash
python worker.py
```

---

## 3. Executar o Cliente

```bash
go run cliente.go
```

---

# Demonstração

Para demonstrar o desacoplamento temporal:

1. Pare o Worker.
2. Execute uma operação no cliente.
3. Verifique no painel do RabbitMQ que existe uma mensagem na fila `fila_banco`.
4. Reinicie o Worker.
5. Observe a mensagem sendo processada automaticamente.

---