import axios from 'axios';

<<<<<<< HEAD
export const API_BASE_URL = 'http://172.20.10.3:5000'; 
=======
export const API_BASE_URL = 'http://172.20.10.3:5000';
>>>>>>> 6705df68af461e8c9895021925ce4379ab68c5cb

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