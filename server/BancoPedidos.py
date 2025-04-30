import sqlite3
import re # comparação de palavras de intençao
import difflib # percentual de similaridade com o pedido no cardapio
from server.prompts import *

# Criação do banco de dados
def CreateDatabase():
    conexao = sqlite3.connect("chatbot.db")
    cursor = conexao.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_cliente TEXT NOT NULL,
        pedido TEXT NOT NULL,
        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

    conexao = sqlite3.connect("chatbot.db")
    cursor = conexao.cursor()
    cursor.execute("INSERT INTO pedidos (numero_cliente, pedido) VALUES (?, ?)", (numero_cliente, pedido))  # Alterado para "pedidos"

    conexao.commit()
    conexao.close()
    print("Pedido registrado com sucesso!")


# Buscar pedidos no banco de dados
def BuscarPedidos(numero_cliente):
    conexao = sqlite3.connect("chatbot.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT pedido, datetime(data, '-3 hours') FROM pedidos WHERE numero_cliente = ?", (numero_cliente,))
    pedidos = cursor.fetchall()
    conexao.close()

    if not pedidos:
        return "Nenhum pedido encontrado para esse número."

    return "\n".join([f"Pedido: {p[0]} - Data: {p[1]}" for p in pedidos])


def VerificarItensCardapio(pedido):
    pedido = pedido.lower()
    if pedido in itensCardapio:
        return pedido, True  

    prato_sugerido = difflib.get_close_matches(pedido, itensCardapio, n=1, cutoff=0.6)
    if prato_sugerido:
        return prato_sugerido[0], False  

    return None, False  



CreateDatabase()


