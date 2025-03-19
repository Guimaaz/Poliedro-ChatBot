import google.generativeai as genai
from prompts import * 
from BancoPedidos import *
import re

# Configuração da API do Gemini
genai.configure(api_key="AIzaSyDhE12w58FQQQHr2jMHh1Jsl2ZmipQ65qA")

model = genai.GenerativeModel("gemini-1.5-flash")

def extrair_intencao(texto):
    """
    Extrai a intenção do modelo a partir do texto gerado.
    Ele deve conter INTENÇÃO: FAZER_PEDIDO ou INTENÇÃO: CONSULTAR_PEDIDO
    """
    match = re.search(r'INTENÇÃO:\s*(FAZER_PEDIDO|CONSULTAR_PEDIDO|NENHUMA)', texto, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return "NENHUMA"

def iniciar_chat():
    print("Olá, tudo bem? Sou o Popoli, assistente do restaurante Poliedro. Em que posso te ajudar?")

    chat_history = []

    while True:
        user_input = input("Você: ")

        if user_input.lower() == "sair":
            print("Até mais! Popoli estará à disposição caso tenha alguma dúvida.")
            break

        chat_history.append({"role": "user", "parts": [user_input]})

        # Criando um prompt mais estruturado
        prompt_completo = (
            prompt_restaurante + prompt_dos_Horarios + prompt_do_Cardapio + 
            prompt_do_preco + prompt_intencao +
            "\n\nBaseado na conversa acima, identifique a intenção do usuário.\n"
            "Responda no seguinte formato (sem explicar):\n\n"
            "**INTENÇÃO: FAZER_PEDIDO** ou **INTENÇÃO: CONSULTAR_PEDIDO** ou **INTENÇÃO: CONVERSAR**"
        )

        # Gera a resposta
        response = model.generate_content([
            {"role": "user", "parts": [prompt_completo + user_input]}
        ])

        bot_reply = response.text.strip()

        print(f"Popoli: {bot_reply}\n")

       

        # Extrai a intenção corretamente
        intencao = extrair_intencao(bot_reply)
        
        if intencao == "FAZER_PEDIDO":
            numero_cliente = input("Por favor, informe seu número de telefone (formato (XX) XXXXX-XXXX): ")
            if not validar_numero(numero_cliente):
                print("Número inválido! Use o formato correto.")
                continue

            pedido = input("Qual o seu pedido? ")
            PedidosArmazenados(numero_cliente, pedido)
            print("Pedido registrado com sucesso!")

        elif intencao == "CONSULTAR_PEDIDO":
            numero_cliente = input("Informe seu número de telefone para consultar os pedidos (formato (XX) XXXXX-XXXX): ")
            if not validar_numero(numero_cliente):
                print("Número inválido! Use o formato correto.")
                continue

            resultado = BuscarPedidos(numero_cliente)
            print(f"Seus pedidos: {resultado}")
        
        chat_history.append({"role": "model", "parts": [bot_reply]})