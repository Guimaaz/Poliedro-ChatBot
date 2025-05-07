import React from 'react';
import Message from './Message';
import InputArea from './InputArea';

const ChatWindow = ({ messages, onSendMessage }) => {
  return (
    <div className="chat-container">
      <div className="messages-container">
        {messages.map((message, index) => (
          <Message 
            key={index}
            sender={message.sender}
            text={message.text}
            timestamp={message.timestamp}
          />
        ))}
      </div>
      <div className="divider"></div>
      <InputArea onSendMessage={onSendMessage} />
    </div>
  );
};

export default ChatWindow;