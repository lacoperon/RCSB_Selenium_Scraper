'''
Elliot Williams
January 10th, 2018
RCSB Selenium Scraper

If you end up using this code, let me know! I'd probably find what you're doing
very cool.
'''

# # TODO: Generalize to any structure title search with function
# TODO: Add try except block to catch any errors and close the browser window

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
import time

# Configures headless minion Chrome browser and opens to the RCSB Search Page
opts = Options()
# opts.set_headless() # TODO: Change this back
browser = Chrome(options=opts)
browser.get("https://www.rcsb.org/pdb/search/advSearch.do?search=new")

# Selects to search by Structure Title
# (you can change this by looking at the HTML for the page up to this point,
#  and altering the `select_by_value` to that of the dropdown opt you want)
select = Select(browser.find_element_by_id("smartSearchSubtype_0"))
select.select_by_value("StructTitleQuery")
time.sleep(0.1)


# Selects to search specifically for ribosome structures
elt = browser.find_element_by_id("struct.title.value_0")
elt.send_keys("ribosome")

# Clicks the `Submit` button to actually do the search
browser.find_element_by_id("doSearch").click()


# find_elements_by_xpath()
