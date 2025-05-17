import axios from 'axios';

export const API_BASE_URL = 'http://192.168.15.6:5000';

export const sendMessage = async (messageData) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/chat`, messageData, {
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 8000,
    });   
    return response.data;
  } catch (error) {
    console.error('Erro na requisição:', {
      message: error.message,
      response: error.response?.data,
      code: error.code
    });

    let errorMessage = 'Erro de conexão';
    if (error.response) {
      errorMessage = error.response.data.resposta || 'Erro no servidor';
    } else if (error.request) {
      errorMessage = 'Servidor não respondeu';
    }

    return {
      resposta: `${errorMessage}\nVerifique:\n1. Servidor rodando\n2. IP correto\n3. Mesma rede`,
      error: true
    };
  }
};

export const testConnection = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/teste`, { timeout: 3000 });
    return { success: true, data: response.data };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      details: error.response?.data
    };
  }
};