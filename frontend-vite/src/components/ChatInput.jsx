import React, { useState } from "react";
import { Send } from "lucide-react"; // Import Send icon

function ChatInput({ onSendMessage, isLoading }) {
  const [inputText, setInputText] = useState("");
  const inputId = "chat-input-field"; // Define a unique ID for the input

  const handleSubmit = (e) => {
    e.preventDefault();
    onSendMessage(inputText);
    setInputText("");
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2">
      {/* Added a label for accessibility */}
      <label htmlFor={inputId} className="sr-only">
        Type your message
      </label>
      <input
        type="text"
        id={inputId}
        value={inputText}
        onChange={(e) =>
          e.target.value.length <= 500 && setInputText(e.target.value)
        }
        placeholder="Type your message..."
        // Border and focus ring use header color (cyan)
        className="flex-1 p-3 border border-cyan-800 bg-gray-800 text-gray-100 rounded-xl focus:outline-none focus:ring-2 focus:ring-cyan-600 transition shadow-sm"
        disabled={isLoading}
        maxLength={500}
      />
      <button
        type="submit"
        // Send button uses header color (cyan)
        className="p-3 bg-cyan-800 hover:bg-cyan-900 text-white rounded-xl shadow-md transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-cyan-600"
        disabled={isLoading || !inputText.trim()}
        aria-label="Send message"
      >
        <Send size={20} />
      </button>
    </form>
  );
}

export default ChatInput;
