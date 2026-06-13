import os
import asyncio
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv('.env.example')

class TestBackupChecker:
    def __init__(self):
        self.username = os.getenv('WHM_USERNAME')
        self.passwords = {
           os.getenv('SERVERS1').replace('https://', '').replace('/', ''): os.getenv('SERVERS1_PASSWORD'),
           os.getenv('SERVERS2').replace('https://', '').replace('/', ''): os.getenv('SERVERS2_PASSWORD'),
           os.getenv('SERVERS3').replace('https://', '').replace('/', ''): os.getenv('SERVERS3_PASSWORD')
       }
        self.servers = [
            os.getenv('SERVERS1').replace('https://', '').replace('/', ''),
            os.getenv('SERVERS2').replace('https://', '').replace('/', ''),
            os.getenv('SERVERS3').replace('https://', '').replace('/', '')
        ]
        
        self.channel_id_bale = os.getenv('BALE_CHANNEL_ID')
        self.bot_token_bale = os.getenv('BALE_BOT_TOKEN')
        
    def setup_driver(self):
        """Initialize and return a Chrome WebDriver with a simple, direct approach"""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--allow-insecure-localhost')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--remote-debugging-port=9222')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        
        from selenium.webdriver.chrome.service import Service
        # service = Service(executable_path='/usr/bin/chromedriver')
        
        try:
            logging.info("Initializing Chrome with explicit chromedriver path...")
            driver = webdriver.Chrome(options=options)
            logging.info("Successfully initialized Chrome driver.")
            return driver
        except Exception as e:
            logging.error(f"Failed to initialize Chrome driver with explicit path: {e}")
            import traceback
            logging.error(traceback.format_exc()) # لاگ کامل خطا برای دیباگ
            raise Exception("Could not initialize Chrome driver.")

    
    async def send_Bale_message(self, message, max_retries=3):
        """Send message to Bale channel using bot with retry mechanism"""
        url = f"https://tapi.bale.ai/bot{self.bot_token_bale}/sendMessage"
        data = {
            "chat_id": self.channel_id_bale,
            "text": message,
            "parse_mode": "HTML"
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, data=data, timeout=10)
                response.raise_for_status()
                return
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    logging.error(f"Error sending Bale message after {max_retries} attempts: {str(e)}")
                else:
                    logging.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    await asyncio.sleep(2)  # Wait before retrying
    
    async def check_backup_status(self):
        """Check backup status for May 1st on all servers"""
        driver = self.setup_driver()
        target_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            for server in self.servers:
                try:
                    logging.info(f"Checking server: {server}")
                    logging.info(f"Looking for backups on: {target_date}")
                    
                    # Navigate directly to JetBackup page
                    jetbackup_url = f'https://{server}:2087/cgi/addons/jetbackup/index.cgi'
                    driver.get(jetbackup_url)
                    logging.info("Accessed JetBackup page")
                    
                    # Handle SSL warning if present
                    try:
                        advanced_button = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, 'details-button'))
                        )
                        advanced_button.click()
                        proceed_link = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, 'proceed-link'))
                        )
                        proceed_link.click()
                        logging.info("Handled SSL warning")
                    except Exception as e:
                        logging.info(f"No SSL warning found: {str(e)}")
                    
                    # Wait for login form and input credentials
                    username_field = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, 'user'))
                    )
                    password_field = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, 'pass'))
                    )
                    login_button = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, 'login_submit'))
                    )
                    
                    username_field.clear()
                    username_field.send_keys(self.username)
                    password_field.clear()
                    password_field.send_keys(self.passwords[server])
                    login_button.click()
                    logging.info("Submitted login credentials")
                    
                    # Wait for JetBackup page to load after login
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '#sidebar-menu'))
                    )
                    logging.info("JetBackup page loaded")
                    
                    # Click on Logs in the sidebar menu
                    logs_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, '#sidebar-menu > div > ul > li:nth-child(9) > a > em'))
                    )
                    logs_button.click()
                    logging.info("Clicked on Logs button")
                    
                    # Wait for logs table to load
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '#accounts_table'))
                    )
                    logging.info("Logs table loaded successfully")
                    
                    # Add a small delay to ensure table is fully loaded
                    await asyncio.sleep(2)
                    
                    # Find all rows in the logs table
                    rows = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#accounts_table tbody tr[id^="log_row_"]'))
                    )
                    logging.info(f"Found {len(rows)} rows in the logs table")
                    
                    # Log the first few rows' content for debugging
                    logging.info("First 3 rows content:")
                    for i in range(min(3, len(rows))):
                        try:
                            row_text = rows[i].text
                            logging.info(f"Row {i+1} content: {row_text}")
                        except Exception as e:
                            logging.error(f"Error getting row {i+1} content: {str(e)}")
                    
                    backup_found = False
                    backup_details = []
                    
                    for index, row in enumerate(rows, 1):
                        logging.info(f"Checking row {index} of {len(rows)}")
                        try:
                            # Get the date from the Start Time column
                            date_cell = row.find_element(By.CSS_SELECTOR, 'td[data-title="Start Time"] span')
                            date_text = date_cell.get_attribute('title')
                            logging.info(f"Row {index} date: {date_text}")
                            
                            # Log all column values for debugging
                            try:
                                all_columns = row.find_elements(By.CSS_SELECTOR, 'td')
                                column_values = {}
                                for col in all_columns:
                                    title = col.get_attribute('data-title')
                                    if title:
                                        value = col.find_element(By.CSS_SELECTOR, 'span').text
                                        column_values[title] = value
                                logging.info(f"Row {index} all column values: {column_values}")
                            except Exception as e:
                                logging.error(f"Error getting column values for row {index}: {str(e)}")
                            
                            # Convert the date to a format we can compare
                            try:
                                date_obj = datetime.strptime(date_text, '%a, %b %d, %Y, %I:%M %p')
                                formatted_date = date_obj.strftime('%Y-%m-%d')
                                logging.info(f"Formatted date for comparison: {formatted_date}")
                                
                                if formatted_date == target_date:
                                    # Check if the backup type is "Backup"
                                    backup_type = row.find_element(By.CSS_SELECTOR, 'td[data-title="Type"] span').text
                                    logging.info(f"Backup type for row {index}: {backup_type}")
                                    
                                    if backup_type == "Backup":
                                        backup_found = True
                                        logging.info(f"Found matching backup in row {index}")
                                        
                                        # Extract backup details
                                        process_id = row.find_element(By.CSS_SELECTOR, 'td[data-title="Process ID"] span').text
                                        start_time = row.find_element(By.CSS_SELECTOR, 'td[data-title="Start Time"] span').get_attribute('title')
                                        end_time = row.find_element(By.CSS_SELECTOR, 'td[data-title="End Time"] span').get_attribute('title')
                                        execution_time = row.find_element(By.CSS_SELECTOR, 'td[data-title="Total Execution Time"]').text
                                        status = row.find_element(By.CSS_SELECTOR, 'td[data-title="Status"] span').text
                                        
                                        logging.info(f"Backup details for row {index}:")
                                        logging.info(f"Process ID: {process_id}")
                                        logging.info(f"Type: {backup_type}")
                                        logging.info(f"Start Time: {start_time}")
                                        logging.info(f"End Time: {end_time}")
                                        logging.info(f"Execution Time: {execution_time}")
                                        logging.info(f"Status: {status}")
                                        
                                        backup_details.append({
                                            'process_id': process_id,
                                            'type': backup_type,
                                            'start_time': start_time,
                                            'end_time': end_time,
                                            'execution_time': execution_time,
                                            'status': status
                                        })
                                    else:
                                        logging.info(f"Skipping row {index} - Not a backup entry (Type: {backup_type})")
                            except Exception as e:
                                logging.error(f"Error processing date for row {index}: {str(e)}")
                        except Exception as e:
                            logging.error(f"Error processing row {index}: {str(e)}")
                            continue
                    
                    # Prepare and send message
                    if backup_found:
                        message = f"* Backup Status for {server} *\n"
                        message += f"Date: {target_date}\n\n"
                        message += "* Backup Details: *\n"
                        for detail in backup_details:
                            # Format status with appropriate emojis
                            status_emoji = ""
                            if detail['status'] == "Completed":
                                status_emoji = "✅ ✅ ✅"
                            elif detail['status'] == "Partially completed":
                                status_emoji = "⚠️ ⚠️ ⚠️"
                            else:
                                status_emoji = "❌ ❌ ❌"
                            
                            message += f"Start Time: {detail['start_time']}\n"
                            message += f"End Time: {detail['end_time']}\n"
                            message += f"Execution Time: {detail['execution_time']}\n"
                            message += f"Status: * {detail['status']} * {status_emoji}\n"
                            message += "-------------------\n"
                        logging.info("Prepared message with backup details")
                    else:
                        message = f"* ⚠️ No backup found for {server} on {target_date} *\n"
                        message += "Please check the backup status manually."
                        logging.info("Prepared message for no backup found")
                    
                    logging.info("Attempting to send Bale message...")
                    await self.send_Bale_message(message)
                    logging.info("Bale message sent successfully")
                    
                    # If we reach here, it means the current server check was successful
                    logging.info(f"Successfully completed check for {server}")
                    
                except Exception as e:
                    error_message = f"* Error during navigation for {server}: *\n{str(e)}"
                    logging.error(f"Navigation error for {server}: {str(e)}")
                    await self.send_Bale_message(error_message)
                    # If there's an error, break the loop and don't proceed to the next server
                    break
        
        except Exception as e:
            error_message = f"* Critical error in backup checker: *\n{str(e)}"
            logging.error(f"Critical error: {str(e)}")
            await self.send_Bale_message(error_message)
        
        finally:
            driver.quit()
            logging.info("Browser closed")

async def run_test():
    """Run the test backup check"""
    checker = TestBackupChecker()
    await checker.check_backup_status()

if __name__ == "__main__":
    asyncio.run(run_test()) 