from backend.app.rag import ERPChatbot

chatbot = ERPChatbot()
query = "How do I track stock levels?"

retrieved_docs = chatbot._retrieve_relevant_documents(query)

if retrieved_docs:
    print("\n✅ Retrieved documents:")
    for doc in retrieved_docs[:3]:  # Show first 3 retrieved docs
        print(f"- {doc['content'][:100]}...")  # Preview first 100 characters
else:
    print("\n❌ No relevant documents found! Retrieval may be failing.")