import random
import time

from selenium import webdriver


def get_movie_links(nums=1000):
    with open('all_links.csv', 'r')as opener:
        link_list = opener.readlines()
    print(link_list)
    link_list = set(link.strip() for link in link_list)
    # print(link_list)
    browser.get(url)
    links = browser.find_elements_by_xpath("html//div[@class='list-wp']//a[@target='_blank']")
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(1)
    try:
        while len(links) < nums:
            print('nums:', len(links))
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(random.randint(3, 5))
            more = browser.find_element_by_xpath("html//a[@class='more']")
            while len(browser.window_handles) > 1:
                browser.switch_to.window(browser.window_handles[1])
                browser.close()
                browser.switch_to.window(browser.window_handles[0])
            print(more.get_attribute('href'))
            more.click()
            links = browser.find_elements_by_xpath("html//div[@class='list-wp']//a[@target='_blank']")
            for link in links:
                href = link.get_attribute('href')
                print('href', href)
                if href not in link_list:
                    link_list.add(href)
                else:
                    print('exist!')
    except Exception:
        with open('all_links.csv', 'w')as opener:
            for href in link_list:
                opener.write(href + '\n')


if __name__ == '__main__':
    url = 'https://movie.douban.com/tv/#!type=tv&tag=%E7%83%AD%E9%97%A8&sort=recommend&page_limit=20&page_start=0'
    option = webdriver.ChromeOptions()
    # option.add_experimental_option('excludeSwitches', ['enable-automation'])
    browser = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver', options=option)
    get_movie_links(2000)
    browser.close()
