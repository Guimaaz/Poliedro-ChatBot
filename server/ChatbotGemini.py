import google.generativeai as genai
from server.prompts import * 
from server.BancoPedidos import *
import re
import os
from dotenv import load_dotenv

#funções q "escondem a api" e puxam ela pelo .env usando o import os e o dotent load_dontenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
senha = os.getenv("API_KEY")
genai.configure(api_key=senha)

model = genai.GenerativeModel("gemini-1.5-flash")

def extrair_intencao(texto):
    """
    Extrai a intenção do modelo a partir do texto gerado.
    Ele deve conter INTENÇÃO: FAZER_PEDIDO ou INTENÇÃO: CONSULTAR_PEDIDO ou INTENÇÃO: REMOVER_PEDIDO.
    """
    match = re.search(r'INTENÇÃO:\s*(FAZER_PEDIDO|CONSULTAR_PEDIDO|REMOVER_PEDIDO)', texto, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return None  

def iniciar_chat():
    print("Olá, tudo bem? Sou o Popoli, assistente do restaurante Poliedro. Em que posso te ajudar?")
    
    chat_history = []

    while True:
        user_input = input("Você: ")

        if user_input.lower() == "sair":
            print("Até mais! Popoli estará à disposição caso tenha alguma dúvida.")
            break

        chat_history.append({"role": "user", "parts": [user_input]})

       
        

        response = model.generate_content([
            {"role": "user", "parts": [prompt_completo + user_input]}
        ])
        
        bot_reply = response.text.strip()
        intencao = extrair_intencao(bot_reply)
        
        if intencao:
            if intencao == "FAZER_PEDIDO":
                print("Popoli: Certo! Vamos fazer seu pedido. Por favor, informe seu número de telefone.")
                numero_cliente = input("Número (formato (XX) XXXXX-XXXX): ")
        
                if not validar_numero(numero_cliente):
                    print("Popoli : Número inválido! Solicite para fazer um pedido novamente e coloque o número correto.")
                    continue

                pedido = input("Qual o seu pedido? ")
                itemSugerido, exato = VerificarItensCardapio(pedido)

                if itemSugerido:
                    if exato:
                        PedidosArmazenados(numero_cliente, itemSugerido)
                    else:
                        confirmacao = input(f"Popoli : Você quis dizer '{itemSugerido}'? (sim/não): ").strip().lower()
                        if confirmacao == "sim":
                            PedidosArmazenados(numero_cliente, itemSugerido)
                        else:
                            print("Popoli : Entendido. Pedido cancelado. Por favor, solicite novamente com o nome correto do prato.")
                else:
                    print("Popoli : Desculpa, não trabalhamos com esse item. Por favor, peça algo presente em nosso cardápio.")

  
            elif intencao == "CONSULTAR_PEDIDO":
                print("Popoli: Claro! Para consultar seu pedido, preciso do seu número de telefone.")
                numero_cliente = input("Número (formato (XX) XXXXX-XXXX): ")
                if not validar_numero(numero_cliente):
                    print("Número inválido! Solicite para consultar os pedidos novamente e coloque o numero correto")
                    continue

                resultado = BuscarPedidos(numero_cliente)
                print(resultado)

            elif intencao == "REMOVER_PEDIDO":
                print("Popoli: Claro! Para remover seu pedido, preciso do seu número de telefone.")
                numero_cliente = input("Número (Formato (XX) XXXXX-XXXX): ")
    
                if not validar_numero(numero_cliente):
                    print("Número inválido! Solicite para remover o(os) pedidos novamente e coloque o número correto")
                    continue

                pedidos_atuais = BuscarPedidos(numero_cliente)
                if "nenhum pedido" in pedidos_atuais.lower():
                    print("Popoli: Não encontramos pedidos ativos para esse número.")
                    continue

                print("Popoli: Aqui estão seus pedidos atuais:")
                print(pedidos_atuais)

                pedido = input("Qual pedido você gostaria de remover? ").strip().lower()

   
                linhas = pedidos_atuais.split("\n")
                pedidos_listados = [linha.split(" (ID")[0].split(": ")[1].strip().lower() for linha in linhas]

                if pedido not in pedidos_listados:
                    print("Popoli: Esse pedido não foi encontrado entre os seus pedidos. Verifique o nome e tente novamente.")
                    continue

                resultado = removerPedidos(numero_cliente, pedido)
                


        else:
           
            print(f"Popoli: {bot_reply}")
        
        chat_history.append({"role": "model", "parts": [bot_reply]})
