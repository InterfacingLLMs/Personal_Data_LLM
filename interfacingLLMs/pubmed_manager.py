from typing import List, Optional
from llama_index.readers.base import BaseReader
from llama_index.readers.schema.base import Document
import asyncio
from Bio import Entrez
import time
import xml.etree.ElementTree as xml
import requests
from metapub import PubMedFetcher
import os

class PubmedManager(BaseReader):

    def __init__(self):
        os.environ["NCBI_API_KEY"] = "71836676d726923c4d2847443faae0fef308"
        self.cachePath = "/Users/arihantbarjatya/Documents/fastbio/database_storage/stored_embeddings/pubmed"
    
    def search(self,query):
        Entrez.email = 'arihantbadjatya@gmail.com'
        handle = Entrez.esearch(db='pubmed',sort='relevance',retmax='5',retmode='xml',term=query)
        results = Entrez.read(handle)
        return results

    def fetch_details(self,query):
        fetch = PubMedFetcher(cachedir=self.cachePath)
        response = self.search(query)
        pmids = response["IdList"]
        pubmed_search = []

        for pmid in pmids:
            try:
                article = fetch.article_by_pmid(pmid)
            except Exception as e:
                print(e)
                continue
            title = article.title
            abstract = article.abstract
            url = "https://pubmed.ncbi.nlm.nih.gov/"+pmid+"/"
            pubmed_search.append({
                "title":title,
                "abstract":abstract,
                "url":url
            })

        pubmed_documents = []
        for paper in pubmed_search:
            if paper == None or paper["abstract"] == None:
                continue
            pubmed_documents.append(
                Document(
                    text=paper["abstract"],
                    extra_info={
                    "Title of this paper": paper["title"],
                    "URL": paper["url"]
                    }
                )
            )

        return pubmed_documents
