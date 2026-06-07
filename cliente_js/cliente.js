import * as readline from 'node:readline/promises';
import { stdin as input, stdout as output } from 'node:process';
import amqplib from 'amqplib';
import crypto from 'crypto';

const rl = readline.createInterface({ input, output });

async function iniciarCliente() {
   
    const connection = await amqplib.connect('amqp://localhost');
    const channel = await connection.createChannel();

    
    const q = await channel.assertQueue('', { exclusive: true });

    
    const pendingRequests = new Map();

    
    channel.consume(q.queue, (msg) => {
        if (msg && pendingRequests.has(msg.properties.correlationId)) {
            const resolve = pendingRequests.get(msg.properties.correlationId);
            resolve(JSON.parse(msg.content.toString()));
            pendingRequests.delete(msg.properties.correlationId);
        }
    }, { noAck: true });

   
    async function enviarParaFila(acao, dados) {
        return new Promise((resolve) => {
            const correlationId = crypto.randomUUID();
            pendingRequests.set(correlationId, resolve);

            const payload = JSON.stringify({ acao, dados });

            channel.sendToQueue('fila_banco', Buffer.from(payload), {
                correlationId: correlationId,
                replyTo: q.queue 
            });
        });
    }

    async function menu() {
        console.log("\n--- BANCO RN (Cliente MQ / Node.js) ---");
        console.log("1 - Criar conta");
        console.log("2 - Depositar");
        console.log("3 - Sacar");
        console.log("4 - Consultar saldo");
        console.log("5 - Transferir");
        console.log("6 - Sair");

        const opcao = await rl.question("\nEscolha: ");

        if (opcao === "1") {
            const login = await rl.question("Login: ");
            const nome = await rl.question("Nome: ");
            const tipo = await rl.question("Tipo de conta (corrente/poupanca): ");
            const numero = await rl.question("Numero da conta: ");
            const saldo = await rl.question("Saldo inicial: ");
            
            let limite = 0, taxa = 0;
            if (tipo === "corrente") {
                limite = await rl.question("Limite cheque especial: ");
            } else {
                taxa = await rl.question("Taxa de rendimento (ex: 0.05): ");
            }

            const dados = {
                login, nome, numero: parseInt(numero), tipo,
                saldo_inicial: parseFloat(saldo), limite: parseFloat(limite), taxa: parseFloat(taxa)
            };

            const resposta = await enviarParaFila("criar_cliente", dados);
            console.log(`\n=> [MQ] ${resposta.mensagem}`);

        } else if (opcao === "2") {
            const numero = await rl.question("Número da conta: ");
            const valor = await rl.question("Valor para depositar: ");
            
            const resposta = await enviarParaFila("depositar", { numero: parseInt(numero), valor: parseFloat(valor) });
            console.log(`\n=> [MQ] ${resposta.mensagem}. ${resposta.sucesso ? 'Novo saldo: R$ ' + resposta.saldo : ''}`);

        } else if (opcao === "3") {
            const numero = await rl.question("Número da conta: ");
            const valor = await rl.question("Valor para sacar: ");
            
            const resposta = await enviarParaFila("sacar", { numero: parseInt(numero), valor: parseFloat(valor) });
            console.log(`\n=> [MQ] ${resposta.mensagem}. ${resposta.sucesso ? 'Novo saldo: R$ ' + resposta.saldo : ''}`);

        } else if (opcao === "4") {
            const numero = await rl.question("Número da conta: ");
            
            const resposta = await enviarParaFila("consultar_saldo", { numero: parseInt(numero) });
            if (resposta.sucesso) {
                console.log(`\n=> [MQ] Saldo atual: R$ ${resposta.saldo} (${resposta.tipo})`);
            } else {
                console.log(`\n=> [MQ] Erro: ${resposta.mensagem}`);
            }

        } else if (opcao === "5") {
            const origem = await rl.question("Sua conta (Origem): ");
            const destino = await rl.question("Conta destino: ");
            const valor = await rl.question("Valor para transferir: ");
            
            const resposta = await enviarParaFila("transferir", {
                origem: parseInt(origem), destino: parseInt(destino), valor: parseFloat(valor)
            });
            console.log(`\n=> [MQ] ${resposta.mensagem}. ${resposta.sucesso ? 'Seu saldo: R$ ' + resposta.saldo_origem : ''}`);

        } else if (opcao === "6") {
            console.log("Até logo");
            await channel.close();
            await connection.close();
            rl.close();
            process.exit(0);
        } else {
            console.log("\n=> Opção inválida.");
        }

        if (opcao !== "6") await menu();
    }

    menu();
}

iniciarCliente().catch(console.error);
