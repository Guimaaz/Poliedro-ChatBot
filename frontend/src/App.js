import React, { useState } from 'react';
import ChatWindow from './components/ChatWindow';
import './styles.css';

function App() {
  const [messages, setMessages] = useState([
    {
      sender: 'bot',
      text: 'Olá, sou o atendente do Poliedro Pizzaria, como posso te ajudar hoje?',
      timestamp: new Date()
    }
  ]);

  const handleSendMessage = (message) => {
    const newMessage = {
      sender: 'user',
      text: message,
      timestamp: new Date()
    };
    
    setMessages([...messages, newMessage]);
    
    // Aqui você pode adicionar a lógica para enviar a mensagem para o backend
  };

  return (
    <div className="app">
      <h1 className="header">Poliedro Projeto</h1>
      <div className="subheader">
        <h2>Poliedro</h2>
        <span>•</span>
        <p>Educação</p>
      </div>
      <ChatWindow messages={messages} onSendMessage={handleSendMessage} />
    </div>
  );
}

export default App;