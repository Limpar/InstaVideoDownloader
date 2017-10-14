import os
import os.path as path
import re
import tempfile
import time
from urllib import request

import lxml.html as html
from selenium import webdriver

INSTAGRAM_LOGIN_PAGE = 'https://www.instagram.com/accounts/login/'
INSTAGRAM_HOME_PAGE = 'https://www.instagram.com'

TEST_LOGIN = ""
TEST_PASSWORD = ""
NEEDED_ACCOUNT = ""


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


def login(web_browser, login, password):
    """
    login with setted login and password account to instagram via opened webdriver
    :param web_browser: webdriver object
    :param login: str with login
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
    login_field.send_keys(login)

    password_field.click()
    password_field.send_keys(password)

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
    tmp_file = path.join(tempfile.gettempdir(), "insta_profile.txt")

    # scroll down to find expand all posts in profile
    web_browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # find button "load more" and click on it, wait loading
    load_button = web_browser.find_element_by_xpath('//*[@id="react-root"]/section/main/article/div/a')
    load_button.click()

    time.sleep(2)

    # scrolls_count - how much it will scroll the profile
    # more photos\videos  load partially each scroll-down action
    # we doesn't know for sure how much we need to reach the end
    # let it be 20
    scrolls_count = 20
    for scroll in range(scrolls_count):
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


def download_video_files(urls, account):
    """
    simple download files in ~/Downlads/profile_folder
    saves log file ~/Downlaods/insta_downloader_log_file.txt
    with urls on videos and result of downloading
    sometimes there is a 404error happen unexpectedly, if so,
    it will be possible to download it manually.
    :param urls: str list
    :return: nothing
    """
    folder = path.join(path.expanduser("~"), "Downloads")
    acc_folder = path.join(folder, account)
    os.mkdir(acc_folder)

    log_file = path.join(folder, "insta_downloader_log_file.txt")

    with open(log_file, "a") as fp:
        for numb, link in enumerate(urls):
            file_name = path.join(acc_folder, f"{account}_{numb}.mp4")
            try:
                request.urlretrieve(link, file_name)
                result = "success"
            except:
                print(link, "downloading failed")
                result = "fail"
            finally:
                fp.write(f"{time.ctime()}: {link} - {result}\n")


if __name__ == "__main__":
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

    # download video files to ~/Downloads/NEEDED_ACCOUNT/
    # with log file in ~/Downloads/insta_downloader_log_file.txt
    download_video_files(video_urls, NEEDED_ACCOUNT)
