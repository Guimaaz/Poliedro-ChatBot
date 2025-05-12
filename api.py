from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from server.prompts import *
from server.BancoPedidos import *
import re
import os
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)  # Permite todas as origens

# Carrega as variáveis de ambiente
load_dotenv()
senha = os.getenv("API_KEY")

# Configuração do modelo Gemini (igual ao seu código)
genai.configure(api_key=senha)
model = genai.GenerativeModel("gemini-1.5-flash")

# Banco de dados de pedidos (simulado como no seu código)
pedidos_db = {}

def extrair_intencao(texto):
    """
    Extrai a intenção do modelo a partir do texto gerado.
    Exatamente como no seu código original.
    """
    match = re.search(r'INTENÇÃO:\s*(FAZER_PEDIDO|CONSULTAR_PEDIDO|REMOVER_PEDIDO)', texto, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return None

def validar_numero(numero):
    """Valida o formato do número de telefone (igual ao seu código)"""
    padrao = r'^\(\d{2}\) \d{5}-\d{4}$'
    return re.match(padrao, numero) is not None

@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', '*')
        response.headers.add('Access-Control-Allow-Methods', '*')
        return response

    try:
        data = request.get_json()
        
        # Campos esperados (igual à lógica do seu código)
        user_input = data.get('mensagem')
        numero_cliente = data.get('numero_cliente')
        pedido = data.get('pedido')
        confirmacao = data.get('confirmacao')
        item_sugerido = data.get('item_sugerido')

        # Geração da resposta pelo modelo Gemini (igual ao seu código)
        response = model.generate_content([
            {"role": "user", "parts": [prompt_completo + user_input]}
        ])
        bot_reply = response.text.strip()
        intencao = extrair_intencao(bot_reply)

        # Lógica de resposta (igual ao seu código original)
        if not intencao:
            return jsonify({'resposta': bot_reply})

        if intencao == "FAZER_PEDIDO":
            if not numero_cliente:
                return jsonify({
                    'resposta': "Certo! Vamos fazer seu pedido. Por favor, informe seu número de telefone (formato (XX) XXXXX-XXXX).",
                    'requer_numero': True
                })
            
            if not validar_numero(numero_cliente):
                return jsonify({
                    'resposta': "Número inválido! Solicite para fazer um pedido novamente e coloque o número correto.",
                    'requer_numero': True
                })

            if not pedido:
                return jsonify({
                    'resposta': "Qual o seu pedido?",
                    'requer_pedido': True
                })

            itemSugerido, exato = VerificarItensCardapio(pedido)

            if not itemSugerido:
                return jsonify({
                    'resposta': "Desculpa, não trabalhamos com esse item. Por favor, peça algo presente em nosso cardápio."
                })

            if not exato:
                if confirmacao is None:
                    return jsonify({
                        'resposta': f"Você quis dizer '{itemSugerido}'? (sim/não)",
                        'requer_confirmacao': True,
                        'item_sugerido': itemSugerido
                    })
                elif confirmacao.lower() != 'sim':
                    return jsonify({
                        'resposta': "Entendido. Pedido cancelado. Por favor, solicite novamente com o nome correto do prato."
                    })

            pedido_id = PedidosArmazenados(numero_cliente, itemSugerido if exato else item_sugerido)
            return jsonify({
                'resposta': f"Pedido realizado com sucesso! Seu ID de pedido é {pedido_id}.",
                'pedido_id': pedido_id
            })

        elif intencao == "CONSULTAR_PEDIDO":
            if not numero_cliente:
                return jsonify({
                    'resposta': "Claro! Para consultar seu pedido, preciso do seu número de telefone (formato (XX) XXXXX-XXXX).",
                    'requer_numero': True
                })

            if not validar_numero(numero_cliente):
                return jsonify({
                    'resposta': "Número inválido! Solicite para consultar os pedidos novamente e coloque o numero correto",
                    'requer_numero': True
                })

            resultado = BuscarPedidos(numero_cliente)
            return jsonify({'resposta': resultado})

        elif intencao == "REMOVER_PEDIDO":
            if not numero_cliente:
                return jsonify({
                    'resposta': "Claro! Para remover seu pedido, preciso do seu número de telefone (formato (XX) XXXXX-XXXX).",
                    'requer_numero': True
                })

            if not validar_numero(numero_cliente):
                return jsonify({
                    'resposta': "Número inválido! Solicite para remover o(os) pedidos novamente e coloque o número correto",
                    'requer_numero': True
                })

            pedidos_atuais = BuscarPedidos(numero_cliente)
            if "nenhum pedido" in pedidos_atuais.lower():
                return jsonify({
                    'resposta': "Não encontramos pedidos ativos para esse número."
                })

            if not pedido:
                return jsonify({
                    'resposta': "Aqui estão seus pedidos atuais:\n" + pedidos_atuais + "\nQual pedido você gostaria de remover?",
                    'requer_pedido_remocao': True,
                    'pedidos_atuais': pedidos_atuais
                })

            linhas = pedidos_atuais.split("\n")
            pedidos_listados = [linha.split(" (ID")[0].split(": ")[1].strip().lower() for linha in linhas]

            if pedido.lower() not in pedidos_listados:
                return jsonify({
                    'resposta': "Esse pedido não foi encontrado entre os seus pedidos. Verifique o nome e tente novamente."
                })

            resultado = removerPedidos(numero_cliente, pedido)
            return jsonify({'resposta': resultado})

    except Exception as e:
        print(f"Erro na API: {str(e)}")
        return jsonify({'resposta': f"Erro interno: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)