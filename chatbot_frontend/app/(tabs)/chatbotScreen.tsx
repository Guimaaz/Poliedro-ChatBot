import React, { useState, useRef, useEffect } from "react";
import { View, Text, TextInput, TouchableOpacity, FlatList, StyleSheet, SafeAreaView, useWindowDimensions, Keyboard, Alert } from 'react-native';
import { sendMessage, testConnection } from '../../utils/api';

type Message = {
  id: string;
  text: string;
  sender: 'user' | 'bot';
};

type Contexto = {
  numero_cliente?: string;
  esperando?: 'numero' | 'pedido' | 'confirmacao' | 'pedido_remocao';
  item_sugerido?: string;
  pedidos_atuais?: string;
};

export default function ChatScreen() {
  const { width } = useWindowDimensions();
  const containerWidth = width < 600 ? width * 0.9 : 1000;
  const flatListRef = useRef<FlatList>(null);

  const [messages, setMessages] = useState<Message[]>([
    { id: '1', text: 'Olá! Sou o assistente do restaurante. Como posso ajudar?', sender: 'bot' }
  ]);
  const [inputText, setInputText] = useState('');
  const [contexto, setContexto] = useState<Contexto>({});
  const [inputPlaceholder, setInputPlaceholder] = useState('Digite sua mensagem...');
  const [isLoading, setIsLoading] = useState(false);



  const addBotMessage = (text: string) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      text,
      sender: 'bot'
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const enviarMensagem = async (mensagem: string) => {
    try {
      const payload = {
        mensagem,
        ...contexto,
        ...(contexto.esperando === 'confirmacao' && { 
          confirmacao: mensagem.toLowerCase(),
          item_sugerido: contexto.item_sugerido 
        }),
        ...(contexto.esperando === 'pedido' && { pedido: mensagem }),
        ...(contexto.esperando === 'pedido_remocao' && { 
          pedido: mensagem,
          pedidos_atuais: contexto.pedidos_atuais 
        })
      };

      console.log('Enviando para API:', payload);
      const response = await sendMessage(payload);
      console.log('Resposta da API:', response);
      
      return response;

    } catch (error) {
      console.error('Erro ao enviar:', error);
      return { resposta: 'Erro ao processar requisição', error: true };
    }
  };

  const handleSend = async () => {
    if (!inputText.trim() || isLoading) return;

    Keyboard.dismiss();
    setIsLoading(true);
    
    // Adiciona mensagem do usuário
    const userMessage: Message = { 
      id: Date.now().toString(), 
      text: inputText, 
      sender: 'user' 
    };
    setMessages(prev => [...prev, userMessage]);
    setInputText('');

    // Processa a resposta da API
    const respostaApi = await enviarMensagem(inputText);
    
    // Adiciona resposta do bot
    if (respostaApi.error) {
      addBotMessage(respostaApi.resposta);
    } else {
      addBotMessage(respostaApi.resposta);
      // Atualiza contexto se necessário
      if (respostaApi.contexto) {
        setContexto(respostaApi.contexto);
        updatePlaceholder(respostaApi.contexto);
      } else {
        setContexto({});
        setInputPlaceholder('Digite sua mensagem...');
      }
    }

    setIsLoading(false);
    scrollToBottom();
  };

  const updatePlaceholder = (ctx: Contexto) => {
    if (ctx.esperando === 'numero') {
      setInputPlaceholder('Digite seu número (XX) XXXXX-XXXX');
    } else if (ctx.esperando === 'pedido') {
      setInputPlaceholder('Qual é o seu pedido?');
    } else if (ctx.esperando === 'confirmacao') {
      setInputPlaceholder('Responda "sim" ou "não"');
    } else if (ctx.esperando === 'pedido_remocao') {
      setInputPlaceholder('Qual pedido deseja remover?');
    } else {
      setInputPlaceholder('Digite sua mensagem...');
    }
  };

  const scrollToBottom = () => {
    setTimeout(() => {
      flatListRef.current?.scrollToEnd({ animated: true });
    }, 100);
  };

  const renderMessage = ({ item }: { item: Message }) => (
    <View style={[
      styles.messageBubble, 
      item.sender === 'user' ? styles.userBubble : styles.botBubble
    ]}>
      <Text style={styles.MessageText}>{item.text}</Text>
    </View>
  );

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={[styles.container, { width: containerWidth }]}>
        <FlatList
          ref={flatListRef}
          data={messages}
          keyExtractor={(item) => item.id}
          renderItem={renderMessage}
          contentContainerStyle={styles.chatContainer}
          onContentSizeChange={scrollToBottom}
          onLayout={scrollToBottom}
        />
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            placeholder={inputPlaceholder}
            value={inputText}
            onChangeText={setInputText}
            onSubmitEditing={handleSend}
            editable={!isLoading}
            placeholderTextColor="#999"
          />
          <TouchableOpacity 
            onPress={handleSend} 
            style={[styles.sendButton, isLoading && styles.disabledButton]}
            disabled={isLoading}
          >
            <Text style={styles.sendButtonText}>
              {isLoading ? '...' : 'Enviar'}

            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#4B3D3D',
  },
  container: {
    flex: 1,
    backgroundColor: '#bfb493',
    borderRadius: 30,
    margin: 20,
    alignSelf: 'center',
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3.84,
    elevation: 5,
  },
  chatContainer: {
    padding: 20,
    paddingBottom: 10,
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 15,
    borderRadius: 20,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 2,
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: '#f7e223',
    borderBottomRightRadius: 5,
  },
  botBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#fff',
    borderBottomLeftRadius: 5,
  },
  MessageText: {
    fontSize: 16,
    color: '#000',
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 15,
    borderTopWidth: 1,
    borderColor: '#ddd',
    backgroundColor: '#fff',
    alignItems: 'center',
  },
  input: {
    flex: 1,
    minHeight: 50,
    maxHeight: 100,
    paddingHorizontal: 15,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 25,
    marginRight: 10,
    paddingVertical: 12,
    backgroundColor: '#fff',
  },
  sendButton: {
    backgroundColor: '#5497f0',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 25,
  },
  disabledButton: {
    backgroundColor: '#aaa',
  },
  sendButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
});