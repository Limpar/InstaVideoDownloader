import os
import time
import threading
import re

from urllib import request, error

from selenium import webdriver
from bs4 import BeautifulSoup, SoupStrainer
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.units import inch, cm
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase import ttfonts

INSTAGRAM_LOGIN_PAGE = 'https://www.instagram.com/accounts/login/'
INSTAGRAM_HOME_PAGE = 'https://www.instagram.com'
# scrolls_count - how much it will scroll the profile
# more photos\videos  load partially each scroll-down action
# we doesn't know for sure how much we need to reach the end
# let it be 20
SCROLLS_COUNT = 15
WAIT_IN_SECS = 5


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


def login():
    """
    login with setted login and password account to instagram via opened webdriver
    :param account_login: str with login
    :param account_password: str with password
    :return: nothing
    """
    BROWSER.get(INSTAGRAM_LOGIN_PAGE)
    time.sleep(1)  # give browser some time to load

    # find a login field
    login_field = find_by(By.XPATH,
                          '//input[@name="username"]')

    # fidn a password field
    password_field = find_by(By.XPATH,
                             '//input[@name="password"]')

    # a little user-emulation:
    # click on each field and enter text inside
    # this makes login button become visible, et least for now
    if login_field and password_field:
        login_field.click()
        login_field.send_keys(LOGIN)

        password_field.click()
        password_field.send_keys(PASSWORD)

        # find login button and click on it with a little delay
        login_button = find_by(By.XPATH, '//button')

        if login_button:
            login_button.click()
            time.sleep(1)

            # code_field = find_by(By.XPATH, '//input[@name="verificationCode"')
            # if code_field:
            #     code_field.click()
            #     code_field.send_keys(BACKUP_CODE)
            #     confirm = find_by(By.XPATH, '//button')
            #     if confirm:
            #         confirm.click()


def switch_to_needed_account():
    """
    switching to instagram/account_name/ page to parse the videos
    :param account_name: profile name as str
    :return: page source
    """

    # create the global link
    BROWSER.get(INSTAGRAM_HOME_PAGE + "/" + NEEDED_ACCOUNT + "/?hl=ru")

    # scroll down to find expand all posts in profile
    BROWSER.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # find button "load more" and click on it, wait loading
    load_button = find_by(By.XPATH, '//*[@id="react-root"]/section/main/article/div/a')
    if load_button:
        load_button.click()

    # time.sleep(2)

    for scroll in range(SCROLLS_COUNT):
        BROWSER.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    return BROWSER.page_source


def parse_profile(source_page):
    """
    parse insta profile source page to find link on video
    :param source_page: str with page source
    :return: list with strings, contains urls on videos
    """
    video_urls = []
    text_urls = []

    text_filter = SoupStrainer(name='a', href=re.compile(f'taken-by={NEEDED_ACCOUNT}'))

    for url in BeautifulSoup(source_page, 'lxml', parse_only=text_filter).find_all('a'):
        for child in url.descendants:
            try:
                if 'coreSpriteVideoIconLarge' in child.attrs.get('class', []):
                    video_urls.append(url.attrs.get('href', ''))
                    break
            except AttributeError:
                pass
        else:
            image = url.find_all('img')
            if image:
                image = image[0]
                img_dict = {
                    'url': image.get('src', ''),
                    'text': image.get('alt', 'no text')
                }
            text_urls.append(img_dict)

    return video_urls, text_urls


def parse_video_urls(urls):
    """
    just opens a video url and parses global video url
    :param urls: urls on pages with video
    :return: global video urls list
    """
    videos = list()
    for url in urls:
        global_url = INSTAGRAM_HOME_PAGE + url
        BROWSER.get(global_url)
        video_link = find_by(By.XPATH, "//video[1]")
        videos.append(video_link.get_attribute("src"))
    return videos


def download_file(link, file_name):
    try:
        request.urlretrieve(link, file_name)
    except error.URLError:
        pass
    except ConnectionResetError:
        print(link)


def save_folder():
    folder = os.path.join(os.path.expanduser("~"), "Downloads")
    acc_folder = os.path.join(folder, NEEDED_ACCOUNT)
    add_folder(acc_folder)
    return acc_folder


def add_folder(folder):
    try:
        os.mkdir(folder)
    except FileExistsError:
        pass


def download_video_files(urls):
    """
    simple download files in ~/Downloads/profile_folder
    :param urls: str list
    :param account str
    :return: nothing
    """
    acc_folder = save_folder()

    threads = []

    for numb, link in enumerate(urls):
        file_name = os.path.join(acc_folder, f"{numb}.mp4")
        thread = threading.Thread(target=download_file, args=(link, file_name))
        threads.append(thread)
        thread.start()

    [thread.join() for thread in threads]


def find_by(type_, mask):
    try:
        element = WebDriverWait(BROWSER, WAIT_IN_SECS).until(
            expected_conditions.visibility_of_element_located((type_, mask)))
    except TimeoutException:
        element = None
    finally:
        return element


def save_texts(texts):
    """

    :param texts:
    [{'url': image.get('src', ''),
      'text': image.get('alt', '')
    },
    ]
    :return:
    """
    main_path = save_folder()
    img_path = os.path.join(main_path, 'img')
    add_folder(img_path)

    for i, text in enumerate(texts):
        with open(os.path.join(img_path, f'{i}.txt'), 'w') as f:
            f.write(text.get('text', 'no text'))
        img_url = text.get('url', '')
        if img_url:
            file_name = os.path.join(img_path, f'{i}.jpg')
            download_file(img_url, file_name)
    _to_pdf(len(texts))

def _to_pdf(size=0):
    main_path = save_folder()
    file_path = os.path.join(main_path, f'{NEEDED_ACCOUNT}.pdf')
    img_path = os.path.join(main_path, 'img')

    image_w, image_h = 130, 130


    pdf = Canvas(file_path, pagesize=A4)
    my_font = ttfonts.TTFont('tms', 'TIMCYR.TTF')
    pdfmetrics.registerFont(my_font)
    pdf.setFont('tms', 10)

    for i in range(size-1, -1, -1):
        image_file = os.path.join(img_path, f'{i}.jpg')
        text_file = os.path.join(img_path, f'{i}.txt')

        rhyme = pdf.beginText(inch * 1, inch * 10)
        with open(text_file, 'r') as f:
            for line in f.readlines():
                rhyme.textLine('')

        pdf.drawText(rhyme)
        #pdf.drawImage(image_file, 0, 0, 10 * cm, 10 * cm)
        pdf.showPage()
    pdf.save()





if __name__ == "__main__":

    TEST = False
    LOGIN = input("Login: ")
    PASSWORD = input("Password: ")
    NEEDED_ACCOUNT = input("Instagram Account: ")

    #BROWSER = open_browser_with_options()

    if TEST:
        NEEDED_ACCOUNT = 'beyonce'
    elif LOGIN and PASSWORD and NEEDED_ACCOUNT:
        pass
    #     login()
    #
    # saved_page = switch_to_needed_account()
    #
    # video_pages, texts = parse_profile(saved_page)
    #
    # #video_urls = parse_video_urls(video_pages)
    # BROWSER.close()
    # #download_video_files(video_urls)
    # save_texts(texts)
    _to_pdf(10)
