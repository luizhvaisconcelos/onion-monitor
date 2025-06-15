
from seleniumwire import webdriver
from bs4 import BeautifulSoup

def buscar_com_selenium(termo):
    options = {
        'proxy': {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050',
            'no_proxy': 'localhost,127.0.0.1'
        }
    }

    url = f"https://ahmia.fi/search/?q={termo}"

    driver = webdriver.Firefox(seleniumwire_options=options)
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True) if '.onion' in a['href']]
    driver.quit()
    return links
