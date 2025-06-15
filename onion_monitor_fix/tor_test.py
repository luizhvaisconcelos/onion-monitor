from seleniumwire import webdriver
from selenium.webdriver.firefox.service import Service

options = webdriver.FirefoxOptions()
options.headless = True
options.set_preference("network.proxy.type", 1)
options.set_preference("network.proxy.socks", "127.0.0.1")
options.set_preference("network.proxy.socks_port", 9050)

# Adicionando o log
service = Service(log_path="geckodriver.log")

print("[INFO] Iniciando navegador com proxy TOR...")
driver = webdriver.Firefox(options=options, service=service)
driver.get("http://check.torproject.org")
print(driver.page_source)
driver.quit()
