import streamlit as st
import os
import asyncio
import time
from biorxiv_manager import BioRxivManager  
from llama_index import (
    load_index_from_storage, 
    ServiceContext, 
    StorageContext, 
    LangchainEmbedding,
    LLMPredictor
)
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from llama_index.llms import OpenAI
import openai
from llama_index.query_engine import FLAREInstructQueryEngine
from llama_index.tools import QueryEngineTool, ToolMetadata
from llama_index.query_engine import SubQuestionQueryEngine
from llama_index.response_synthesizers import get_response_synthesizer
from llama_index.callbacks import CallbackManager, LlamaDebugHandler
from llama_index.callbacks.schema import CBEventType, EventPayload

st.set_page_config(page_title="fastbio")
st.title("FastBio")

if "search" not in st.session_state:
    st.session_state["search"] = False

if "query" not in st.session_state:
    st.session_state["query"] = None

if "response" not in st.session_state:
    st.session_state["response"] = None

if "feedbackRating" not in st.session_state:
    st.session_state["feedbackRating"] = None

if "feedbackText" not in st.session_state:
    st.session_state["feedbackText"] = None

if "apikey" not in st.session_state:
    st.session_state["apikey"] = None

if "engine" not in st.session_state:
    st.session_state["engine"] = None

if "references" not in st.session_state:
    st.session_state["references"] = []

# if "rag_fail" not in st.session_state:
#     st.session_state["rag_fail"] = False


apiKey = st.sidebar.text_input("OpenAI API Key", type="password")
st.session_state.apikey = apiKey
openai.api_key = st.session_state.apikey
if not st.session_state.apikey:
    st.info("Please add your OpenAI API key to continue.")
    st.stop()

@st.cache_resource(show_spinner=False)
class SearchBackend:
    def __init__(self,persistDir):
        self.debugger = LlamaDebugHandler(print_trace_on_end=True)
        self.callbackManager = CallbackManager([self.debugger])
        self.queryEmbedModel = LangchainEmbedding(HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2"))
        self.serviceContext = ServiceContext.from_defaults(llm=OpenAI(model="gpt-3.5-turbo", temperature=0, chunk_size=512), embed_model=self.queryEmbedModel, callback_manager=self.callbackManager)
        self.storageContext = StorageContext.from_defaults(persist_dir=persistDir)
        self.biorxivDocsIndex = load_index_from_storage(self.storageContext, service_context=self.serviceContext)   
        self.biorxivDocsEngine = self.biorxivDocsIndex.as_query_engine(similarity_top_k=5, service_context=self.serviceContext)
        self.searchEngine1 = FLAREInstructQueryEngine(
            query_engine=self.biorxivDocsEngine,
            service_context=self.serviceContext,
            verbose=True
        )
        self.queryEngineTools = [
            QueryEngineTool(
                query_engine=self.biorxivDocsEngine,
                metadata=ToolMetadata(name="biorxiv_docs_engine", description="Provides information about the recent BioRxiv papers") 
            ), 
        ]
        self.searchEngine2 = SubQuestionQueryEngine.from_defaults(query_engine_tools=self.queryEngineTools, service_context=self.serviceContext, response_synthesizer=get_response_synthesizer(streaming=True), verbose=True, use_async=False)
    
    @st.cache_data(show_spinner=False)
    def search(_self,query,engine):
        if engine == "Engine1":
            response = _self.searchEngine1.query(query)
        if engine == "Engine2":
            citedSourcesText = []
            response = _self.searchEngine2.query(query)
            responseText = str(response)
            citedSources = response.source_nodes
            citedSourcesText = []
            for node in citedSources:
                citedSourcesText.append(node.node.text)
            # for i, (start_event, end_event) in enumerate(_self.debugger.get_event_pairs(CBEventType.SUB_QUESTION)):
            #     qa_pair = end_event.payload[EventPayload.SUB_QUESTION]
            #     question = qa_pair.sub_q.sub_question.strip()
            #     answer = qa_pair.answer.strip()
            #     citedSourcesText.append((question,answer))
            #     if answer.contains("The given context information does not provide any information about"):
            #         st.session_state["rag_fail"] = True
        return responseText,citedSourcesText



def searchButtonCallback():
    st.session_state.search = True


if st.session_state["search"] == False:
    engine = st.selectbox('Select Engine',["Engine2"])   
    st.session_state["engine"] = engine
    userInput = st.text_input("Ask your question")
    st.session_state.query = userInput
    buttonClick = st.button("Search",on_click=searchButtonCallback)

persistDir = "database_storage/stored_embeddings/biorxiv"
searchObj = SearchBackend(persistDir)

def reboot():
    st.session_state["search"] = False
    st.session_state["query"] = None
    st.session_state["response"] = None
    st.session_state["feedbackRating"] = None
    st.session_state["feedbackText"] = None
    st.session_state["engine"] = None
    st.session_state["references"] = []
    #st.session_state["rag_fail"] = False

if st.session_state.search:
    with st.spinner("Creating the best result for you"):
        response,references = searchObj.search(st.session_state.query,st.session_state.engine)
    st.session_state.response = response
    st.session_state.references = references
    st.subheader("Query")
    st.markdown(st.session_state.query)
    st.subheader("Response")
    st.markdown(st.session_state.response)
    showSources = st.checkbox("*Click here to see how we generated the response*")
    if showSources:
        # for i,reference in enumerate(references):
        #     st.caption(f"Subquestion{i} : {reference[0]}")
        #     st.caption(f"Response : {reference[1]}")
        for i,reference in enumerate(references):
            st.caption(reference)
    
    responseFeedback =  st.radio('Please rate the response',options=('Correct Response, No Hallucinations','Hallucinations','No Response'))
    st.session_state["feedbackRating"] = responseFeedback
    if responseFeedback:
        feedbackText = st.text_area("Please help us understand your feedback better")
        st.session_state["feedbackText"] = feedbackText
    searchAgain = st.button("Search Again", on_click=reboot)

    # with st.form("my_form"):
    #     st.session_state.response = response
    #     st.markdown(f"Query: {st.session_state.query}")
    #     st.markdown(f"Response: {response}")
    #     showSources = st.checkbox("References")
    #     if showSources:
    #         for i,reference in enumerate(references):
    #             st.caption(f"{i}-> {reference}")
    #     responseFeedback = st.radio('Rate the response',options=('Good','Bad','Ugly'))
    #     st.session_state["feedbackRating"] = responseFeedback
    #     if responseFeedback:
    #         feedbackText = st.text_area("Please help us understand your feedback better")
    #         st.session_state["feedbackText"] = feedbackText
    #     newSearch = st.form_submit_button("Search Again")
    #     if newSearch:
    #         st.write(st.session_state)
    #         reboot()





        



