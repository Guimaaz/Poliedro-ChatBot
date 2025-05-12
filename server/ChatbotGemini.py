from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from server.prompts import prompt_completo
from server.BancoPedidos import (
    VerificarItensCardapio,
    PedidosArmazenados,
    BuscarPedidos,
    removerPedidos
)
import re
import os
from dotenv import load_dotenv

# Configuração inicial
app = Flask(__name__)
CORS(app, resources={
    r"/chat": {
        "origins": ["*"],  # Em produção, restrinja aos seus domínios
        "methods": ["POST"],
        "allow_headers": ["Content-Type"]
    }
})

# Carregar variáveis de ambiente
load_dotenv()
senha = os.getenv("API_KEY")

# Configuração do Gemini
genai.configure(api_key=senha)
model = genai.GenerativeModel("gemini-1.5-flash")

def extrair_intencao(texto):
    """Extrai a intenção do texto gerado pelo modelo"""
    match = re.search(r'INTENÇÃO:\s*(FAZER_PEDIDO|CONSULTAR_PEDIDO|REMOVER_PEDIDO)', texto, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return None

def validar_numero(numero):
    """Valida o formato do número de telefone"""
    padrao = r'^\(\d{2}\) \d{5}-\d{4}$'
    return re.match(padrao, numero) is not None

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        
        # Campos recebidos do frontend
        user_input = data.get('mensagem', '')
        numero_cliente = data.get('numero_cliente', '')
        pedido = data.get('pedido', '')
        confirmacao = data.get('confirmacao', '')
        item_sugerido = data.get('item_sugerido', '')

        # Geração da resposta pelo modelo Gemini
        response = model.generate_content([
            {"role": "user", "parts": [prompt_completo + user_input]}
        ])
        bot_reply = response.text.strip()
        intencao = extrair_intencao(bot_reply)

        # Se não detectar intenção específica
        if not intencao:
            return jsonify({
                'resposta': bot_reply,
                'contexto': {}  # Reseta o contexto
            })

        # Fluxo: Fazer Pedido
        if intencao == "FAZER_PEDIDO":
            if not numero_cliente:
                return jsonify({
                    'resposta': "Certo! Vamos fazer seu pedido. Por favor, informe seu número de telefone no formato (XX) XXXXX-XXXX.",
                    'contexto': {'esperando': 'numero'},
                    'requer_numero': True
                })
            
            if not validar_numero(numero_cliente):
                return jsonify({
                    'resposta': "Número inválido! Por favor, use o formato (XX) XXXXX-XXXX.",
                    'contexto': {'esperando': 'numero'},
                    'requer_numero': True
                })

            if not pedido:
                return jsonify({
                    'resposta': "Ótimo! Agora, qual será o seu pedido?",
                    'contexto': {'numero_cliente': numero_cliente, 'esperando': 'pedido'},
                    'requer_pedido': True
                })

            itemSugerido, exato = VerificarItensCardapio(pedido)

            if not itemSugerido:
                return jsonify({
                    'resposta': "Desculpe, não encontramos esse item no cardápio. Por favor, escolha outro.",
                    'contexto': {'numero_cliente': numero_cliente, 'esperando': 'pedido'}
                })

            if not exato:
                if not confirmacao:
                    return jsonify({
                        'resposta': f"Você quis dizer '{itemSugerido}'? Responda 'sim' ou 'não'.",
                        'contexto': {
                            'numero_cliente': numero_cliente,
                            'item_sugerido': itemSugerido,
                            'pedido_original': pedido,
                            'esperando': 'confirmacao'
                        },
                        'requer_confirmacao': True
                    })
                elif confirmacao.lower() != 'sim':
                    return jsonify({
                        'resposta': "Entendido. Por favor, especifique novamente o pedido.",
                        'contexto': {'numero_cliente': numero_cliente, 'esperando': 'pedido'}
                    })

            # Confirmação OK ou item exato
            pedido_final = itemSugerido if (exato or confirmacao.lower() == 'sim') else pedido
            pedido_id = PedidosArmazenados(numero_cliente, pedido_final)
            
            return jsonify({
                'resposta': f"Pedido confirmado! N° {pedido_id}: {pedido_final}. Obrigado!",
                'pedido_id': pedido_id,
                'contexto': {}  # Reseta o contexto
            })

        # Fluxo: Consultar Pedido
        elif intencao == "CONSULTAR_PEDIDO":
            if not numero_cliente:
                return jsonify({
                    'resposta': "Para consultar seus pedidos, preciso do seu número no formato (XX) XXXXX-XXXX.",
                    'contexto': {'esperando': 'numero_consulta'},
                    'requer_numero': True
                })

            if not validar_numero(numero_cliente):
                return jsonify({
                    'resposta': "Formato inválido! Use (XX) XXXXX-XXXX.",
                    'contexto': {'esperando': 'numero_consulta'},
                    'requer_numero': True
                })

            resultado = BuscarPedidos(numero_cliente)
            return jsonify({
                'resposta': resultado,
                'contexto': {'numero_cliente': numero_cliente}
            })

        # Fluxo: Remover Pedido
        elif intencao == "REMOVER_PEDIDO":
            if not numero_cliente:
                return jsonify({
                    'resposta': "Para remover um pedido, preciso do seu número no formato (XX) XXXXX-XXXX.",
                    'contexto': {'esperando': 'numero_remocao'},
                    'requer_numero': True
                })

            if not validar_numero(numero_cliente):
                return jsonify({
                    'resposta': "Número inválido! Use (XX) XXXXX-XXXX.",
                    'contexto': {'esperando': 'numero_remocao'},
                    'requer_numero': True
                })

            pedidos_atuais = BuscarPedidos(numero_cliente)
            if "nenhum pedido" in pedidos_atuais.lower():
                return jsonify({
                    'resposta': "Você não tem pedidos ativos.",
                    'contexto': {}
                })

            if not pedido:
                return jsonify({
                    'resposta': f"Seus pedidos ativos:\n{pedidos_atuais}\n\nQual você deseja remover?",
                    'contexto': {
                        'numero_cliente': numero_cliente,
                        'pedidos_atuais': pedidos_atuais,
                        'esperando': 'pedido_remocao'
                    },
                    'requer_pedido_remocao': True
                })

            resultado = removerPedidos(numero_cliente, pedido)
            return jsonify({
                'resposta': resultado,
                'contexto': {}
            })

    except Exception as e:
        print(f"Erro na API: {str(e)}")
        return jsonify({
            'resposta': "Desculpe, ocorreu um erro interno. Por favor, tente novamente.",
            'erro': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)