import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def create_screenshot():
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280,800")
    
    try:
        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate to the application
        driver.get("http://localhost:5001")
        
        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "model-select"))
        )
        
        # Wait a bit more for any animations or resources to load
        time.sleep(2)
        
        # Take a screenshot
        driver.save_screenshot("static/images/app_screenshot.png")
        print("Screenshot saved to static/images/app_screenshot.png")
        
    except Exception as e:
        print(f"Error creating screenshot: {e}")
    
    finally:
        # Close the driver
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    create_screenshot()