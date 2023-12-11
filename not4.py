import pinecone
import numpy as np
import os
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
import pinecone
from openai import OpenAI
from uuid import uuid4
from tqdm.auto import tqdm
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken
import datetime
from time import sleep
from langchain.document_loaders import TextLoader
from langchain.document_loaders import JSONLoader
import json


os.environ["OPENAI_API_KEY"] = "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"
OPENAI_API_KEY =  "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"
client = OpenAI()
client.api_key = OPENAI_API_KEY






pinecone.init(api_key="d6e0065f-1b75-4255-8866-e05a685b5817",#config.pinecone.api_key,
              environment="gcp-starter")

index_name = pinecone.Index("pravo")

pinecone.whoami()
index = pinecone.Index(index_name)
pinecone.list_indexes()
index.describe_index_stats()

#loader = CSVLoader(file_path="/workspaces/ole/docs/kolzot.csv", source_column="text")
json_path ="/workspaces/ole/docs/kolzot.json"
loader = JSONLoader(
    file_path=json_path,
    jq_schema='.[].',
    text_content=False)



docs = loader.load()




chunks = []
retry_count = 0



from tqdm.auto import tqdm
from uuid import uuid4

retry_count = 0
max_retries = 3  # Define max_retries

batch_size = 500  # how many embeddings we create and insert at once
text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=0)
documents = text_splitter.split_documents(docs)











from uuid import uuid4
from tqdm.auto import tqdm

chunks = []

for idx, record in enumerate(tqdm(docs)):
    # Access the 'text' attribute directly
    text = record.page_content

    # Split the text using the text_splitter
    texts = text_splitter.split_text(text)

    # Extend the chunks list with the new data
    chunks.extend([{
        'id': str(uuid4()),
        'text': text,
        'chunk': i
    } for i, text in enumerate(texts)])




for i in tqdm(range(0, len(chunks), batch_size)):
    # find end of batch
    i_end = min(len(chunks), i + batch_size)
    meta_batch = documents[i:i_end]

    # get ids
    #ids_batch = [x['id'] for x in meta_batch]
    #ids_batch = [doc.generate_id() for doc in meta_batch]
    ids_batch = [str(uuid4()) for _ in meta_batch]


    # get texts to encode
    #texts = [x['text'] for x in meta_batch]
    texts = [x for x in meta_batch]

    res = client.embeddings.create(input=[texts], model="text-embedding-ada-002")

    #texts = [doc.text for doc in meta_batch]


    # create embeddings (try-except added to avoid RateLimitError)
    try:
        res = client.embeddings.create(input=texts, model="text-embedding-ada-002")
    except:
        done = False
        while not done and retry_count < max_retries:
            try:
                res = client.embeddings.create(input=texts, model="text-embedding-ada-002")
                print("im here")
                done = True
            except Exception as e:
                retry_count += 1
                print(f"Retrying... ({retry_count}/{max_retries})")
                pass  # Removed indent here


    

    embeds = [record['embedding'] for record in res.data]
    # cleanup metadata
    meta_batch = [{
        'text': x['text'],
        'chunk': x['chunk'],
        'url': x['url']
    } for x in meta_batch]
    to_upsert = list(zip(ids_batch, embeds, meta_batch))
    # upsert to Pinecone
    index.upsert(vectors=to_upsert)






tokenizer = tiktoken.get_encoding('cl100k_base')




# create the length function
def tiktoken_len(text):
    tokens = tokenizer.encode(
        text,
        disallowed_special=()
    )
    return len(tokens)



text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=0)
documents = text_splitter.split_documents(docs)



chunks = []

for idx, record in enumerate(tqdm(docs)):
    print("for idx, record in enumerate(tqdm(data)):")
    texts = text_splitter.split_text(record['text'])
    chunks.extend([{
        'id': str(uuid4()),
        'text': texts[i],
        'chunk': i,
        'url': record['url']
    } for i in range(len(texts))])






with open("/workspaces/ole/docs/kolzot.json", "r") as json_file:
    dataJSON = json.load(json_file)
col_zot = [dict(t) for t in {tuple(d.items()) for d in dataJSON}]


import re

# Words to be removed
print("working")

