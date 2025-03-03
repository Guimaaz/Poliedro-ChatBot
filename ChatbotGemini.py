import google.generativeai as genai
from prompts import prompt_restaurante, prompt_dos_Horarios, prompt_do_Cardapio

genai.configure(api_key="AIzaSyDhE12w58FQQQHr2jMHh1Jsl2ZmipQ65qA")


model = genai.GenerativeModel("gemini-1.5-flash")

def chatbot():
    print("Ola, tudo bem?, sou um chat bot especializado em atendimento do restaurante poliedro, em que posso te ajudar?.\n")

    chat_history = []


        # dentro de history, posso limitar tambem sem o prompt
    #  {"role": "system", "parts": [
    #         "Você é um assistente virtual para atendimento em um restaurante. Porem limitar com o prompt ele somenta sobre outros assuntos sem ser a mesma resposata de desculpa, alternando como ( n consigo falar sobre x assunto e etc) "
    #         "Responda apenas perguntas relacionadas ao cardápio, horários de funcionamento, pedidos e entregas. "
    #         "Se a pergunta for fora desse contexto, diga educadamente que só pode responder a questões sobre o restaurante."
    #     ]}

    while True:
        user_input = input("Você: ")

        if user_input.lower() == "sair":
            print(" Encerrando o chatbot. Até logo!")
            break

      
        chat_history.append({"role": "user", "parts": [user_input]})


        # --------------------------------------------Região de prompt------------------------------------------
        


        # response = model.generate_content(chat_history, stream=True) 
        response = model.generate_content([{"role": "user", "parts": [prompt_restaurante + prompt_dos_Horarios + prompt_do_Cardapio + user_input]}], stream=True)


        print("Bot:", end=" ")
        bot_reply = ""

       
        for chunk in response:
            print(chunk.text, end="", flush=True)
            bot_reply += chunk.text

        print("\n")

        
        chat_history.append({"role": "model", "parts": [bot_reply]})

chatbot()