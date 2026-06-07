package main

import (
	"bufio"
	"context" 
	"crypto/rand"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"strconv"
	"strings"

	amqp "github.com/rabbitmq/amqp091-go"
)

func failOnError(err error, msg string) {
	if err != nil {
		log.Panicf("%s: %s", msg, err)
	}
}


func randomString(l int) string {
	bytes := make([]byte, l)
	rand.Read(bytes)
	return fmt.Sprintf("%x", bytes)
}

func readStr(reader *bufio.Reader, prompt string) string {
	fmt.Print(prompt)
	text, _ := reader.ReadString('\n')
	return strings.TrimSpace(text)
}

func readFloat(reader *bufio.Reader, prompt string) float64 {
	str := readStr(reader, prompt)
	val, _ := strconv.ParseFloat(str, 64)
	return val
}

func readInt(reader *bufio.Reader, prompt string) int {
	str := readStr(reader, prompt)
	val, _ := strconv.Atoi(str)
	return val
}

func main() {
	// Conecta ao RabbitMQ
	conn, err := amqp.Dial("amqp://guest:guest@localhost:5672/")
	failOnError(err, "Falha ao conectar no RabbitMQ")
	defer conn.Close()

	ch, err := conn.Channel()
	failOnError(err, "Falha ao abrir o canal")
	defer ch.Close()

	
	q, err := ch.QueueDeclare("", false, false, true, false, nil)
	failOnError(err, "Falha ao declarar a fila de callback")

	msgs, err := ch.Consume(q.Name, "", true, false, false, false, nil)
	failOnError(err, "Falha ao registrar consumidor")

	reader := bufio.NewReader(os.Stdin)

	
	enviarParaFila := func(acao string, dados map[string]interface{}) map[string]interface{} {
		corrId := randomString(32)
		payloadMap := map[string]interface{}{"acao": acao, "dados": dados}
		payloadBytes, _ := json.Marshal(payloadMap)

		
		err = ch.PublishWithContext(
			context.Background(),
			"",
			"fila_banco",
			false,
			false,
			amqp.Publishing{
				DeliveryMode: amqp.Persistent,
				ContentType:   "application/json",
				CorrelationId: corrId,
				ReplyTo:       q.Name,
				Body:          payloadBytes,

			})
		failOnError(err, "Falha ao publicar a mensagem")

		// Aguarda a resposta correta chegar
		for d := range msgs {
			if corrId == d.CorrelationId {
				var res map[string]interface{}
				json.Unmarshal(d.Body, &res)
				return res
			}
		}
		return nil
	}

	for {
		fmt.Println("\n--- BANCO RN (Cliente MQ / GO) ---")
		fmt.Println("1 - Criar conta")
		fmt.Println("2 - Depositar")
		fmt.Println("3 - Sacar")
		fmt.Println("4 - Consultar saldo")
		fmt.Println("5 - Transferir")
		fmt.Println("6 - Sair")

		opcao := readStr(reader, "\nEscolha: ")

		switch opcao {
		case "1":
			login := readStr(reader, "Login: ")
			nome := readStr(reader, "Nome: ")
			tipo := readStr(reader, "Tipo de conta (corrente/poupanca): ")
			numero := readInt(reader, "Numero da conta: ")
			saldo := readFloat(reader, "Saldo inicial: ")

			var limite, taxa float64
			if tipo == "corrente" {
				limite = readFloat(reader, "Limite cheque especial: ")
			} else {
				taxa = readFloat(reader, "Taxa de rendimento (ex: 0.05): ")
			}

			dados := map[string]interface{}{
				"login": login, "nome": nome, "numero": numero, "tipo": tipo,
				"saldo_inicial": saldo, "limite": limite, "taxa": taxa,
			}
			res := enviarParaFila("criar_cliente", dados)
			fmt.Printf("\n=> [MQ] %v\n", res["mensagem"])

		case "4":
			numero := readInt(reader, "Número da conta: ")
			res := enviarParaFila("consultar_saldo", map[string]interface{}{"numero": numero})
			if res["sucesso"] == true {
				fmt.Printf("\n=> [MQ] Saldo atual: R$ %v (%v)\n", res["saldo"], res["tipo"])
			} else {
				fmt.Printf("\n=> [MQ] Erro: %v\n", res["mensagem"])
			}

		case "6":
			fmt.Println("Até logo!")
			return

		default:
			fmt.Println("=> Opção inválida (ou não implementada no atalho).")
		}
	}
}