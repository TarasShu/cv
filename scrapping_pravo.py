import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin


from datetime import datetime

date_format = "%d.%m.%y"




def extract_info(html):
    soup = BeautifulSoup(html, 'html.parser')
    elements = soup.find_all('span', class_='num')

    info_list = []
    for element in elements:
        info = {}
        if element.has_attr('class'):
            info['class'] = element['class']
        if element.text and '№' not in element.text:
            info['text'] = element.text
            info_list.append(info)

    return info_list



# Base URL
word = "fin"
#base_url = 'https://pravo.israelinfo.co.il/answers/admin/'
base_url="https://pravo.israelinfo.co.il/answers/" +word +"/"
#base_url ="https://pravo.israelinfo.co.il/answers/sem/"
# List to store question-answer pairs
qa_pairs = []
qa_pairs2 = []


def parse_document(document_url):
    if word not in document_url:
        return
    else:
        response = requests.get(document_url)

        response.encoding = "windows-1251"
        soup = BeautifulSoup(response.text, 'html.parser')

        try:
            # Extract question
            question_span = soup.find('span', class_='ital')
            br_tag = soup.select_one('span.ital br')
            br_tag = soup.find('br')
            p_element = br_tag.parent
            text_question = p_element.get_text(strip=True).lstrip('Вопрос')

            # Extract answer
            answer_p = soup.find('span', class_='ital').find_next('p')
            text_answer = answer_p.get_text(strip=True).lstrip('Ответ')
            date = extract_info(response.text)[0]["text"]
            date_object = datetime.strptime(date, date_format)




            # Add question-answer pair to the list
            qa_pairs.append({
                "category": word,
                "question": text_question,
                "answer": text_answer,
                "date": date_object
            })

            # Print question and answ
        except AttributeError:
            print("ОMisstaken getting docs")
            return


# Function to navigate through pages and open documents
def navigate_pages(url, page_count=1):
    if page_count > 40:
        return

    response = requests.get(url)
    response.encoding = "windows-1251"
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all document links on the page
    documents = soup.find_all('h3', class_='t100 di')

    # Open each document
    for document in documents:
        link = document.find('a')['href']
        document_url = urljoin(base_url, link)
        parse_document(document_url)

    # Increment page count
    page_count += 1

    # Check if there are more pages
    pagination_div = soup.find('div', class_='fl t90')
    next_page_link = pagination_div.find('a', text='След.')

    # Open next page if available
    if next_page_link:
        next_page_url = urljoin(base_url, next_page_link['href'])
        navigate_pages(next_page_url, page_count)

# Start navigation
navigate_pages(base_url)

# Save question-answer pairs to a JSON file
with open("pravo_filter.json", "w") as json_file:
    json.dump(qa_pairs, json_file, ensure_ascii=False, indent=4)
