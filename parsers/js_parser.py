import requests
from bs4 import BeautifulSoup
import json
import time


PRODUCT_NUM = 40

def write_down_products(products):
    save_path = r'C:\Users\ASUS\OneDrive\Рабочий стол\!!!!Рыбалка\FishingUpdatesBot\temp_parsed_data\jpsnasti_products.json'
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=4)


def parse_jpsnasti():
    url = 'https://www.jpsnasti.ru/novinki'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        products = []
        
        product_cards = soup.find_all('div', class_='p-card')[:PRODUCT_NUM]
        
        for card in product_cards:
            # Извлекаем название и ссылку
            title_link = card.find('a', itemprop='name')
            if not title_link:
                continue
                
            title = title_link.text.strip()
            product_url = 'https://www.jpsnasti.ru' + title_link['href']

            # Цена
            price_elem = card.find('span', class_='price')
            price = price_elem.text.strip().replace(' ', '').replace('₽', '') if price_elem else None

            # Старая цена и скидка
            old_price_elem = card.find('span', class_='oldprice')
            old_price = old_price_elem.text.strip().replace(' ', '').replace('₽', '') if old_price_elem else None
            
            discount_elem = card.find('span', class_='discount')
            discount = discount_elem.text.strip() if discount_elem else None

            # Изображение
            img_elem = card.find('div', class_='pic').find('img')
            image_url = img_elem['src'] if img_elem else None

            # Наличие
            exist_elem = card.find('div', class_='exist')
            availability = exist_elem.text.strip() if exist_elem else 'В наличии'

            product_data = {
                'title': title,
                'price': float(price) if price else None,
                'old_price': float(old_price) if old_price else None,
                'discount': discount,
                'image_url': image_url,
                'product_url': product_url,
                'availability': availability
            }
            
            products.append(product_data)
            
        return products
    
    except Exception as e:
        print(f'Произошла ошибка: {str(e)}')

if __name__ == '__main__':
    prev_products = parse_jpsnasti()
    prev_timestamp = time.time()

    while True:
        temp_timestamp = time.time()

        if temp_timestamp - prev_timestamp >= 300:
            prev_timestamp = temp_timestamp

            temp_products = parse_jpsnasti()
            for i in range(PRODUCT_NUM):
                if temp_products[i] != prev_products[i]:
                    allert_products = temp_products[::5] # их алертим
                    
