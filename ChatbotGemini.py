import google.generativeai as genai
from prompts import * 
from BancoPedidos import *
import re

genai.configure(api_key="AIzaSyDhE12w58FQQQHr2jMHh1Jsl2ZmipQ65qA")


model = genai.GenerativeModel("gemini-1.5-flash")


def iniciar_chat():
    print("Olá, tudo bem? Sou o Popoli, assistente do restaurante Poliedro. Em que posso te ajudar?")

    chat_history = []

    while True:
        user_input = input("Você: ")

        if user_input.lower() == "sair":
            print("Até mais! Popoli estará à disposição caso tenha alguma dúvida.")
            break

        chat_history.append({"role": "user", "parts": [user_input]})

        # Gera a resposta com base nos prompts e na entrada do usuário
        response = model.generate_content([
            {"role": "user", "parts": [prompt_restaurante + prompt_dos_Horarios + prompt_do_Cardapio + prompt_do_preco  + prompt_dePedidos + user_input]}
        ], stream=True)

        print("Popoli:", end=" ")
        bot_reply = ""

        for chunk in response:
            print(chunk.text, end="", flush=True)
            bot_reply += chunk.text

        print("\n")

        # Identifica e processa pedidos ou consultas ao banco de dados
        if re.search(r"\b(pedir|fazer um pedido|novo pedido|pedir algo)\b", user_input.lower()):
            numero_cliente = input("Por favor, informe seu número de telefone (formato (XX) XXXXX-XXXX): ")
            if not validar_numero(numero_cliente):
                print("Número inválido! Use o formato correto.")
                continue

            pedido = input("Qual o seu pedido? ")
            PedidosArmazenados(numero_cliente, pedido)

        elif re.search(r"\b(ver|consultar|meus pedidos|ver o que já pedi)\b", user_input.lower()):
            numero_cliente = input("Informe seu número de telefone para consultar os pedidos: ")
            if not validar_numero(numero_cliente):
                print("Número inválido! Use o formato correto.")
                continue

            resultado = BuscarPedidos(numero_cliente)
            print(resultado)

        chat_history.append({"role": "model", "parts": [bot_reply]})
