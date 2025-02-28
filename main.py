__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import os
import json

import streamlit as st
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from vectorize_documents import embeddings


working_dir = os.path.dirname(os.path.abspath("__file__"))
config_data = json.load(open(f"{working_dir}/config.json"))
GROQ_API_KEY = config_data["GROQ_API_KEY"]
os.environ["GROQ_API_KEY"] = GROQ_API_KEY


def setup_vectorstore():
    persist_directory = f"{working_dir}/vector_db_dir"
    embedddings = HuggingFaceEmbeddings()
    vectorstore = Chroma(persist_directory=persist_directory,
                         embedding_function=embeddings)
    return vectorstore


def chat_chain(vectorstore):
    llm = ChatGroq(model="llama-3.3-70b-versatile",
                   temperature=0.1)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    memory = ConversationBufferMemory(
        llm=llm,
        output_key="answer",
        memory_key="chat_history",
        return_messages=True
    )

    custom_prompt = PromptTemplate(
        input_variables=["context", "question"],
        template=(
            "You are an AI assistant for answering personal loan queries for ABC Bank. "
            "Use the provided context or existing knowledge to answer the question. If the context does not contain the answer, "
            "politely inform the user that you do not have the requested information, but DO NOT say that the document does not mention it. "
            "Provide alternative guidance if possible.\n\n"
            "Context:\n{context}\n\n"
            "Question: {question}\n\n"
            "Answer:"
        )
    )

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        memory=memory,
        verbose=True,
        return_source_documents=True,
        combine_docs_chain_kwargs={"prompt": custom_prompt}
    )

    return chain


st.set_page_config(
    page_title="ABC Bank - Personal Loan Assistant",
    page_icon="\U0001F3E6",
    layout="wide"
)

st.title("🤖 Personal Loan Query Chatbot - ABC Bank")

st.sidebar.title("Settings ⚙️")

# Clear chat history button
if st.sidebar.button("🗑️ Clear Chat History"):
    st.session_state.chat_history = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = setup_vectorstore()

if "conversational_chain" not in st.session_state or st.session_state.conversational_chain is None:
    st.session_state.conversational_chain = chat_chain(st.session_state.vectorstore)

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("💬 Ask your personal loan questions here...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        response = st.session_state.conversational_chain.invoke({"question": user_input})
        assistant_response = response["answer"]
        st.markdown(assistant_response)
        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})

# Sidebar API Usage Monitoring
st.sidebar.subheader("🔢 Token Usage Monitor")
st.sidebar.text("API Limit: 100,000 Tokens")
st.sidebar.progress(min(len(st.session_state.chat_history) * 500, 100000) / 100000)