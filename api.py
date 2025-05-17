from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import re
import os
from dotenv import load_dotenv
from pathlib import Path
from server.prompts import prompt_completo
from server.BancoPedidos import (
    CreateDatabase,
    PedidosArmazenados,
    BuscarPedidos,
    removerPedidos,
    VerificarItensCardapio,
    registrar_cliente,
    autenticar_cliente,
    buscar_pedidos_admin,
    finalizar_pedido_admin,
    reabrir_pedido_admin,
    buscar_cardapio_admin,
    atualizar_cardapio_admin,
    deletar_cardapio_admin,
    buscar_clientes_admin,
    buscar_cardapio_completo
)

app = Flask(__name__)
CORS(app)

load_dotenv(dotenv_path=Path('.') / '.env')
genai.configure(api_key=os.getenv("API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

CreateDatabase()


conversa_estado = {}

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

    senha_correta, is_admin = autenticar_cliente(numero_cliente, senha)
    if senha_correta:
        print(f"Login bem-sucedido para: {numero_cliente}, isAdmin: {is_admin}")
        return jsonify({'success': True, 'message': 'Login realizado com sucesso!', 'numero_cliente': numero_cliente, 'is_admin': is_admin}), 200
    else:
        print(f"Falha no login para: {numero_cliente}")
        return jsonify({'success': False, 'message': 'Credenciais inválidas.'}), 401

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('mensagem', '').strip()
    numero_cliente_logado = data.get('numero_cliente')
    id_conversa = data.get('id_conversa', 'default')

    if not numero_cliente_logado:
        return jsonify({'resposta': 'Você precisa estar logado para usar o chatbot para pedidos.', 'error': True, 'id_conversa': id_conversa}), 401

    # Inicializa o estado da conversa se não existir
    if id_conversa not in conversa_estado:
        conversa_estado[id_conversa] = {'esperando': None, 'itens_pedido': [], 'item_sugerido': None, 'descricao_sugerida': None, 'pedidos_atuais': None}

    estado_conversa = conversa_estado[id_conversa]
    esperando = estado_conversa['esperando']
    itens_pedido = estado_conversa['itens_pedido']
    item_sugerido = estado_conversa['item_sugerido']
    descricao_sugerida = estado_conversa['descricao_sugerida']
    pedidos_atuais = estado_conversa['pedidos_atuais']

    try:
        if esperando == 'pedido':
            itemSugerido_verificado, exato, descricao_item, preco_item = VerificarItensCardapio(user_input)

            if not itemSugerido_verificado:
                return jsonify({
                    'resposta': "Não entendi o que você gostaria de pedir. Por favor, diga o nome exato do item.",
                    'esperando': 'pedido',
                    'id_conversa': id_conversa
                })

            if not exato:
                estado_conversa['esperando'] = 'confirmacao_pedido'
                estado_conversa['item_sugerido'] = itemSugerido_verificado
                estado_conversa['descricao_sugerida'] = descricao_item
                estado_conversa['preco_sugerido'] = preco_item
                return jsonify({
                    'resposta': f"Você quis dizer '{itemSugerido_verificado}'? ({descricao_item} - R${preco_item:.2f}) (sim/não)",
                    'esperando': 'confirmacao_pedido',
                    'item_sugerido': itemSugerido_verificado,
                    'descricao_sugerida': descricao_item,
                    'preco_sugerido': preco_item,
                    'id_conversa': id_conversa
                })

            estado_conversa['itens_pedido'].append(itemSugerido_verificado)
            estado_conversa['esperando'] = 'adicionar_mais'
            return jsonify({
                'resposta': f"'{itemSugerido_verificado}' adicionado ao pedido. Deseja adicionar mais alguma coisa? (sim/não)",
                'esperando': 'adicionar_mais',
                'id_conversa': id_conversa
            })

        elif esperando == 'confirmacao_pedido':
            if user_input.lower() in ['sim', 's']:
                estado_conversa['itens_pedido'].append(item_sugerido)
                estado_conversa['esperando'] = 'adicionar_mais'
                estado_conversa['item_sugerido'] = None
                estado_conversa['descricao_sugerida'] = None
                estado_conversa['preco_sugerido'] = None
                return jsonify({
                    'resposta': f"'{item_sugerido}' adicionado ao pedido. Deseja adicionar mais alguma coisa? (sim/não)",
                    'esperando': 'adicionar_mais',
                    'id_conversa': id_conversa
                })
            else:
                estado_conversa['esperando'] = 'pedido'
                estado_conversa['item_sugerido'] = None
                estado_conversa['descricao_sugerida'] = None
                estado_conversa['preco_sugerido'] = None
                return jsonify({
                    'resposta': "Entendido. Por favor, diga novamente o que gostaria de pedir.",
                    'esperando': 'pedido',
                    'id_conversa': id_conversa
                })

        elif esperando == 'adicionar_mais':
            if user_input.lower() in ['sim', 's']:
                estado_conversa['esperando'] = 'pedido'
                return jsonify({
                    'resposta': "Certo, o que mais gostaria de adicionar?",
                    'esperando': 'pedido',
                    'id_conversa': id_conversa
                })
            else:
                estado_conversa['esperando'] = 'confirmar_finalizar'
                itens_listados = "\n- ".join(itens_pedido)
                return jsonify({
                    'resposta': f"Seu pedido atual é:\n- {itens_listados}\n\nConfirma o pedido? (sim/não)",
                    'esperando': 'confirmar_finalizar',
                    'itens_pedido': itens_pedido,
                    'id_conversa': id_conversa
                })

        elif esperando == 'confirmar_finalizar':
            if user_input.lower() in ['sim', 's']:
                for item in itens_pedido:
                    PedidosArmazenados(numero_cliente_logado, item)
                estado_conversa['esperando'] = None
                estado_conversa['itens_pedido'] = []
                return jsonify({
                    'resposta': "Pedido finalizado com sucesso! Obrigado!",
                    'id_conversa': id_conversa
                })
            else:
                estado_conversa['esperando'] = None
                estado_conversa['itens_pedido'] = []
                return jsonify({
                    'resposta': "Pedido cancelado. Se quiser fazer um novo pedido, diga 'quero fazer um pedido'.",
                    'id_conversa': id_conversa
                })

        elif esperando == 'pedido_remocao':
            pedido_remover = user_input.strip()
            resultado_remocao = removerPedidos(numero_cliente_logado, pedido_remover)
            estado_conversa['esperando'] = None
            return jsonify({
                'resposta': resultado_remocao,
                'id_conversa': id_conversa
            })

        else:
            response = model.generate_content([{"role": "user", "parts": [prompt_completo + user_input]}])
            bot_reply = response.text.strip()
            intencao = extrair_intencao(bot_reply)

            if not intencao:
                return jsonify({'resposta': bot_reply, 'id_conversa': id_conversa})

            if intencao == "FAZER_PEDIDO":
                estado_conversa['esperando'] = 'pedido'
                estado_conversa['itens_pedido'] = [] # Inicializa a lista de itens do pedido
                return jsonify({
                    'resposta': "Certo! Qual será seu primeiro item?",
                    'esperando': 'pedido',
                    'id_conversa': id_conversa
                })

            elif intencao == "CONSULTAR_PEDIDO":
                resultado = BuscarPedidos(numero_cliente_logado)
                estado_conversa['esperando'] = None
                return jsonify({
                    'resposta': resultado,
                    'id_conversa': id_conversa
                })

            elif intencao == "REMOVER_PEDIDO":
                pedidos_atuais_texto = BuscarPedidos(numero_cliente_logado)
                estado_conversa['esperando'] = 'pedido_remocao'
                estado_conversa['pedidos_atuais'] = pedidos_atuais_texto
                if "nenhum pedido" in pedidos_atuais_texto.lower():
                    return jsonify({ 'resposta': "Não encontramos pedidos ativos para este número.",
                        'id_conversa': id_conversa
                    })
                return jsonify({
                    'resposta': f"Aqui estão seus pedidos atuais:\n{pedidos_atuais_texto}\n\nPor favor, digite o NOME EXATO do pedido que deseja remover:",
                    'esperando': 'pedido_remocao',
                    'pedidos_atuais': pedidos_atuais_texto,
                    'id_conversa': id_conversa
                })
            elif intencao == "VER_CARDAPIO":
                cardapio_db = buscar_cardapio_completo()
                if cardapio_db:
                    cardapio_texto = "Cardápio do Restaurante\n"
                    for categoria, itens in cardapio_db.items():
                        cardapio_texto += f"\n*{categoria}*\n"
                        for item in itens:
                            cardapio_texto += f"- {item['pedido']} - R${item['preco']:.2f}"
                            if item['descricao']:
                                cardapio_texto += f" - {item['descricao']}"
                            cardapio_texto += "\n"
                    return jsonify({'resposta': cardapio_texto.strip(), 'id_conversa': id_conversa})
                else:
                    return jsonify({'resposta': "O cardápio está vazio no momento.", 'id_conversa': id_conversa})

            return jsonify({'resposta': bot_reply, 'id_conversa': id_conversa})

    except Exception as e:
        print(f"Erro no chat: {e}")
        return jsonify({'resposta': "Ocorreu um erro inesperado.", 'error': True, 'id_conversa': id_conversa}), 500

# Rotas para o painel de administração
@app.route('/admin/pedidos', methods=['GET'])
def admin_listar_pedidos():
    pedidos = buscar_pedidos_admin()
    nao_finalizados = [p for p in pedidos if not p['finalizado']]
    finalizados = [p for p in pedidos if p['finalizado']]
    return jsonify({'nao_finalizados': nao_finalizados, 'finalizados': finalizados})

@app.route('/admin/pedidos/<int:pedido_id>/finalizar', methods=['POST'])
def admin_finalizar_pedido(pedido_id):
    mensagem = finalizar_pedido_admin(pedido_id)
    return jsonify({'message': mensagem})

@app.route('/admin/pedidos/<int:pedido_id>/reabrir', methods=['POST'])
def admin_reabrir_pedido(pedido_id):
    mensagem = reabrir_pedido_admin(pedido_id)
    return jsonify({'message': mensagem})

@app.route('/admin/cardapio', methods=['GET'])
def admin_listar_cardapio():
    cardapio = buscar_cardapio_admin()
    return jsonify(cardapio)

@app.route('/admin/cardapio/<int:item_id>', methods=['PUT'])
def admin_atualizar_cardapio(item_id):
    data = request.json
    pedido = data.get('pedido')
    preco = data.get('preco')
    descricao = data.get('descricao', '')
    categoria = data.get('categoria', 'Outros')
    if pedido is None or preco is None:
        return jsonify({'error': 'Pedido e preço são obrigatórios'}), 400
    mensagem = atualizar_cardapio_admin(item_id, pedido, preco, descricao, categoria)
    return jsonify({'message': mensagem})

@app.route('/admin/cardapio/<int:item_id>', methods=['DELETE'])
def admin_deletar_cardapio(item_id):
    mensagem = deletar_cardapio_admin(item_id)
    return jsonify({'message': mensagem})

@app.route('/admin/clientes', methods=['GET'])
def admin_listar_clientes():
    clientes = buscar_clientes_admin()
    return jsonify(clientes)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)