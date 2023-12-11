import json
from pathlib import Path
import pinecone
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import JSONLoader
from uuid import uuid4
from tqdm import tqdm


from openai import OpenAI



OPENAI_API_KEY =  "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"
client = OpenAI(api_key=OPENAI_API_KEY)

pinecone.init(api_key="d6e0065f-1b75-4255-8866-e05a685b5817",#config.pinecone.api_key,
              environment="gcp-starter")

index = pinecone.Index("pravo")

# Assuming the necessary imports and classes for JSONLoader, RecursiveCharacterTextSplitter, etc. are defined elsewhere

# Define the OpenAI client with the API key


# Define the path to the folder containing JSON files
json_folder_path = "/workspaces/ole/docs/json_for_pravo/json"

# Define a function to modify metadata
def metadata_func(record: dict, metadata: dict) -> dict:
    if "source" in metadata:
        source = metadata["source"].split("/")
        metadata["source"] = "/".join(source)
        metadata["source"] = metadata["source"].replace("/workspaces/ole/docs/json_for_pravo/json/", "").replace(".json", "")
    return metadata

# Define a function to process JSON files

def process_json_files(json_file_path):
    loader = JSONLoader(
        file_path=json_file_path,
        jq_schema='.',
        text_content=False,
        metadata_func=metadata_func,
    )
    data = loader.load()
    return data

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

from pathlib import Path

def process_json_files(json_file_path):
    # Convert the string file path to a Path object
    path = Path(json_file_path)
    
    # Initialize the JSONLoader with the file path
    loader = JSONLoader(
        file_path=path,
        jq_schema='.',
        text_content=False,
        metadata_func=metadata_func,
    )
    
    # Load the data using the loader
    try:
        data = loader.load()
    except UnicodeDecodeError as e:
        print(f"Error reading file {json_file_path}: {e}")
        # Handle the error or return an empty list or None
        return []
    
    return data

# Define a function to generate unique IDs for chunks
def generate_id(source: str, chunk_number: int) -> str:
    return f"{source}_chunk_{chunk_number}"

# Define a function to create embeddings
def create_embedding(text):
    emb = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text,
        encoding_format="float"
    )
    return emb.data[0].embedding

# Initialize Pinecone


# Define the text splitter
text_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", " ", "\n"],
    chunk_size=200, 
    chunk_overlap=50,
    is_separator_regex=True,
)

# Process each JSON file in the folder
for json_file in os.listdir(json_folder_path):
    json_file_path = os.path.join(json_folder_path, json_file)
    if os.path.isfile(json_file_path):
        # Process the JSON file
        data = process_json_files(json_file_path)
        
        # Split the documents into chunks
        chunks = text_splitter.split_documents(data)
        
        # Embed and insert into Pinecone
        batch_size = 200
        count_of_chunks = 0

        for i in tqdm(range(0, len(chunks), batch_size)):
            i_end = min(len(chunks), i + batch_size)
            batch = chunks[i:i_end]
            ids_batch = [generate_id(json_file.replace(".json", ""), count_of_chunks + j) for j in range(len(batch))]
            count_of_chunks += len(batch)
            texts = [chunk.page_content for chunk in batch]

            # Embed text using OpenAI API
            try:
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
                'chunk': str(count_of_chunks),
                'text': x.page_content,
                'source': x.metadata.get("source")
            } for x in batch]

            # Upsert to Pinecone
            vectors_to_upsert = list(zip(ids_batch, embeddings, metadata_batch))
            index.upsert(vectors=vectors_to_upsert)
        print(f"Finished processing {json_file}")
