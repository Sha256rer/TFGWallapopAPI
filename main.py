from decimal import Decimal
from typing import List
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from models import Busqueda, Producto


# Configuración Selenium
def set_options():
    options = Options()
    options.headless = True
    options.add_argument("--window-size=1920,1080")
    options.add_argument("start-maximized")
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    return options

def click_cookies(driver):
    try:
        cookies = driver.find_element(By.XPATH, '/html/body/div/div[2]/div/div[1]/div/div[2]/div/button[2]')
        cookies.click()
    except:
        print("No se encontraron cookies o ya estaban aceptadas.")

def wait_for_cards(driver):
    try:
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH, "//a[@class='ItemCardList__item']")))
    except TimeoutException:
        print("Los productos tardaron demasiado en cargar.")

def order_by() -> str:
    options = ["", "newest", "closest", "price_low_to_high", "price_high_to_low"]
    curropt = int(input("Ordena por [0: relevante, 1: nuevo, 2: más cercano, 3: bajo a alto, 4: alto a bajo]: "))
    return options[curropt]

def select_product() -> str:
    return input("¿Qué producto quieres buscar? ")

# Parsing de precios
def parse_price(text: str) -> float:
    cleaned = text.replace(".", "").replace(" €", "").replace(",", ".")
    return float(Decimal(cleaned))
def parse_uuid(card: WebElement) -> str:
    curr = card.get_attribute("href")
    url = curr.rsplit("-", 1)

    #mostramos solo el segundo element, id del producto
    return str(url[1])

# Lógica principal
def run_scraper(producto: str, order: str, usuario: str) -> List[Busqueda]:
    driver = webdriver.Chrome(options=set_options())
    url = f"https://es.wallapop.com/app/search?filters_source=search_box&keywords={producto}&longitude=-3.69196&latitude=40.41956&order_by={order}"
    driver.get(url)

    try:
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, '//tsl-public')))
    except TimeoutException:
        print("La página principal tardó demasiado en cargar.")
        driver.quit()
        return []

    click_cookies(driver)
    wait_for_cards(driver)
    card = driver.find_elements(By.XPATH, "//a[contains(@class, 'ItemCard')]")

    titles = driver.find_elements(By.XPATH, "//p[@class='ItemCard__title my-1']")
    prices = driver.find_elements(By.XPATH, "//span[@class ='ItemCard__price ItemCard__price--bold']")
    #List[producto]

    resultados = []
    for i in range(min(len(titles), len(prices))):
        try:
            precio = parse_price(prices[i].text)
            titulo = titles[i].text
            uuid = parse_uuid(card[i])
            producto = Producto(nombre=titulo, precio=precio, uuid=uuid)
            resultados.append(producto)
        except Exception as e:
            print(f"Error al procesar resultado {i}: {e}")

    driver.quit()
    return resultados

# Ejecución directa
if __name__ == "__main__":
    producto = select_product()
    orden = order_by()
    usuario = "testusr"  # Aquí podrías pedir el nombre o pasarlo desde Flask
    resultados = run_scraper(producto, orden, usuario)

    for r in resultados:
        print(f"{r.nombre} - {r.precio}€ - {r.uuid}")




    # Press F9 to toggle the breakpoint.

# Press the green button in the gutter to run the script.


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
