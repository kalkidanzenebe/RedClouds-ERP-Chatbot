import React from "react";
import { MessageSquarePlus, History, X } from "lucide-react";

function Sidebar({
  isOpen,
  onClose,
  conversations,
  onNewChat,
  onConversationSelect,
  currentConversationId,
}) {
  return (
    <div
      className={`absolute inset-y-0 left-0 w-64 bg-gray-900 text-gray-100 shadow-lg z-20 transform ${
        isOpen ? "translate-x-0" : "-translate-x-full"
      } transition-transform duration-300 ease-in-out`}
      // Removed: md:relative md:translate-x-0 (These forced it open on desktop)
    >
      <div className="flex justify-between items-center p-4 border-b border-gray-800">
        <button
          onClick={onNewChat}
          className="flex items-center justify-center bg-cyan-500 hover:bg-cyan-600 text-white font-semibold py-2 px-3 rounded-lg shadow-md transition duration-200 focus:outline-none focus:ring-2 focus:ring-cyan-400"
        >
          <MessageSquarePlus size={18} className="mr-2" />
          New Chat
        </button>
        <button
          onClick={onClose}
          className="p-2 rounded-full hover:bg-gray-700 text-gray-300"
          // Removed: md:hidden (The close button should always be available as it's an overlay)
          aria-label="Close sidebar"
        >
          <X size={20} />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
        <h3 className="text-lg font-semibold mb-3 flex items-center text-cyan-300">
          <History size={18} className="mr-2" />
          Past Conversations
        </h3>
        {conversations.length === 0 ? (
          <p className="text-gray-400 text-sm">No past conversations yet.</p>
        ) : (
          <ul>
            {conversations.map((conv) => (
              <li key={conv.conversation_id} className="mb-2">
                <button
                  onClick={() => onConversationSelect(conv.conversation_id)}
                  className={`w-full text-left py-2 px-3 rounded-lg hover:bg-gray-700 transition duration-150 ${
                    currentConversationId === conv.conversation_id
                      ? "bg-gray-700 text-cyan-300 font-medium"
                      : "text-gray-200"
                  }`}
                >
                  <span className="block truncate">
                    {conv.first_question ||
                      `Chat with ${conv.conversation_id.substring(0, 8)}...`}
                  </span>
                  <span className="block text-xs text-gray-400">
                    {new Date(conv.updated_at).toLocaleString()}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default Sidebar;
