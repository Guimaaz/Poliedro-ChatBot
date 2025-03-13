import sqlite3

# conexão com o banco 
def CreateDatabase () :
    conexao = sqlite3.connect("chatbot.db")
    cursor = conexao.cursor()

    #criação da tabela
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_cliente TEXT NOT NULL UNIQUE,
        pedido TEXT NOT NULL,
        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    conexao.commit()
    conexao.close()

# Armazenar um pedido 
def PedidosArmazenados(numero_cliente, pedido) :
    conexao = sqlite3.connect("chatbot.db")
    cursor = conexao.cursor()
    cursor.execute("INSERT INTO pedidos (numero_cliente, pedido) VALUES (?,?)", (numero_cliente,pedido))
    conexao.commit()
    conexao.close()



#Procurar pedidos caso hajam

def BuscarPedidos(numerio_cliente) :
    conexao = sqlite3.connect("chatbot.db")
    cursor = conexao.cursor()
    cursor.execute("SELECT * FROM pedidos WHERE numero_cliente = ?", (numerio_cliente))
    pedidos = cursor.fetchall()
    conexao.close()
    return pedidos


CreateDatabase()
