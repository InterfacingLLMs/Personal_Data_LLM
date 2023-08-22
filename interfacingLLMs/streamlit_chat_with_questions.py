import streamlit as st
from pubmed_manager import PubmedManager
from llama_index import VectorStoreIndex
from llama_index.evaluation import DatasetGenerator
from llama_index.readers.schema.base import Document
import os 
import openai
import uuid
#from trubrics.integrations.streamlit import FeedbackCollector
from langchain.agents import create_csv_agent
from langchain.chat_models import ChatOpenAI
import os
from langchain.agents.agent_types import AgentType
import pandas as pd

# userId = str(uuid.uuid4())

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


collectorCitations = FeedbackCollector(
    component_name="citations-feedback",
    email=st.secrets["TRUBRICS_EMAIL"], # Store your Trubrics credentials in st.secrets:
    password=st.secrets["TRUBRICS_EMAIL"], # https://blog.streamlit.io/secrets-in-sharing-apps/
)


collectorMain=FeedbackCollector(
    component_name="default",
    email=st.secrets["TRUBRICS_EMAIL"], # Store your Trubrics credentials in st.secrets:
    password=st.secrets["TRUBRICS_EMAIL"], # https://blog.streamlit.io/secrets-in-sharing-apps/
)

openai.api_key = st.secrets["OPENAI_API_KEY"]
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

#main content
#add logic to create a userId
#link userId to VectorStoreIndices
#@st.cache_resource(show_spinner=False)
class SearchBackend1():
  def __init__(self):
    #   self.indexCreated = False
    self.index = None
    #self.queryEngine = None
    #self.persistDir = "/Users/arihantbarjatya/Documents/fastbio/database_storage/stored_embeddings/pubmed"
    #self.userId = str(uuid.uuid4())
    self.pubObj = PubmedManager()


  #@st.cache_data(show_spinner=False)
  def fetch_docs(_self,query):
    docs = _self.pubObj.fetch_details(query)
    return docs
  
  def update_index(self,docs):  
    for doc in docs:
      self.index.insert(doc)


  # add userId logic so once a users DB is created its remembered
  @st.cache_data(show_spinner=False)
  def main(_self,query):
    with st.spinner("Searching PubMed"):
        currentDocs,pubmedPapers = _self.fetch_docs(query)
        
        _self.index = VectorStoreIndex.from_documents(currentDocs)
        _self.queryEngine = _self.index.as_query_engine()
        response = _self.queryEngine.query(query)
        citations = []
        for node in response.source_nodes:
            # print(node)
            start_idx = node.node.start_char_idx
            end_idx = node.node.end_char_idx
            text = node.node.text
            text = text[start_idx:end_idx]
            score = node.score
            title = node.node.metadata["Title of this paper"]
            url = node.node.metadata["URL"]
            citations.append([text,title,url,score])
    
    return response,citations,pubmedPapers

def searchButtonCallback():
    st.session_state.search = True
    #st.session_state.toggle1 = not st.session_state.toggle2 
    # print(userInput)
    # response,citations,pubmedPapers = searchObj1.main(userInput)
    # st.session_state.query = userInput
    # st.session_state.response = str(response)
    # st.session_state.references = citations
    # st.session_state.pubmedPapers = pubmedPapers


def editcallback():
    st.session_state["search"] = False
    st.session_state["response"] = None
    st.session_state["feedbackRating"] = None
    st.session_state["feedbackText"] = None
    #st.session_state["engine"] = None
    st.session_state["references"] = []

def reboot():
    st.session_state["search"] = False
    st.session_state["query"] = None
    st.session_state["response"] = None
    st.session_state["feedbackRating"] = None
    st.session_state["feedbackText"] = None
    #st.session_state["engine"] = None
    st.session_state["references"] = []

def generatedQuestionCallback(newQuery):
    st.session_state["query"] = newQuery
    st.session_state["response"] = None
    #st.session_state["feedbackRating"] = None
    #st.session_state["feedbackText"] = None
    st.session_state["references"] = []
    st.session_state["search"] = True




@st.cache_data(show_spinner=False,experimental_allow_widgets=True)
def createNewQuestions(query,response):
    responseDoc = Document(text=response,extra_info={"Original Query":query})
    dataGenerator = DatasetGenerator.from_documents([responseDoc])
    numberOfQuestions = 3 
    newQuestions = dataGenerator.generate_questions_from_nodes(numberOfQuestions)
    newQuestions = sorted(newQuestions,key=len)
    #print(newQuestions)
           
    
    # try:
    #     newQuestions = newQuestions[:numberOfQuestions]
    # except Exception as e:
    #     pass
    
    # newQuestions = sorted(newQuestions,key=len)    
    # return newQuestions
    
    # n = len(newQuestions)

    return newQuestions


searchObj1 = SearchBackend1()
# userInput = st.text_input("Typer your query and Press Enter!")
# st.session_state.query = userInput
userEmail = st.experimental_user.email


        
tab1,tab2 = st.tabs(["Search","Dataset Explorer"])
            
with tab1:

    if st.session_state["search"] == False:
        # engine = st.selectbox('Select Engine',["Engine1","Engine2","Engine3"])   
        # st.session_state["engine"] = engine
        if st.session_state.query == None:
            userInput = st.text_input("Search with papers")
        else:
            userInput = st.text_input("Search with papers",value=st.session_state.query)
        st.session_state.query = userInput
        buttonClick = st.button("Search",on_click=searchButtonCallback)


    if st.session_state.search:

        response,citations,pubmedPapers = searchObj1.main(st.session_state.query)
        st.session_state.response = str(response)
        st.session_state.references = citations

        queryCol1,queryCol2 = st.columns([0.8,0.2])
        with queryCol1:
            #st.subheader("Query")
            st.write(f'<p style="font-size:30px"><b>Query</b></p>',unsafe_allow_html=True)
            #st.markdown(st.session_state.query)
            st.write(f'{st.session_state.query}',
    unsafe_allow_html=True)
        with queryCol2:
            st.button("Edit Query",on_click = editcallback)
        
        st.write(f'<p style="font-size:30px"><b>Response</b></p>',unsafe_allow_html=True)
        #st.markdown(f"*:{st.session_state.response}:*")
        if st.session_state.response != "None":
            st.write(f'<i>{st.session_state.response}</i>',unsafe_allow_html=True)
        else:
            st.write(f'<i>Sorry! Try a different question</i>',unsafe_allow_html=True)
        st.markdown("")
        st.markdown("")

        if st.session_state.response != "None":
            newQuestions = createNewQuestions(st.session_state.query,st.session_state.response) 
            col1,col2,col3 = st.columns([0.3,0.3,0.4])
            col1.button(newQuestions[0],on_click=generatedQuestionCallback,args=[newQuestions[0]])
            col2.button(newQuestions[1],on_click=generatedQuestionCallback,args=[newQuestions[1]])
            col3.button(newQuestions[2],on_click=generatedQuestionCallback,args=[newQuestions[2]])

        otherPaperCheck = []
        with st.expander("Citations"):
            for i,reference in enumerate(citations):
                citationsCol1,citationsCol2 = st.columns([0.9,0.1])
                otherPaperCheck.append(reference[2])
                with citationsCol1:
                    st.write(f'<a href = {reference[2]}>{reference[1]}</a>',unsafe_allow_html=True)
                    st.caption(f'Confidence Score: {round(reference[3],2)}')
                    showText = st.checkbox("Show Text",key=f"citations{i}")
                    if showText:
                        st.caption(f'<i>{reference[0]}</i>',unsafe_allow_html=True)
                    st.markdown("")
                with citationsCol2:
                    collectorCitations.st_feedback(
                        feedback_type="thumbs",
                        model="model-001",
                        metadata={"query":st.session_state.query,"response":st.session_state.response,"url":reference[2]},
                        success_fail_message=False,
                        key=f"Citations-Feedback:{i}",
                        user_id=userEmail
                    )
                    # citationPositive = st.button(":thumbsup:",key=f"citationsPositive{i}")
                    # citationPositive = st.button(":thumbsdown:",key=f"citationsNegative{i}")    

        with st.expander("Other relevant papers"):
            for i,data in enumerate(pubmedPapers):
                url = data["url"]
                url = str(url)
                relevantCol1,relevantCol2 = st.columns([0.9,0.1])
                if url not in otherPaperCheck:
                    with relevantCol1:
                        st.write(f'<a href = {url}>{data["title"]}</a>',unsafe_allow_html=True)
                        showText = st.checkbox("Show Text",key=f"moreInfo{i}")
                        if showText:
                            st.caption(f'<i>{data["abstract"]}</i>',unsafe_allow_html=True)
                    with relevantCol2:
                        collectorCitations.st_feedback(
                            feedback_type="thumbs",
                            model="model-001",
                            metadata={"query":st.session_state.query,"response":st.session_state.response,"url":url},
                            success_fail_message=False,
                            key=f"Pubmed-Feedback:{i}",
                            user_id=userEmail
                        )

        st.markdown("")
        st.divider()
        st.subheader("Feedback")
        collectorMain.st_feedback(
            feedback_type="faces",
            model="model-001",
            metadata={"query":st.session_state.query,"response":st.session_state.response},
            success_fail_message=False,
            user_id=userEmail,
            align="flex-start",
            open_feedback_label="Please help us understand your response better"
        )

        #st.divider()
        feedbackCol1, feedbackCol2, feedbackCol3 = st.columns([1,1,1])
        with feedbackCol2:
            searchAgain = st.button("Search Again!", on_click=reboot,type="primary")



@st.cache_data(show_spinner=False)
def load_csv(path):
    df = pd.read_csv(path)
    return df
    
with tab2:


    #metadataDF = load_csv("/Users/arihantbarjatya/Documents/fastbio/fastbio/database_storage/metadata.csv")
    metadataDF = load_csv("path here")
    dataset = st.selectbox("Select the dataset to analyse",metadataDF["ID"])
    if dataset: 
        #datasetPath = "/Users/arihantbarjatya/Documents/fastbio/database_storage/omics_data/" + dataset + ".csv"
        datasetPath = "path here"
        data = load_csv(datasetPath)
        st.dataframe(data)
        agent = create_csv_agent(ChatOpenAI(temperature=0, model="gpt-3.5-turbo-0613"),datasetPath,verbose=True,agent_type=AgentType.OPENAI_FUNCTIONS)

    datasetQuery = st.text_input("Query this dataset")
    if datasetQuery:
        agentResponse = agent.run(datasetQuery)
        st.write(f'<i>{agentResponse}</i>',unsafe_allow_html=True)


    st.divider()
    with st.expander("Metadata File"):
        metadata = st.dataframe(metadataDF)
        
                        

        










    
