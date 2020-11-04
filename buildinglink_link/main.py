from collections import defaultdict
from datetime import datetime, timedelta
import logging
import time

from pkg_resources import resource_stream
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
import yaml

BASE_URL = "https://www.buildinglink.com/V2"
RESERVE_PAGE = "Tenant/Amenities/NewReservation.aspx"
NAME_MAP = {"Clay": "David Hambrick", "Semmie": "Semmie Kim"}
AMENITY_MAP = {"": "[12th Floor] Fitness Center (", "pool": "[12th Floor] Saltwater Lap Pool ("}


def load_page(driver, page):
    driver.get(page)
    try:
        driver.find_element_by_id("UserName")
    except NoSuchElementException:
        return
    logging.info("Logging in.")
    creds = yaml.load(resource_stream("buildinglink_link", "config/creds.yaml"))
    username_box = driver.find_element_by_id("UserName")
    username_box.clear()
    username_box.send_keys(creds["username"])

    password_box = driver.find_element_by_id("Password")
    password_box.clear()
    password_box.send_keys(creds["password"])
    password_box.send_keys(Keys.ENTER)


def next_day_schedule(today):
    schedule = yaml.load(resource_stream("buildinglink_link", "config/schedule.yaml"))
    tomorrow_day_of_week = (today.date() + timedelta(days=1)).strftime("%A")
    tomorrow_schedule = defaultdict(list)
    for person, timeslot_amenity in schedule.get(tomorrow_day_of_week, {}).items():
        if not timeslot_amenity:
            continue
        tsa_list = timeslot_amenity.split() + [""]
        amenity_timeslot_str = AMENITY_MAP[tsa_list[1]] + tsa_list[0]
        tomorrow_schedule[amenity_timeslot_str].append(NAME_MAP[person])
    return tomorrow_schedule.items()


def main():
    logging.basicConfig(level=logging.INFO)
    driver = webdriver.Firefox()
    driver.implicitly_wait(10)
    tomorrow_str = (datetime.now() + timedelta(days=1)).strftime("%A, %B %d, %Y")
    for amenity_timeslot, people in next_day_schedule(datetime.now()):
        logging.info("Registering %s for %s on %s.", people, amenity_timeslot + ")", tomorrow_str)
        load_page(driver, f"{BASE_URL}/{RESERVE_PAGE}")
        driver.find_element_by_partial_link_text(amenity_timeslot).click()
        occupant_dropdown = driver.find_element_by_id("ctl00_ContentPlaceHolder1_OccupantList")
        occupant_dropdown.click()
        for resident in driver.find_element_by_id("ctl00_ContentPlaceHolder1_OccupantList_DropDown").find_elements_by_tag_name("label"):
            res_input = resident.find_element_by_tag_name("input")
            if (resident.text in people) ^ (res_input.is_selected()):
                res_input.click()
        occupant_dropdown.click()
        time.sleep(2)
        driver.find_element_by_xpath(f"//td[@title='{tomorrow_str}']").click()
        try:
            driver.find_element_by_id("ctl00_ContentPlaceHolder1_liabilityWaiverAgreeTextbox").send_keys("Yes")
        except NoSuchElementException:
            pass
        time.sleep(2)
        save_button = driver.find_element_by_id("ctl00_ContentPlaceHolder1_FooterSaveButton")
        save_button.find_element_by_tag_name("span").click()
    time.sleep(5)
    driver.quit()