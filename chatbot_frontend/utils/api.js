
import axios from 'axios';

const API_URL = 'http://192.168.15.13:5000/chat';  // Altere para o IP da sua máquina

export const sendMessage = async (messageData) => {
  try {
    const response = await axios.post(API_URL, { messageData }, {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 5000,
      });
      return response.data;
    } catch (error) {
      console.error('Erro detalhado:', error);
      return { resposta: 'Erro de conexão. Verifique:\n1. Se o servidor está rodando\n2. Se o IP está correto\n3. Sua conexão com a rede' };
  }
};


