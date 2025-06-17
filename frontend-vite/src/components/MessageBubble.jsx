import React from "react";

function MessageBubble({ message, onSendMessage }) {
  const isUser = message.type === "user";
  const bubbleColorClass = isUser
    ? "bg-blue-600 text-white rounded-br-none" // User message: vibrant blue background
    : "bg-gray-800 text-gray-100 rounded-bl-none"; // Bot message: dark gray background, light text

  return (
    <div
      className={`flex flex-col mb-4 w-full ${
        isUser ? "items-end" : "items-start"
      }`}
    >
      <div
        // The actual message bubble, with its max-width and color
        className={`p-4 rounded-2xl shadow-md max-w-[80%] md:max-w-[70%] ${bubbleColorClass}`}
      >
        <p className="text-sm sm:text-base whitespace-pre-wrap">
          {message.text}
        </p>
        {message.sources && message.sources.length > 0 && (
          <div className="mt-2 text-xs text-opacity-80 text-gray-300">
            <h4 className="font-semibold mb-1">Sources:</h4>
            <ul className="list-disc list-inside">
              {message.sources.map((source, idx) => (
                <li key={idx} className="truncate">
                  {source.source}
                </li>
              ))}
            </ul>
          </div>
        )}
        {message.suggested_questions &&
          message.suggested_questions.length > 0 && (
            <div className="mt-2 text-xs text-opacity-80 text-gray-300">
              <h4 className="font-semibold mb-1">Suggested Questions:</h4>
              <ul className="list-disc list-inside">
                {message.suggested_questions.map((sq, idx) => (
                  <li key={idx}>
                    <button
                      onClick={() => onSendMessage(sq)}
                      className="text-cyan-400 hover:text-cyan-300 text-left w-full truncate focus:outline-none focus:underline"
                    >
                      {sq}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
      </div>
      {/* The timestamp now naturally aligns with its parent's items-end/items-start */}
      <span className="text-xs text-gray-400 mt-1">
        {message.timestamp.toLocaleTimeString()}
      </span>
    </div>
  );
}

export default MessageBubble;
