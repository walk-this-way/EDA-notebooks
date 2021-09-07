# Data manipulation libraries
import os
import pandas as pd
import csv

# System libaries
# System libraries
import platform
from pathlib import Path, PureWindowsPath

# Datetime libraries
import time
from datetime import datetime, date, timedelta
from pytz import timezone
import dateparser

# Computational libraries
import numpy as np
import re
import random

# Scraping libraries
import requests
import lxml.html
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup

# Logging libraries
import logging

logging.basicConfig(level=logging.INFO)


def get_vids(search_query, driver, num_results):
    youtube_url = 'https://www.youtube.com/results?search_query='
    page = youtube_url + search_query
    try:
        driver.get(page)
        logging.info('Retrieving data from ' + page)
        time.sleep(1)
    except:
        logging.info('Error retrieving data. Try again.')

    # Clear pop up alerts
    try:
        viewpopup = driver.find_element_by_xpath(
            '//ytd-button-renderer[@id="dismiss-button"]/a/paper-button[@id="button"]')
        time.sleep(1)
        viewpopup.click()
        logging.info('Pop up found and cleared')
        time.sleep(1)
    except:
        logging.info('No pop up found :)')

    # Make soup
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    html_txt = soup.prettify()

    video_wrappers_max20 = soup.find_all('div', attrs={'id': 'dismissable', 'class': 'style-scope ytd-video-renderer'})
    video_wrappers = video_wrappers_max20[:num_results]
    video_row = []

    for video in video_wrappers:
        # Find original comment
        original = video.find_all('div', attrs={'class': 'text-wrapper style-scope ytd-video-renderer'})
        video_data = {'title': None,
                      'owner': None,
                      'owner_channel': None,
                      'url': None
                      }

        # Get author name
        try:
            for b in original:
                video_data['owner'] = b.find(name="a", attrs={
                    "class": "yt-simple-endpoint style-scope yt-formatted-string"}).text.strip()
        except:
            logging.info('No owner found')

        # Get author channel link
        try:
            for d in original:
                link = d.find(name="a",
                              attrs={"class": "yt-simple-endpoint style-scope yt-formatted-string", "href": True})
                channel = "https://youtube.com" + link['href']
                video_data['owner_channel'] = channel
        except:
            logging.info('No owner channel link found')

        # Get title
        try:
            for c in original:
                video_data['title'] = c.find(name="yt-formatted-string",
                                             attrs={"class": "style-scope ytd-video-renderer"}).text.strip()
        except:
            logging.info('No title found')

        # Get vid url
        try:
            for a in original:
                title_link = a.find(name="a", attrs={"id": "video-title", "href": True})
                url = "https://youtube.com" + title_link['href']
                video_data['url'] = url
        except:
            logging.info('No url found')

        video_row.append(video_data)

    videodf = pd.DataFrame(video_row)
    videodf['vid_index'] = videodf.index + 1
    # print(videodf)
    vid_urls = videodf['url'].tolist()
    return videodf, vid_urls


def get_channel_vids(channel_list, driver, num_results):
    channel_vid_urls = []
    channel_df = []
    for page in channel_list:
        try:
            driver.get(page + '/videos')
            logging.info('Retrieving data from ' + page + '/videos')
            time.sleep(1)
        except:
            logging.info('Error retrieving data. Try again.')

        if num_results > 30:
            logging.info('scrolling down for more videos')
            driver.execute_script('window.scrollBy(0,1500)')
            time.sleep(2)
            if num_results > 60:
                logging.info('scrolling down for more videos')
                driver.execute_script('window.scrollBy(0,1500)')
                time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        video_wrappers_all = soup.find_all('div', attrs={'id': 'details', 'class': 'style-scope ytd-grid-video-renderer'})
        video_wrappers = video_wrappers_all[:num_results]
        video_row = []

        if video_wrappers:
            for video in video_wrappers:
                video_data = {'title': None,
                              'url': None
                              }
                # Get title
                try:
                    video_data['title'] = video.find(name="a",
                                                     attrs={"id": "video-title",
                                                            "class": "yt-simple-endpoint style-scope ytd-grid-video-renderer"}).text.strip()
                except:
                    logging.info('No title found')

                # Get vid url
                try:
                    title_link = video.find(name="a", attrs={"id": "video-title", "href": True})
                    url = "https://youtube.com" + title_link['href']
                    video_data['url'] = url
                except:
                    logging.info('No url found')

                video_row.append(video_data)
            videodf = pd.DataFrame(video_row)
            vid_urls = videodf['url'].tolist()
            channel_vid_urls.extend(vid_urls)

        try:
            driver.get(page + '/about')
            logging.info('Retrieving data from ' + page + '/about')
            time.sleep(1)
        except:
            logging.info('Error retrieving data. Try again.')
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        # html_txt = soup.prettify()

        channel_name = soup.find(name="yt-formatted-string",
                                 attrs={"id": "text", "class": "style-scope ytd-channel-name"}).text.strip()
        description = soup.find(name="yt-formatted-string", attrs={"id": "description",
                                                                   "class": "style-scope ytd-channel-about-metadata-renderer"}).text.strip()

        stats = \
            soup.find_all('div',
                          attrs={"id": "right-column", 'class': 'style-scope ytd-channel-about-metadata-renderer'})[
                0].text.strip()

        location = soup.find_all('tr', attrs={'class': 'style-scope ytd-channel-about-metadata-renderer'})[
            -1].text.strip()
        links = soup.find_all('a', attrs={"class": "yt-simple-endpoint style-scope ytd-channel-about-metadata-renderer",
                                          "href": True})
        links_url = []
        for i in links:
            links_url.append(i['href'])

        channel_dict = {'channel_name': None,
                        'description': None,
                        'stats': None,
                        'location': None
                        }

        channel_dict['channel_name'] = channel_name
        channel_dict['description'] = description
        channel_dict['stats'] = stats
        channel_dict['location'] = location
        channeldf = pd.DataFrame([channel_dict])
        for i in range(len(links_url)):
            channeldf['link_url_' + str(i)] = links_url[i]
        channel_df.append(channeldf)
    channel_info_df = pd.concat(channel_df, ignore_index=True)

    filename = "YOUTUBE_" + datetime.now().strftime("%Y-%m-%dT%H-%M-%S") + "_CHANNEL" + ".xlsx"
    channel_info_df.to_excel(str(raw_data_dir / filename), index=False, na_rep='None', encoding='UTF-16')

    return channel_info_df, channel_vid_urls


def yt_scrape(url_list, raw_data_directory, driver, max_scrolls):
    vid_row = []
    comment_row = []
    for page in url_list:
        # metadata #############################################################
        # <editor-fold desc="Metadata">
        try:
            driver.get(page)
            logging.info('Retrieving data from ' + page)
            time.sleep(1)
        except:
            logging.info('Error retrieving data. Try again.')

        # Clear pop up alerts
        try:
            viewpopup = driver.find_element_by_xpath(
                '//ytd-button-renderer[@id="dismiss-button"]/a/paper-button[@id="button"]')
            time.sleep(1)
            viewpopup.click()
            logging.info('Pop up found and cleared')
            time.sleep(1)
        except:
            logging.info('No pop up found :)')

        # Open transcript
        open_transcript = False
        try:
            time.sleep(1)
            menu = driver.find_element_by_xpath(
                '//div[@id="menu-container"]/div/ytd-menu-renderer/yt-icon-button/button[@id="button"]')
            time.sleep(1)
            menu.click()
            logging.info('Opened menu')
            try:
                opentranscript = driver.find_element_by_xpath(
                    '//ytd-menu-popup-renderer/paper-listbox/ytd-menu-service-item-renderer/paper-item[@class="style-scope ytd-menu-service-item-renderer"]')
                opentranscript.click()
                logging.info('Opened video transcript')
                open_transcript = True
                time.sleep(1)
            except:
                logging.info('No transcript found')
                time.sleep(1)
        except:
            logging.info('Cannot open menu')
            time.sleep(1)

        # Open show more description
        try:
            time.sleep(1)
            description = driver.find_element_by_xpath('//ytd-expander/paper-button[@id="more"]')
            description.click()
            logging.info('Showing more description')
            time.sleep(1)
        except:
            logging.info('Cannot show more description')

        # # Scroll down past comment header
        # driver.execute_script('window.scrollTo(0,500)')
        # time.sleep(1)
        #
        # # Scroll to comment header
        # try:
        #     commentheader = driver.find_element_by_xpath(
        #         '//paper-button[@class="dropdown-trigger style-scope yt-dropdown-menu"]')
        # except:
        #     try:
        #         logging.info('scrolling more to find comment order dropdown')
        #         driver.execute_script('window.scrollBy(0,500)')
        #         time.sleep(1)
        #         commentheader = driver.find_element_by_xpath(
        #             '//paper-button[@class="dropdown-trigger style-scope yt-dropdown-menu"]')
        #     except:
        #         logging.info('scrolling even more to find comment order dropdown')
        #         driver.execute_script('window.scrollBy(0,500)')
        #         time.sleep(1)
        #         commentheader = driver.find_element_by_xpath(
        #             '//paper-button[@class="dropdown-trigger style-scope yt-dropdown-menu"]')
        #
        #
        # action = ActionChains(driver)
        # action.move_to_element(commentheader).perform()
        # time.sleep(1)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        # html_txt = soup.prettify()

        vid_metadata = {'url': "Original Comment",
                        'title': None,
                        'datetime_yt': None,
                        'datetime_adj': None,
                        'duration': None,
                        'views': None,
                        'votes': None,
                        'num_comments': None,
                        'owner': None,
                        'owner_channel': None,
                        'owner_subscribers': None,
                        'description': None,
                        'type': None,
                        'transcript': None,
                        }

        # For number formatting
        multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}

        # Get URL
        vid_metadata['url'] = page

        # Get title
        try:
            title = soup.find(name="h1",
                              attrs={"class": "title style-scope ytd-video-primary-info-renderer"}).text.strip()
            vid_metadata['title'] = title
        except:
            logging.info('No title found')

        # Get date & set video type
        try:
            vid_metadata['type'] = 'Video'
            date = soup.find(name="div", attrs={"id": "date"}).text.strip()
            date = re.sub(u"\u2022", '', date)
            if "tream" in date:
                vid_metadata['type'] = 'Livestream'
            date = date.strip("Streamed live on ").strip("Started streaming on ").strip("Started streaming ").strip("Streamed live ").strip("Premiered ")
            adj = datetime.strptime(date, '%b %d, %Y')
            adj = adj.strftime("%m/%d/%Y")
            vid_metadata['datetime_yt'] = date
            vid_metadata['datetime_adj'] = adj
        except:
            logging.info('No date found')

        # Get video duration
        try:
            duration = soup.find(name="span", attrs={"class": "ytp-time-duration"}).text.strip()
            duration_formatted = datetime.strptime(duration, '%M:%S').time()
            vid_metadata['duration'] = duration_formatted
        except:
            logging.info('duration is '+str(duration)+", trying H:M:S")
            try:
                duration_formatted = datetime.strptime(duration, '%H:%M:%S').time()
                vid_metadata['duration'] = duration_formatted
            except:
                logging.info('duration is ' + str(duration) + ", trying D:H:M:S")
                try:
                    duration_formatted = datetime.strptime(duration, '%D:%H:%M:%S').time()
                    vid_metadata['duration'] = duration_formatted
                except:
                    logging.info('duration is ' + str(duration) + ", unknown format")

        # Get views
        try:
            views = soup.find(name="span",
                              attrs={"class": "view-count style-scope yt-view-count-renderer"}).text.strip()
            views = views.strip(' views').strip(' watching now')
            views = int(views.replace(",", ""))
            vid_metadata['views'] = views
        except:
            logging.info('No views found')

        # Get votes
        try:
            votes = []
            for a in soup.find_all(name="ytd-toggle-button-renderer"):
                vote = a.find(name="yt-formatted-string",
                              attrs={"class": "style-scope ytd-toggle-button-renderer style-text", "aria-label": True})
                values = vote["aria-label"].strip(" dislikes")
                values = int(values.replace(",", ""))
                votes.append(values)
                vid_metadata['votes'] = votes
        except:
            logging.info('No votes found')

        driver.execute_script('window.scrollBy(0,500)')
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        # Get number of comments
        try:
            #num = driver.find_element_by_xpath(
            #    "/html/body/ytd-app/div/ytd-page-manager/ytd-watch-flexy/div[4]/div[1]/div/ytd-comments/ytd-item-section-renderer/div[1]/ytd-comments-header-renderer/div[1]/h2/yt-formatted-string")
            num = soup.find(name="h2",
                            attrs={"id": "count", "class": "style-scope ytd-comments-header-renderer"}).text.strip()
            num = num.strip(' Comments')
            num = int(num.replace(",", ""))
            vid_metadata['num_comments'] = num
        except:
            logging.info('No comments found, scrolling more just in case')
            driver.execute_script('window.scrollBy(0,500)')
            time.sleep(3)
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            try:
                num = soup.find(name="h2",
                                    attrs={"id": "count", "class": "style-scope ytd-comments-header-renderer"}).text.strip()
                #num = soup.find_all(name="yt-formatted-string", attrs={"class": "count-text style-scope ytd-comments-header-renderer"}) #.text.strip()
                num = num.strip(' Comments')
                num = int(num.replace(",", ""))
                vid_metadata['num_comments'] = num
            except:
                logging.info('No comments found, scrolling more just in case')
                driver.execute_script('window.scrollBy(0,500)')
                time.sleep(3)
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                try:
                    num = soup.find(name="h2",
                                        attrs={"id": "count", "class": "style-scope ytd-comments-header-renderer"}).text.strip()
                    #num = soup.find_all(name="yt-formatted-string", attrs={"class": "count-text style-scope ytd-comments-header-renderer"}) #.text.strip()
                    num = num.strip(' Comments')
                    num = int(num.replace(",", ""))
                    vid_metadata['num_comments'] = num
                except:
                    logging.info('No comments found')

        # Get owner/channel
        try:
            owner = soup.find(name="ytd-channel-name", attrs={"id": "channel-name"})
            channel = soup.find(name="a",
                                attrs={"class": "yt-simple-endpoint style-scope yt-formatted-string", "href": True})
            vid_metadata['owner_channel'] = "https://youtube.com" + channel["href"]
            vid_metadata['owner'] = owner.text.replace("\n", "")
        except:
            logging.info('No owner found')

        # Get owner subscriber
        try:
            subscribers = soup.find(name="yt-formatted-string", attrs={"id": "owner-sub-count"}).text.strip()
            subscribers = subscribers.strip(" subscribers")
            if subscribers[-1].isdigit():
                formatted = int(subscribers)
            else:
                mult = multipliers[subscribers[-1]]
                formatted = int(float(subscribers[:-1]) * mult)
            vid_metadata['owner_subscribers'] = formatted
        except:
            logging.info('No owner subscriber count found')

        # Get description
        try:
            description = soup.find(name="yt-formatted-string", attrs={
                "class": "content style-scope ytd-video-secondary-info-renderer"}).text.strip()
            vid_metadata['description'] = description
        except:
            logging.info('No description found')

        # Get transcript
        try:
            if open_transcript:
                transcript = soup.find_all(name="ytd-transcript-body-renderer")[0].text.replace("\n", "")
                vid_metadata['transcript'] = transcript
            else:
                logging.info('No transcript found')
        except:
            logging.info('No transcript found')

        vid_row.append(vid_metadata)
        # </editor-fold>

        # comments #############################################################
        # <editor-fold desc="Comments">
        print('Retrieving comments from ' + str(page))

        # Scroll to past comment header
        driver.execute_script('window.scrollTo(0,500)')
        time.sleep(1)

        # <editor-fold desc="Sort by newest first">
        # # Scroll to "Sort By" drop down
        # sortcomment = driver.find_element_by_xpath(
        #     '//paper-button[@class="dropdown-trigger style-scope yt-dropdown-menu"]')
        # action = ActionChains(driver)
        # action.move_to_element(sortcomment).perform()
        #
        # # Sort comments by newest first
        # try:
        #     sortcomment.click()
        #     time.sleep(1)
        #     newestfirst = driver.find_element_by_xpath(
        #         '//a[@class="yt-simple-endpoint style-scope yt-dropdown-menu"]/paper-item[@class="style-scope yt-dropdown-menu"]')
        #     newestfirst.click()
        #     logging.info(
        #         'Sorted comments by newest first')  # Selected sort view has CSS selector "yt-simple-endpoint style-scope yt-dropdown menu iron-selected" - Default is by Most Relevant
        #     time.sleep(1)
        # except:
        #     driver.execute_script('window.scrollTo(0,{0})').format(scroll_down * 100)
        #     logging.info('Cannot sort comments')
        #     time.sleep(1)
        # </editor-fold>

        # Scroll down page
        scroll_down = 1
        while scroll_down <= max_scrolls:  # Max scrolls defined in System-Dependent Configurations
            driver.execute_script("window.scrollTo(0,{0})".format(scroll_down * 100000))
            scroll_down += 1
            time.sleep(5)


        replies_div = driver.find_elements_by_xpath(
             '//ytd-button-renderer[@id="more-replies"]/a/paper-button[@id="button"]')
        morereplies_div = driver.find_elements_by_xpath(
            '//div[@id="expander-contents"]/div/yt-next-continuation/paper-button[@role="button"]')

        for reply in replies_div:
            try:
                driver.execute_script("arguments[0].scrollIntoView(false);", reply)
                reply.click()
                logging.info("Replies found and clicked")
                time.sleep(2)
            except:
                logging.info("Replies not found, trying again")
                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", reply)
                    reply.click()
                    logging.info("Replies found and clicked")
                    time.sleep(2)
                except:
                    logging.info("Replies not found")

        for more in morereplies_div:
            try:
                driver.execute_script("arguments[0].scrollIntoView(false);", more)
                more.click()
                logging.info("More replies found and clicked")
                time.sleep(1)
            except:
                logging.info("More replies not found")

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        comment_wrappers = soup.find_all('ytd-comment-thread-renderer', attrs={'class': 'style-scope ytd-item-section-renderer'})
        # comment_wrappers2 = soup.select('#contents > ytd-comment-thread-renderer')
        for comment in comment_wrappers:
            # Find original comment
            original = comment.find_all(name='ytd-comment-renderer', attrs={'id': 'comment'})
            comment_data = {'type': "Original Comment",
                            'datetime_yt': None,
                            'datetime_adj': None,
                            'author': None,
                            'author_channel': None,
                            'text': None,
                            'comment_votes': None,
                            'url': page
                            }
            # Get time of post
            try:
                for a in original:
                    dt = a.find(name="a",
                                attrs={"class": "yt-simple-endpoint style-scope yt-formatted-string"}).text.strip()
                    comment_data['datetime_yt'] = dt
                    comment_data['datetime_adj'] = dateparser.parse(dt.rstrip("(edited)")).strftime("%m/%d/%Y")
            except:
                logging.info('No datetime found')

            # Get author name
            try:
                for b in original:
                    comment_data['author'] = b.find(name="a", attrs={"id": "author-text"}).text.strip()
            except:
                logging.info('No author found')

            # Get author channel link
            try:
                for d in original:
                    link = d.find(name="a", attrs={"id": "author-text", "href": True})
                    channel = "https://youtube.com" + link['href']
                    comment_data['author_channel'] = channel
            except:
                logging.info('No author channel link found')

            # Get comment
            try:
                for c in original:
                    comment_data['text'] = c.find(name="yt-formatted-string",
                                                  attrs={"id": "content-text"}).text.strip()
            except:
                logging.info('No comment found')

            # Get votes
            try:
                for e in original:
                    # votes = e.find_all("span", attrs={"class": "style-scope ytd-comment-action-buttons-renderer", "id": "vote-count-middle"})
                    votes = e.find(name="span", attrs={"id": "vote-count-middle"}).text.strip()
                    comment_data['comment_votes'] = votes
            except:
                logging.info('No votes found')

            comment_df = pd.DataFrame([comment_data])

            # Find replies
            #reply = driver.find_element_by_xpath('//*[@id="loaded-replies"]/ytd-comment-renderer[1]')
            # reply = comment.find_all()
            reply = comment.find_all('ytd-comment-renderer', attrs={'class': 'style-scope ytd-comment-replies-renderer'})
            for post in reply:
                reply_data = {'type': "Reply",
                                'datetime_yt': None,
                                'datetime_adj': None,
                                'author': None,
                                'author_channel': None,
                                'text': None,
                                'comment_votes': None,
                                'url': page
                                }

                # Get time of post
                try:
                    dt = post.find(name="a", attrs={
                        "class": "yt-simple-endpoint style-scope yt-formatted-string"}).text.strip()
                    reply_data['datetime_yt'] = dt
                    reply_data['datetime_adj'] = dateparser.parse(dt.rstrip("(edited)")).strftime("%m/%d/%Y")
                except:
                    logging.info('No datetime found')

                # Get author
                try:
                    reply_data['author'] = post.find(name="a", attrs={"id": "author-text"}).text.strip()
                except:
                    logging.info('No author found')

                # Get author channel link
                try:
                    link = post.find(name="a", attrs={"id": "author-text", "href": True})
                    channel = "https://youtube.com" + link['href']
                    reply_data['author_channel'] = channel
                except:
                    logging.info('No author channel link found')

                # Get comment
                try:
                    reply_data['text'] = post.find(name="yt-formatted-string",
                                                     attrs={"id": "content-text"}).text.strip()
                except:
                    logging.info('No comment found')

                # Get votes
                try:
                    votes = post.find(name="span", attrs={"id": "vote-count-middle"}).text.strip()
                    reply_data['comment_votes'] = int(votes)
                except:
                    logging.info('No votes found')
                reply_df = pd.DataFrame([reply_data])

                comment_df = pd.concat([comment_df, reply_df], ignore_index=True)

            comment_row.append(comment_df)
        # </editor-fold>

    metadf = pd.DataFrame.from_dict(vid_row)
    print(metadf.head())
    file_name = "YOUTUBE_" + datetime.now().strftime("%Y-%m-%dT%H-%M-%S") + "_METADATA" + ".xlsx"
    metadf.to_excel(str(raw_data_directory / file_name), index=False, na_rep='None', encoding='UTF-16')

    commentdf = pd.concat(comment_row, ignore_index=True)
    commentdf['comment_index'] = commentdf.index + 1
    print(commentdf.head())
    file_name = "YOUTUBE_" + datetime.now().strftime("%Y-%m-%dT%H-%M-%S") + "_VIDEO" + ".xlsx"
    commentdf.to_excel(str(raw_data_directory / file_name), index=False, na_rep='None', encoding='UTF-16')


if __name__ == '__main__':
    # Global variables and parametrs used throughout the notebook
    # Make true if you want to watch scrape
    WATCH_SCRAPE = True

    # Update when running
    raw_data_dir = Path(
        "/Users/jennifer.jin/OneDrive - Accenture Federal Services/Downloads/social_media/youtube_scraper/data/raw")

    # Change based on how many comments you want to scrape
    max_num_scrolls = 1

    # System dependent configuration
    os.getcwd()
    PLATFORM_SYSTEM = platform.system()

    if PLATFORM_SYSTEM == "Darwin":
        # EXECUTABLE_PATH = Path("../dependencies/chromedriver")
        EXECUTABLE_PATH = Path(
            "/Users/jennifer.jin/OneDrive - Accenture Federal Services/Downloads/social_media/chromedriver")
    elif PLATFORM_SYSTEM == "Windows":
        EXECUTABLE_PATH = Path("~/../dependencies")
        file = EXECUTABLE_PATH / "chromedriver.exe"
    else:
        logging.critical("System not supported...")
        exit()

    metadata_cols = ['url', 'title', 'datetime_yt', 'datetime_adj' 'duration', 'views', 'votes', 'num_comments',
                     'owner',
                     'owner_channel', 'owner_subscribers', 'description', 'category', 'category_link', 'transcript']

    comment_cols = ['type', 'datetime_yt', 'datetime_adj', 'author', 'author_channel', 'text', 'comment_votes', 'url',
                    'comment_index']

    # Create the driver
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--incognito')
    if not WATCH_SCRAPE:
        chrome_options.add_argument('--headless')

    try:
        web_driver = webdriver.Chrome(options=chrome_options, executable_path=EXECUTABLE_PATH)
        logging.info('Chrome launched.')
    except:
        logging.critical(
            'Chrome could not be launched. Check executable path and if Chromedriver supports the version of the browser.')

    urls = ["https://www.youtube.com/watch?v=UpIcfw7Q14w"
    ,"https://www.youtube.com/watch?v=HgaHpLBGTRY"
    , "https://www.youtube.com/watch?v=PAY56ovT4Qc"
    , "https://www.youtube.com/watch?v=VQl2KVISh1w"
    , "https://www.youtube.com/watch?v=poRAut99bRk"
    , "https://www.youtube.com/watch?v=A9mny08uI8s"
    , "https://www.youtube.com/watch?v=AWyJ8vJQ6Vo"
          ]

    # urls = ['https://www.youtube.com/watch?v=HgaHpLBGTRY']
    # search_term = "fish"

    num_vids = 2
    channels = ['https://youtube.com/channel/UC0Wf8S7q9hDz8LbBDLVkiYw'
        , 'https://youtube.com/channel/UCPOYW7dOo_mqPP6-HkjJ2ng'
        # , 'https://youtube.com/channel/UChGPLteUhl8SdM4ZuwZvyhQ'
        # , 'https://youtube.com/channel/UCFdKC2cpE7mkBe2VAndcjqA'
        # , 'https://youtube.com/user/Ironclaw007'
        # , 'https://youtube.com/channel/UCp3qQc5YSUN-FbN3_qhZX1Q'
                ]

    # searchresultsdf, urls = get_vids(search_term, web_driver, num_vids)

    channel_df, urls = get_channel_vids(channels, web_driver, num_vids)

    # yt_scrape(urls, raw_data_dir, web_driver, max_num_scrolls)
    web_driver.close()
