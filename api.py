from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import re
import os
import sqlite3
from dotenv import load_dotenv
from pathlib import Path
from server.prompts import prompt_completo
from server.BancoPedidos import (
    CreateDatabase,
    PedidosArmazenados,
    BuscarPedidos,
    finalizar_pedidos_cliente,
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
import uuid

app = Flask(__name__)
CORS(app)

load_dotenv(dotenv_path=Path('.') / '.env')
genai.configure(api_key=os.getenv("API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

CreateDatabase()

conversa_estado = {}

def extrair_intencao(texto):
    match_pedido = re.search(r'INTENÇÃO:\s*(FAZER_PEDIDO|CONSULTAR_PEDIDO|REMOVER_PEDIDO|VER_CARDAPIO|OUTRA)', texto, re.IGNORECASE)
    if match_pedido:
        return match_pedido.group(1).upper()
    return None

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
        conversa_estado[id_conversa] = {'esperando': None, 'itens_pedido': [], 'valor_total': 0.0, 'item_sugerido': None, 'descricao_sugerida': None, 'preco_sugerido': 0.0, 'pedidos_atuais': None, 'pedido_sessao_id': None}

    estado_conversa = conversa_estado[id_conversa]
    esperando = estado_conversa['esperando']
    itens_pedido = estado_conversa['itens_pedido']
    valor_total = estado_conversa['valor_total']
    item_sugerido = estado_conversa['item_sugerido']
    descricao_sugerida = estado_conversa['descricao_sugerida']
    preco_sugerido = estado_conversa['preco_sugerido']
    pedidos_atuais = estado_conversa['pedidos_atuais']
    pedido_sessao_id_atual = estado_conversa.get('pedido_sessao_id')

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

            estado_conversa['itens_pedido'].append({'nome': itemSugerido_verificado, 'preco': preco_item})
            estado_conversa['valor_total'] += preco_item
            estado_conversa['esperando'] = 'adicionar_mais'
            return jsonify({
                'resposta': f"'{itemSugerido_verificado}' (R${preco_item:.2f}) adicionado ao pedido. Deseja adicionar mais alguma coisa? (sim/não)",
                'esperando': 'adicionar_mais',
                'id_conversa': id_conversa
            })

        elif esperando == 'confirmacao_pedido':
            if user_input.lower() in ['sim', 's']:
                estado_conversa['itens_pedido'].append({'nome': item_sugerido, 'preco': preco_sugerido})
                estado_conversa['valor_total'] += preco_sugerido
                estado_conversa['esperando'] = 'adicionar_mais' # Agora espera por mais itens
                estado_conversa['item_sugerido'] = None
                estado_conversa['descricao_sugerida'] = None
                estado_conversa['preco_sugerido'] = None
                return jsonify({
                    'resposta': f"'{item_sugerido}' (R${preco_sugerido:.2f}) adicionado ao pedido. Deseja adicionar mais alguma coisa? (sim/não)",
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
            elif user_input.lower() in ['não', 'nao', 'finalizar', 'confirmar', 'ok']:
                estado_conversa['esperando'] = 'confirmar_finalizar'
                itens_listados = "\n- ".join([item['nome'] for item in estado_conversa['itens_pedido']])
                return jsonify({
                    'resposta': f"Seu pedido atual é:\n- {itens_listados}\n\nValor total: R${estado_conversa['valor_total']:.2f}\n\nDeseja confirmar o pedido? (sim/não)",
                    'esperando': 'confirmar_finalizar',
                    'itens_pedido': estado_conversa['itens_pedido'],
                    'valor_total': estado_conversa['valor_total'],
                    'id_conversa': id_conversa
                })
            elif "remover" in user_input.lower() or "tirar" in user_input.lower() or "excluir" in user_input.lower():
                estado_conversa['esperando'] = 'remover_item'
                return jsonify({
                    'resposta': "Qual item você gostaria de remover?",
                    'esperando': 'remover_item',
                    'itens_pedido': [item['nome'] for item in estado_conversa['itens_pedido']],
                    'id_conversa': id_conversa
                })
            else:
                return jsonify({
                    'resposta': "Não entendi sua resposta. Por favor, diga 'sim' para adicionar mais ou 'não' para finalizar.",
                    'esperando': 'adicionar_mais',
                    'id_conversa': id_conversa
                })

        elif esperando == 'confirmar_finalizar':
            if user_input.lower() in ['sim', 's', 'confirmar', 'finalizar', 'ok']:
                PedidosArmazenados(numero_cliente_logado, estado_conversa['itens_pedido'], estado_conversa['valor_total'], estado_conversa['pedido_sessao_id'])
                estado_conversa['esperando'] = None
                estado_conversa['itens_pedido'] = []
                estado_conversa['valor_total'] = 0.0
                estado_conversa['pedido_sessao_id'] = None
                return jsonify({
                    'resposta': "Pedido finalizado com sucesso! Obrigado!",
                    'id_conversa': id_conversa
                })
            elif user_input.lower() in ['não', 'nao', 'cancelar']:
                estado_conversa['esperando'] = 'opcoes_pos_confirmacao'
                return jsonify({
                    'resposta': "Pedido não confirmado. Deseja adicionar mais itens, remover algum item ou finalizar o pedido?",
                    'esperando': 'opcoes_pos_confirmacao',
                    'id_conversa': id_conversa
                })
            elif "remover" in user_input.lower() or "tirar" in user_input.lower() or "excluir" in user_input.lower():
                estado_conversa['esperando'] = 'remover_item'
                return jsonify({
                    'resposta': "Qual item você gostaria de remover?",
                    'esperando': 'remover_item',
                    'itens_pedido': [item['nome'] for item in estado_conversa['itens_pedido']],
                    'id_conversa': id_conversa
                })
            elif "adicionar" in user_input.lower() or "mais" in user_input.lower() or "outro" in user_input.lower() or "pedir" in user_input.lower():
                estado_conversa['esperando'] = 'pedido'
                return jsonify({
                    'resposta': "Certo, o que mais gostaria de adicionar?",
                    'esperando': 'pedido',
                    'id_conversa': id_conversa
                })
            else:
                return jsonify({
                    'resposta': "Não entendi sua resposta. Por favor, diga 'sim' para confirmar ou 'não' para fazer alterações.",
                    'esperando': 'confirmar_finalizar',
                    'id_conversa': id_conversa
                })

        elif esperando == 'opcoes_pos_confirmacao':
            if "remover" in user_input.lower() or "tirar" in user_input.lower() or "excluir" in user_input.lower():
                estado_conversa['esperando'] = 'remover_item'
                return jsonify({
                    'resposta': "Qual item você gostaria de remover?",
                    'esperando': 'remover_item',
                    'itens_pedido': [item['nome'] for item in estado_conversa['itens_pedido']],
                    'id_conversa': id_conversa
                })
            elif "adicionar" in user_input.lower() or "mais" in user_input.lower() or "outro" in user_input.lower() or "pedir" in user_input.lower():
                estado_conversa['esperando'] = 'pedido'
                return jsonify({
                    'resposta': "Certo, o que mais gostaria de adicionar?",
                    'esperando': 'pedido',
                    'id_conversa': id_conversa
                })
            elif user_input.lower() in ['finalizar', 'confirmar', 'ok']:
                estado_conversa['esperando'] = 'confirmar_finalizar'
                itens_listados = "\n- ".join([item['nome'] for item in estado_conversa['itens_pedido']])
                return jsonify({
                    'resposta': f"Seu pedido atual é:\n- {itens_listados}\n\nValor total: R${estado_conversa['valor_total']:.2f}\n\nDeseja confirmar o pedido agora? (sim/não)",
                    'esperando': 'confirmar_finalizar',
                    'itens_pedido': estado_conversa['itens_pedido'],
                    'valor_total': estado_conversa['valor_total'],
                    'id_conversa': id_conversa
                })
            else:
                return jsonify({
                    'resposta': "Não entendi sua solicitação. Por favor, diga se quer 'adicionar', 'remover' ou 'finalizar'.",
                    'esperando': 'opcoes_pos_confirmacao',
                    'id_conversa': id_conversa
                })

        elif esperando == 'remover_item':
            item_para_remover = user_input.strip().lower()
            removido = False
            indice_para_remover = -1
            for i in range(len(estado_conversa['itens_pedido'])):
                if estado_conversa['itens_pedido'][i]['nome'].lower() == item_para_remover:
                    removido = True
                    indice_para_remover = i
                    break
            if removido:
                item_removido = estado_conversa['itens_pedido'].pop(indice_para_remover)
                estado_conversa['valor_total'] -= item_removido['preco']
                itens_listados = "\n- ".join([item['nome'] for item in estado_conversa['itens_pedido']])
                estado_conversa['esperando'] = 'confirmar_finalizar' # Após remover, volta para a confirmação
                return jsonify({
                    'resposta': f"'{item_para_remover}' removido do pedido. Seu pedido atual é:\n- {itens_listados}\n\nValor total: R${estado_conversa['valor_total']:.2f}\n\nDeseja confirmar o pedido? (sim/não)",
                    'esperando': 'confirmar_finalizar',
                    'id_conversa': id_conversa
                })
            else:
                estado_conversa['esperando'] = 'confirmar_finalizar' # Se não encontrar, volta para a confirmação
                return jsonify({
                    'resposta': f"'{item_para_remover}' não encontrado no seu pedido atual. Deseja confirmar o pedido? (sim/não)",
                    'esperando': 'confirmar_finalizar',
                    'itens_pedido': [item['nome'] for item in estado_conversa['itens_pedido']],
                    'id_conversa': id_conversa
                })

        elif esperando == 'pedido_remocao': # Mantive essa parte para remover pedidos antigos (histórico)
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
                estado_conversa['itens_pedido'] = []
                estado_conversa['valor_total'] = 0.0
                estado_conversa['pedido_sessao_id'] = str(uuid.uuid4()) # Gera um novo ID de sessão
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
            elif intencao == "REMOVER_PEDIDO": # Intenção antiga para remover pedidos históricos
                pedidos_atuais_texto = BuscarPedidos(numero_cliente_logado)
                estado_conversa['esperando'] = 'pedido_remocao'
                estado_conversa['pedidos_atuais'] = pedidos_atuais_texto
                if "nenhum pedido" in pedidos_atuais_texto.lower():
                    return jsonify({ 'resposta': "Não encontramos pedidos ativos para este número.",
                        'id_conversa': id_conversa
                    })
                return jsonify({
                    'resposta': f"Aqui estão seus pedidos atuais:\n{pedidos_atuais_texto}\n\nPor favor, digite o ID do pedido que deseja remover:",
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

@app.route('/admin/pedidos')
def admin_listar_pedidos():
    pedidos_data = buscar_pedidos_admin()
    print(f"Tipo de pedidos_data: {type(pedidos_data)}")
    print(f"Conteúdo de pedidos_data: {(pedidos_data)}")
    nao_finalizados = pedidos_data.get('nao_finalizados', [])
    finalizados = pedidos_data.get('finalizados', [])
    return jsonify({"nao_finalizados": nao_finalizados, "finalizados": finalizados})


@app.route('/admin/pedidos/cliente/<numero_cliente>/finalizar', methods=['POST'])
def finalizar_pedidos_cliente_route(numero_cliente):
    resultado = finalizar_pedidos_cliente(numero_cliente) # Chama a função do banco
    return jsonify(resultado), 200

@app.route('/admin/pedidos/<pedido_id>/finalizar', methods=['POST'])
def admin_finalizar_pedido(pedido_id):
    mensagem = finalizar_pedido_admin(pedido_id)
    return jsonify({'message': mensagem})

@app.route('/admin/pedidos/<pedido_id>/reabrir', methods=['POST'])
def admin_reabrir_pedido(pedido_id):
    mensagem = reabrir_pedido_admin(pedido_id)
    return jsonify({'message': mensagem})

@app.route('/admin/cardapio', methods=['GET'])
def admin_listar_cardapio():
    cardapio = buscar_cardapio_admin()
    return jsonify(cardapio)

@app.route('/admin/cardapio', methods=['POST'])
def admin_adicionar_cardapio_item():
    data = request.json
    pedido = data.get('pedido')
    preco = data.get('preco')
    descricao = data.get('descricao', '')
    categoria = data.get('categoria', 'Outros')

    if not pedido or preco is None:
        return jsonify({'error': 'Nome do pedido e preço são obrigatórios.'}), 400

    conexao = sqlite3.connect("chatbot.db") # Usando diretamente o nome do banco aqui
    cursor = conexao.cursor()
    try:
        cursor.execute("INSERT INTO cardapios (pedido, preco, categoria, descricao) VALUES (?, ?, ?, ?)", (pedido, preco, categoria, descricao))
        conexao.commit()
        item_id = cursor.lastrowid
        conexao.close()
        return jsonify({'message': f"Item '{pedido}' adicionado ao cardápio com ID {item_id}.", 'id': item_id}), 201
    except sqlite3.IntegrityError:
        conexao.close()
        return jsonify({'error': f"Já existe um item com o nome '{pedido}' no cardápio."}), 409
    except sqlite3.Error as e:
        conexao.close()
        return jsonify({'error': f"Erro ao adicionar item ao cardápio: {str(e)}"}), 500

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