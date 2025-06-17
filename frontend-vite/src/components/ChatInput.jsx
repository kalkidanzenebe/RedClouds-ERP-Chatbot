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
        id={inputId} // Assign the ID to the input field
        value={inputText}
        onChange={(e) =>
          e.target.value.length <= 500 && setInputText(e.target.value)
        } // Added character limit
        placeholder="Type your message..."
        // Input field - Dark background, light text, neon blue focus ring
        className="flex-1 p-3 border border-gray-700 bg-gray-800 text-gray-100 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 transition shadow-sm"
        disabled={isLoading}
        maxLength={500} // HTML attribute for character limit
      />
      <button
        type="submit"
        // Send button - Neon blue background
        className="p-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl shadow-md transition duration-200 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-blue-500"
        disabled={isLoading || !inputText.trim()}
        aria-label="Send message"
      >
        <Send size={20} />
      </button>
    </form>
  );
}

export default ChatInput;
