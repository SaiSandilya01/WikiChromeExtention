import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [wikiUrl, setWikiUrl] = useState('');
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      setWikiUrl(tabs[0].url);
    });
  }, []);

  const sendQuestion = async () => {
    if (!question.trim()) return;
    setMessages((prev) => [...prev, { sender: 'You', text: question }]);

    const res = await fetch('http://localhost:8000/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ wiki_url: wikiUrl, question })
    });

    const data = await res.json();
    setMessages((prev) => [...prev, { sender: 'Bot', text: data.answer }]);
    setQuestion('');
  };

  return (
    <div className="App">
      <h3>Wiki Chat</h3>
      <div className="chat-box">
        {messages.map((msg, i) => (
          <div key={i} className={`msg ${msg.sender === 'You' ? 'user' : 'bot'}`}>
            <strong>{msg.sender}:</strong> {msg.text}
          </div>
        ))}
      </div>
      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask something..."
      />
      <button onClick={sendQuestion}>Send</button>
    </div>
  );
}

export default App;
