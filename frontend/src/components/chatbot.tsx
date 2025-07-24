"use client";

import { useState, useRef, useEffect } from "react";
import { MessageCircle, Send, X, Bot, User } from "lucide-react";

export default function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<{ text: string; isUser: boolean }[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    
    // Add user message to chat
    setMessages((prev) => [...prev, { text: userMessage, isUser: true }]);
    setInput("");
    setIsLoading(true);

    try {
      // Send message to backend
      const res = await fetch("http://localhost:8000/crypto-assistant", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage }),
      });

      const data = await res.json();
      
      // Add AI response to chat
      setMessages((prev) => [...prev, { text: data.response, isUser: false }]);
    } catch (error) {
      setMessages((prev) => [...prev, { 
        text: "Sorry, I'm having trouble connecting. Please try again later.", 
        isUser: false 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {/* Toggle Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="flex items-center justify-center w-14 h-14 bg-gradient-to-r from-cyan-600 to-blue-700 rounded-full shadow-lg hover:from-cyan-700 hover:to-blue-800 transition-all transform hover:scale-105 active:scale-95"
        >
          <MessageCircle className="w-6 h-6 text-white" />
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className="w-80 h-[28rem] bg-gradient-to-br from-gray-800 to-gray-900 border border-cyan-500/30 shadow-2xl rounded-xl flex flex-col overflow-hidden backdrop-blur-sm">
          {/* Header */}
          <div className="bg-gradient-to-r from-cyan-700 to-blue-800 px-4 py-3 flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <Bot className="w-5 h-5 text-white" />
              <span className="text-white font-semibold">Crypto Assistant</span>
            </div>
            <button 
              onClick={() => setIsOpen(false)}
              className="text-white/80 hover:text-white transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          {/* Chat Messages */}
          <div className="flex-1 p-4 space-y-3 overflow-y-auto">
            {/* Welcome message */}
            {messages.length === 0 && (
              <div className="text-center py-8">
                <div className="flex justify-center mb-3">
                  <Bot className="w-10 h-10 text-cyan-400" />
                </div>
                <h3 className="text-lg font-semibold text-cyan-400 mb-1">Crypto Assistant</h3>
                <p className="text-gray-400 text-sm">
                  Ask me about cryptocurrency prices, trends, or market data!
                </p>
                <div className="mt-4 text-xs text-gray-500">
                  <p>Try: "What's the price of Bitcoin?"</p>
                  <p>Or: "Show me Ethereum market data"</p>
                </div>
              </div>
            )}
            
            {/* Messages */}
            {messages.map((msg, idx) => (
              <div 
                key={idx} 
                className={`flex ${msg.isUser ? "justify-end" : "justify-start"}`}
              >
                <div 
                  className={`max-w-[80%] rounded-xl p-3 ${
                    msg.isUser 
                      ? "bg-gradient-to-r from-cyan-600/30 to-blue-700/30 rounded-br-none" 
                      : "bg-gray-700/50 rounded-bl-none"
                  }`}
                >
                  <div className="flex items-start space-x-2">
                    {!msg.isUser && <Bot className="w-4 h-4 text-cyan-400 mt-0.5 flex-shrink-0" />}
                    <p className="text-white text-sm whitespace-pre-line">{msg.text}</p>
                    {msg.isUser && <User className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />}
                  </div>
                </div>
              </div>
            ))}
            
            {/* Loading indicator */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-700/50 rounded-xl rounded-bl-none p-3">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
                    <div className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce" style={{ animationDelay: "0.4s" }}></div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
          
          {/* Input Area */}
          <div className="p-3 border-t border-gray-700">
            <div className="flex items-center bg-gray-700/50 rounded-lg">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                className="flex-1 px-4 py-2 bg-transparent text-white placeholder-gray-400 outline-none"
                placeholder="Ask about crypto..."
                disabled={isLoading}
              />
              <button
                onClick={sendMessage}
                disabled={isLoading}
                className={`p-2 mr-1 rounded-full ${
                  isLoading 
                    ? "text-gray-500" 
                    : "text-cyan-400 hover:text-cyan-300"
                }`}
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
            <p className="text-xs text-gray-500 text-center mt-2">
              Powered by Crypto AI • Real-time data
            </p>
          </div>
        </div>
      )}
    </div>
  );
}