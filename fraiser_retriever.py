from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

# Set up Selenium WebDriver options
options = Options()
options.add_argument("--headless")  # Run headlessly

# Path to your ChromeDriver executable (replace with your path)
chrome_service = Service('/path/to/chromedriver')  # Update this path

# Set up WebDriver
driver = webdriver.Chrome(service=chrome_service, options=options)

# URL to be scraped
url = "https://www.compareschoolrankings.org/school/ab/elementary/9373"

try:
    # Load the webpage
    driver.get(url)
    time.sleep(5)  # Wait for JavaScript to render (adjust based on network speed)

    # Get the page source and parse it with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Extract school name
    school_name = soup.find('div', class_='flex school-name row xs12')
    if school_name:
        print('School Name:', school_name.get_text(strip=True))

    # Extract school type (e.g., Public or Private)
    school_type = school_name.find_next('div', class_='flex row xs12')
    if school_type:
        print('School Type:', school_type.get_text(strip=True))

    # Extract score
    score_div = soup.find('div', class_='flex score_color_1')
    if score_div:
        score = score_div.get_text(strip=True)
        print('Score:', score)

    # Extract rank
    rank_div = score_div.find_next('div', text=lambda x: '/' in x)
    if rank_div:
        rank = rank_div.get_text(strip=True)
        print('Rank:', rank)

    # Extract website link
    website_div = soup.find('div', class_='flex field xs5 md6')
    website_link = website_div.find('a') if website_div else None
    if website_link:
        website_href = website_link.get('href')
        print('Website:', website_href)

    # Extract address
    address_div = soup.find('div', class_='flex school-map-address')
    if address_div:
        address = address_div.get_text(strip=True)
        print('Address:', address)

    # Extract phone number
    phone_div = soup.find('div', text='Phone')
    if phone_div:
        phone = phone_div.find_next('div', class_='flex field xs5 md6')
        if phone:
            phone_number = phone.get_text(strip=True)
            print('Phone:', phone_number)

    # Extract ESL %
    esl_div = soup.find('div', text='ESL %')
    if esl_div:
        esl_percentage = esl_div.find_next('div', class_='flex field xs5 md6')
        if esl_percentage:
            print('ESL %:', esl_percentage.get_text(strip=True))

    # Extract special needs %
    special_needs_div = soup.find('div', text=lambda t: t and 'Special Needs %' in t)
    if special_needs_div:
        special_needs_percentage = special_needs_div.find_next('div', class_='flex field xs5 md6')
        if special_needs_percentage:
            print('Special Needs %:', special_needs_percentage.get_text(strip=True))

    # Extract Grade 6 enrolment
    grade6_enrolment_div = soup.find('div', text=lambda t: t and 'Gr 6 Enrolment' in t)
    if grade6_enrolment_div:
        grade6_enrolment = grade6_enrolment_div.find_next('div', class_='flex field xs5 md6')
        if grade6_enrolment:
            print('Grade 6 Enrolment:', grade6_enrolment.get_text(strip=True))

finally:
    # Quit the driver
    driver.quit()
