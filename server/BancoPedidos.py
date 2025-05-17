import sqlite3
import re
import difflib
import hashlib
from server.cardapio import itensCardapio
from flask import jsonify

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

    cursor.execute('''CREATE TABLE IF NOT EXISTS cardapios (
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
    FOREIGN KEY (numero_cliente) REFERENCES clientes (numero_cliente),
    FOREIGN KEY (item_id) REFERENCES cardapios (id)
    )
    ''')

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

    # usuários teste chumbados
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

def PedidosArmazenados(numero_cliente, itens_pedido, valor_total):
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()

    cursor.execute("SELECT id FROM clientes WHERE numero_cliente = ?", (numero_cliente,))
    cliente = cursor.fetchone()

    if not cliente:
        conexao.close()
        return "Cliente não encontrado. Por favor, faça login novamente."

    pedido_id_principal = None  # Para armazenar o ID do pedido principal

    for item_info in itens_pedido:
        pedido_nome = item_info['nome']
        preco_item = item_info['preco']

        cursor.execute("SELECT id, pedido FROM cardapios WHERE pedido = ?", (pedido_nome,))
        item_cardapio = cursor.fetchone()

        if item_cardapio:
            item_id = item_cardapio[0]
            cursor.execute(
                "INSERT INTO pedidos (numero_cliente, item, item_id, preco) VALUES (?, ?, ?, ?)",
                (numero_cliente, pedido_nome, item_id, preco_item)
            )
            if pedido_id_principal is None:
                pedido_id_principal = cursor.lastrowid  # Captura o ID do primeiro item inserido (pode ser útil para referência futura)
        else:
            conexao.rollback()
            conexao.close()
            return f"Item '{pedido_nome}' não encontrado no cardápio."

    conexao.commit()
    conexao.close()
    return "Pedido registrado com sucesso!"

def removerPedidos(numero_cliente, pedido):
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM pedidos WHERE numero_cliente = ? AND item = ?",
                        (numero_cliente, pedido))
        if not cursor.fetchone():
            return f"Pedido '{pedido}' não encontrado para este número."

        cursor.execute("DELETE FROM pedidos WHERE numero_cliente = ? AND item = ?",
                        (numero_cliente, pedido))
        conn.commit()

        if cursor.rowcount > 0:
            return f"Pedido '{pedido}' removido com sucesso!"
        else:
            return f"Não foi possível remover o pedido '{pedido}'."

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
        SELECT p.item, p.item_id, p.preco, datetime(p.data, '-3 hours')
        FROM pedidos p
        WHERE p.numero_cliente = ?
    ''', (numero_cliente,))

    pedidos = cursor.fetchall()
    conexao.close()

    if not pedidos:
        return "Nenhum pedido encontrado para esse número."

    return "\n".join([f"Pedido: {p[0]} (ID: {p[1]}) - Preço: R${p[2]:.2f} - Data: {p[3]}" for p in pedidos])

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

    cursor.execute("INSERT INTO pedidos (numero_cliente, item, item_id, preco) VALUES (?, ?, ?, ?)",
                    (numero_cliente, item[1], item[0], item[2]))

    conexao.commit()
    conexao.close()
    return f"'{item_nome}' adicionado ao seu pedido."

def buscar_pedidos_admin():
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    cursor.execute('''
        SELECT numero_cliente, GROUP_CONCAT(item || ' (R$' || preco || ')', '\n- ') AS itens, SUM(preco), MIN(datetime(data, '-3 hours')), MAX(datetime(data, '-3 hours'))
        FROM pedidos
        WHERE finalizado = 0
        GROUP BY numero_cliente
        ORDER BY MIN(data) DESC
    ''')
    pedidos_pendentes = cursor.fetchall()

    cursor.execute('''
        SELECT numero_cliente, GROUP_CONCAT(item || ' (R$' || preco || ')', '\n- ') AS itens, SUM(preco), MIN(datetime(data, '-3 hours')), MAX(datetime(data, '-3 hours'))
        FROM pedidos
        WHERE finalizado = 1
        GROUP BY numero_cliente
        ORDER BY MAX(data) DESC
    ''')
    pedidos_finalizados = cursor.fetchall()

    conexao.close()

    pedidos_pendentes_formatados = [
        {"cliente": p[0], "itens": p[1], "preco_total": float(p[2]), "data_inicio": p[3], "data_fim": p[4], "finalizado": False}
        for p in pedidos_pendentes
    ]

    pedidos_finalizados_formatados = [
        {"cliente": p[0], "itens": p[1], "preco_total": float(p[2]), "data_inicio": p[3], "data_fim": p[4], "finalizado": True}
        for p in pedidos_finalizados
    ]

    return {"nao_finalizados": pedidos_pendentes_formatados, "finalizados": pedidos_finalizados_formatados}

def finalizar_pedido_admin(pedido_id):
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    cursor.execute("UPDATE pedidos SET finalizado = 1 WHERE id = ?", (pedido_id,))
    conexao.commit()
    conexao.close()
    return f"Pedido ID {pedido_id} finalizado."

def reabrir_pedido_admin(pedido_id):
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    cursor.execute("UPDATE pedidos SET finalizado = 0 WHERE id = ?", (pedido_id,))
    conexao.commit()
    conexao.close()
    return f"Pedido ID {pedido_id} reaberto."


def finalizar_pedidos_cliente(numero_cliente):
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    cursor.execute("UPDATE pedidos SET finalizado = 1 WHERE numero_cliente = ? AND finalizado = 0", (numero_cliente,))
    conexao.commit()
    conexao.close()
    return {'message': f"Pedidos de {numero_cliente} finalizados com sucesso."}

def buscar_cardapio_admin():
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    cursor.execute("SELECT id, pedido, preco, categoria, descricao FROM cardapios")
    cardapio = cursor.fetchall()
    conexao.close()
    return [{"id": c[0], "pedido": c[1], "preco": float(c[2]), "categoria": c[3], "descricao": c[4]} for c in cardapio]

def atualizar_cardapio_admin(item_id, pedido, preco, descricao, categoria='Outros'):
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    try:
        cursor.execute("UPDATE cardapios SET pedido = ?, preco = ?, descricao = ?, categoria = ? WHERE id = ?", (pedido, preco, descricao, categoria, item_id))
        conexao.commit()
        return f"Item ID {item_id} atualizado para '{pedido}' com preço R${preco:.2f} e descrição '{descricao}' na categoria '{categoria}'."
    except sqlite3.IntegrityError:
        return f"Erro: Já existe um item com o nome '{pedido}'."
    finally:
        conexao.close()

def deletar_cardapio_admin(item_id):
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM cardapios WHERE id = ?", (item_id,))
    conexao.commit()
    conexao.close()
    return f"Item ID {item_id} deletado do cardápio."

def buscar_clientes_admin():
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    cursor.execute("SELECT id, numero_cliente, is_admin FROM clientes")
    clientes = cursor.fetchall()
    conexao.close()
    return [{"id": c[0], "numero_cliente": c[1], "is_admin": bool(c[2])} for c in clientes]

def buscar_cardapio_completo():
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()
    cursor.execute("SELECT categoria, pedido, preco, descricao FROM cardapios ORDER BY categoria, pedido")
    itens = cursor.fetchall()
    conexao.close()

    cardapio_organizado = {}
    for categoria, pedido, preco, descricao in itens:
        if categoria not in cardapio_organizado:
            cardapio_organizado[categoria] = []
        cardapio_organizado[categoria].append({'pedido': pedido, 'preco': float(preco), 'descricao': descricao})

    return cardapio_organizado