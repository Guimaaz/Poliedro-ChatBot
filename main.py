from server.BancoPedidos import CreateDatabase
from server.ChatbotGemini import iniciar_chat

if __name__ == "__main__":
    CreateDatabase() 
    iniciar_chat()      