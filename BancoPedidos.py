import sqlite3

# conexão com o banco 
def CreateDatabase () :
    conexao = sqlite3.connect("chatbot.db")
    cursor = conexao.cursor()

    #criação da tabela
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

def PedidosArmazenados(numero_cliente, pedido):
    print(f"Armazenando pedido: {pedido} para {numero_cliente}")
    conexao = sqlite3.connect("chatbot.db")
    cursor = conexao.cursor()
    cursor.execute("INSERT INTO pedidos (numero_cliente, pedido) VALUES (?,?)", (numero_cliente, pedido))
    conexao.commit()
    conexao.close()

def BuscarPedidos(numero_cliente):
    print(f"Buscando pedidos para: {numero_cliente}")
    conexao = sqlite3.connect("chatbot.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM pedidos WHERE numero_cliente = ?", (numero_cliente,))
    pedidos = cursor.fetchall()
    conexao.close()
    print(f"Pedidos encontrados: {pedidos}")
    return pedidos



CreateDatabase()
