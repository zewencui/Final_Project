import requests
from bs4 import BeautifulSoup
import pandas as pd
from time import sleep
import requests_cache

# 常量
SEARCH_QUERY = 'clothing'.replace(' ', '+')
BASE_URL = 'https://www.amazon.com/s?k={0}'.format(SEARCH_QUERY)
MAX_PAGE_NUM = 50  # 最大爬取页数
RATING_COUNT_RANGE = (0, 1000000)  # 评价数量范围

# 请求头
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0',
    'Accept-Language': 'en-US, en;q=0.5'
}

requests_cache.install_cache('amazon_cache', expire_after=3600)
response = requests.get(BASE_URL, headers=HEADERS)
# 爬取指定页码的商品信息
def scrape_products_on_page(page_num):
    url = BASE_URL + '&page={0}'.format(page_num)
    print('Processing {0}...'.format(url))
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.content, 'html.parser')

    results = soup.find_all('div', {'class': 's-result-item', 'data-component-type': 's-search-result'})

    items = []
    for result in results:
        product_name = result.h2.text
        rating, rating_count = get_rating_info(result)

        try:
            price1 = result.find('span', {'class': 'a-price-whole'}).text
            price2 = result.find('span', {'class': 'a-price-fraction'}).text
            price = float(price1 + price2)
            product_url = 'https://amazon.com' + result.h2.a['href']
            items.append([product_name, rating, rating_count, price, product_url])
        except AttributeError:
            continue

    return items

# Get the rating information of a product
def get_rating_info(result):
    try:
        rating = result.find('i', {'class': 'a-icon'}).text
        rating_counts = result.find_all('span', {'aria-label': True})
        if len(rating_counts) > 1:
            rating_count = rating_counts[1].text.replace(',', '')
        else:
            rating_count = "N/A"
    except AttributeError:
        rating, rating_count = "N/A", "N/A"

    return rating, rating_count

# Filter out products whose rating count is not within the specified range.
def filter_by_rating_count(items):
    return [item for item in items if is_in_rating_count_range(item[2])]

#Check if the rating count is within the specified range.
def is_in_rating_count_range(rating_count):
    if rating_count == "N/A":
        return False
    count = int(rating_count)
    return count >= RATING_COUNT_RANGE[0] and count <= RATING_COUNT_RANGE[1]

# main
def main():
    items = []
    for i in range(1, MAX_PAGE_NUM + 1):
        page_items = scrape_products_on_page(i)
        items.extend(page_items)
        sleep(1.5)

    filtered_items = filter_by_rating_count(items)
    df = pd.DataFrame(filtered_items, columns=['product', 'rating', 'rating count', 'price', 'product url'])
    df.to_csv('clothing.csv', index=False)

if __name__ == '__main__':
    main()
