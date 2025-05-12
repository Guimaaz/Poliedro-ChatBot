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
    VerificarItensCardapio
)
import re
import os
from dotenv import load_dotenv
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Configuração inicial
load_dotenv(dotenv_path=Path('.') / '.env')
genai.configure(api_key=os.getenv("API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# Dicionário para manter o contexto das conversas
conversation_context = {}

def extrair_intencao(texto):
    match = re.search(r'INTENÇÃO:\s*(FAZER_PEDIDO|CONSULTAR_PEDIDO|REMOVER_PEDIDO)', texto, re.IGNORECASE)
    return match.group(1).upper() if match else None

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('mensagem', '').strip()
    session_id = data.get('session_id', 'default')
    
    # Inicializa contexto se não existir
    if session_id not in conversation_context:
        conversation_context[session_id] = {
            'step': None,
            'numero_cliente': None,
            'pedido': None,
            'item_sugerido': None
        }
    
    ctx = conversation_context[session_id]

    try:
        # Se não estiver em um passo intermediário, analise a intenção
        if not ctx['step']:
            response = model.generate_content([{"role": "user", "parts": [prompt_completo + user_input]}])
            bot_reply = response.text.strip()
            intencao = extrair_intencao(bot_reply)
            
            if not intencao:
                return jsonify({'resposta': bot_reply, 'session_id': session_id})
            
            if intencao == "FAZER_PEDIDO":
                ctx['step'] = 'solicitar_numero'
                return jsonify({
                    'resposta': "Popoli: Certo! Vamos fazer seu pedido. Por favor, informe seu número de telefone (formato (XX) XXXXX-XXXX).",
                    'requer_numero': True,
                    'session_id': session_id
                })
            # ... (outros fluxos mantidos)

        # Processamento dos passos do pedido
        if ctx['step'] == 'solicitar_numero':
            if not validar_numero(user_input):
                return jsonify({
                    'resposta': "Popoli: Número inválido! Por favor, use o formato (XX) XXXXX-XXXX.",
                    'requer_numero': True,
                    'session_id': session_id
                })
            
            ctx['numero_cliente'] = user_input
            ctx['step'] = 'solicitar_pedido'
            return jsonify({
                'resposta': "Popoli: Qual será seu pedido?",
                'requer_pedido': True,
                'session_id': session_id
            })
            
        elif ctx['step'] == 'solicitar_pedido':
            # Verificação robusta do item do cardápio
            itemSugerido, exato = VerificarItensCardapio(user_input)
            
            if not itemSugerido:
                ctx['step'] = None
                return jsonify({
                    'resposta': "Popoli: Desculpa, não trabalhamos com esse item. Por favor, peça algo presente em nosso cardápio.",
                    'session_id': session_id
                })
            
            if not exato:
                ctx['item_sugerido'] = itemSugerido
                ctx['pedido'] = user_input
                ctx['step'] = 'confirmar_item'
                return jsonify({
                    'resposta': f"Popoli: Você quis dizer '{itemSugerido}'? (sim/não)",
                    'requer_confirmacao': True,
                    'session_id': session_id
                })
            
            # Se o item for reconhecido corretamente
            try:
                pedido_id = PedidosArmazenados(ctx['numero_cliente'], user_input)
                ctx['step'] = None
                return jsonify({
                    'resposta': f"Popoli: Pedido confirmado! N° {pedido_id}: {user_input}. Obrigado!",
                    'pedido_id': pedido_id,
                    'session_id': session_id
                })
            except Exception as e:
                print(f"Erro ao registrar pedido: {str(e)}")
                ctx['step'] = None
                return jsonify({
                    'resposta': "Popoli: Ocorreu um erro ao registrar seu pedido. Por favor, tente novamente.",
                    'session_id': session_id
                })
                
        elif ctx['step'] == 'confirmar_item':
            if user_input.lower() == 'sim':
                try:
                    pedido_id = PedidosArmazenados(ctx['numero_cliente'], ctx['item_sugerido'])
                    ctx['step'] = None
                    return jsonify({
                        'resposta': f"Popoli: Pedido confirmado! N° {pedido_id}: {ctx['item_sugerido']}. Obrigado!",
                        'pedido_id': pedido_id,
                        'session_id': session_id
                    })
                except Exception as e:
                    print(f"Erro ao registrar pedido: {str(e)}")
                    ctx['step'] = None
                    return jsonify({
                        'resposta': "Popoli: Ocorreu um erro ao registrar seu pedido. Por favor, tente novamente.",
                        'session_id': session_id
                    })
            else:
                ctx['step'] = 'solicitar_pedido'
                return jsonify({
                    'resposta': "Popoli: Entendido. Por favor, especifique novamente o pedido.",
                    'requer_pedido': True,
                    'session_id': session_id
                })

    except Exception as e:
        print(f"Erro na API: {str(e)}")
        ctx['step'] = None
        return jsonify({
            'resposta': "Popoli: Desculpe, ocorreu um erro. Vamos começar novamente.",
            'session_id': session_id
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)