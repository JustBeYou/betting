from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from lxml.html import fromstring
import urllib2
import time
import pickle

def urlencode(s):
    return urllib2.quote(s)

def urldecode(s):
    return urllib2.unquote(s).decode('utf8')

driver = None
browser_state = {}
def load_state():
    global browser_state
    browser_state = pickle.load( open( "browser.session", "rb" ) )
def save_state():
    pickle.dump( browser_state, open( "browser.session", "wb" ) )

class SessionRemote(webdriver.Remote):
    def start_session(self, desired_capabilities, browser_profile=None):
        # Skip the NEW_SESSION command issued by the original driver
        # and set only some required attributes
        self.w3c = True

# ---------------------------------------------------------------------------------------------------------
class Pinnacle(object):
    logged_in = False

    @classmethod
    def login(cls, user, password):
        global browser_state
        if cls.logged_in: return
        cls.logged_in = True
        browser_state["Pinnacle"] = True
        save_state()

        print ("[*] Login with {}:{}".format(user, password))

        driver.get("https://www.pinnacle.com/en/")
        driver.find_element(By.XPATH, '//input[@name="CustomerId"]').send_keys(user)
        driver.find_element(By.XPATH, '//input[@name="Password"]').send_keys(password)
        driver.find_element(By.XPATH, '//a[@id="loginControlsButton"]').click()

        # save the page, debugging only purpose
        #with open('save.html', 'w') as f:
        #    f.write(driver.page_source.encode("utf-8"))
        print ("[+] Done")
    @classmethod
    def bet(cls, nav, amount):
        driver.get('https://members.pinnacle.com/Sportsbook')
        try:
            el = driver.find_element_by_xpath("//*[contains(text(), \"{}\")]".format(urldecode(nav['tab'])))
            el.click()
        except:
            pass
        time.sleep(0.5)
        driver.find_element(By.XPATH, '//span[@class="RefreshCountDown Live"]').click()
        time.sleep(0.5)
        while True:
            try:
                el = driver.find_element_by_xpath("//a[contains(@href, \"{}\")]".format(urldecode(nav['nav'])))
                print ("Bet on: {}".format(el))
                break
            except Exception as e:
                scroll()

        el.click()
        time.sleep(0.5)
        confirm()
        driver.find_element(By.XPATH, '//input[@class="stakeInput"]').click()
        driver.find_element(By.XPATH, '//input[@class="stakeInput"]').send_keys(str(amount))
        driver.find_element(By.XPATH, '//a[@id="BetTicketSubmitLink"]').click()
        confirm()
        time.sleep(0.5)

        if "insufficient funds" in alert_text():
            return False
        return True
# ---------------------------------------------------------------------------------------------------

class OneXBet(object):
    logged_in = False

    @classmethod
    def login(cls, user, password):
        logged_in = True
        driver.get("https://1xbet.com/en/line/Football/")

    @classmethod
    def bet(cls, nav, amount):
        print (nav)

        arrows = driver.find_elements(By.XPATH, '//span[@class="strelochka arr_open"]')
        for arrow in arrows:
            try:
                driver.execute_script("arguments[0].click()", arrow)
                time.sleep(0.05)
            except Exception as e:
                print (e)

            try:
                leagueId = nav["leagueId"]
                el = driver.find_element_by_xpath("//a[contains(@href, \"{}\")]".format(leagueId))
                driver.execute_script("arguments[0].click()", el)
                break
            except Exception as e:
                print (e)

        eventId = nav["eventId"]
        time.sleep(0.5)
        el = driver.find_element_by_xpath("//a[contains(@href, \"{}\")]".format(eventId))
        driver.execute_script("arguments[0].click()", el)

        return False
# ---------------------------------------------------------------------------------------------------


def init():
    global driver, browser_state

    try:
        load_state()
        if browser_state["Pinnacle"]:
            Pinnacle.logged_in = True
        if browser_state["1xBet"]:
            OneXBet.logged_in = True
        #driver = SessionRemote(command_executor=browser_state["url"],desired_capabilities=webdriver.DesiredCapabilities.FIREFOX)
        driver=webdriver.Remote(command_executor=browser_state["url"],desired_capabilities=webdriver.DesiredCapabilities.CHROME)
        driver.session_id = browser_state["id"]

    except Exception as e:
        print ("Nothing to load {}".format(e))
        options = Options()
        # don't open the browser
        options.headless = False
        #driver = SessionRemote("http://127.0.0.1:4444",desired_capabilities=webdriver.DesiredCapabilities.FIREFOX)
        driver=webdriver.Remote("http://127.0.0.1:9515",desired_capabilities=webdriver.DesiredCapabilities.CHROME)

        browser_state["url"] = driver.command_executor._url
        browser_state["id"]  = driver.session_id
        browser_state["Pinnacle"] = False
        browser_state["1xBet"] = False

    save_state()
def destroy():
    global driver
    #driver.quit()
    #driver = None
    pass

def scroll():
    SCROLL_PAUSE_TIME = 0.5

    # Scroll down to bottom
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # Wait to load page
    time.sleep(SCROLL_PAUSE_TIME)

def confirm():
    try:
        WebDriverWait(driver, 3).until(EC.alert_is_present())

        alert = driver.switch_to_alert()
        alert.accept()
        print("alert accepted")
    except TimeoutException:
        print("no alert")

def alert_text():
    try:
        WebDriverWait(driver, 3).until(EC.alert_is_present())
        alert = driver.switch_to_alert()
        text = alert.text
        alert.accept()
        return text
    except TimeoutException:
        print("no alert")

    return ""

init()
def login(bookmaker):
    if bookmaker == "Pinnacle":
        Pinnacle.login("BC999271", "Bogdan197!")
    elif bookmaker == "1xBet":
        OneXBet.login("bocristian20@gmail.com", "Bogdan1977!")

def bet(bookmaker, nav, amount):
    if bookmaker == "Pinnacle":
        return Pinnacle.bet(nav, amount)
    elif bookmaker == "1xBet":
        return OneXBet.bet(nav, amount)
    return False
