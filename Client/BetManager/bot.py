from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from lxml.html import fromstring
from json import loads, dump
import urllib.parse
import time
import pickle
import logging
import re

from BetManager.mainApi import ODD_TYPES
from BetManager.config import *

# Global state
driver = None
browser_state = {}

# Helpers
def str_float(x):
    return "{:.2f}".format(x)

def urldecode(s):
    return urllib.parse.unquote(s)

def load_state():
    global browser_state
    browser_state = pickle.load(open("browser.session", "rb"))

def save_state():
    pickle.dump( browser_state, open("browser.session", "wb"))

# Basic bitch
def init():
    global driver, browser_state

    chrome_options = webdriver.ChromeOptions()
    if HEADLESS:
        chrome_options.add_argument("headless")
    chrome_options.add_argument("--window-size=1920,1080")

    try:
        logging.info("Trying to load saved browser session")
        load_state()
        if browser_state["Pinnacle"]:
            Pinnacle.logged_in = True
        if browser_state["1xBet"]:
            OneXBet.logged_in = True
        driver=webdriver.Remote(command_executor=browser_state["url"],desired_capabilities=chrome_options.to_capabilities())
        driver.session_id = browser_state["id"]
        logging.info("Session loaded successfully: {}".format(driver.session_id))

    except Exception as e:
        driver=webdriver.Remote("http://127.0.0.1:9515",desired_capabilities=chrome_options.to_capabilities())

        browser_state["url"] = driver.command_executor._url
        browser_state["id"]  = driver.session_id
        browser_state["Pinnacle"] = False
        browser_state["1xBet"] = False
        logging.info("Failed to load session. New session created: {}".format(driver.session_id))

    save_state()

def scroll():
    SCROLL_PAUSE_TIME = 0.3
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(SCROLL_PAUSE_TIME)

def confirm():
    try:
        WebDriverWait(driver, 2).until(EC.alert_is_present())
        alert = driver.switch_to_alert()
        alert.accept()
    except TimeoutException:
        pass

def alert_text():
    text = ""
    try:
        WebDriverWait(driver, 2).until(EC.alert_is_present())
        alert = driver.switch_to_alert()
        text = alert.text
        alert.accept()
    except TimeoutException:
        pass

    return text

# Individual bookmakers automatization
class Pinnacle(object):
    logged_in = False

    @classmethod
    def login(cls, user, password):
        global browser_state
        if cls.logged_in: return
        cls.logged_in = True
        browser_state["Pinnacle"] = True
        save_state()

        driver.get("https://www.pinnacle.com/en/")
        driver.find_element(By.XPATH, '//input[@name="CustomerId"]').send_keys(user)
        driver.find_element(By.XPATH, '//input[@name="Password"]').send_keys(password)
        driver.find_element(By.XPATH, '//a[@id="loginControlsButton"]').click()

    @classmethod
    def bet(cls, nav, amount):
        driver.get('https://members.pinnacle.com/Sportsbook')
        if re.search(r'Your session has expired', driver.page_source) != None:
            cls.logged_in = False
            cls.login("BC999271", "Bogdan197!")
            logging.info("Restoring session on Pinnacle")

        el = driver.find_element_by_xpath('//a[@href="/Sportsbook/?sport=Soccer"]')
        driver.execute_script("arguments[0].click()", el)
        time.sleep(1)

        driver.get('https://members.pinnacle.com/Sportsbook/Asia/en-GB/Bet/Soccer/Today/Double/null/0/Regular/SportsBookAll/Decimal/45/#tab=Menu&sport=/Sportsbook/Asia/en-GB/GetLines/Soccer/Today/1/null/0/Regular/SportsBookAll/Decimal/45/false/')
        try:
            el = driver.find_element_by_xpath("//*[contains(text(), \"{}\")]".format(urldecode(nav['tab'])))
            driver.execute_script("arguments[0].click()", el)
        except Exception as e:
            pass
        time.sleep(1)

        scrolls = 0
        while scrolls < 80:
            scrolls += 1
            try:
               el = driver.find_element_by_xpath('//a[contains(@href, "Alternate") and contains(@href, \"{}\")]'.format(nav["arbmate"]["eventId"]))
               el.click()
               break
            except Exception as e:
                scroll()
        scroll()
        time.sleep(1)

        el = driver.find_element_by_xpath('//a[contains(@href, \"{}\")]'.format(nav["nav"]))
        driver.execute_script("arguments[0].click()", el)

        confirm()
        driver.find_element(By.XPATH, '//input[@class="stakeInput"]').click()
        driver.find_element(By.XPATH, '//input[@class="stakeInput"]').clear()

        to_type = str_float(amount)
        for c in to_type:
            driver.find_element(By.XPATH, '//input[@class="stakeInput"]').send_keys(c)
            time.sleep(0.2)

        if DEBUG_BETTING:
            logging.info("Actual betting is disabled (Pinnacle)")
            return False

        driver.find_element(By.XPATH, '//a[@id="BetTicketSubmitLink"]').click()
        confirm()

        time.sleep(3)
        if "insufficient funds" in alert_text():
            return False
        return True

class OneXBet(object):
    logged_in = False
    betting_map = {
        ODD_TYPES["1"]: 1,
        ODD_TYPES["X"]: 2,
        ODD_TYPES["2"]: 3,
        ODD_TYPES["1X"]: 4,
        ODD_TYPES["12"]: 5,
        ODD_TYPES["X2"]: 6,
        ODD_TYPES["Over"]: 9,
        ODD_TYPES["Under"]: 10
    }

    @classmethod
    def login(cls, user, password):
        pass

    @classmethod
    def bet(cls, nav, amount):
        if nav["scope"] == "prematch":
            driver.get("https://1xbet.com/en/line/Football/")
            arrows = driver.find_elements(By.XPATH, '//span[@class="strelochka arr_open"]')
            for arrow in arrows:
                try:
                    driver.execute_script("arguments[0].click()", arrow)
                    time.sleep(0.05)
                except Exception as e:
                    pass

                try:
                    leagueId = nav["leagueId"]
                    el = driver.find_element_by_xpath("//a[contains(@href, \"{}\")]".format(leagueId))
                    driver.execute_script("arguments[0].click()", el)
                    break
                except Exception as e:
                    pass
        else:
            driver.get("https://1xbet.com/en/live/Football/")
        time.sleep(3)

        eventId = nav["eventId"]
        el = driver.find_element_by_xpath("//a[contains(@href, \"{}\")]".format(eventId))
        driver.execute_script("arguments[0].click()", el)
        time.sleep(0.25)

        type_id = nav["type_id"]
        if type_id == ODD_TYPES["Over"] or type_id == ODD_TYPES["Under"]:
            to_click_id = OneXBet.betting_map[type_id]
            to_click_hc = None

            if type_id == ODD_TYPES["Over"]:
                to_click_hc = "Total Over {:.1f}".format(nav["hc"]).replace('.0', '')
            else:
                to_click_hc = "Total Under {:.1f}".format(nav["hc"]).replace('.0', '')

            el = driver.find_element_by_xpath("//span[@data-type=\"{}\" and contains(text(), \"{}\")]".format(to_click_id, to_click_hc))
            el.click()
        else:
            to_click = OneXBet.betting_map[type_id]
            el = driver.find_element_by_xpath("//span[@class=\"bet_type\" and @data-type=\"{}\"]".format(to_click))
            driver.execute_script("arguments[0].click()", el)

        el = driver.find_element_by_xpath("//input[@class=\"c-spinner__input bet_sum_input\"]")
        el.click()
        time.sleep(0.25)
        el.clear()
        el.send_keys(str_float(amount))

        time.sleep(0.25)
        el = driver.find_element_by_xpath("//button[contains(text(), \"place a bet\")]")

        if DEBUG_BETTING:
            logging.info("Actual betting is disabled (1xbet)")
            return False

        el.click()

        time.sleep(5)
        return True

# Generic wrappers for login/betting
def login(bookmaker):
    if bookmaker == "Pinnacle":
        Pinnacle.login("BC999271", "Bogdan197!")
    elif bookmaker == "1xBet":
        pass
        # TODO: bypass ReCaptcha v3
        #OneXBet.login("bocristian20@gmail.com", "Bogdan1977!")

def bet(bookmaker, nav, amount):
    if bookmaker == "Pinnacle":
        return Pinnacle.bet(nav, amount)
    elif bookmaker == "1xBet":
        return OneXBet.bet(nav, amount)
    return False

# Default initialization
if not DEBUG_BOT_DISABLED:
    init()

# Testing code
def main():
    pass
if __name__ == "__main__":
    main()
