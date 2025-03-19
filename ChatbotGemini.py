import google.generativeai as genai
from prompts import * 
from BancoPedidos import *
import re

#apikey
genai.configure(api_key="AIzaSyDhE12w58FQQQHr2jMHh1Jsl2ZmipQ65qA")

model = genai.GenerativeModel("gemini-1.5-flash")

def extrair_intencao(texto):
    """
    Extrai a intenção do modelo a partir do texto gerado.
    Ele deve conter INTENÇÃO: FAZER_PEDIDO ou INTENÇÃO: CONSULTAR_PEDIDO.
    """
    match = re.search(r'INTENÇÃO:\s*(FAZER_PEDIDO|CONSULTAR_PEDIDO)', texto, re.IGNORECASE)
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

       
        prompt_completo = (
            prompt_restaurante + prompt_dos_Horarios + prompt_do_Cardapio + 
            prompt_do_preco + prompt_intencao +
            "\n\nBaseado na conversa acima, identifique a intenção do usuário.\n"
            "Se o usuário deseja fazer um pedido, responda com: **INTENÇÃO: FAZER_PEDIDO**\n"
            "Se o usuário deseja consultar um pedido, responda com: **INTENÇÃO: CONSULTAR_PEDIDO**\n"
            "Caso contrário, responda normalmente de forma amigável e interativa, sem mencionar a intenção."
        )

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
                    print("Número inválido! Solicite para fazer um pedido novamente e coloque o numero correto")
                    continue

                pedido = input("Qual o seu pedido? ")
                PedidosArmazenados(numero_cliente, pedido)
                print("Popoli: Pedido registrado com sucesso!")
            elif intencao == "CONSULTAR_PEDIDO":
                print("Popoli: Claro! Para consultar seu pedido, preciso do seu número de telefone.")
                numero_cliente = input("Número (formato (XX) XXXXX-XXXX): ")
                if not validar_numero(numero_cliente):
                    print("Número inválido! Solicite para consultar os pedidos novamente e coloque o numero correto")
                    continue

                resultado = BuscarPedidos(numero_cliente)
                print(f"Popoli: Seus pedidos: {resultado}")
        else:
           
            print(f"Popoli: {bot_reply}")
        
        chat_history.append({"role": "model", "parts": [bot_reply]})
