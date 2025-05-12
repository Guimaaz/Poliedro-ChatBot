from server.ChatbotGemini import model, extrair_intencao
from server.BancoPedidos import *
from server.prompts import *

class ChatSession:
    def __init__(self):
        self.etapa = "inicio"
        self.intencao = None
        self.telefone = None
        self.pedido = None

    def processar_mensagem(self, mensagem):
        if self.etapa == "inicio":
            prompt_completo = (
                prompt_restaurante + prompt_dos_Horarios + prompt_do_Cardapio +
                prompt_do_preco + prompt_intencao +
                "\n\nBaseado na conversa acima, identifique a intenção do usuário.\n"
                "Se o usuário deseja fazer um pedido, responda com: **INTENÇÃO: FAZER_PEDIDO**\n"
                "Se o usuário deseja consultar um pedido, responda com: **INTENÇÃO: CONSULTAR_PEDIDO**\n"
                "Se o usuário deseja remover um pedido, responda com: **INTENÇÃO: REMOVER_PEDIDO**\n"
                "Caso contrário, responda normalmente de forma amigável e interativa, sem mencionar a intenção."
            )
            response = model.generate_content([
                {"role": "user", "parts": [prompt_completo + mensagem]}
            ])
            bot_reply = response.text.strip()
            self.intencao = extrair_intencao(bot_reply)

            if self.intencao == "FAZER_PEDIDO":
                self.etapa = "aguardando_telefone"
                return "Claro! Qual o número de telefone para registrar o pedido?"
            elif self.intencao == "CONSULTAR_PEDIDO":
                self.etapa = "consultar_telefone"
                return "Certo! Informe seu número de telefone para consultar o pedido."
            elif self.intencao == "REMOVER_PEDIDO":
                self.etapa = "remover_telefone"
                return "Tudo bem! Qual o número de telefone para localizar o pedido a remover?"
            else:
                return bot_reply

        elif self.etapa == "aguardando_telefone":
            if not validar_numero(mensagem):
                return "Número inválido. Envie no formato (XX) XXXXX-XXXX."
            self.telefone = mensagem
            self.etapa = "aguardando_pedido"
            return "Perfeito! Agora me diga o que deseja pedir."

        elif self.etapa == "aguardando_pedido":
            item, exato = VerificarItensCardapio(mensagem)
            if item:
                if exato:
                    PedidosArmazenados(self.telefone, item)
                    self.etapa = "concluido"
                    return f"Pedido de '{item}' realizado com sucesso!"
                else:
                    self.pedido = item
                    self.etapa = "confirmar_pedido"
                    return f"Você quis dizer '{item}'? Responda com sim ou não."
            else:
                return "Item não encontrado no cardápio. Tente outro prato."

        elif self.etapa == "confirmar_pedido":
            if mensagem.lower() == "sim":
                PedidosArmazenados(self.telefone, self.pedido)
                self.etapa = "concluido"
                return f"Pedido de '{self.pedido}' confirmado e registrado!"
            else:
                self.etapa = "aguardando_pedido"
                return "Tudo bem. Qual o item deseja pedir?"

        elif self.etapa == "consultar_telefone":
            if not validar_numero(mensagem):
                return "Número inválido. Tente novamente."
            return BuscarPedidos(mensagem)

        elif self.etapa == "remover_telefone":
            if not validar_numero(mensagem):
                return "Número inválido. Tente novamente."
            pedidos = BuscarPedidos(mensagem)
            if "nenhum pedido" in pedidos.lower():
                return "Nenhum pedido encontrado para esse número."
            self.telefone = mensagem
            self.etapa = "remover_item"
            return f"Aqui estão seus pedidos:\n{pedidos}\nQual deseja remover?"

        elif self.etapa == "remover_item":
            resultado = removerPedidos(self.telefone, mensagem)
            self.etapa = "concluido"
            return resultado

        return "Desculpe, não entendi. Pode repetir?"

