# torcheck.py
import logging
from seleniumwire import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import WebDriverException

def executar_teste_tor():
    log_path = "geckodriver.log"
    try:
        options = webdriver.FirefoxOptions()
        options.headless = True
        options.set_preference("network.proxy.type", 1)
        options.set_preference("network.proxy.socks", "127.0.0.1")
        options.set_preference("network.proxy.socks_port", 9050)

        service = Service(log_path=log_path)
        driver = webdriver.Firefox(options=options, service=service)
        driver.get("https://check.torproject.org")
        resultado = driver.page_source
        driver.quit()
        return resultado
    except WebDriverException as e:
        return f"Erro ao iniciar navegador: {e}"
