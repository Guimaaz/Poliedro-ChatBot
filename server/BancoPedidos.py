import sqlite3
import re
import difflib
import hashlib
import uuid
from server.cardapio import itensCardapio
import logging

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
    pedido_sessao_id TEXT,
    FOREIGN KEY (numero_cliente) REFERENCES clientes (numero_cliente),
    FOREIGN KEY (item_id) REFERENCES cardapios (id)
    )
    ''')


    try:
        cursor.execute("ALTER TABLE pedidos ADD COLUMN pedido_sessao_id TEXT")
        conexao.commit()
        print("Coluna 'pedido_sessao_id' adicionada à tabela 'pedidos'.")
    except sqlite3.OperationalError:
        print("Coluna 'pedido_sessao_id' já existe na tabela 'pedidos'.")

    for item_info in itensCardapio:
        pedido, preco, categoria, descricao = item_info
        try:
            cursor.execute("INSERT OR IGNORE INTO cardapios (pedido, preco, categoria, descricao) VALUES (?, ?, ?, ?)", (pedido, preco, categoria, descricao))
        except sqlite3.IntegrityError:
            pass

    numero_admin = "(11) 97430-6793"
    senha_admin_hash = hash_senha("admin")
    try:
        cursor.execute("INSERT OR IGNORE INTO clientes (numero_cliente, senha, is_admin) VALUES (?, ?, ?)", (numero_admin, senha_admin_hash, 1))
        conexao.commit()
        print("Usuário administrador adicionado (ou já existia).")
    except sqlite3.IntegrityError:
        print("Erro ao inserir usuário administrador.")

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
            print(f"Usuário de teste com número {numero} adicionado (ou já existia).")
        except sqlite3.IntegrityError:
            print(f"Erro ao inserir usuário de teste com número {numero}.")

    conexao.commit()
    conexao.close()

pedido_sessoes = {} # armazena o id de cada sessão por cliente

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
    print(f"Tentando autenticar cliente: {numero_cliente}")
    cursor.execute("SELECT id, senha, is_admin FROM clientes WHERE numero_cliente = ?", (numero_cliente,))
    resultado = cursor.fetchone()
    print(f"Resultado da busca no banco: {resultado}")
    conexao.close()

    if resultado:
        user_id, senha_hash_db, is_admin = resultado
        senha_correta = verificar_senha(senha, senha_hash_db)
        print(f"Senha digitada hash: {hash_senha(senha)}")
        print(f"Senha do banco hash: {senha_hash_db}")
        print(f"Senha correta: {senha_correta}")
        return senha_correta, is_admin
    return False, 0


def PedidosArmazenados(numero_cliente, itens_pedido, valor_total, pedido_sessao_id):
    conexao = None
    try:
        conexao = sqlite3.connect(DATABASE_NAME)
        cursor = conexao.cursor()
        logging.info(f"Conexão com o banco de dados estabelecida para o cliente: {numero_cliente}, sessão: {pedido_sessao_id}")

        cursor.execute("SELECT id FROM clientes WHERE numero_cliente = ?", (numero_cliente,))
        cliente = cursor.fetchone()

        if not cliente:
            logging.warning(f"Cliente não encontrado: {numero_cliente}")
            if conexao:
                conexao.close()
            return "Cliente não encontrado. Por favor, faça login novamente."

        logging.info(f"Cliente encontrado com ID: {cliente[0]}")

        for item_info in itens_pedido:
            pedido_nome = item_info['nome']
            preco_item = item_info['preco']
            logging.info(f"Processando item: {pedido_nome}, preço: {preco_item}")

            cursor.execute("SELECT id, pedido FROM cardapios WHERE pedido = ?", (pedido_nome,))
            item_cardapio = cursor.fetchone()

            if item_cardapio:
                item_id = item_cardapio[0]
                cursor.execute(
                    "INSERT INTO pedidos (numero_cliente, item, item_id, preco, pedido_sessao_id) VALUES (?, ?, ?, ?, ?)",
                    (numero_cliente, pedido_nome, item_id, preco_item, pedido_sessao_id)
                )
                logging.info(f"Item '{pedido_nome}' inserido no pedido. Item ID: {item_id}")
            else:
                logging.error(f"Item '{pedido_nome}' não encontrado no cardápio.")
                if conexao:
                    conexao.rollback()
                    conexao.close()
                return f"Item '{pedido_nome}' não encontrado no cardápio."

        conexao.commit()
        logging.info(f"Pedido para o cliente {numero_cliente} (sessão {pedido_sessao_id}) registrado com sucesso!")
        if conexao:
            conexao.close()
        return "Pedido registrado com sucesso!"

    except sqlite3.Error as e:
        logging.error(f"Erro de banco de dados ao registrar o pedido: {str(e)}")
        if conexao:
            conexao.rollback()
            conexao.close()
        return f"Erro ao registrar o pedido: {str(e)}"
    except Exception as e:
        logging.error(f"Erro inesperado ao registrar o pedido: {str(e)}")
        if conexao:
            conexao.rollback()
            conexao.close()
        return f"Erro inesperado ao registrar o pedido: {str(e)}"
    finally:
        if conexao:
            conexao.close()
            logging.info("Conexão com o banco de dados fechada.")
def removerPedidos(numero_cliente, pedido_sessao_id):
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM pedidos WHERE numero_cliente = ? AND pedido_sessao_id = ?",
                        (numero_cliente, pedido_sessao_id))
        if not cursor.fetchone():
            return f"Pedido com ID '{pedido_sessao_id}' não encontrado para este número."

        cursor.execute("DELETE FROM pedidos WHERE numero_cliente = ? AND pedido_sessao_id = ?",
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
        SELECT p.item, p.item_id, p.preco, datetime(p.data, '-3 hours'), p.pedido_sessao_id
        FROM pedidos p
        WHERE p.numero_cliente = ?
        ORDER BY p.data DESC
    ''', (numero_cliente,))

    pedidos = cursor.fetchall()
    conexao.close()

    if not pedidos:
        return "Nenhum pedido encontrado para esse número."

    pedidos_formatados = {}
    for item, item_id, preco, data, sessao_id in pedidos:
        if sessao_id not in pedidos_formatados:
            pedidos_formatados[sessao_id] = {"itens": [], "data_primeiro_item": data, "data_ultimo_item": data, "valor_total": 0.0}
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

    return resposta.strip() if resposta else "Nenhum pedido encontrado para esse número."

def VerificarItensCardapio(pedido):
    pedido = pedido.lower()
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    cursor.execute("SELECT pedido, descricao, preco FROM cardapios")
    itens_db_info = {row[0].lower(): (row[0], row[1], row[2]) for row in cursor.fetchall()}
    conexao.close()

    if pedido in itens_db_info:
        nome_exato, descricao, preco = itens_db_info[pedido]
        return nome_exato, True, descricao, preco

    prato_sugerido = difflib.get_close_matches(pedido, list(itens_db_info.keys()), n=1, cutoff=0.6)
    if prato_sugerido:
        nome_sugerido, descricao_sugerida, preco_sugerido = itens_db_info[prato_sugerido[0]]
        return nome_sugerido, False, descricao_sugerida, preco_sugerido

    return None, False, "", 0

def AdicionarItemPedido(numero_cliente, item_nome):
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()

    cursor.execute("SELECT id FROM clientes WHERE numero_cliente = ?", (numero_cliente,))
    cliente = cursor.fetchone()

    if not cliente:
        conexao.close()
        return "Cliente não encontrado. Por favor, faça login novamente."

    cursor.execute("SELECT id, pedido, preco FROM cardapios WHERE pedido = ?", (item_nome,))
    item = cursor.fetchone()

    if not item:
        conexao.close()
        return f"Item '{item_nome}' não encontrado no cardápio."

    pedido_sessao_id = pedido_sessoes.get(numero_cliente)
    if pedido_sessao_id is None:
        pedido_sessao_id = str(uuid.uuid4())
        pedido_sessoes[numero_cliente] = pedido_sessao_id

    cursor.execute("INSERT INTO pedidos (numero_cliente, item, item_id, preco, pedido_sessao_id) VALUES (?, ?, ?, ?, ?)",
                    (numero_cliente, item[1], item[0], item[2], pedido_sessao_id))

    conexao.commit()
    conexao.close()
    return f"'{item_nome}' adicionado ao seu pedido."

def buscar_pedidos_admin():
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    cursor.execute('''
        SELECT numero_cliente, GROUP_CONCAT(item || ' (R$' || preco || ')', '\n- ') AS itens, SUM(preco), MIN(datetime(data, '-3 hours')), MAX(datetime(data, '-3 hours')), pedido_sessao_id
        FROM pedidos
        WHERE finalizado = 0
        GROUP BY pedido_sessao_id
        ORDER BY MIN(data) DESC
    ''')
    pedidos_pendentes = cursor.fetchall()

    cursor.execute('''
        SELECT numero_cliente, GROUP_CONCAT(item || ' (R$' || preco || ')', '\n- ') AS itens, SUM(preco), MIN(datetime(data, '-3 hours')), MAX(datetime(data, '-3 hours')), pedido_sessao_id
        FROM pedidos
        WHERE finalizado = 1
        GROUP BY pedido_sessao_id
        ORDER BY MAX(data) DESC
    ''')
    pedidos_finalizados = cursor.fetchall()

    conexao.close()

    pedidos_pendentes_formatados = []
    for p in pedidos_pendentes:
        pedidos_pendentes_formatados.append({
            "cliente": p[0],
            "itens": p[1],
            "preco_total": float(p[2]),
            "data_inicio": p[3],
            "data_fim": p[4],
            "finalizado": False,
            "pedido_sessao_id": p[5]
        })

    pedidos_finalizados_formatados = []
    for p in pedidos_finalizados:
        pedidos_finalizados_formatados.append({
            "cliente": p[0],
            "itens": p[1],
            "preco_total": float(p[2]),
            "data_inicio": p[3],
            "data_fim": p[4],
            "finalizado": True,
            "pedido_sessao_id": p[5]
        })

    return {"nao_finalizados": pedidos_pendentes_formatados, "finalizados": pedidos_finalizados_formatados}

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

def finalizar_pedido_admin(pedido_sessao_id):
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    cursor.execute("UPDATE pedidos SET finalizado = 1 WHERE pedido_sessao_id = ?", (pedido_sessao_id,))
    conexao.commit()
    registros_alterados = cursor.rowcount
    conexao.close()
    if registros_alterados > 0:
        return f"Pedido com ID {pedido_sessao_id} finalizado."
    else:
        return f"Nenhum pedido encontrado com o ID {pedido_sessao_id}."

def reabrir_pedido_admin(pedido_sessao_id):
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    cursor.execute("UPDATE pedidos SET finalizado = 0 WHERE pedido_sessao_id = ?", (pedido_sessao_id,))
    conexao.commit()
    registros_alterados = cursor.rowcount
    conexao.close()
    if registros_alterados > 0:
        return f"Pedido com ID {pedido_sessao_id} reaberto."
    else:
        return f"Nenhum pedido finalizado encontrado com o ID {pedido_sessao_id}."

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

def atualizar_cardapio_admin(item_id, pedido, preco, descricao, categoria):
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    try:
        cursor.execute("UPDATE cardapios SET pedido=?, preco=?, descricao=?, categoria=? WHERE id=?",
                       (pedido, preco, descricao, categoria, item_id))
        conexao.commit()
        return f"Item com ID {item_id} atualizado."
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

def buscar_cardapio_completo():
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