import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def download_album_images(driver, album_index):
    """
    Download images from a specified album and save them in a corresponding folder.
    
    :param driver: Selenium WebDriver instance
    :param album_index: Index of the album to download images from
    """
    # Get folder date and title
    date_element = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, f'#display_item_groups > main > div > section > div.corner-content > div > ol > li:nth-child({album_index}) .time'))
    )
    folder_date = date_element.text

    title_element = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, f'#display_item_groups > main > div > section > div.corner-content > div > ol > li:nth-child({album_index}) > a > div.thumb-body.contents-body > div.title > h3 > span'))
    )
    folder_title = title_element.text.strip()

    # Use date and title to create folder name
    folder_name = f"{folder_date} {folder_title}"

    # Ensure the folder exists
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    selector = f'#display_item_groups > main > div > section > div.corner-content > div > ol > li:nth-child({album_index}) > a'
    clickable_album = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
    )
    print(f'clicking album {album_index}')
    clickable_album.send_keys(Keys.END)
    clickable_album.click()

    # Wait for the page to load and locate all matching <a> elements
    WebDriverWait(driver, 20).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[data-fancybox="gallery"]'))
    )

    # Find all attributes with href in <a>
    image_links = driver.find_elements(By.CSS_SELECTOR, 'a[data-fancybox="gallery"]')

    if not image_links:
        print(f"No images found in album {album_index}. Moving to the next album.")
        driver.back()  # Back to the album list
        return

    # Download images
    for link in image_links:
        try:
            # Get href URL
            img_url = link.get_attribute("href")
            if img_url:
                response = requests.get(img_url, stream=True)
                if response.status_code == 200:
                    # Save image file
                    filename = os.path.join(folder_name, os.path.basename(img_url.split("?")[0]))
                    with open(filename, "wb") as img_file:
                        for chunk in response.iter_content(1024):
                            img_file.write(chunk)
                    print(f"download success: {filename}")
                else:
                    print(f"download failed: {img_url} (status code: {response.status_code})")
        except Exception as e:
            print(f"handle error: {img_url} : {e}")

    # Back to previous page
    driver.back()

def download_all_albums(driver):
    """
    Download all albums on the current page and navigate to the next page if available.
    
    :param driver: Selenium WebDriver instance
    """
    album_count = 12  # Assume there are 12 albums on a page
    for i in range(1, album_count + 1):
        download_album_images(driver, i)

    # Check if there is a next page and click it
    try:
        next_page = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#display_item_groups > main > div > section > div.corner-content > div > div > div > span.next > a'))  # Update this selector based on the actual next button's selector
        )
        print("Going to the next page...")
        next_page.click()
        time.sleep(2)  # Wait for the next page to load
        download_all_albums(driver)  # Recursively download albums on the next page
    except Exception as e:
        print("No more pages or error: ", e)

# Initialize chromedriver
driver = webdriver.Chrome()  
driver.get("https://sayuri-yellow.com/signin")  
driver.maximize_window()

# login info
username = input("Enter your username: ")
password = input("Enter your password: ")
WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "user_login"))).send_keys(username)
WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "user_password"))).send_keys(password, Keys.ENTER)

time.sleep(5)
# click photo on main page
photo = WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, '#nav > div > ul > li:nth-child(5) > a')))
photo.click()

# Download all albums
download_all_albums(driver)

# Close WebDriver
driver.quit()
