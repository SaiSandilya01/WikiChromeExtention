import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './App.css';

function App() {
  const [url, setUrl] = useState('');
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    // Get active tab URL
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs.length > 0) {
        setUrl(tabs[0].url);
      }
    });
  }, []);

  const sendQuestion = async () => {
    if (!question.trim()) return;

    // Show user's message
    setMessages((prev) => [...prev, { sender: 'You', text: question }]);

    try {
      const res = await fetch('http://localhost:8000/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, question })
      });

      const data = await res.json();

      if (res.ok) {
        setMessages((prev) => [...prev, { sender: 'Bot', text: data.answer }]);
      } else {
        setMessages((prev) => [...prev, { sender: 'Bot', text: `Error: ${data.detail || 'Something went wrong'}` }]);
      }
    } catch (err) {
      setMessages((prev) => [...prev, { sender: 'Bot', text: `Request failed: ${err.message}` }]);
    }

    setQuestion('');
  };

  return (
    <div className="App">
      <h3>Webpage Q&A</h3>
      <div className="chat-box">
        {messages.map((msg, i) => (
          <div key={i} className={`msg ${msg.sender === 'You' ? 'user' : 'bot'}`}>
            <strong>{msg.sender}:</strong> 
            <ReactMarkdown>{msg.text}</ReactMarkdown>
          </div>
        ))}
      </div>
      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask something about this page..."
      />
      <button onClick={sendQuestion}>Send</button>
    </div>
  );
}

export default App;
