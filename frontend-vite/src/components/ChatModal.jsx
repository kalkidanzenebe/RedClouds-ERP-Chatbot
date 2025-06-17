import React, { useState, useEffect, useRef, useCallback } from "react";
import { Menu, X, Info } from "lucide-react";
import { v4 as uuidv4 } from "uuid";
import Sidebar from "./Sidebar";
import ChatWindow from "./ChatWindow";
import ChatInput from "./ChatInput";

const API_BASE_URL = "http://127.0.0.1:8000";

const getOrCreateUserId = () => {
  let userId = localStorage.getItem("redclouds_user_id");
  if (!userId) {
    userId = `user_${uuidv4()}`;
    localStorage.setItem("redclouds_user_id", userId);
  }
  return userId;
};

function ChatModal({ onClose }) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [userId, setUserId] = useState("");
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const chatWindowRef = useRef(null);

  useEffect(() => {
    const id = getOrCreateUserId();
    setUserId(id);
  }, []);

  useEffect(() => {
    if (userId) {
      fetchConversations();
    }
  }, [userId]);

  useEffect(() => {
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  const fetchConversations = useCallback(async () => {
    setError(null);
    setIsLoading(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/user_conversations/${userId}`
      );
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setConversations(data.conversations || []);
    } catch (e) {
      console.error("Failed to fetch conversations:", e);
      if (conversations.length === 0) {
        setError("Failed to load conversation history. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  }, [userId, conversations.length]);

  const fetchChatHistory = useCallback(async (convId) => {
    if (!convId) return;
    setIsLoading(true);
    setMessages([]);
    setError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/conversation/${convId}`);
      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();

      const formattedMessages = (data.messages || []).flatMap((msg) => [
        {
          type: "user",
          text: msg.question,
          timestamp: new Date(msg.timestamp),
        },
        {
          type: "bot",
          text: msg.response,
          sources: msg.sources || [],
          suggested_questions: msg.suggested_questions || [],
          timestamp: new Date(msg.timestamp),
        },
      ]);

      setMessages(formattedMessages);
      setCurrentConversationId(convId);
    } catch (e) {
      console.error("Failed to fetch chat history:", e);
      setError("Failed to load chat history. Starting new conversation.");
      handleNewChat();
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleSendMessage = async (text) => {
    if (!text.trim()) return;

    const newUserMessage = { type: "user", text, timestamp: new Date() };
    setMessages((prev) => [...prev, newUserMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: text,
          user_id: userId,
          conversation_id: currentConversationId,
        }),
      });

      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);

      const data = await response.json();
      const newBotMessage = {
        type: "bot",
        text: data.response,
        sources: data.sources || [],
        suggested_questions: data.suggested_questions || [],
        timestamp: new Date(data.timestamp),
      };

      setMessages((prev) => [...prev, newBotMessage]);
      setCurrentConversationId(data.conversation_id);
      fetchConversations();
    } catch (e) {
      console.error("Failed to send message:", e);
      setError("Failed to get response. Please try again.");
      setMessages((prev) => [
        ...prev,
        {
          type: "bot",
          text: "Sorry, I couldn't connect to the assistant. Please try again later.",
          timestamp: new Date(),
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    setCurrentConversationId(null);
    setMessages([]);
    fetchConversations();
    setIsSidebarOpen(false);
    setError(null);
  };

  const handleConversationSelect = (convId) => {
    setCurrentConversationId(convId);
    fetchChatHistory(convId);
    setIsSidebarOpen(false);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-85 flex items-start justify-end p-4 z-50 font-inter">
      <div className="relative bg-gray-900 rounded-2xl shadow-2xl flex w-full max-w-md lg:max-w-xl h-full max-h-[95vh] overflow-hidden">
        <Sidebar
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
          conversations={conversations}
          onNewChat={handleNewChat}
          onConversationSelect={handleConversationSelect}
          currentConversationId={currentConversationId}
        />

        <div
          // Changed ml-64/ml-0 to md:ml-64/md:ml-0 so it only applies on medium screens and larger
          className={`flex flex-col flex-1 bg-gray-950 ${
            isSidebarOpen ? "md:ml-0" : "md:ml-0"
          }`}
        >
          <div className="flex items-center justify-between p-4 bg-gradient-to-r from-gray-800 to-gray-950 text-cyan-400 shadow-md">
            {!isSidebarOpen ? (
              <button
                onClick={() => setIsSidebarOpen(true)}
                className="p-2 rounded-full hover:bg-white hover:bg-opacity-10 focus:outline-none focus:ring-2 focus:ring-cyan-400 transition"
                aria-label="Open sidebar"
              >
                <Menu size={24} />
              </button>
            ) : (
              <div className="w-10"></div>
            )}
            <h2 className="text-2xl font-bold tracking-tight">
              RedClouds AI Assistant
            </h2>
            <div className="w-10"></div>
          </div>

          <div
            ref={chatWindowRef}
            className="flex-1 p-6 overflow-y-auto custom-scrollbar"
          >
            {error && (
              <div className="bg-red-700 bg-opacity-70 border border-red-500 text-white px-4 py-3 rounded-lg mb-4">
                <strong>Error:</strong> {error}
              </div>
            )}
            <ChatWindow
              messages={messages}
              isLoading={isLoading}
              onSendMessage={handleSendMessage}
            />
          </div>
          <div className="p-4 bg-gray-900 border-t border-gray-800">
            <ChatInput
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default ChatModal;
