from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from datetime import datetime
import re
import time
import logging
import csv

logging.basicConfig(level=logging.INFO)
# PROXY = "127.0.0.1:43619"
PROXY = "127.0.0.1:42847"

co = webdriver.ChromeOptions()
co.add_argument("--proxy-server=%s" % PROXY)

country_code = "jp"
# co.add_argument("--lang=ja_JP")

chrome = webdriver.Chrome(options=co)
# chrome.implicitly_wait(5)

csv_header = ["name", "time", "url", "company", "company_url", "category", "category_url", "comment_number",
              "comment_score", "score5ratio", "score4ratio", "score3ratio", "score2ratio", "score1ratio",
              "updatetime", "size", "android", "screen", "installnum", "version"]

with open("data_out.csv", "a") as f:
    f_csv = csv.DictWriter(f, csv_header)
    f_csv.writeheader()

URLSTACK = [("basepage", "https://play.google.com/store/apps/category/GAME" + "?gl=" + country_code)]
# URLSTACK = [('morepage', 'https://play.google.com/store/apps/collection/cluster?clp=ogoQCAESBEdBTUUqAggCUgIIAQ%3D%3D:S:ANO1ljJlEdM&gsr=ChOiChAIARIER0FNRSoCCAJSAggB:S:ANO1ljJdubc')]
# URLSTACK = [('catpage', 'https://play.google.com/store/apps/category/GAME_STRATEGY')]
# URLSTACK = [('detailpage', 'https://play.google.com/store/apps/details?id=com.nianticlabs.pokemongo')]

def scrollToBottomUntillNotLoad(chrome, xpathstr):
    oldEnum = 0
    cs = chrome.find_elements_by_xpath(xpathstr)
    newEnum = len(cs)

    while newEnum != oldEnum:
        # print(newEnum, oldEnum)
        oldEnum = newEnum
        chrome.find_element_by_tag_name('body').send_keys(Keys.END)
        time.sleep(2)
        cs = chrome.find_elements_by_xpath(xpathstr)
        newEnum = len(cs)

noLoopMap = {}

def grabFromStack(chrome):
    while len(URLSTACK)>0:
        u = URLSTACK.pop(0)
        if u[1] not in noLoopMap:
            noLoopMap[u[1]] = 1
            logging.info("type:{},url:{}".format(u[0], u[1]))
            if u[0] == "basepage":
                chrome.get(u[1])
                scrollToBottomUntillNotLoad(chrome, "//div[@class='wXUyZd']/a")

                ms = chrome.find_elements_by_xpath("//div[@class='W9yFB']/a")
                for ele in ms:
                    URLSTACK.append(("morepage", ele.get_attribute('href').strip()))

                cs = chrome.find_elements_by_xpath("//div/ul/li/ul/li/a[@class='r2Osbf']")
                for i in range(17):
                    URLSTACK.append(("catpage", cs[-1-i].get_attribute('href').strip()))

                hs = chrome.find_elements_by_xpath("//div[@class='wXUyZd']/a")
                for i in hs:
                    URLSTACK.append(("detailpage", i.get_attribute('href').strip()))
            elif u[0] == "morepage":
                chrome.get(u[1])
                scrollToBottomUntillNotLoad(chrome, "//div[@class='wXUyZd']/a")

                hs = chrome.find_elements_by_xpath("//div[@class='wXUyZd']/a")
                for i in hs:
                    URLSTACK.append(("detailpage", i.get_attribute('href').strip()))
            elif u[0] == "catpage":
                chrome.get(u[1])
                scrollToBottomUntillNotLoad(chrome, "//div[@class='wXUyZd']/a")
                hs = chrome.find_elements_by_xpath("//div[@class='wXUyZd']/a")
                for i in hs:
                    URLSTACK.append(("detailpage", i.get_attribute('href').strip()))
                ms = chrome.find_elements_by_xpath("//div[@class='W9yFB']/a")
                for ele in ms:
                    URLSTACK.append(("morepage", ele.get_attribute('href').strip()))
            elif u[0] == "detailpage":
                ginfo = {"url":u[1],"time":datetime.utcnow().timestamp()}
                chrome.get(u[1])
                title = chrome.find_elements_by_xpath("//h1[@class='AHFaub']/span")
                ginfo["name"] = title[0].text if len(title) > 0 else ""

                company = chrome.find_elements_by_xpath("//span[contains(@class,'T32cc')]/a")
                # logging.info("company Length is "+str(len(company)))
                ginfo["company"] = company[0].text if len(company) >= 2 else ""
                ginfo["company_url"] = company[0].get_attribute("href") if len(company) >= 2 else ""
                ginfo["category"] = company[1].text if len(company) >= 2 else ""
                ginfo["category_url"] = company[1].get_attribute("href") if len(company) >= 2 else ""

                comment_num = chrome.find_elements_by_xpath("//span[contains(@class,'AYi5wd')]/span")
                ginfo["comment_number"] = comment_num[0].text if len(comment_num) > 0 else ""

                comment_score = chrome.find_elements_by_xpath("//div[@class='K9wGie']/div[@class='BHMmbe']")
                ginfo["comment_score"] = comment_score[0].text if len(comment_score) > 0 else ""

                score_detail = chrome.find_elements_by_xpath("//div[@class='mMF0fd']/span[contains(@class,'L2o20d')]")
                for index, s in enumerate(score_detail):
                    s_num = s.get_attribute("style")
                    sr = re.search("(\d+)%", s_num)
                    ginfo["score"+str(5-index)+"ratio"] = sr.group(1) if sr else "0"

                anchor_list = chrome.find_elements_by_xpath("//div[@class='hAyfc']")
                for ac in anchor_list:
                    ac_title = ac.find_elements_by_xpath("div[@class='BgcNfc']")
                    ac_con = ac.find_elements_by_xpath("span/div/span[@class='htlgb']")
                    if len(ac_title) > 0 and len(ac_con) > 0:
                        t = ac_title[0].text.strip()
                        c = ac_con[0].text.strip()
                        if t == "更新日期":
                            ginfo["updatetime"] = c
                        elif t == "大小":
                            ginfo["size"] = c
                        elif t == "Android 系统版本要求":
                            ginfo["android"] = c
                        elif t == "内容分级":
                            ginfo["screen"] = c
                        elif t == "安装次数":
                            ginfo["installnum"] = c
                        elif t == "当前版本":
                            ginfo["version"] = c
                for item in csv_header:
                    if item not in ginfo:
                        ginfo[item] = ""
                # print(ginfo)
                with open("data_out.csv", "a") as f:
                    f_csv = csv.DictWriter(f, csv_header)
                    f_csv.writerow(ginfo)




# def grabBaseGamePage(chrome): #grab content from https://play.google.com/store/apps/category/GAME
#     chrome.get("https://play.google.com/store/apps/category/GAME")
#     hs = chrome.find_elements_by_xpath("//div[@class='wXUyZd']/a")
#     for i in hs:
#         print(i.get_attribute('href'))


if __name__ == "__main__":
    grabFromStack(chrome)
    print(URLSTACK)
    print(len(URLSTACK))