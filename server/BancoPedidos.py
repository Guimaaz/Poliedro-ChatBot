import sqlite3
import re  # comparação de palavras de intenção
import difflib  # percentual de similaridade com o pedido no cardápio
from server.prompts import *


def CreateDatabase():
    conexao = sqlite3.connect("chatbot.db")
    cursor = conexao.cursor()

   # Tabela de Clientes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_cliente TEXT NOT NULL UNIQUE
)
''')

# Tabela de Cardápios
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cardapios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido TEXT NOT NULL,
    preco DECIMAL(10, 2) NOT NULL
)
''')

# Tabela de Pedidos
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


    conexao.commit()
    conexao.close()



def validar_numero(numero_cliente):
    padrao = r"\(\d{2}\) \d{5}-\d{4}"
    return re.match(padrao, numero_cliente)


def PedidosArmazenados(numero_cliente, pedido):
    if not validar_numero(numero_cliente):
        print("Número inválido! Use o formato (XX) XXXXX-XXXX.")
        return

    # Verificar se o cliente já existe na tabela
    conexao = sqlite3.connect("chatbot.db")
    cursor = conexao.cursor()

    cursor.execute("SELECT id FROM clientes WHERE numero_cliente = ?", (numero_cliente,))
    cliente = cursor.fetchone()

    # Caso o cliente não exista, criamos um novo
    if not cliente:
        cursor.execute("INSERT INTO clientes (numero_cliente) VALUES (?)", (numero_cliente,))
        conexao.commit()

    # Verificar se o pedido já existe
    cursor.execute("SELECT id, pedido, preco FROM cardapios WHERE pedido = ?", (pedido,))
    item = cursor.fetchone()

   
    if not item:
        for p, preco in itensCardapio:
            if p == pedido:
                cursor.execute("INSERT INTO cardapios (pedido, preco) VALUES (?, ?)", (pedido, preco))
                conexao.commit()
                cursor.execute("SELECT id, pedido, preco FROM cardapios WHERE pedido = ?", (pedido,))
                item = cursor.fetchone()
                break

   
    cursor.execute("INSERT INTO pedidos (numero_cliente, item, item_id, preco) VALUES (?, ?, ?, ?)", 
                   (numero_cliente, item[1], item[0], item[2]))

    conexao.commit()
    conexao.close()
    print("Pedido registrado com sucesso!")


def BuscarPedidos(numero_cliente):
    conexao = sqlite3.connect("chatbot.db")
    cursor = conexao.cursor()

    cursor.execute("SELECT id FROM clientes WHERE numero_cliente = ?", (numero_cliente,))
    cliente = cursor.fetchone()

    if not cliente:
        conexao.close()
        return "Cliente não encontrado."

    cursor.execute(''' 
        SELECT item, item_id, preco, datetime(data, '-3 hours') 
        FROM pedidos 
        WHERE numero_cliente = ? 
    ''', (numero_cliente,))

    pedidos = cursor.fetchall()
    conexao.close()

    if not pedidos:
        return "Nenhum pedido encontrado para esse número."

    return "\n".join([f"Pedido: {p[0]} (ID: {p[1]}) - Preço: R${p[2]:.2f} - Data: {p[3]}" for p in pedidos])

# Função para verificar itens do cardápio
def VerificarItensCardapio(pedido):
    pedido = pedido.lower()

    if pedido in [item[0] for item in itensCardapio]:
        return pedido, True

    prato_sugerido = difflib.get_close_matches(pedido, [item[0] for item in itensCardapio], n=1, cutoff=0.6)
    if prato_sugerido:
        return prato_sugerido[0], False

    return None, False

CreateDatabase()