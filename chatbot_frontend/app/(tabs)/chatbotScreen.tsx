import React, { useState, useRef } from "react";
import { View, Text, TextInput, TouchableOpacity, FlatList, StyleSheet, SafeAreaView, useWindowDimensions, Keyboard } from 'react-native';
import axios from 'axios';

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

const API_URL = 'http://192.168.15.13:5000/chat';

export default function ChatScreen() {
  const { width } = useWindowDimensions();
  const containerWidth = width < 600 ? width * 0.9 : 1000;
  const flatListRef = useRef<FlatList>(null);

  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [contexto, setContexto] = useState<Contexto>({});
  const [inputPlaceholder, setInputPlaceholder] = useState('Digite sua mensagem...');

  const enviarMensagem = async (mensagem: string) => {
    try {
      const dataToSend = {
        mensagem,
        ...contexto,
        ...(contexto.esperando === 'confirmacao' && { confirmacao: mensagem.toLowerCase() }),
        ...(contexto.esperando === 'pedido' && { pedido: mensagem }),
        ...(contexto.esperando === 'pedido_remocao' && { pedido: mensagem })
      };

      const response = await axios.post(API_URL, dataToSend);
      return response.data;
    } catch (error) {
      console.error('Erro ao enviar mensagem:', error);
      return { resposta: 'Erro ao conectar com o servidor.' };
    }
  };

  const handleSend = async () => {
    if (!inputText.trim()) return;

    Keyboard.dismiss();
    
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
    const botMessage: Message = { 
      id: (Date.now() + 1).toString(), 
      text: respostaApi.resposta, 
      sender: 'bot' 
    };
    setMessages(prev => [...prev, botMessage]);

    // Atualiza contexto e placeholder
    atualizarContexto(respostaApi);
    
    // Rola para a última mensagem
    setTimeout(() => {
      flatListRef.current?.scrollToEnd({ animated: true });
    }, 100);
  };

  const atualizarContexto = (respostaApi: any) => {
    const novoContexto = respostaApi.contexto || {};
    setContexto(novoContexto);

    // Atualiza placeholder baseado no contexto
    if (novoContexto.esperando === 'numero') {
      setInputPlaceholder('Digite seu número (XX) XXXXX-XXXX');
    } else if (novoContexto.esperando === 'pedido') {
      setInputPlaceholder('Qual é o seu pedido?');
    } else if (novoContexto.esperando === 'confirmacao') {
      setInputPlaceholder('Digite "sim" ou "não"');
    } else if (novoContexto.esperando === 'pedido_remocao') {
      setInputPlaceholder('Qual pedido deseja remover?');
    } else {
      setInputPlaceholder('Digite sua mensagem...');
    }
  };

  const renderMessage = ({ item }: { item: Message }) => (
    <View style={[
      styles.messageBubble, 
      item.sender === 'user' ? styles.userBubble : styles.botBubble
    ]}>
      <Text style={styles.messageText}>{item.text}</Text>
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
          onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        />

        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            placeholder={inputPlaceholder}
            value={inputText}
            onChangeText={setInputText}
            onSubmitEditing={handleSend}
            multiline
          />
          <TouchableOpacity onPress={handleSend} style={styles.sendButton}>
            <Text style={styles.sendButtonText}>Enviar</Text>
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
  },
  chatContainer: {
    padding: 20,
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 15,
    borderRadius: 20,
    marginVertical: 8,
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: '#465575',
    borderBottomRightRadius: 5,
  },
  botBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#fff',
    borderBottomLeftRadius: 5,
  },
  messageText: {
    fontSize: 16,
    color: '#000',
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 15,
    borderTopWidth: 1,
    borderColor: '#ccc',
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
  },
  sendButton: {
    backgroundColor: '#465575',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 25,
  },
  sendButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
});