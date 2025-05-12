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
import sqlite3
from dotenv import load_dotenv
from pathlib import Path

app = Flask(__name__)
CORS(app)

 # pega o dotenv que é onde esta a api do gemini
load_dotenv(dotenv_path=Path('.') / '.env')
genai.configure(api_key=os.getenv("API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

#gera o banco, caso ele ainda não exista ( esta local )
CreateDatabase()

#criamos um dicionario para manter o contexto da conversa
conversa_contexto = {}

def extrair_intencao(texto):
    match = re.search(r'INTENÇÃO:\s*(FAZER_PEDIDO|CONSULTAR_PEDIDO|REMOVER_PEDIDO)', texto, re.IGNORECASE)
    return match.group(1).upper() if match else None

#inicio da rota com a api por método post, input do usuário
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_input = data.get('mensagem', '').strip()
    id_conversa = data.get('id_conversa', 'default')
    
# da inicio a uma conversa, caso não tenha uma ainda
    if id_conversa not in conversa_contexto:
        conversa_contexto[id_conversa] = {
            'step': None,
            'numero_cliente': None,
            'pedido': None,
            'item_sugerido': None,
            'pedido_a_remover': None
        }
    
    ctx = conversa_contexto[id_conversa]

    try:
       #  ele verifica o passo atual da conversa, e definimos que stpe inicial é o padrão ( sem intenções, caso ele identifique uma, ele chama o os métodos para tal)
        if not ctx['step']:
            response = model.generate_content([{"role": "user", "parts": [prompt_completo + user_input]}])
            bot_reply = response.text.strip()
            intencao = extrair_intencao(bot_reply)
            
            if not intencao:
                return jsonify({'resposta': bot_reply, 'id_conversa': id_conversa})
            
            if intencao == "FAZER_PEDIDO":
                ctx['step'] = 'solicitar_numero'
                return jsonify({
                    'resposta': " Certo! Vamos fazer seu pedido. Por favor, informe seu número de telefone (formato (XX) XXXXX-XXXX).",
                    'requer_numero': True,
                    'id_conversa': id_conversa
                })
            
            elif intencao == "CONSULTAR_PEDIDO":
                ctx['step'] = 'consultar_numero'
                return jsonify({
                    'resposta': " Claro! Para consultar seu pedido, preciso do seu número de telefone (formato (XX) XXXXX-XXXX).",
                    'requer_numero': True,
                    'id_conversa': id_conversa
                })
            
            elif intencao == "REMOVER_PEDIDO":
                ctx['step'] = 'remover_numero'
                return jsonify({
                    'resposta': " Claro! Para remover seu pedido, preciso do seu número de telefone (formato (XX) XXXXX-XXXX).",
                    'requer_numero': True,
                    'id_conversa': id_conversa
                })

        # parte do numero para pedidos
        if ctx['step'] == 'solicitar_numero':
            if not validar_numero(user_input):
                return jsonify({
                    'resposta': " Número inválido! Por favor, use o formato (XX) XXXXX-XXXX.",
                    'requer_numero': True,
                    'id_conversa': id_conversa
                })
            
            ctx['numero_cliente'] = user_input
            ctx['step'] = 'solicitar_pedido'
            return jsonify({
                'resposta': " Qual será seu pedido?",
                'requer_pedido': True,
                'id_conversa': id_conversa
            })
            
        elif ctx['step'] == 'solicitar_pedido':
            itemSugerido, exato = VerificarItensCardapio(user_input)
            
            if not itemSugerido:
                ctx['step'] = None
                return jsonify({
                    'resposta': " Desculpa, não trabalhamos com esse item. Por favor, peça algo presente em nosso cardápio.",
                    'id_conversa': id_conversa
                })
            
            if not exato:
                ctx['item_sugerido'] = itemSugerido
                ctx['pedido'] = user_input
                ctx['step'] = 'confirmar_item'
                return jsonify({
                    'resposta': f" Você quis dizer '{itemSugerido}'? (sim/não)",
                    'requer_confirmacao': True,
                    'id_conversa': id_conversa
                })
            
            try:
                pedido_id = PedidosArmazenados(ctx['numero_cliente'], user_input)
                ctx['step'] = None
                return jsonify({
                    'resposta': f" Pedido confirmado! N° {pedido_id}: {user_input}. Obrigado!",
                    'pedido_id': pedido_id,
                    'id_conversa': id_conversa
                })
            except Exception as e:
                print(f"Erro ao registrar pedido: {str(e)}")
                ctx['step'] = None
                return jsonify({
                    'resposta': " Ocorreu um erro ao registrar seu pedido. Por favor, tente novamente.",
                    'id_conversa': id_conversa
                })
                
        elif ctx['step'] == 'confirmar_item':
            if user_input.lower() in ['sim', 's']:
                try:
                    pedido_id = PedidosArmazenados(ctx['numero_cliente'], ctx['item_sugerido'])
                    ctx['step'] = None
                    return jsonify({
                        'resposta': f" Pedido confirmado! N° {pedido_id}: {ctx['item_sugerido']}. Obrigado!",
                        'pedido_id': pedido_id,
                        'id_conversa': id_conversa
                    })
                except Exception as e:
                    print(f"Erro ao registrar pedido: {str(e)}")
                    ctx['step'] = None
                    return jsonify({
                        'resposta': " Ocorreu um erro ao registrar seu pedido. Por favor, tente novamente.",
                        'id_conversa': id_conversa
                    })
            else:
                ctx['step'] = 'solicitar_pedido'
                return jsonify({
                    'resposta': " Entendido. Por favor, especifique novamente o pedido.",
                    'requer_pedido': True,
                    'id_conversa': id_conversa
                })
        
        #  parte da consulta dos pedidos
        elif ctx['step'] == 'consultar_numero':
            if not validar_numero(user_input):
                return jsonify({
                    'resposta': " Número inválido! Por favor, use o formato (XX) XXXXX-XXXX.",
                    'requer_numero': True,
                    'id_conversa': id_conversa
                })
            
            resultado = BuscarPedidos(user_input)
            ctx['step'] = None
            return jsonify({
                'resposta': resultado,
                'id_conversa': id_conversa
            })
        
        # parte da remoção de pedidos
        elif ctx['step'] == 'remover_numero':
            if not validar_numero(user_input):
                return jsonify({
                    'resposta': " Número inválido! Por favor, use o formato (XX) XXXXX-XXXX.",
                    'requer_numero': True,
                    'id_conversa': id_conversa
                })
            
            ctx['numero_cliente'] = user_input
            try:
                pedidos_atuais = BuscarPedidos(user_input)
                
                if "nenhum pedido" in pedidos_atuais.lower():
                    ctx['step'] = None
                    return jsonify({
                        'resposta': " Não encontramos pedidos ativos para esse número.",
                        'id_conversa': id_conversa
                    })
                
                ctx['step'] = 'selecionar_pedido_remover'
                return jsonify({
                    'resposta': f" Aqui estão seus pedidos atuais:\n{pedidos_atuais}\n\nPor favor, digite o NOME EXATO do pedido que deseja remover:",
                    'requer_pedido_remover': True,
                    'id_conversa': id_conversa
                })
            except Exception as e:
                print(f"Erro ao buscar pedidos: {str(e)}")
                ctx['step'] = None
                return jsonify({
                    'resposta': " Ocorreu um erro ao consultar seus pedidos. Por favor, tente novamente.",
                    'id_conversa': id_conversa
                })
        
        elif ctx['step'] == 'selecionar_pedido_remover':
            pedido = user_input.strip()
            try:
                pedidos_atuais = BuscarPedidos(ctx['numero_cliente'])
                
                #pega a linha por linha dos pedidos nas tabelas
                linhas = [linha for linha in pedidos_atuais.split('\n') if 'Pedido:' in linha]
                pedidos_lista = []
                for linha in linhas:
                    pedido_nome = linha.split('Pedido:')[1].split('(ID')[0].strip()
                    pedidos_lista.append(pedido_nome.lower())
                
                if pedido.lower() not in pedidos_lista:
                    return jsonify({
                        'resposta': f" Pedido '{pedido}' não encontrado. Por favor, verifique o nome e tente novamente.",
                        'requer_pedido_remover': True,
                        'id_conversa': id_conversa
                    })
                
                resultado = removerPedidos(ctx['numero_cliente'], pedido)
                
                if "sucesso" in resultado.lower() or "removido" in resultado.lower():
                    resposta = f" Pedido '{pedido}' foi removido com sucesso!"
                else:
                    resposta = f" {resultado}"
                
                ctx['step'] = None
                return jsonify({
                    'resposta': resposta,
                    'id_conversa': id_conversa
                })
            except Exception as e:
                print(f"Erro ao remover pedido: {str(e)}")
                ctx['step'] = None
                return jsonify({
                    'resposta': f" Ocorreu um erro ao remover o pedido. Por favor, tente novamente.",
                    'id_conversa': id_conversa
                })

    except Exception as e:
        print(f"Erro na API: {str(e)}")
        ctx['step'] = None
        return jsonify({
            'resposta': " Desculpe, ocorreu um erro. Vamos começar novamente.",
            'id_conversa': id_conversa
        })

if __name__ == '__main__':
    #irá garantir que antes de iniciar, existirá um banco criado
    try:
        CreateDatabase()
    except Exception as e:
        print(f"Erro ao criar banco de dados: {str(e)}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)