# This is a sample Python script.
from decimal import Decimal
from typing import List

# Press Ctrl+F5 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import selenium
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.common.exceptions import TimeoutException

import DbCon
from Busqueda import Busqueda

lista : List[Busqueda] = []
con = DbCon.Connector()

def cheaperthan(*args, price: int):
    for x in args:
        if price>=x:
            print(x)

def waituntilcards():
    try:
        myElem = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.XPATH, "//a[@class='ItemCardList__item']")))

    except TimeoutException:
        print("Loading took too much time!")

def orderby():
    option = ["", "newest", "closest", "price_low_to_high", "price_high_to_low"]
    curropt :int = int(input("Ordena por [relevante, nuevo, mas cercano, bajo a alto ,alto a bajo]"))
    return  option[curropt]
def selectprod():
    product = input("que producto quieres ")
    return  product
def clickcookies():
    cookies = driver.find_element(By.XPATH, '/html/body/div/div[2]/div/div[1]/div/div[2]/div/button[2]')
    cookies.click()

def setoptions():
    options = Options()
    options.headless = True  # hide GUI
    options.add_argument("--window-size=1920,1080")  # set window size to native GUI size
    options.add_argument("start-maximized")
    prefs = {"profile.managed_default_content_settings.images": 2}
    options.add_experimental_option("prefs", prefs)
    return options

driver = webdriver.Chrome(options=setoptions())
order = orderby()
producto = selectprod()
driver.get("https://es.wallapop.com/app/search?filters_source=search_box&keywords="+producto+"&longitude=-3.69196&latitude=40.41956"+"&order_by="+order)

try:
    myElem = WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.XPATH, '//tsl-public')))

except TimeoutException:
    print("Loading took too much time!")

clickcookies()
waituntilcards()
elements = driver.find_elements(By.XPATH, "//p[@class='ItemCard__title my-1']")
price = driver.find_elements(By.XPATH, "//span[@class ='ItemCard__price ItemCard__price--bold']")

preciomedio = 0
for i in range(price.__len__()):
    if price[i].text.__contains__("."):
     newstr = price[i].text.replace(".", "")

     f = float(Decimal(newstr.replace(",", ".").removesuffix(" €")))
     print(f)
    #Para precios muy garndes
    else:
     f = float(Decimal(price[i].text.removesuffix(" €").replace(",", ".")))
    b : Busqueda= Busqueda(elements[i].text, f , "testusr")
    con.inserta(b)
    preciomedio += f
rows =  con.selectall()
for i in rows:
    print(i)
print("El precio medio del producto es: ")
print(preciomedio/price.__len__())





    # Press F9 to toggle the breakpoint.

# Press the green button in the gutter to run the script.


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
