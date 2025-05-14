from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from server.prompts import *
from server.BancoPedidos import (
    CreateDatabase,
    validar_numero,
    PedidosArmazenados,
    BuscarPedidos,
    removerPedidos,
    VerificarItensCardapio,
    registrar_cliente,
    autenticar_cliente
)
import re
import os
import sqlite3
from dotenv import load_dotenv
from pathlib import Path

app = Flask(__name__)
CORS(app)

load_dotenv(dotenv_path=Path('.') / '.env')
genai.configure(api_key=os.getenv("API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

CreateDatabase()

def extrair_intencao(texto):
    match = re.search(r'INTENÇÃO:\s*(FAZER_PEDIDO|CONSULTAR_PEDIDO|REMOVER_PEDIDO|VER_CARDAPIO|OUTRA)', texto, re.IGNORECASE)
    return match.group(1).upper() if match else None

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    numero_cliente = data.get('numero_cliente')
    senha = data.get('senha')

    if not numero_cliente or not senha:
        return jsonify({'success': False, 'message': 'Número de telefone e senha são obrigatórios.'}), 400

    mensagem = registrar_cliente(numero_cliente, senha)
    if "sucesso" in mensagem.lower():
        return jsonify({'success': True, 'message': mensagem}), 201
    else:
        return jsonify({'success': False, 'message': mensagem}), 400

@app.route('/login', methods=['OPTIONS'])
def handle_login_options():
    """Handles OPTIONS requests for /login."""
    response = jsonify()
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    return response

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    numero_cliente = data.get('numero_cliente')
    senha = data.get('senha')

    print(f"Recebida tentativa de login para: {numero_cliente}")
    print(f"Senha fornecida: {senha}")

    if not numero_cliente or not senha:
        print("Erro: Número de telefone e senha são obrigatórios.")
        return jsonify({'success': False, 'message': 'Número de telefone e senha são obrigatórios.'}), 400

    if autenticar_cliente(numero_cliente, senha):
        print(f"Login bem-sucedido para: {numero_cliente}")
        return jsonify({'success': True, 'message': 'Login realizado com sucesso!'}), 200
    else:
        print(f"Falha no login para: {numero_cliente}")
        return jsonify({'success': False, 'message': 'Credenciais inválidas.'}), 401

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('mensagem', '').strip()
    numero_cliente_logado = data.get('numero_cliente')
    esperando = data.get('esperando')
    item_sugerido = data.get('item_sugerido')
    pedidos_atuais = data.get('pedidos_atuais')

    if not numero_cliente_logado:
        return jsonify({'resposta': 'Você precisa estar logado para usar o chatbot para pedidos.', 'error': True}), 401

    try:
        if esperando == 'pedido':
            itemSugerido, exato = VerificarItensCardapio(user_input)

            if not itemSugerido:
                return jsonify({
                    'resposta': "Desculpa, não trabalhamos com esse item. Por favor, peça algo presente em nosso cardápio.",
                    'esperando': 'pedido'
                })

            if not exato:
                return jsonify({
                    'resposta': f"Você quis dizer '{itemSugerido}'? (sim/não)",
                    'esperando': 'confirmacao',
                    'item_sugerido': itemSugerido,
                    'pedido': user_input
                })

            resultado_pedido = PedidosArmazenados(numero_cliente_logado, user_input)
            return jsonify({
                'resposta': f"{resultado_pedido}"
            })

        elif esperando == 'confirmacao':
            if user_input.lower() in ['sim', 's']:
                resultado_confirmacao = PedidosArmazenados(numero_cliente_logado, item_sugerido)
                return jsonify({
                    'resposta': f"{resultado_confirmacao}"
                })
            else:
                return jsonify({
                    'resposta': "Entendido. Por favor, especifique novamente o pedido.",
                    'esperando': 'pedido'
                })

        elif esperando == 'pedido_remocao':
            pedido_remover = user_input.strip()
            resultado_remocao = removerPedidos(numero_cliente_logado, pedido_remover)
            return jsonify({
                'resposta': resultado_remocao
            })

        else:
            response = model.generate_content([{"role": "user", "parts": [prompt_completo + user_input]}])
            bot_reply = response.text.strip()
            intencao = extrair_intencao(bot_reply)

            if not intencao:
                return jsonify({'resposta': bot_reply})

            if intencao == "FAZER_PEDIDO":
                resposta_pedido = "Certo! Qual será seu pedido?"
                return jsonify({
                    'resposta': resposta_pedido,
                    'esperando': 'pedido'
                })

            elif intencao == "CONSULTAR_PEDIDO":
                resultado = BuscarPedidos(numero_cliente_logado)
                return jsonify({
                    'resposta': resultado
                })

            elif intencao == "REMOVER_PEDIDO":
                pedidos_atuais_texto = BuscarPedidos(numero_cliente_logado)
                if "nenhum pedido" in pedidos_atuais_texto.lower():
                    return jsonify({
                        'resposta': "Não encontramos pedidos ativos para este número."
                    })
                return jsonify({
                    'resposta': f"Aqui estão seus pedidos atuais:\n{pedidos_atuais_texto}\n\nPor favor, digite o NOME EXATO do pedido que deseja remover:",
                    'esperando': 'pedido_remocao',
                    'pedidos_atuais': pedidos_atuais_texto
                })
            elif intencao == "VER_CARDAPIO":
                cardapio_texto = """Olá! 😊

Peixes
- Filé de Salmão Grelhado - Acompanha arroz e legumes salteados - 35.90
- Bacalhau à Brás - Bacalhau desfiado com batata palha e ovos - 42.50
- Tilápia Empanada - Servida com purê de batata e salada verde - 28.90

Frango
- Frango à Parmegiana - Frango empanado com molho de tomate e queijo, acompanhado de arroz e batata frita - 24.90
- Peito de Frango Grelhado - Acompanha arroz integral e salada mista - 22.50
- Strogonoff de Frango - Servido com arroz branco e batata palha - 26.00

Carnes
- Picanha na Chapa - Acompanha arroz, feijão tropeiro e vinagrete - 58.90
- Filé Mignon ao Molho Madeira - Servido com arroz e batata gratinada - 55.00
- Costela Assada - Acompanha mandioca cozida e salada - 49.90

Massas
- Lasanha Bolonhesa - Camadas de massa, molho de carne e queijo - 32.90
- Fettuccine Alfredo - Massa com molho cremoso de queijo parmesão - 30.50
- Nhoque ao Sugo - Massa de batata com molho de tomate fresco - 27.00

Vegano
- Risoto de Cogumelos - Arroz cremoso com mix de cogumelos - 34.00
- Hambúrguer de Grão-de-Bico - Servido com batatas rústicas - 18.90
- Espaguete de Abobrinha - Com molho ao sugo e manjericão - 20.90

Porções
- Batata Frita - Porção generosa de batata frita crocante - 10.90
- Isca de Peixe - Peixe empanado com molho tártaro - 15.50
- Bolinho de Aipim - Recheado com carne seca - 12.50

Sobremesas
- Pudim de Leite - Tradicional e cremoso - 8.90
- Torta de Limão - Massa crocante com recheio azedinho - 10.00
- Brownie com Sorvete - Brownie de chocolate servido com sorvete de creme - 15.90

Saladas
- Caesar - Alface, croutons, parmesão e molho caesar - 14.90
- Salada Tropical - Mix de folhas, frutas da época e molho de iogurte - 18.00
- Salada Caprese - Tomate, muçarela de búfala, manjericão e azeite - 19.00

Qual categoria te interessa mais hoje? 😋"""
                return jsonify({'resposta': cardapio_texto})

            return jsonify({'resposta': bot_reply})

    except Exception as e:
        print(f"Erro na API: {str(e)}")
        return jsonify({
            'resposta': "Desculpe, ocorreu um erro. Por favor, tente novamente.",
            'error': True
        })

@app.route('/teste', methods=['GET'])
def teste_conexao():
    return jsonify({'message': 'Servidor Flask rodando!'}), 200

if __name__ == '__main__':
    try:
        CreateDatabase()
    except Exception as e:
        print(f"Erro ao criar banco de dados: {str(e)}")

    app.run(host='0.0.0.0', port=5000, debug=True)