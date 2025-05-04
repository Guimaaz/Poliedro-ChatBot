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
        pedido TEXT NOT NULL
    )
    ''')

    # Tabela de Pedidos
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_cliente TEXT NOT NULL,
        item TEXT NOT NULL,
        item_id INTEGER NOT NULL,
        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (numero_cliente) REFERENCES clientes (numero_cliente),
        FOREIGN KEY (item_id) REFERENCES cardapios (id),
        FOREIGN KEY (item) REFERENCES cardapios (pedido)
    )
    ''')

    conexao.commit()
    conexao.close()


# Validação do número de telefone
def validar_numero(numero_cliente):
    padrao = r"\(\d{2}\) \d{5}-\d{4}"
    return re.match(padrao, numero_cliente)


# Armazenar pedido no banco de dados
def PedidosArmazenados(numero_cliente, pedido):
    if not validar_numero(numero_cliente):
        print("Número inválido! Use o formato (XX) XXXXX-XXXX.")
        return

    # Verificar se o cliente já existe na tabela para fins de evitar repeticao
    conexao = sqlite3.connect("chatbot.db")
    cursor = conexao.cursor()

    cursor.execute("SELECT id FROM clientes WHERE numero_cliente = ?", (numero_cliente,))
    cliente = cursor.fetchone()

    # caso nao exista a gnt cria
    if not cliente:
        cursor.execute("INSERT INTO clientes (numero_cliente) VALUES (?)", (numero_cliente,))
        conexao.commit()

    # Ver se o pedido ja existe
    cursor.execute("SELECT id, pedido FROM cardapios WHERE pedido = ?", (pedido,))
    item = cursor.fetchone()

    # caso contrairo a gnt cria
    if not item:
        cursor.execute("INSERT INTO cardapios (pedido) VALUES (?)", (pedido,))
        conexao.commit()
        cursor.execute("SELECT id, pedido FROM cardapios WHERE pedido = ?", (pedido,))
        item = cursor.fetchone()

    # inserir o pedido na tebela, para consultar dps
    cursor.execute("INSERT INTO pedidos (numero_cliente, item, item_id) VALUES (?, ?, ?)", (numero_cliente, item[1], item[0]))

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

   
    cursor.execute(''' SELECT item, item_id, datetime(data, '-3 hours') FROM pedidos WHERE numero_cliente = ? ''', (numero_cliente,))
    
    pedidos = cursor.fetchall()
    conexao.close()

    if not pedidos:
        return "Nenhum pedido encontrado para esse número."

    return "\n".join([f"Pedido: {p[0]} (ID: {p[1]}) - Data: {p[2]}" for p in pedidos])



def VerificarItensCardapio(pedido):
    pedido = pedido.lower()

   
    if pedido in itensCardapio:
        return pedido, True

    # erro de escrita do pedido
    prato_sugerido = difflib.get_close_matches(pedido, itensCardapio, n=1, cutoff=0.6)
    if prato_sugerido:
        return prato_sugerido[0], False

    return None, False


CreateDatabase()
