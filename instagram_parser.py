import os
import re
import tempfile
import time
import threading

from urllib import request

import lxml.html as html
from selenium import webdriver

INSTAGRAM_LOGIN_PAGE = 'https://www.instagram.com/accounts/login/'
INSTAGRAM_HOME_PAGE = 'https://www.instagram.com'
# scrolls_count - how much it will scroll the profile
# more photos\videos  load partially each scroll-down action
# we doesn't know for sure how much we need to reach the end
# let it be 20
SCROLLS_COUNT = 5


def open_browser_with_options():
    """
    opens Chrome browser with some special attributes
    :return: webdriver object
    """
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")  # This make Chromium reachable
    options.add_argument("--no-default-browser-check")  # Overrides default choices
    options.add_argument("--no-first-run")
    options.add_argument("--disable-default-apps")
    return webdriver.Chrome(chrome_options=options)


def login(web_browser, account_login, account_password):
    """
    login with setted login and password account to instagram via opened webdriver
    :param web_browser: webdriver object
    :param account_login: str with login
    :param password: str with password
    :return: nothing
    """
    web_browser.get(INSTAGRAM_LOGIN_PAGE)
    time.sleep(1)  # give browser some time to load

    # find a login field
    login_field = web_browser.find_element_by_css_selector(
        "#react-root > section > main > div > article > div > div:nth-child(1) > div > form > div:nth-child(1) > div > input")

    # fidn a password field
    password_field = web_browser.find_element_by_css_selector(
        "#react-root > section > main > div > article > div > div:nth-child(1) > div > form > div:nth-child(2) > div > input")

    # a little user-emulation:
    # click on each field and enter text inside
    # this makes login button become visible, et least for now

    login_field.click()
    login_field.send_keys(account_login)

    password_field.click()
    password_field.send_keys(account_password)

    # find login button and click on it with a little delay
    login_button = browser.find_element_by_xpath(
        '//*[@id="react-root"]/section/main/div/article/div/div[1]/div/form/span/button')

    time.sleep(1)

    login_button.click()

    time.sleep(1)


def switch_to_needed_account(web_browser, account_name):
    """
    switching to instagram/account_name/ page to parse the videos
    :param web_browser: webdriver object
    :param account_name: profile name as str
    :return: temp_file path with page_source
    """

    # create the global link
    web_browser.get(INSTAGRAM_HOME_PAGE + "/" + account_name + "/?hl=ru")

    # create filepath to temp directory
    tmp_file = os.path.join(tempfile.gettempdir(), "insta_profile.txt")

    # scroll down to find expand all posts in profile
    web_browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # find button "load more" and click on it, wait loading
    load_button = web_browser.find_element_by_xpath('//*[@id="react-root"]/section/main/article/div/a')
    load_button.click()

    time.sleep(2)

    for scroll in range(SCROLLS_COUNT):
        web_browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    # save all page source
    with open(tmp_file, "w", encoding="utf-8") as fp:
        fp.write(web_browser.page_source)

    return tmp_file


def parse_profile(source_file):
    """
    parse insta profile source page to find link on video
    :param source_file: filepath
    :return: list with strings, contains urls on videos
    """
    correct_url_re = re.compile(r'.*?taken-by=\w+$')

    # parse all links from source page with lxml.html lib
    opened_page = html.parse(source_file)
    urls = list(opened_page.getroot().iterlinks())

    video_urls = list()
    for url in urls:
        # filter some trash and notneeded links,only with correct_url_re regex
        if correct_url_re.match(url[2]):
            # look for url with video icon inside on of a child, it mark that it's link on video
            video_icons = url[0].xpath('*/div/span[contains(@class, "coreSpriteVideoIconLarge")]')
            video_icons_counter = len(video_icons)
            # if url contain video icon, so it's a video, add it to the list
            if video_icons_counter:
                video_urls.append(url[2])
    return video_urls


def parse_video_urls(web_browser, urls):
    """
    just opens a video url and parses global video url
    :param web_browser: webdriver object
    :param urls: urls on pages with video
    :return: global video urls list
    """
    videos = list()
    for url in urls:
        global_url = INSTAGRAM_HOME_PAGE + url
        web_browser.get(global_url)
        video_link = web_browser.find_element_by_xpath("//video[1]")
        videos.append(video_link.get_attribute("src"))
        time.sleep(1)
    return videos


def download_file(link, file_name):
    try:
        request.urlretrieve(link, file_name)
        result = "success"
    except:
        result = "fail"
    finally:
        print(f"{time.ctime()}: {link} - {result}\n")


def download_video_files(urls, account):
    """
    simple download files in ~/Downloads/profile_folder
    :param urls: str list
    :param account str
    :return: nothing
    """
    folder = os.path.join(os.path.expanduser("~"), "Downloads")
    acc_folder = os.path.join(folder, account)
    os.mkdir(acc_folder)

    threads = []

    for numb, link in enumerate(urls):
        file_name = os.path.join(acc_folder, f"{account}_{numb}.mp4")
        thread = threading.Thread(target=download_file, args=(link, file_name))
        threads.append(thread)
        thread.start()

    [thread.join() for thread in threads]


if __name__ == "__main__":
    TEST_LOGIN = input("Login: ")
    TEST_PASSWORD = input("Password: ")
    NEEDED_ACCOUNT = input("Instagram Account: ")
    if TEST_LOGIN and TEST_PASSWORD and NEEDED_ACCOUNT:
        # create webdriver object
        browser = open_browser_with_options()

        # login with TEST_LOGIN and TEST_PASSWORD
        login(browser, TEST_LOGIN, TEST_PASSWORD)

        # switch to needed page and save it to tmp file
        saved_page = switch_to_needed_account(browser, NEEDED_ACCOUNT)

        # parse tmp file to find video pages
        video_pages = parse_profile(saved_page)

        # go to each video page and take video url from there
        video_urls = parse_video_urls(browser, video_pages)

        browser.close()

        download_video_files(video_urls, NEEDED_ACCOUNT)
