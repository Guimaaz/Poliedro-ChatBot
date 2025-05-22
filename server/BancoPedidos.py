import sqlite3
import re
import difflib
import hashlib
import uuid
from server.cardapio import itensCardapio
import logging
import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
DATABASE_NAME = "chatbot.db"

def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()

def verificar_senha(senha_digitada, senha_hash):
    return hash_senha(senha_digitada) == senha_hash

def CreateDatabase():
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_cliente TEXT NOT NULL UNIQUE,
    senha TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cardapios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido TEXT NOT NULL UNIQUE,
    preco DECIMAL(10, 2) NOT NULL,
    categoria TEXT NOT NULL DEFAULT 'Outros',
    descricao TEXT NOT NULL DEFAULT ''
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_cliente TEXT NOT NULL,
    item TEXT NOT NULL,
    item_id INTEGER NOT NULL,
    preco DECIMAL(10, 2) NOT NULL,
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finalizado INTEGER DEFAULT 0,
    pedido_sessao_id TEXT NOT NULL,
    FOREIGN KEY (numero_cliente) REFERENCES clientes (numero_cliente),
    FOREIGN KEY (item_id) REFERENCES cardapios (id)
    )
    ''')

    try:
        cursor.execute("PRAGMA table_info(pedidos)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'pedido_sessao_id' not in columns:
            cursor.execute("ALTER TABLE pedidos ADD COLUMN pedido_sessao_id TEXT")
            conexao.commit()
        else:
            pass
    except sqlite3.OperationalError as e:
        logging.error(f"Erro ao verificar/adicionar coluna pedido_sessao_id: {e}")

    for item_info in itensCardapio:
        pedido = item_info[0] 
        preco = item_info[1]  
        categoria = item_info[2] 
        descricao = item_info[3]
        try:
            cursor.execute("INSERT OR IGNORE INTO cardapios (pedido, preco, categoria, descricao) VALUES (?, ?, ?, ?)", (pedido, preco, categoria, descricao))
        except sqlite3.IntegrityError:
            pass

    numero_admin = "(11) 97430-6793"
    senha_admin_hash = hash_senha("admin")
    try:
        cursor.execute("INSERT OR IGNORE INTO clientes (numero_cliente, senha, is_admin) VALUES (?, ?, ?)", (numero_admin, senha_admin_hash, 1))
        conexao.commit()
    except sqlite3.IntegrityError:
        pass

    usuarios_teste = [
        ("(11) 99999-1111", "senha123"),
        ("(11) 97430-6792", "Nhe45657"),
        ("(11) 98765-4321", "senha123")
    ]

    for numero, senha_plana in usuarios_teste:
        senha_hash = hash_senha(senha_plana)
        try:
            cursor.execute("INSERT OR IGNORE INTO clientes (numero_cliente, senha) VALUES (?, ?)", (numero, senha_hash))
            conexao.commit()
        except sqlite3.IntegrityError:
            pass

    conexao.commit()
    conexao.close()

def validar_numero(numero_cliente):
    padrao = r"\(\d{2}\) \d{5}-\d{4}"
    return re.match(padrao, numero_cliente)

def registrar_cliente(numero_cliente, senha):
    if not validar_numero(numero_cliente):
        return "Número de telefone inválido! Use o formato (XX) XXXXX-XXXX."

    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()

    try:
        cursor.execute("INSERT INTO clientes (numero_cliente, senha) VALUES (?, ?)", (numero_cliente, hash_senha(senha)))
        conexao.commit()
        return "Cliente registrado com sucesso!"
    except sqlite3.IntegrityError:
        return "Este número de telefone já está registrado."
    finally:
        conexao.close()

def autenticar_cliente(numero_cliente, senha):
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    cursor.execute("SELECT id, senha, is_admin FROM clientes WHERE numero_cliente = ?", (numero_cliente,))
    resultado = cursor.fetchone()
    conexao.close()

    if resultado:
        user_id, senha_hash_db, is_admin = resultado
        senha_correta = verificar_senha(senha, senha_hash_db)
        return senha_correta, is_admin
    return False, 0

def PedidosArmazenados(numero_cliente, itens_pedido, valor_total, pedido_sessao_id):
    conexao = None
    try:
        conexao = sqlite3.connect(DATABASE_NAME)
        cursor = conexao.cursor()

        cursor.execute("SELECT id FROM clientes WHERE numero_cliente = ?", (numero_cliente,))
        cliente = cursor.fetchone()

        if not cliente:
            return "Cliente não encontrado. Por favor, faça login novamente."

        for item_info in itens_pedido:
            pedido_nome = item_info['nome']
            preco_item = item_info['preco']

            cursor.execute("SELECT id, pedido FROM cardapios WHERE pedido = ?", (pedido_nome,))
            item_cardapio = cursor.fetchone()

            if item_cardapio:
                item_id = item_cardapio[0]
                cursor.execute(
                    "INSERT INTO pedidos (numero_cliente, item, item_id, preco, pedido_sessao_id) VALUES (?, ?, ?, ?, ?)",
                    (numero_cliente, pedido_nome, item_id, preco_item, pedido_sessao_id)
                )
            else:
                conexao.rollback()
                return f"Item '{pedido_nome}' não encontrado no cardápio. Pedido não registrado."

        conexao.commit()
        return "Pedido registrado com sucesso!"

    except sqlite3.Error as e:
        if conexao:
            conexao.rollback()
        return f"Erro ao registrar o pedido: {str(e)}"
    except Exception as e:
        if conexao:
            conexao.rollback()
        return f"Erro inesperado ao registrar o pedido: {str(e)}"
    finally:
        if conexao:
            conexao.close()

def removerPedidos(numero_cliente, pedido_sessao_id):
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM pedidos WHERE numero_cliente = ? AND pedido_sessao_id = ? AND finalizado = 0",
                       (numero_cliente, pedido_sessao_id))
        if not cursor.fetchone():
            return f"Pedido com ID '{pedido_sessao_id}' não encontrado ou já foi finalizado/removido."

        cursor.execute("DELETE FROM pedidos WHERE numero_cliente = ? AND pedido_sessao_id = ? AND finalizado = 0",
                       (numero_cliente, pedido_sessao_id))
        conn.commit()

        if cursor.rowcount > 0:
            return f"Pedido com ID '{pedido_sessao_id}' removido com sucesso!"
        else:
            return f"Não foi possível remover o pedido com ID '{pedido_sessao_id}'."

    except sqlite3.Error as e:
        return f"Erro no banco de dados: {str(e)}"
    finally:
        if conn:
            conn.close()

def BuscarPedidos(numero_cliente):
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()

    cursor.execute("SELECT id FROM clientes WHERE numero_cliente = ?", (numero_cliente,))
    cliente = cursor.fetchone()

    if not cliente:
        conexao.close()
        return "Cliente não encontrado. Por favor, faça login novamente."

    cursor.execute('''
        SELECT p.id, p.item, p.preco, datetime(p.data, '-3 hours'), p.pedido_sessao_id
        FROM pedidos p
        WHERE p.numero_cliente = ? AND p.finalizado = 0
        ORDER BY p.data DESC
    ''', (numero_cliente,))

    pedidos = cursor.fetchall()
    conexao.close()

    if not pedidos:
        return "Nenhum pedido ativo encontrado para esse número."

    pedidos_formatados = {}
    for p_id, item, preco, data, sessao_id in pedidos:
        if sessao_id not in pedidos_formatados:
            pedidos_formatados[sessao_id] = {
                "id_interno": p_id,
                "itens": [],
                "data_primeiro_item": data,
                "data_ultimo_item": data,
                "valor_total": 0.0
            }
        pedidos_formatados[sessao_id]["itens"].append(f"{item} (R${preco:.2f})")
        pedidos_formatados[sessao_id]["valor_total"] += preco
        pedidos_formatados[sessao_id]["data_primeiro_item"] = min(pedidos_formatados[sessao_id]["data_primeiro_item"], data)
        pedidos_formatados[sessao_id]["data_ultimo_item"] = max(pedidos_formatados[sessao_id]["data_ultimo_item"], data)

    resposta = ""
    for sessao_id, info in pedidos_formatados.items():
        itens_str = "\n- ".join(info["itens"])
        resposta += f"**Pedido ID:** {sessao_id}\n"
        resposta += f"**Itens:**\n- {itens_str}\n"
        resposta += f"**Valor Total:** R${info['valor_total']:.2f}\n"
        resposta += f"**Data do Pedido:** {info['data_primeiro_item']}\n\n"

    return resposta.strip() if resposta else "Nenhum pedido ativo encontrado para esse número."

def VerificarItensCardapio(pedido):
    pedido_lower = pedido.lower()
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    cursor.execute("SELECT id, pedido, descricao, preco FROM cardapios")
    cursor.execute("SELECT id, pedido, descricao, preco FROM cardapios")
    itens_db_info = {}
    for row in cursor.fetchall():
        itens_db_info[row[1].lower()] = (row[0], row[1], row[2], row[3])
    conexao.close()

    if pedido_lower in itens_db_info:
        item_id, nome_exato, descricao, preco = itens_db_info[pedido_lower]
        return nome_exato, True, descricao, preco

    prato_sugerido_key = difflib.get_close_matches(pedido_lower, list(itens_db_info.keys()), n=1, cutoff=0.7)
    if prato_sugerido_key:
        item_id, nome_sugerido, descricao_sugerida, preco_sugerido = itens_db_info[prato_sugerido_key[0]]
        return nome_sugerido, False, descricao_sugerida, preco_sugerido

    return None, False, "", 0.0

def buscar_pedidos_admin():
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    
    cursor.execute('''
        SELECT 
            MIN(p.id) as id_interno_primeiro_item,
            p.numero_cliente, 
            GROUP_CONCAT(p.item || ' (R$' || p.preco || ')', '\n- ') AS itens, 
            SUM(p.preco) AS total_pedido, 
            MIN(datetime(p.data, '-3 hours')) AS data_inicio_pedido, 
            MAX(datetime(p.data, '-3 hours')) AS data_fim_pedido, 
            p.pedido_sessao_id
        FROM pedidos p
        WHERE p.finalizado = 0
        GROUP BY p.numero_cliente, p.pedido_sessao_id
        ORDER BY data_inicio_pedido DESC
    ''')
    pedidos_pendentes_db = cursor.fetchall()

    cursor.execute('''
        SELECT 
            MIN(p.id) as id_interno_primeiro_item,
            p.numero_cliente, 
            GROUP_CONCAT(p.item || ' (R$' || p.preco || ')', '\n- ') AS itens, 
            SUM(p.preco) AS total_pedido, 
            MIN(datetime(p.data, '-3 hours')) AS data_inicio_pedido, 
            MAX(datetime(p.data, '-3 hours')) AS data_fim_pedido, 
            p.pedido_sessao_id
        FROM pedidos p
        WHERE p.finalizado = 1
        GROUP BY p.numero_cliente, p.pedido_sessao_id
        ORDER BY data_fim_pedido DESC
    ''')
    pedidos_finalizados_db = cursor.fetchall()

    conexao.close()

    pedidos_pendentes_formatados = []
    for p in pedidos_pendentes_db:
        pedidos_pendentes_formatados.append({
            "id": p[0],
            "cliente": p[1],
            "itens": p[2],
            "preco_total": float(p[3]),
            "data_inicio": p[4],
            "data_fim": p[5],
            "finalizado": False,
            "pedido_sessao_id": p[6]
        })
    pedidos_finalizados_formatados = []
    for p in pedidos_finalizados_db:
        pedidos_finalizados_formatados.append({
            "id": p[0],
            "id": p[0],
            "cliente": p[1],
            "itens": p[2],
            "preco_total": float(p[3]),
            "data_inicio": p[4],
            "data_fim": p[5],
            "finalizado": True,
            "pedido_sessao_id": p[6]
        })

    return {"nao_finalizados": pedidos_pendentes_formatados, "finalizados": pedidos_finalizados_formatados}

def finalizar_pedido_admin(pedido_sessao_id):
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    cursor.execute("UPDATE pedidos SET finalizado = 1 WHERE pedido_sessao_id = ? AND finalizado = 0", (pedido_sessao_id,))
    conexao.commit()
    registros_alterados = cursor.rowcount
    conexao.close()
    if registros_alterados > 0:
        return f"Pedido com ID {pedido_sessao_id} finalizado."
    else:
        return f"Nenhum pedido pendente encontrado com o ID {pedido_sessao_id} para finalizar."

def reabrir_pedido_admin(pedido_sessao_id):
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    cursor.execute("UPDATE pedidos SET finalizado = 0 WHERE pedido_sessao_id = ? AND finalizado = 1", (pedido_sessao_id,))
    conexao.commit()
    registros_alterados = cursor.rowcount
    conexao.close()
    if registros_alterados > 0:
        return f"Pedido com ID {pedido_sessao_id} reaberto."
    else:
        return f"Nenhum pedido finalizado encontrado com o ID {pedido_sessao_id} para reabrir."

def finalizar_pedidos_cliente(numero_cliente):
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    cursor.execute("UPDATE pedidos SET finalizado = 1 WHERE numero_cliente = ? AND finalizado = 0", (numero_cliente,))
    conexao.commit()
    registros_alterados = cursor.rowcount
    conexao.close()
    if registros_alterados > 0:
        return {"message": f"Todos os pedidos pendentes para o cliente {numero_cliente} foram finalizados."}
    else:
        return {"message": f"Não há pedidos pendentes para o cliente {numero_cliente}."}

def buscar_cardapio_admin():
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    cursor.execute("SELECT id, pedido, preco, categoria, descricao FROM cardapios ORDER BY categoria, pedido")
    cardapio = cursor.fetchall()
    conexao.close()
    cardapio_lista = []
    for item in cardapio:
        cardapio_lista.append({
            "id": item[0],
            "pedido": item[1],
            "preco": float(item[2]),
            "categoria": item[3],
            "descricao": item[4]
        })
    return cardapio_lista

def adicionar_item_cardapio_admin(pedido, preco, descricao, categoria):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO cardapios (pedido, preco, descricao, categoria) VALUES (?, ?, ?, ?)", (pedido, preco, descricao, categoria))
        conn.commit()
        return "Item adicionado ao cardápio com sucesso!"
    except sqlite3.IntegrityError:
        return "Já existe um item com este nome no cardápio."
    except Exception as e:
        return f"Erro ao adicionar item: {str(e)}"
    finally:
        conn.close()

def atualizar_cardapio_admin(item_id, pedido, preco, descricao, categoria):
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    try:
        cursor.execute("UPDATE cardapios SET pedido=?, preco=?, descricao=?, categoria=? WHERE id=?",
                       (pedido, preco, descricao, categoria, item_id))
        conexao.commit()
        if cursor.rowcount > 0:
            return f"Item com ID {item_id} atualizado."
        else:
            return f"Nenhum item do cardápio encontrado com o ID {item_id}."
    except sqlite3.IntegrityError:
        conexao.rollback()
        return f"Já existe um item com o nome '{pedido}' no cardápio."
    finally:
        conexao.close()

def deletar_cardapio_admin(item_id):
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM cardapios WHERE id=?", (item_id,))
    conexao.commit()
    if cursor.rowcount > 0:
        return f"Item com ID {item_id} deletado."
    else:
        return f"Nenhum item encontrado com o ID {item_id}."

def buscar_clientes_admin():
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    cursor.execute("SELECT id, numero_cliente, is_admin FROM clientes ORDER BY numero_cliente")
    clientes = cursor.fetchall()
    conexao.close()
    clientes_lista = []
    for cliente in clientes:
        clientes_lista.append({
            "id": cliente[0],
            "numero_cliente": cliente[1],
            "is_admin": bool(cliente[2])
        })
    return clientes_lista

def Cardapio_banco():
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    cursor.execute("SELECT pedido, preco, categoria, descricao FROM cardapios ORDER BY categoria, pedido")
    cardapio_data = cursor.fetchall()
    conexao.close()

    cardapio_organizado = {}
    for pedido, preco, categoria, descricao in cardapio_data:
        if categoria not in cardapio_organizado:
            cardapio_organizado[categoria] = []
        cardapio_organizado[categoria].append({"pedido": pedido, "preco": preco, "descricao": descricao})

    return cardapio_organizado