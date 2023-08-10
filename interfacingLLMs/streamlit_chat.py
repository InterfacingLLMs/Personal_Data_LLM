import streamlit as st
from pubmed_manager import PubmedManager
from llama_index import VectorStoreIndex
import os 
import openai
import uuid


#initialisation
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
if "references" not in st.session_state:
    st.session_state["references"] = []


#streamlit code

st.set_page_config(page_title="fastbio")
col1,col2,col3 = st.columns([1,1,1])
col2.title("FastBio")
st.divider()

#sidebar
apiKey = st.sidebar.text_input("OpenAI API Key", type="password")
st.session_state.apikey = apiKey
if not apiKey:
    st.info("Please add your OpenAI API key to continue.")
    st.stop()
openai.api_key = apiKey


#main content




#add logic to create a userId
#link userId to VectorStoreIndices
@st.cache_resource(show_spinner=False)
class SearchBackend1():
  def __init__(self):
    self.indexCreated = False
    self.index = None
    self.queryEngine = None
    self.persistDir = "interfacingLLMs/stored_embeddings/pubmed"
    self.userId = str(uuid.uuid4())
    self.pubObj = PubmedManager()


  #@st.cache_data(show_spinner=False)
  def fetch_docs(_self,query):
    docs = _self.pubObj.fetch_details(query)
    return docs
  
  def update_index(self,docs):  
    for doc in docs:
      self.index.insert(doc)


  # add userId logic so once a users DB is created its remembered
  def main(self,query):
    with st.spinner("Creating the best response for you"):
        currentDocs = self.fetch_docs(query)
    if self.indexCreated == False:
        self.index = VectorStoreIndex.from_documents(currentDocs)
        self.index.set_index_id(self.userId)
        indexPath = self.persistDir+"/"+self.userId
        if not os.path.exists(indexPath):
        	os.makedirs(indexPath)
        self.index.storage_context.persist(indexPath)
        self.indexCreated = True
        self.queryEngine = self.index.as_query_engine()
    else:
        self.update_index(currentDocs)
        self.queryEngine = self.index.as_query_engine()
    
    response = self.queryEngine.query(query)
    return response

def searchButtonCallback():
	st.session_state.search = True


if st.session_state["search"] == False:
    # engine = st.selectbox('Select Engine',["Engine1","Engine2","Engine3"])   
    # st.session_state["engine"] = engine
    if st.session_state.query == None:
        userInput = st.text_input("Search with papers")
    else:
        userInput = st.text_input("Search with papers",value=st.session_state.query)
    st.session_state.query = userInput
    buttonClick = st.button("Ask",on_click=searchButtonCallback)


def editcallback():
    st.session_state["search"] = False
    st.session_state["response"] = None
    st.session_state["feedbackRating"] = None
    st.session_state["feedbackText"] = None
    #st.session_state["engine"] = None
    st.session_state["references"] = []

def rebootandlog():
    st.session_state["search"] = False
    st.session_state["query"] = None
    st.session_state["response"] = None
    st.session_state["feedbackRating"] = None
    st.session_state["feedbackText"] = None
    #st.session_state["engine"] = None
    st.session_state["references"] = []

searchObj1 = SearchBackend1()

if st.session_state.search:
    response = searchObj1.main(st.session_state.query)
    st.session_state.response = str(response)
    
    citations = []
    for node in response.source_nodes:
        title = node.node.metadata["Title of this paper"]
        url = node.node.metadata["URL"]
        citations.append((title,url))
    
    col1,col2 = st.columns([0.8,0.2])
    st.session_state.references = citations
    with col1:
        st.subheader("Query")
        st.markdown(st.session_state.query)
    with col2:
        st.button("Edit Query",on_click = editcallback)
    st.subheader("Response")
    st.markdown(st.session_state.response)

    with st.expander("Citations"):
        for i,reference in enumerate(citations):
            st.caption(reference[0])
            st.caption(reference[1])


    st.divider()
    st.subheader("Feedback")

    responseFeedback = st.radio('Choose for the generated response',options=('Correct Response, No Hallucinations','Hallucinations','No Response'))
    st.session_state["feedbackRating"] = responseFeedback
    if responseFeedback:
        feedbackText = st.text_area("Please help us understand your feedback better")
        st.session_state["feedbackText"] = feedbackText
    st.markdown("")
    st.markdown("") 
    col1, col2, col3 = st.columns([1,1,1])
    col2.button("Search Again!", on_click=rebootandlog)




