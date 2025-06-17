import React from "react";
import { Info, Loader2 } from "lucide-react";
import MessageBubble from "./MessageBubble";

function ChatWindow({ messages, isLoading, onSendMessage }) {
  return (
    <div className="flex flex-col flex-1 p-6">
      {messages.length === 0 && !isLoading ? (
        <div className="flex flex-col items-center justify-center h-full text-gray-500">
          <Info size={48} className="text-gray-700 mb-4" />
          <p className="text-lg text-center text-gray-400">
            Start a new conversation or select from history.
          </p>
          <p className="text-md text-center text-gray-400">
            Ask me anything about RedClouds ERP solutions!
          </p>
        </div>
      ) : (
        messages.map((msg, index) => (
          <MessageBubble
            key={index}
            message={msg}
            onSendMessage={onSendMessage}
          />
        ))
      )}
      {isLoading && (
        <div className="flex items-center justify-start mt-4">
          <div className="bg-gray-800 p-3 rounded-br-2xl rounded-tr-2xl rounded-bl-2xl text-white">
            <Loader2 className="animate-spin" size={20} />
          </div>
        </div>
      )}
    </div>
  );
}

export default ChatWindow;
