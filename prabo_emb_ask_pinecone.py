



from openai import OpenAI

import os

import pinecone
import numpy as np



client = OpenAI(api_key=api_key_open_ai)


index_name=index_name
pinecone.init(api_key=pinecone_api_key,
              environment="gcp-starter")

pinecone.whoami()
index = pinecone.Index(index_name)
pinecone.list_indexes()
index.describe_index_stats()


query = "Каким образом я могу получить помощь для оплаты жилья ?"


xq = client.embeddings.create(input=query, 
                              model="text-embedding-ada-002").data[0].embedding

res = index.query(vector=xq, top_k=5, include_metadata=True)
#for match in res['matches']:
   # print(f"{match['score']:.2f}: {match['metadata']['text']}")


#vectorstore = Pinecone.from_existing_index(index_name, embeddings)
#query = "Я разбил машину соседа. Что мне делать ?"
#docs = vectorstore.similarity_search(query)


contexts = [item['metadata']['text'] for item in res['matches']]
#print(contexts)

augmented_query = "\n\n---\n\n".join(contexts)+"\n\n-----\n\n"+query


primer = """
You are Q&A bot. A highly intelligent system that answers user questions based on the
information provided by the documents about Israel and only israel. If the information can not be found in the information provided by the given docs you truthfully say I don't know. All ways give a links where to go and where to call
answer the quaestion in the same leanguage as the question was asked.
answer the same language you have been asked
"""


res = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "system", "content": primer},
    {"role": "user", "content": augmented_query}
  ]
)

answer=res.choices[0].message.content




print(answer)



