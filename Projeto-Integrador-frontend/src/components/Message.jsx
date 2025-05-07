import React from 'react';

const Message = ({ sender, text, timestamp }) => {
  return (
    <div className={`message ${sender}`}>
      <div className="message-content">
        <p>{text}</p>
      </div>
    </div>
  );
};

export default Message;