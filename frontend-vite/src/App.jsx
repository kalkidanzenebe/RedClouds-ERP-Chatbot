import React, { useState } from "react";
import { X, MessageSquareText } from "lucide-react"; // Import icons for the toggle button
import ChatModal from "./components/ChatModal"; // Import ChatModal component

function App() {
  const [isModalOpen, setIsModalOpen] = useState(false); // State to control modal visibility

  // Function to toggle the modal's open/close state
  const toggleModal = () => {
    setIsModalOpen((prev) => !prev);
  };

  return (
    <div className="relative flex items-center justify-center min-h-screen bg-gradient-to-br from-zinc-900 to-black font-inter">
      {/* The toggle button, fixed at the bottom right, now only an icon with a tooltip */}
      <div className="fixed bottom-8 right-8 z-50 group">
        {" "}
        {/* Added a wrapper div for tooltip */}
        <button
          onClick={toggleModal}
          // Updated colors for neon blue primary action
          className="p-4 bg-cyan-400 text-gray-900 rounded-full shadow-lg hover:shadow-xl transform hover:scale-110 transition duration-300 ease-in-out focus:outline-none focus:ring-4 focus:ring-cyan-200 flex items-center justify-center"
          aria-label={isModalOpen ? "Close AI Assistant" : "Ask Anything!"}
        >
          {/* Conditional rendering of icons based on modal state */}
          {isModalOpen ? <X size={32} /> : <MessageSquareText size={32} />}
        </button>
        {/* Tooltip text that appears on hover */}
        <div className="absolute right-full top-1/2 -translate-y-1/2 mr-4 p-2 bg-gray-700 text-white text-sm rounded-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
          {isModalOpen ? "Close Assistant" : "Ask Anything!"}
        </div>
      </div>

      {/* Render ChatModal when open */}
      {isModalOpen && (
        // Pass toggleModal to close the modal
        <ChatModal onClose={toggleModal} />
      )}
    </div>
  );
}

export default App;
