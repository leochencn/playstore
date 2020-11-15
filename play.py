from selenium import webdriver
PROXY = "127.0.0.1:43619"

co = webdriver.ChromeOptions()
co.add_argument("--proxy-server=%s" % PROXY)


chrome = webdriver.Chrome(options=co)

if __name__ == "__main__":
    chrome.get("https://www.google.com")