import sqlite3
import re
import difflib
from server.prompts import *
from server.cardapio import itensCardapio
import hashlib

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
    senha TEXT NOT NULL
)
''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cardapios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido TEXT NOT NULL UNIQUE,
    preco DECIMAL(10, 2) NOT NULL
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
    FOREIGN KEY (numero_cliente) REFERENCES clientes (numero_cliente),
    FOREIGN KEY (item_id) REFERENCES cardapios (id)
)
''')

    # Inserir itens do cardápio se não existirem
    for pedido, preco in itensCardapio:
        try:
            cursor.execute("INSERT INTO cardapios (pedido, preco) VALUES (?, ?)", (pedido, preco))
        except sqlite3.IntegrityError:
            pass # Item já existe

    # usuários teste chumbados
    numero_teste = "(11) 99999-1111"
    numero_teste2 = "(11) 97430-6792"
    numero_teste3 = "(11) 98765-4321"
    senha_teste_plana = "senha123"
    senha_teste_plana2 = "Nhe45657"
    senha_teste_plana3 = "senha123"
    senha_teste_hash = hash_senha(senha_teste_plana)
    senha_teste_hash2 = hash_senha(senha_teste_plana2)
    senha_teste_hash3 = hash_senha(senha_teste_plana3)

    try:
      
        cursor.execute("INSERT INTO clientes (numero_cliente, senha) VALUES (?, ?)", (numero_teste2, senha_teste_hash2))
        cursor.execute("INSERT INTO clientes (numero_cliente, senha) VALUES (?, ?)", (numero_teste, senha_teste_hash))
        cursor.execute("INSERT INTO clientes (numero_cliente, senha) VALUES (?, ?)", (numero_teste3, senha_teste_hash3))
        conexao.commit()
    except sqlite3.IntegrityError:
        print(f"Usuário de teste com número {numero_teste} já existe.")

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
    cursor.execute("SELECT senha FROM clientes WHERE numero_cliente = ?", (numero_cliente,))
    resultado = cursor.fetchone()
    print(f"Resultado da busca no banco: {resultado}")
    conexao.close()

    if resultado:
        senha_hash_db = resultado[0]
        senha_correta = verificar_senha(senha, senha_hash_db)
        print(f"Senha digitada hash: {hash_senha(senha)}")
        print(f"Senha do banco hash: {senha_hash_db}")
        print(f"Senha correta: {senha_correta}")
        return senha_correta
    return False

def PedidosArmazenados(numero_cliente, pedido):
    conexao = sqlite3.connect(DATABASE_NAME)
    cursor = conexao.cursor()

    cursor.execute("SELECT id FROM clientes WHERE numero_cliente = ?", (numero_cliente,))
    cliente = cursor.fetchone()

    if not cliente:
        conexao.close()
        return "Cliente não encontrado. Por favor, faça login novamente."

    cursor.execute("SELECT id, pedido, preco FROM cardapios WHERE pedido = ?", (pedido,))
    item = cursor.fetchone()

    if not item:
        for p, preco in itensCardapio:
            if p.lower() == pedido.lower():
                cursor.execute("INSERT OR IGNORE INTO cardapios (pedido, preco) VALUES (?, ?)", (p, preco))
                conexao.commit()
                cursor.execute("SELECT id, pedido, preco FROM cardapios WHERE pedido = ?", (p,))
                item = cursor.fetchone()
                break
        if not item:
            conexao.close()
            return "Item não encontrado no cardápio."

    cursor.execute("INSERT INTO pedidos (numero_cliente, item, item_id, preco) VALUES (?, ?, ?, ?)",
                    (numero_cliente, item[1], item[0], item[2]))

    conexao.commit()
    conexao.close()
    return "Pedido registrado com sucesso!"

def removerPedidos(numero_cliente, pedido):
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

    for item in itensCardapio:
        if item[0].lower() == pedido:
            return item[0], True

    prato_sugerido = difflib.get_close_matches(pedido, [item[0].lower() for item in itensCardapio], n=1, cutoff=0.6)
    if prato_sugerido:
        # Retorna o nome original do cardápio
        for item in itensCardapio:
            if item[0].lower() == prato_sugerido[0]:
                return item[0], False

    return None, False

# Garante que o banco e o cardápio sejam criados na inicialização do módulo
CreateDatabase()