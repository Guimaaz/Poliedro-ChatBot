from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import re
import os
import sqlite3
from dotenv import load_dotenv
from pathlib import Path
from server.prompts import prompt_completo # Presumo que prompt_completo é uma string
from server.BancoPedidos import * # Presumo que estas funções estão definidas e funcionam
import uuid
import difflib # Adicionado para sugestões de itens

app = Flask(__name__)
CORS(app)

load_dotenv(dotenv_path=Path('.') / '.env')
genai.configure(api_key=os.getenv("API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

CreateDatabase()

conversa_estado = {}

def extrair_intencao(texto):
    # Ajuste para ser mais flexível no reconhecimento de intenções gerais
    # e para não tentar extrair INTENÇÃO: quando já sabemos a intenção primária
    
    # Intenções de cardápio
    if re.search(r'\b(cardapio|menu|o que tem para comer|comida|bebida)\b', texto, re.IGNORECASE):
        return "VER_CARDAPIO"
    
    # Intenções de fazer pedido (mais genéricas)
    if re.search(r'\b(quero comer|fazer pedido|pedir|gostaria de pedir|fome|pedir um|pedir uma)\b', texto, re.IGNORECASE):
        return "FAZER_PEDIDO_GENERICO" # Nova intenção para o fluxo de "quer ver o cardápio?"

    # Regex original para as intenções específicas do prompt do Gemini
    match_pedido = re.search(r'INTENÇÃO:\s*(FAZER_PEDIDO|CONSULTAR_PEDIDO|REMOVER_PEDIDO|OUTRA)', texto, re.IGNORECASE)
    if match_pedido:
        return match_pedido.group(1).upper()
    return None

def limpar_string_para_comparacao(texto):
    # Remove caracteres especiais (exceto espaços), converte para minúsculas e remove espaços extras
    # Tenta manter a estrutura para comparação de nomes compostos
    return re.sub(r'[^\w\s]', '', texto).strip().lower()


def parse_e_verificar_itens(user_input):
    """
    Tenta extrair múltiplos itens de um único input, verifica contra o cardápio
    e retorna itens encontrados, não encontrados e sugestões.
    """
    itens_brutos_do_input = []
    
    # Pre-processamento: normaliza 'e' e ',' para um divisor único, mas mantém nomes de itens compostos.
    # Esta regex tenta ser inteligente: substitui ' e ' ou ', ' se não estiverem no início ou fim.
    # Ex: "strogonoff de frango e pudim de leite, salada caesar"
    # -> "strogonoff de frango DIVISOR pudim de leite DIVISOR salada caesar"
    processed_input = re.sub(r'\s+e\s+|\s*,\s*', ' DIVISOR ', user_input.lower())
    
    # Remove palavras irrelevantes ANTES de dividir para evitar que "quero" ou "um" apareçam como itens
    palavras_irrelevantes = ["quero", "um", "uma", "me ve", "me vê", "pedir", "gostaria de", "por favor", "adicionar", "adicione", "e", "com", "favor"]
    
    # Cria uma regex para remover palavras inteiras (usando word boundaries \b)
    regex_irrelevantes = r'\b(?:' + '|'.join(map(re.escape, palavras_irrelevantes)) + r')\b'
    
    processed_input = re.sub(regex_irrelevantes, '', processed_input).strip()
    
    # Divide o input processado pelo divisor único
    partes_brutas = [p.strip() for p in processed_input.split(' DIVISOR ') if p.strip()]
    
    for parte in partes_brutas:
        item_strip = limpar_string_para_comparacao(parte)
        if item_strip:
            itens_brutos_do_input.append(item_strip)
            
    itens_adicionados_sucesso = []
    itens_nao_encontrados = []
    itens_sugeridos = [] # Lista de (nome_original, descricao, preco) para sugerir ao usuário

    # Puxa o cardápio completo uma vez para otimização
    cardapio_db_flat = []
    cardapio_completo = buscar_cardapio_completo()
    for categoria_itens in cardapio_completo.values():
        for item in categoria_itens:
            cardapio_db_flat.append({
                'nome_original': item['pedido'],
                'nome_limpo': limpar_string_para_comparacao(item['pedido']),
                'descricao': item['descricao'],
                'preco': item['preco']
            })
    
    nomes_cardapio_para_match = [item['nome_limpo'] for item in cardapio_db_flat]

    for item_user_input_limpo in itens_brutos_do_input:
        encontrado_diretamente = False
        
        # 1. Tenta encontrar correspondência exata no cardápio limpo
        for card_item in cardapio_db_flat:
            if card_item['nome_limpo'] == item_user_input_limpo:
                itens_adicionados_sucesso.append({
                    'nome': card_item['nome_original'],
                    'preco': card_item['preco'],
                    'descricao': card_item['descricao']
                })
                encontrado_diretamente = True
                break
        
        if not encontrado_diretamente:
            # 2. Se não encontrou exato, tenta encontrar sugestão usando difflib
            sugestoes_difflib = difflib.get_close_matches(item_user_input_limpo, nomes_cardapio_para_match, n=1, cutoff=0.7) 
            
            if sugestoes_difflib:
                nome_sugerido_limpo = sugestoes_difflib[0]
                for card_item in cardapio_db_flat:
                    if card_item['nome_limpo'] == nome_sugerido_limpo:
                        # Adiciona à lista de sugestões, sem adicionar ao pedido ainda
                        if not any(s['nome'] == card_item['nome_original'] for s in itens_sugeridos):
                            itens_sugeridos.append({
                                'nome': card_item['nome_original'],
                                'preco': card_item['preco'],
                                'descricao': card_item['descricao']
                            })
                        break
            else:
                # 3. Se não encontrou nem exato, nem sugestão, é um item não encontrado
                itens_nao_encontrados.append(item_user_input_limpo)
                
    return itens_adicionados_sucesso, itens_nao_encontrados, itens_sugeridos

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

    if id_conversa not in conversa_estado:
        conversa_estado[id_conversa] = {
            'esperando': None,
            'itens_pedido': [],
            'valor_total': 0.0,
            'pedidos_atuais': None,
            'pedido_sessao_id': None,
            'ofereceu_cardapio_antes_de_pedir': False # Novo estado para controlar se já oferecemos o cardápio
        }

    estado_conversa = conversa_estado[id_conversa]
    esperando = estado_conversa['esperando']
    itens_pedido = estado_conversa['itens_pedido']
    valor_total = estado_conversa['valor_total']
    pedido_sessao_id_atual = estado_conversa.get('pedido_sessao_id')
    ofereceu_cardapio_antes_de_pedir = estado_conversa['ofereceu_cardapio_antes_de_pedir']

    try:
        # Lógica de estados de "esperando"
        if esperando == 'pedido':
            itens_adicionados_raw, itens_nao_encontrados, itens_sugeridos_raw = parse_e_verificar_itens(user_input)
            
            resposta_partes = []
            
            if itens_adicionados_raw:
                for item_info in itens_adicionados_raw:
                    itens_pedido.append({'nome': item_info['nome'], 'preco': item_info['preco']})
                    valor_total += item_info['preco']
                
                nomes_adicionados = [item['nome'] for item in itens_adicionados_raw]
                resposta_partes.append(f"'{', '.join(nomes_adicionados)}' adicionado(s) ao pedido.")
            
            # Se houver sugestões, exiba-as.
            if itens_sugeridos_raw:
                nomes_sugeridos = [item['nome'] for item in itens_sugeridos_raw]
                resposta_partes.append(f"\n\nVocê quis dizer:\n" + "\n".join([f"- {s}" for s in nomes_sugeridos]) + "? Por favor, diga o nome exato para adicionar.")
            
            # Se houver itens não encontrados, exiba-os.
            if itens_nao_encontrados:
                resposta_partes.append(f"\n\nNão entendi '{', '.join(itens_nao_encontrados)}'. Por favor, seja mais específico ou consulte o cardápio.")

            if not itens_adicionados_raw and not itens_sugeridos_raw and not itens_nao_encontrados:
                resposta_final = "Não entendi o que você gostaria de pedir. Por favor, diga o nome exato do(s) item(ns)."
            else:
                resposta_final = " ".join(resposta_partes).strip() + f"\n\nDeseja adicionar mais alguma coisa? (sim/não/remover/finalizar)"

            estado_conversa['esperando'] = 'adicionar_mais' # Volta para adicionar mais
            estado_conversa['itens_pedido'] = itens_pedido # Atualiza o estado
            estado_conversa['valor_total'] = valor_total # Atualiza o estado
            
            return jsonify({
                'resposta': resposta_final,
                'esperando': estado_conversa['esperando'],
                'id_conversa': id_conversa,
                'itens_pedido_atual': [{'nome': item['nome'], 'preco': item['preco']} for item in itens_pedido]
            })

        elif esperando == 'adicionar_mais':
            if user_input.lower() in ['sim', 's', 'adicionar', 'quero adicionar mais']:
                estado_conversa['esperando'] = 'pedido'
                return jsonify({
                    'resposta': "Certo, o que mais gostaria de adicionar?",
                    'esperando': 'pedido',
                    'id_conversa': id_conversa,
                    'itens_pedido_atual': [{'nome': item['nome'], 'preco': item['preco']} for item in itens_pedido]
                })
            elif user_input.lower() in ['não', 'nao', 'finalizar', 'confirmar', 'ok', 'não quero mais', 'nao quero mais']:
                if not estado_conversa['itens_pedido']:
                    estado_conversa['esperando'] = None
                    return jsonify({
                        'resposta': "Seu pedido está vazio. Posso ajudar com outra coisa?",
                        'id_conversa': id_conversa
                    })

                estado_conversa['esperando'] = 'confirmar_finalizar'
                itens_listados = "\n- ".join([f"{item['nome']} (R${item['preco']:.2f})" for item in estado_conversa['itens_pedido']])
                return jsonify({
                    'resposta': f"Seu pedido atual é:\n- {itens_listados}\n\nValor total: R${estado_conversa['valor_total']:.2f}\n\nDeseja confirmar o pedido? (sim/não)",
                    'esperando': 'confirmar_finalizar',
                    'itens_pedido': estado_conversa['itens_pedido'],
                    'valor_total': estado_conversa['valor_total'],
                    'id_conversa': id_conversa,
                    'itens_pedido_atual': [{'nome': item['nome'], 'preco': item['preco']} for item in itens_pedido]
                })
            elif "remover" in user_input.lower() or "tirar" in user_input.lower() or "excluir" in user_input.lower():
                estado_conversa['esperando'] = 'remover_item'
                itens_no_carrinho = ", ".join([item['nome'] for item in estado_conversa['itens_pedido']])
                return jsonify({
                    'resposta': f"Qual item você gostaria de remover do pedido atual? Itens no carrinho: {itens_no_carrinho}",
                    'esperando': 'remover_item',
                    'itens_pedido': [item['nome'] for item in estado_conversa['itens_pedido']],
                    'id_conversa': id_conversa,
                    'itens_pedido_atual': [{'nome': item['nome'], 'preco': item['preco']} for item in itens_pedido]
                })
            else:
                # Tratar o caso onde o usuário digita um novo item diretamente sem "sim"
                itens_adicionados_raw, itens_nao_encontrados, itens_sugeridos_raw = parse_e_verificar_itens(user_input)
                
                if itens_adicionados_raw or itens_sugeridos_raw or itens_nao_encontrados:
                    # Se ele digitou algo que parece um item, reprocessa como se estivesse no estado 'pedido'
                    estado_conversa['esperando'] = 'pedido'
                    return chat() # Chama o chat novamente com o mesmo input para reprocessar
                else:
                    return jsonify({
                        'resposta': "Não entendi sua resposta. Por favor, diga 'sim' para adicionar mais, 'não' para finalizar ou 'remover' para tirar um item.",
                        'esperando': 'adicionar_mais',
                        'id_conversa': id_conversa,
                        'itens_pedido_atual': [{'nome': item['nome'], 'preco': item['preco']} for item in itens_pedido]
                    })


        elif esperando == 'confirmar_finalizar':
            if user_input.lower() in ['sim', 's', 'confirmar', 'finalizar', 'ok']:
                if not estado_conversa['itens_pedido']:
                    estado_conversa['esperando'] = None
                    return jsonify({
                        'resposta': "Seu pedido está vazio e não pode ser finalizado. Posso ajudar com outra coisa?",
                        'id_conversa': id_conversa
                    })
                
                # Gera um novo ID de sessão de pedido se não houver um ativo
                if not estado_conversa['pedido_sessao_id']:
                    estado_conversa['pedido_sessao_id'] = str(uuid.uuid4())

                PedidosArmazenados(numero_cliente_logado, estado_conversa['itens_pedido'], estado_conversa['valor_total'], estado_conversa['pedido_sessao_id'])
                response_message = f"Pedido (ID: {estado_conversa['pedido_sessao_id']}) finalizado com sucesso! Obrigado!"
                
                # Limpa o estado da conversa para um novo pedido
                estado_conversa['esperando'] = None
                estado_conversa['itens_pedido'] = []
                estado_conversa['valor_total'] = 0.0
                estado_conversa['pedido_sessao_id'] = None
                estado_conversa['ofereceu_cardapio_antes_de_pedir'] = False
                
                return jsonify({
                    'resposta': response_message,
                    'id_conversa': id_conversa
                })
            elif user_input.lower() in ['não', 'nao', 'cancelar']:
                estado_conversa['esperando'] = 'opcoes_pos_confirmacao'
                return jsonify({
                    'resposta': "Pedido não confirmado. Deseja adicionar mais itens, remover algum item ou finalizar o pedido?",
                    'esperando': 'opcoes_pos_confirmacao',
                    'id_conversa': id_conversa,
                    'itens_pedido_atual': [{'nome': item['nome'], 'preco': item['preco']} for item in itens_pedido]
                })
            elif "remover" in user_input.lower() or "tirar" in user_input.lower() or "excluir" in user_input.lower():
                estado_conversa['esperando'] = 'remover_item'
                itens_no_carrinho = ", ".join([item['nome'] for item in estado_conversa['itens_pedido']])
                return jsonify({
                    'resposta': f"Qual item você gostaria de remover do pedido atual? Itens no carrinho: {itens_no_carrinho}",
                    'esperando': 'remover_item',
                    'itens_pedido': [item['nome'] for item in estado_conversa['itens_pedido']],
                    'id_conversa': id_conversa,
                    'itens_pedido_atual': [{'nome': item['nome'], 'preco': item['preco']} for item in itens_pedido]
                })
            elif "adicionar" in user_input.lower() or "mais" in user_input.lower() or "outro" in user_input.lower() or "pedir" in user_input.lower():
                estado_conversa['esperando'] = 'pedido'
                return jsonify({
                    'resposta': "Certo, o que mais gostaria de adicionar?",
                    'esperando': 'pedido',
                    'id_conversa': id_conversa,
                    'itens_pedido_atual': [{'nome': item['nome'], 'preco': item['preco']} for item in itens_pedido]
                })
            else:
                return jsonify({
                    'resposta': "Não entendi sua resposta. Por favor, diga 'sim' para confirmar ou 'não' para fazer alterações.",
                    'esperando': 'confirmar_finalizar',
                    'id_conversa': id_conversa,
                    'itens_pedido_atual': [{'nome': item['nome'], 'preco': item['preco']} for item in itens_pedido]
                })

        elif esperando == 'opcoes_pos_confirmacao':
            if "remover" in user_input.lower() or "tirar" in user_input.lower() or "excluir" in user_input.lower():
                estado_conversa['esperando'] = 'remover_item'
                itens_no_carrinho = ", ".join([item['nome'] for item in estado_conversa['itens_pedido']])
                return jsonify({
                    'resposta': f"Qual item você gostaria de remover do pedido atual? Itens no carrinho: {itens_no_carrinho}",
                    'esperando': 'remover_item',
                    'itens_pedido': [item['nome'] for item in estado_conversa['itens_pedido']],
                    'id_conversa': id_conversa,
                    'itens_pedido_atual': [{'nome': item['nome'], 'preco': item['preco']} for item in itens_pedido]
                })
            elif "adicionar" in user_input.lower() or "mais" in user_input.lower() or "outro" in user_input.lower() or "pedir" in user_input.lower():
                estado_conversa['esperando'] = 'pedido'
                return jsonify({
                    'resposta': "Certo, o que mais gostaria de adicionar?",
                    'esperando': 'pedido',
                    'id_conversa': id_conversa,
                    'itens_pedido_atual': [{'nome': item['nome'], 'preco': item['preco']} for item in itens_pedido]
                })
            elif user_input.lower() in ['finalizar', 'confirmar', 'ok']:
                estado_conversa['esperando'] = 'confirmar_finalizar'
                itens_listados = "\n- ".join([f"{item['nome']} (R${item['preco']:.2f})" for item in estado_conversa['itens_pedido']])
                return jsonify({
                    'resposta': f"Seu pedido atual é:\n- {itens_listados}\n\nValor total: R${estado_conversa['valor_total']:.2f}\n\nDeseja confirmar o pedido agora? (sim/não)",
                    'esperando': 'confirmar_finalizar',
                    'itens_pedido': estado_conversa['itens_pedido'],
                    'valor_total': estado_conversa['valor_total'],
                    'id_conversa': id_conversa,
                    'itens_pedido_atual': [{'nome': item['nome'], 'preco': item['preco']} for item in itens_pedido]
                })
            else:
                return jsonify({
                    'resposta': "Não entendi sua solicitação. Por favor, diga se quer 'adicionar', 'remover' ou 'finalizar'.",
                    'esperando': 'opcoes_pos_confirmacao',
                    'id_conversa': id_conversa,
                    'itens_pedido_atual': [{'nome': item['nome'], 'preco': item['preco']} for item in itens_pedido]
                })

        elif esperando == 'remover_item':
            item_para_remover = limpar_string_para_comparacao(user_input)
            removido = False
            indice_para_remover = -1
            # Itera de trás para frente para evitar problemas com pop e índices
            for i in range(len(estado_conversa['itens_pedido']) -1, -1, -1):
                if limpar_string_para_comparacao(estado_conversa['itens_pedido'][i]['nome']) == item_para_remover:
                    removido = True
                    indice_para_remover = i
                    break
            
            if removido:
                item_removido = estado_conversa['itens_pedido'].pop(indice_para_remover)
                estado_conversa['valor_total'] -= item_removido['preco']
                
                itens_listados = "\n- ".join([f"{item['nome']} (R${item['preco']:.2f})" for item in estado_conversa['itens_pedido']])
                
                response_text = f"'{item_removido['nome']}' removido do pedido."
                if estado_conversa['itens_pedido']:
                    response_text += f"\nSeu pedido atual é:\n- {itens_listados}\n\nValor total: R${estado_conversa['valor_total']:.2f}"
                else:
                    response_text += "\nSeu carrinho está vazio."
                
                response_text += "\n\nDeseja adicionar mais itens, remover outro item ou finalizar o pedido?"
                estado_conversa['esperando'] = 'opcoes_pos_confirmacao'
                
                return jsonify({
                    'resposta': response_text,
                    'esperando': 'opcoes_pos_confirmacao',
                    'id_conversa': id_conversa,
                    'itens_pedido_atual': [{'nome': item['nome'], 'preco': item['preco']} for item in itens_pedido]
                })
            else:
                itens_no_carrinho = ", ".join([item['nome'] for item in estado_conversa['itens_pedido']])
                return jsonify({
                    'resposta': f"Não encontrei '{user_input}' no seu pedido atual. Itens no carrinho: {itens_no_carrinho}\n\nDeseja adicionar mais itens, remover outro item ou finalizar o pedido?",
                    'esperando': 'opcoes_pos_confirmacao',
                    'itens_pedido_atual': [{'nome': item['nome'], 'preco': item['preco']} for item in itens_pedido],
                    'id_conversa': id_conversa
                })
            
        elif esperando == 'pedido_remocao': # Este estado é para remover pedidos JÁ FINALIZADOS
            pedido_remover = user_input.strip()
            resultado_remocao = removerPedidos(numero_cliente_logado, pedido_remover)
            estado_conversa['esperando'] = None # Volta ao estado neutro
            return jsonify({
                'resposta': resultado_remocao,
                'id_conversa': id_conversa
            })
            
        elif esperando == 'confirmar_ver_cardapio':
            if user_input.lower() in ['sim', 's']:
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
                    estado_conversa['esperando'] = 'pedido' # Direciona para fazer pedido
                    estado_conversa['ofereceu_cardapio_antes_de_pedir'] = False # Reseta a flag
                    return jsonify({'resposta': cardapio_texto.strip() + "\n\nO que gostaria de pedir?", 'id_conversa': id_conversa, 'esperando': 'pedido'})
                else:
                    estado_conversa['esperando'] = None
                    estado_conversa['ofereceu_cardapio_antes_de_pedir'] = False
                    return jsonify({'resposta': "O cardápio está vazio no momento. Posso ajudar com outra coisa?", 'id_conversa': id_conversa})
            else: # Se não quer ver, vai direto para fazer pedido
                estado_conversa['esperando'] = 'pedido' 
                estado_conversa['ofereceu_cardapio_antes_de_pedir'] = False
                return jsonify({'resposta': "Entendido. Então, o que gostaria de pedir?", 'esperando': 'pedido', 'id_conversa': id_conversa})

        # Processamento inicial de intenção (se não está em um estado 'esperando' específico)
        else: # Estado 'esperando' é None ou não reconhecido
            # Primeiro, tente a extração de intenção customizada antes de chamar o Gemini
            intencao_pre_gemini = extrair_intencao(user_input)

            if intencao_pre_gemini == "VER_CARDAPIO":
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
                    return jsonify({'resposta': cardapio_texto.strip() + "\n\nO que gostaria de pedir?", 'id_conversa': id_conversa, 'esperando': 'pedido'})
                else:
                    return jsonify({'resposta': "O cardápio está vazio no momento. Posso ajudar com outra coisa?", 'id_conversa': id_conversa})
            
            elif intencao_pre_gemini == "FAZER_PEDIDO_GENERICO":
                if not ofereceu_cardapio_antes_de_pedir:
                    estado_conversa['esperando'] = 'confirmar_ver_cardapio'
                    estado_conversa['ofereceu_cardapio_antes_de_pedir'] = True
                    return jsonify({
                        'resposta': "Você gostaria de ver o cardápio antes de fazer o pedido? (sim/não)",
                        'esperando': 'confirmar_ver_cardapio',
                        'id_conversa': id_conversa
                    })
                else: # Já ofereceu e o usuário ainda está querendo fazer pedido, vai direto
                    estado_conversa['esperando'] = 'pedido'
                    estado_conversa['itens_pedido'] = [] # Inicia um novo carrinho
                    estado_conversa['valor_total'] = 0.0
                    estado_conversa['pedido_sessao_id'] = str(uuid.uuid4()) # Novo ID para o novo pedido
                    estado_conversa['ofereceu_cardapio_antes_de_pedir'] = False # Reseta a flag
                    return jsonify({
                        'resposta': "Certo! Qual será seu primeiro item?",
                        'esperando': 'pedido',
                        'id_conversa': id_conversa
                    })

            # Se não foi uma das intenções pré-definidas, chama o Gemini
            response = model.generate_content([{"role": "user", "parts": [prompt_completo + user_input]}])
            bot_reply = response.text.strip()
            intencao = extrair_intencao(bot_reply) # Extrai intenção do Gemini

            if not intencao:
                return jsonify({'resposta': bot_reply, 'id_conversa': id_conversa})

            if intencao == "FAZER_PEDIDO":
                estado_conversa['esperando'] = 'pedido'
                estado_conversa['itens_pedido'] = [] # Limpa itens de pedidos anteriores
                estado_conversa['valor_total'] = 0.0
                estado_conversa['pedido_sessao_id'] = str(uuid.uuid4()) # Novo ID para novo pedido
                estado_conversa['ofereceu_cardapio_antes_de_pedir'] = False # Reseta a flag
                return jsonify({
                    'resposta': "Certo! Qual será seu primeiro item?",
                    'esperando': 'pedido',
                    'id_conversa': id_conversa
                })
            elif intencao == "CONSULTAR_PEDIDO":
                resultado = BuscarPedidos(numero_cliente_logado)
                estado_conversa['esperando'] = None # Volta ao estado neutro
                estado_conversa['ofereceu_cardapio_antes_de_pedir'] = False
                return jsonify({
                    'resposta': resultado,
                    'id_conversa': id_conversa
                })
            elif intencao == "REMOVER_PEDIDO": 
                pedidos_atuais_texto = BuscarPedidos(numero_cliente_logado)
                estado_conversa['esperando'] = 'pedido_remocao' # Espera o ID do pedido a remover
                estado_conversa['pedidos_atuais'] = pedidos_atuais_texto # Armazena para exibição
                estado_conversa['ofereceu_cardapio_antes_de_pedir'] = False
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
            elif intencao == "VER_CARDAPIO": # Caso o Gemini ainda retorne VER_CARDAPIO, tratamos aqui
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
                    estado_conversa['ofereceu_cardapio_antes_de_pedir'] = False
                    return jsonify({'resposta': cardapio_texto.strip() + "\n\nO que gostaria de pedir?", 'id_conversa': id_conversa, 'esperando': 'pedido'})
                else:
                    estado_conversa['ofereceu_cardapio_antes_de_pedir'] = False
                    return jsonify({'resposta': "O cardápio está vazio no momento.", 'id_conversa': id_conversa})

            return jsonify({'resposta': bot_reply, 'id_conversa': id_conversa})

    except Exception as e:
        print(f"Erro no chat: {e}")
        return jsonify({'resposta': "Ocorreu um erro inesperado. Por favor, tente novamente mais tarde.", 'error': True, 'id_conversa': id_conversa}), 500

# Rotas para o painel de administração (mantidas inalteradas)

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
    resultado = finalizar_pedidos_cliente(numero_cliente) 
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

    conexao = sqlite3.connect("chatbot.db")
    cursor = conexao.cursor()
    try:
        cursor.execute("INSERT INTO cardapios (pedido, preco, categoria, descricao) VALUES (?, ?, ?, ?)", (pedido, preco, categoria, descricao))
        conexao.commit()
        item_id = cursor.lastrowid
        conexao.close()
        return jsonify({'message': f"Item '{pedido}' adicionado ao cardápio com ID {item_id}.", 'id': item_id}), 201
    except sqlite3.IntegrityError:
        conexao.close()
        return jsonify({'error': f"Já existe um item com o nome '{pedido}' no cardapio."}), 409
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