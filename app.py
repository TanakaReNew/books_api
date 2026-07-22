from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import time

app = Flask(__name__)

BASE_URL = "https://books.toscrape.com/"

CATALOGUE_URL = urljoin(BASE_URL, 'catalogue/')

########### get books detail ###################

def get_product_detail(url):
    try:
        headers = {'User-Agent':'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'lxml')
        
        table_data = {}
        rows = soup.select('table.table.table-striped tr')
        
        for row in rows:
            header = row.find('th').text.strip()
            value = row.find('td').text.strip()
            table_data[header] = value
            
        return table_data
        
    except Exception as e:
        print(f'Error:{e} | URL:{url}')
        return {}
        
########### get one page #######################

def get_page(page_num):
    url = urljoin(CATALOGUE_URL, f'page-{page_num}.html')
    headers = {'User-Agent':'Mozilla/5.0'}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return []
    
    soup = BeautifulSoup(response.text, 'lxml')
    
    rating_map = {
        'One':1,
        'Two':2,
        'Three':3,
        'Four':4,
        'Five':5}

    page_data = []

    books = soup.find_all('article', class_='product_pod')
    for book in books:
        title = book.find('h3').find('a')['title']
        
        link = book.find('h3').find('a')['href']
        product_url = urljoin(CATALOGUE_URL, link)
        
        rating_class = book.find('p', class_='star-rating')['class']
        rating = rating_map.get(rating_class[1], 0)
        
        price = book.find('p', class_='price_color').text.strip()
        
        details = get_product_detail(product_url)
        
        book_data = {
            'title':title,
            'price':price,
            'rating':rating,
            'link': product_url}
        
        book_data.update(details)
        page_data.append(book_data)

    return page_data


############ scrape multiple page ##################

def get_all_pages(pages):
    all_books = []
    pages = 1
    
    for page in range(1, pages+1):
        page_data = get_page(page)
        if not page_data:
            break
        all_books.extend(page_data)
        time.sleep(0.5)
        
    return all_books

################# API ROUTE ####################

@app.route('/books')
def books_api():
    pages = request.args.get('pages', default=1, type=int)
    
    if pages < 0 or pages > 50:
        return jsonify({'error':'pages must be between 1 and 50'}), 400
    
    data = get_all_pages(pages)
    
    return jsonify({
        'pages_requested':pages,
        'total_books':len(data),
        'results':data
        })

if __name__=="__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    
    

    