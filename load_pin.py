import json
from pathlib import Path
import pinecone
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import JSONLoader
from uuid import uuid4
from tqdm import tqdm





from openai import OpenAI




client = OpenAI(api_key=OPENAI_API_KEY)







json_folder_path = "/workspaces/ole/docs/json_for_pravo/json/audit.json"#"/workspaces/ole/docs/json_for_pravo/json"

def metadata_func(record: dict, metadata: dict) -> dict:
    if "source" in metadata:
        source = metadata["source"].split("/")
        metadata["source"] = "/".join(source)
        metadata["source"] = metadata["source"].replace("/workspaces/ole/docs/json_for_pravo/json/", "").replace(".json", "")
    return metadata



data = []

    
def process_json_files(json_folder_path):
    loader = JSONLoader(
        file_path=json_folder_path,
        jq_schema='.',
        text_content=False,
        metadata_func=metadata_func,
    )
    data = loader.load()
    return data


data  = process_json_files(json_folder_path)



text_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", " ", "\n"],
    chunk_size=800, 
    chunk_overlap=50,
    is_separator_regex = True,
)


#text = text_splitter.split_documents(data)


chunks = text_splitter.split_documents(data)

def generate_id(source: str, chunk_number: int) -> str:
    return f"{source}_chunk_{chunk_number}"

# Example usage:
source_example = "example_source"
chunk_number_example = 1
generated_id = generate_id(source_example, chunk_number_example)
print(generated_id)


###### embed

client = OpenAI()


def createEmbedding(text):
    emb= client.embeddings.create(
        model="text-embedding-ada-002",
        input=text,
        encoding_format="float"
    )
    return emb.data[0].embedding


### pinicone 



# Split the documents into chunks


# Embed and insert into Pinecone


pinecone.init(api_key=api_key,#config.pinecone.api_key,
              environment="gcp-starter")

index = pinecone.Index(self)



batch_size = 800

count_of_chunks=0


def load(chunks):
    for i in tqdm(range(0, len(chunks), batch_size)):
        i_end = min(len(chunks), i + batch_size)
        batch = chunks[i:i_end]
        


        ids_batch =[str(uuid4()) for _ in batch] 

        count_of_chunks+=1
        texts = [chunk.page_content for chunk in batch]

        # Embed text using OpenAI API
        try:
            #createEmbedding(texts)
            embeddings_res = client.embeddings.create(
                model="text-embedding-ada-002",
                input=texts,
                encoding_format="float"
            )
        except Exception as e:
            print(f"Error embedding text: {e}")
            continue

        embeddings = [record.embedding for record in embeddings_res.data]

        # Prepare metadata
        metadata_batch = [{
            'chunk': str(count_of_chunks),#str(i_end),
            'text': x.page_content,
            'source': x.metadata.get("source")
        } for x in batch]#chunk, text, source in zip(batch, texts, data)]


        # Upsert to Pinecone
        vectors_to_upsert = list(zip(ids_batch, embeddings, metadata_batch))
        print(vectors_to_upsert)
        index.upsert(vectors=vectors_to_upsert)
        print("done")

for i in tqdm(range(0, len(chunks), batch_size)):
    i_end = min(len(chunks), i + batch_size)
    batch = chunks[i:i_end]
    


    ids_batch =[str(uuid4()) for _ in batch] 

    count_of_chunks+=1
    texts = [chunk.page_content for chunk in batch]

    # Embed text using OpenAI API
    try:
        #createEmbedding(texts)
        embeddings_res = client.embeddings.create(
            model="text-embedding-ada-002",
            input=texts,
            encoding_format="float"
        )
    except Exception as e:
        print(f"Error embedding text: {e}")
        continue

    embeddings = [record.embedding for record in embeddings_res.data]

    # Prepare metadata
    metadata_batch = [{
        'chunk': str(count_of_chunks),#str(i_end),
        'text': x.page_content,
        'source': x.metadata.get("source")
    } for x in batch]#chunk, text, source in zip(batch, texts, data)]


    # Upsert to Pinecone
    vectors_to_upsert = list(zip(ids_batch, embeddings, metadata_batch))
    print(vectors_to_upsert)
    index.upsert(vectors=vectors_to_upsert)
    print("done")
    try:
        upsert_res = index.upsert(vectors=vectors_to_upsert)
        if upsert_res.status != HTTPStatus.SUCCESS:
            print(f"Error upserting vectors: {upsert_res}")
    except Exception as e:
        print(f"Error upserting vectors: {e}")
