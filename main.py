import csv
from os.path import exists
import pandas as pd
from time import sleep
import crawl

SEARCH_QUERY = 'clothing'.replace(' ', '+')
BASE_URL = 'https://www.amazon.com/s?k={0}'.format(SEARCH_QUERY)
MAX_PAGE_NUM = 50  # 最大爬取页数
RATING_COUNT_RANGE = (0, 1000000)  # 评价数量范围


def crawl_data():
    items = []
    for i in range(1, MAX_PAGE_NUM + 1):
        page_items = crawl.scrape_products_on_page(i)
        items.extend(page_items)
        sleep(1.5)
    
    filtered_items = crawl.filter_by_rating_count(items)
    df = pd.DataFrame(filtered_items, columns=['product', 'rating', 'rating count', 'price', 'product url'])
    df.to_csv('clothing.csv', index=False)


def open_file(file_path):
    rows = []
    with open(file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            rows.append(row)
    return rows


def get_all_products(rows):
    """
    This function takes a list of dictionaries as input, 
    and extracts the product names from each dictionary. 
    It then removes duplicate product names,
    and returns a list of unique product names.
    """
    all_products = []
    for item in rows:
        all_products.append(item['product'])
    all_products = list(set(all_products))
    return all_products

def filter_and_count_by_product_type(data, product_type):
    """
    Filter out corresponding products according to the product type, 
    and return a list of product names and their count.
    """
    filtered_data = [item for item in data if product_type.lower() in item['product'].lower()]
    usage = [item['product'] for item in filtered_data]
    count = len(filtered_data)
    return usage,count


def get_products_within_rating_count_range(rest_tree, min_count=0, max_count=5000):
    """
    Given a list of product dictionaries and a minimum and maximum rating count,
    returns a list of products with rating count within the specified range, 
    and the count of products within the range.
    """
    filtered_data = [item for item in rest_tree if min_count <= int(item['rating count'].replace(',', '')) <= max_count]
    usage = [item['product'] for item in filtered_data]
    count = len(filtered_data)
    return usage,count


def filter_by_price(rest_tree, min_price=0, max_price=1000):
    filtered_data = [item for item in rest_tree if min_price <= float(item['price']) <= max_price]
    usage = [item['product'] for item in filtered_data]
    return usage


def build_rating_tree(rest_tree):
    rating_tree = {}
    for item in rest_tree:
        try:
            rating = float(item['rating'][0:3])
            if rating not in rating_tree:
                rating_tree[rating] = []
            rating_tree[rating].append(item['product'])
        except:
            pass
    return rating_tree

def filter_by_rating(rest_tree, min_rating=0, max_rating=5):
    """
    its function filters the clothing products in rest_tree based on their ratings
    """
    
    rating_tree = build_rating_tree(rest_tree)
    usage = []
    count = 0
    for rating in rating_tree:
        if min_rating <= rating <= max_rating:
            usage.extend(rating_tree[rating])
            count += len(rating_tree[rating])
    return usage

def build_rating_tree(rest_tree):
    """
    It builds a rating tree where each node represents a rating value 
    and its values are the names of clothes with the same rating. 
    It iterates through each item in rest_tree 
    and adds the item to the corresponding node if its rating is not empty. 
    The function then returns the rating tree.
    """
    rating_tree = {}
    for item in rest_tree:
        try:
            rating = float(item['rating'][0:3])
            if rating not in rating_tree:
                rating_tree[rating] = []
            rating_tree[rating].append(item['product'])
        except:
            pass
    return rating_tree

def filter_by_rating(rest_tree, min_rating=0, max_rating=5):
    
    """
    filters out clothes that do not meet the rating criteria.
    It iterates through each item in rest_tree, checks its rating, and adds the name of the item to the usage list 
    if the rating is between min_rating and max_rating. 
    It also counts the number of items that meet the criteria and returns the usage list.
    """

    rating_tree = build_rating_tree(rest_tree)
    usage = []
    count = 0
    for rating in rating_tree:
        if min_rating <= rating <= max_rating:
            usage.extend(rating_tree[rating])
            count += len(rating_tree[rating])
    return usage

def get_intersection(use, price, rating, count,rows):
    """
    Get the intersection of products based on the user's input for use, price, rating, and rating count.
    """
    all_products = get_all_products(rows)
    target = set(use) & set(price) & set(rating) & set(count) & set(all_products)
    usage = list(target)
    count = len(usage)
    return usage, count

def extract_product_info(target, rows):
    # create empty lists to store product information
    price_list = []
    rating_list = []
    rating_count_list = []
    
    for item in rows:
        if item['product'] in target:
            try:
                price = float(item['price'])
                rating = float(item['rating'][0:3])
                rating_count = int(item['rating count'].replace(',', ''))
                product_info = {
                    'product': item['product'],
                    'price': price,
                    'rating': rating,
                    'rating_count': rating_count
                }
                price_list.append(product_info)
                rating_list.append(product_info)
                rating_count_list.append(product_info)
            except:
                print(f"你的内容是错的")
                pass
                
    return price_list, rating_list, rating_count_list



def priority_choice(price_least=False, price_most=False, count_least=False, count_most=False, rate_least=False, rate_most=False, price_info=[], rate_info=[], count_info=[]):
    """
    This function selects the optimal clothing based on the user's priority. 
    If the user selects "price_least" or "price_most", 
        it returns the corresponding clothing data with the lowest or highest price respectively. 
    If the user selects "count_least" or "count_most", 
        it filters out the clothing with null rating count, 
        and returns the corresponding clothing data with the least or most rating count respectively. 
    If the user selects "rate_least" or "rate_most", 
        it filters out the clothing with null rating score, 
        and returns the corresponding clothing data with the least or most rating score respectively.
    """
    if price_least:
        if not price_info:
            return None
        elif len(price_info) == 1:
            return price_info[0]
        else:
            return min(price_info, key=lambda x: x['price'])
    elif price_most:
        if not price_info:
            return None
        elif len(price_info) == 1:
            return price_info[0]
        else:
            return max(price_info, key=lambda x: x['price'])
    elif count_least:
        filtered_count_info = [item for item in count_info if item.get('rating_count') is not None]
        if filtered_count_info:
            return min(filtered_count_info, key=lambda x: x['rating_count'])
        else:
            print("No suitable product found for count least priority.")
        #if not count_info:
        #    return None
        #elif len(count_info) == 1:
        #    return count_info[0]
        #else:
        #    return min(count_info, key=lambda x: x['count'])
    elif count_most:
        filtered_count_info = [item for item in count_info if item.get('rating_count') is not None]
        if filtered_count_info:
            return max(filtered_count_info, key=lambda x: x['rating_count'])
        else:
            print("No suitable product found for count least priority.")

        """
        filtered_count_info = [item for item in count_info if item.get('count') is not None]
        if filtered_count_info:
            return max(filtered_count_info, key=lambda x: x['count'])
        else:
            print("No suitable product found for count most priority.")
        """
        #if not count_info:
        #    return None
        #elif len(count_info) == 1:
        #    return count_info[0]
        #else:
        #    return max(count_info, key=lambda x: x['count'])
    elif rate_least:
        if not rate_info:
            return None
        elif len(rate_info) == 1:
            return rate_info[0]
        else:
            def get_rate(x):
                #return x['rate']
                return x.get('rate', 0)
        return min(rate_info,key=get_rate)
            #return min(rate_info, key=lambda x: x['rate'])
    elif rate_most:
        if not rate_info:
            return None
        elif len(rate_info) == 1:
            return rate_info[0]
        else:
            def get_rate(x):
                #return x['rate']
                return x.get('rate', 0)
        return max(rate_info,key=get_rate)
            #return min(rate_info, key=lambda x: x['rate'])

        '''
        if not rate_info:
            return None
        elif len(rate_info) == 1:
            return rate_info[0]
        else:
            return max(rate_info, key=lambda x: x['rate'])
    else:
        return None
        '''


def get_use_input(rows):
    """
    The purpose of this function is to get the clothing type input from the user 
    and return the clothing data that meets the criteria
    """
    print("The typical search key word include: man, woman, baby, boy, girl and so on")
    while True:
        use = input('What type of clothing product would you like to search for? ')
        #use_search, use_count = filter_and_count_by_product_type(rows, use)
        try:
            least_count = int(use)
        except:
            least_count = 0
        use_search, use_count = get_products_within_rating_count_range(rows, min_count=least_count)
        if use_count == 0:
            print("Your requirement is too high, there is no product that meets your requirement at present")
        else:
            print(f"There are {use_count} choices you may like.")
            return use_search


def get_price_input(rows):
    """
    This function prompts the user to enter the lowest and highest price they can afford, 
    and returns a list of products that fall within that price range.
    """
    print("The price range is 0~1000")
    while True:
        try:
            least_price = int(input('What is the minimum price you are willing to pay? '))
            most_price = int(input('What is the maximum price you are willing to pay?'))
            if least_price < 0 or least_price > most_price:
                print("Invalid price range. Please enter again.")
            else:
                price_search = filter_by_price(rows, min_price=least_price, max_price=most_price)
                return price_search
        except ValueError:
            print("Invalid input. Please enter valid numbers.")

def get_rate_search(rows):
    """
    This function asks the user for their minimum accepted rate and 
    filters the input rows based on the user's selection.
    """
    print("The rate range is 0 ~ 5.0")
    while True:
        try:
            least_rate = int(input('What is the minimum rating you are willing to consider?'))
            if least_rate < 0 or least_rate > 5:
                print("Please enter a rate between 0 and 5.0")
                continue
            else:
                break
        except:
            print("Please enter a valid rate between 0 and 5.0")
            
    rate_search = filter_by_rating(rows, min_rating=least_rate, max_rating=5)
    return rate_search


def get_filtered_rows_by_rating_count(rows):

    """
    Prompts the user for a minimum rating count and returns a filtered list of products that
    meet the specified rating count criteria.
    """

    print("The rating count range is 0 ~ 1000")
    try:
        least_count = int(input('What is the minimum number of ratings you are willing to consider?'))
    except:
        least_count = 0
    count_search, count_count = get_products_within_rating_count_range(rows, min_count=least_count)
    if count_count == 0:
        print("your count requirement to high, try again with low requirement.")
        return get_filtered_rows_by_rating_count(rows)
    else:
        print(f"There are {count_count} products that you may LIKE.")
        return count_search

def get_products_within_rating_count_range(rest_tree, min_count=0, max_count=5000):
    """
    This function takes a list of dictionaries, 
    where each dictionary contains information about a product.
    """
    filtered_data = [item for item in rest_tree if min_count <= int(item['rating count'].replace(',', '')) <= max_count]
    usage = [item['product'] for item in filtered_data]
    count = len(filtered_data)
    return usage,count

def get_filtered_rows_by_rating_count1(rows):
    """
    This function filters rows by rating count.
    It prompts the user for the lowest rating count they are willing to accept and 
    searches for products within that range.
    If no products meet the requirement, it prompts the user to try again.
    If there are products that meet the requirement, 
    it returns a filtered list of rows containing only those products.
    """
    print("The rating count range is 0 ~ 1000")
    try:
        least_count = int(input('What is the minimum count you are willing to consider?'))
    except:
        least_count = 0
    rest_tree = [{'product': row['product'], 'rating count': row['rating count']} for row in rows]
    count_search, count_count = get_products_within_rating_count_range(rest_tree, min_count=least_count)
    if count_count == 0:
        print("your count requirement to high, try again with low requirement.")
        return get_filtered_rows_by_rating_count1(rows)
    else:
        print(f"There are {count_count} products that meet your count requirement.")
        return [row for row in rows if row['product'] in count_search]


def get_user_priority(default='count_most'):
    """
    This function prompts the user to enter their priority for selecting the final product
    The default priority is 'count_most'
    The function returns the user's selected priority or the default priority if the input is invalid
    """
    priority = input('What is the most important factor for you? (default: count_most) ')
    priority_list = ['price_least', 'price_most', 'count_least', 'count_most', 'rate_least', 'rate_most']
    if priority in priority_list:
        return priority
    else:
        return default

def main():
    # check if the data file exists, if not, crawl and save data
    file_exists = exists("clothing.csv")
    if not file_exists:
        crawl_data()
        rows = open_file('clothing.csv')
    else:
        rows = open_file('clothing.csv')

    print('Welcome!')
    while True:
        answer = input("let begin? (yes/no) ").lower()
        if answer == "yes":
            use_search = get_use_input(rows)
            price_search = get_price_input(rows)
            rate_search = get_rate_search(rows)
            count_search = get_filtered_rows_by_rating_count(rows)
            target, target_len = get_intersection(use=use_search, price=price_search, rating=rate_search, count=count_search,rows=open_file('clothing.csv'))
            if target_len == 0:
                print("There are no products that match your search criteria. Please try again with different criteria.")
            elif target_len == 1:
                print(f'There is only one product that satisfies all your requirements.')
                for item in rows:
                    if item['product'] == target[0]:
                        url = item['product url']
                final_product = target[0]
                print(f"Your may like is {final_product}")
                print(f"The link of its is {url}")
            else:
                print(f"There are {target_len} you may like. We will find which you prefer")
                price_info, rate_info, count_info = extract_product_info(target, rows)
                #print(f"你的内容是 {len(rate_info)}")
                #print(f"你的内容是 {rate_info}")
                #print(f"你的内容是 {count_info}")
                print("What is the most important factor for you?")
                print("There are some choose: price_least, price_most, count_least, count_most, rate_least or rate_most")
                priority = get_user_priority()
                options = {'price_least': 0, 'price_most': 1, 'count_least': 2, 'count_most': 3, 'rate_least': 4, 'rate_most': 5}
                index = options.get(priority, 0)
                if index == 0:
                    final_suggestion = priority_choice(price_least=True, price_info=price_info)
                elif index == 1:
                    final_suggestion = priority_choice(price_most=True, price_info=price_info)
                elif index == 2:
                    final_suggestion = priority_choice(count_least=True, count_info=count_info)
                elif index == 3:
                    final_suggestion = priority_choice(count_most=True, count_info=count_info)
                elif index == 4:
                    final_suggestion = priority_choice(rate_least=True, rate_info=rate_info)
                elif index == 5:
                    final_suggestion = priority_choice(rate_most=True, rate_info=rate_info)
                if final_suggestion is not None:
                    final_product = final_suggestion['product']
                    print(f"Your may prefer {final_product}")
                    for item in rows:
                        if item['product'] == final_suggestion['product']:
                            url = item['product url']
                    print(f"The link of its is {url}")
                else:
                    print("No suggestion I can give you.")
        elif answer == "no":
            print("Thank you! See you.")
            break
        else:
            print("Please answer yes or no.")



if __name__ == '__main__':
    main()
