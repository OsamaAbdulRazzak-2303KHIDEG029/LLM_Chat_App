import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
from PyPDF2 import PdfReader
import pickle
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores.faiss import FAISS
from langchain.llms import OpenAI
from langchain.callbacks import get_openai_callback
from langchain.chains.question_answering import load_qa_chain
from dotenv import load_dotenv

with st.sidebar:
    st.title('🤗💬 LLM Chat App')
    st.markdown('''
    ## About
    This app is an LLM-powered chatbot built using:
    - [Streamlit](https://streamlit.io/)
    - [LangChain](https://python.langchain.com/)
    - [OpenAI](https://platform.openai.com/docs/models) LLM model
    ''')
    add_vertical_space(5)

load_dotenv()

def main():
    with st.sidebar:
        st.header("Chat with PDF 💬")

        # Upload a PDF file
        pdf = st.file_uploader("Upload your PDF here 📝", type='pdf')

    if pdf is not None:
        pdfreader = PdfReader(pdf)
        text = ''
        for page in pdfreader.pages:
            text += page.extract_text()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_text(text=text)

        # Embeddings
        store_name = pdf.name[:-4]
        if os.path.exists(f"{store_name}.pkl"):
            with open(f"{store_name}.pkl", "rb") as f:
                vectorstore = pickle.load(f)
            st.write("Embedding loaded from Disk")
        else:
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
            vectorstore = FAISS.from_texts(chunks, embedding=embeddings)
            with open(f"{store_name}.pkl", 'wb') as f:
                pickle.dump(vectorstore, f)
            st.write("Embeddings Computation is Completed")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Ask your questions?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Query the assistant using the latest chat history
        docs = vectorstore.similarity_search(query=prompt, k=3)
        llm = OpenAI(model_name='gpt-3.5-turbo')
        chain = load_qa_chain(llm=llm, chain_type='stuff')
        response = chain.run(input_documents=docs, question=prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)
        with get_openai_callback() as cb:
            response = chain.run(input_documents = docs, question = prompt)
            print(cb)

if __name__ == '__main__':
    main()