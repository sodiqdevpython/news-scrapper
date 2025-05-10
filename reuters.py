import requests
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

def req():
    url = "https://www.reuters.com/world/pope-leo-takes-first-trip-outside-vatican-visiting-shrine-near-rome-2025-05-10/"
    headers = {
        "User-Agent": "Mozilla/5.0",
    }

    resp = requests.get(url, headers=headers)

    if resp.status_code == 200:
        print(resp)
    else:
        print("Xato:", resp.status_code)


def sel():
    driver = uc.Chrome()
    driver.get("https://www.reuters.com/world/pope-leo-takes-first-trip-outside-vatican-visiting-shrine-near-rome-2025-05-10/")
    driver.implicitly_wait(10)

    title = driver.find_element(By.XPATH, '/html/body/div[1]/div[4]/div/main/article/div[1]/div/header/div/div/h1')
    print("✅ Title:", title.text)

    driver.quit()

sel()