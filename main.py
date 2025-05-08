from server.BancoPedidos import CreateDatabase
from server.ChatbotGemini import iniciar_chat

import time
import os


def animacao_terminal(nome) :
    os.system('cls'  if os.name =='nt' else 'clear')
    for letra in nome :
        print(letra,end='',flush=True)
        time.sleep(0.1) # espaço tempo entre as letras
    print("\n")
    time.sleep(1)
    

animacao_terminal("iniciando prompt version 1")

if __name__ == "__main__":
    CreateDatabase() 
    iniciar_chat()      