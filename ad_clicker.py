import time
import random
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import (
    NoSuchElementException, 
    TimeoutException, 
    ElementNotInteractableException,
    StaleElementReferenceException,
    InvalidElementStateException,
    WebDriverException
)

class AdClicker:
    def __init__(self):
        self.setup_driver()
        self.main_window = None
        self.start_time = None
        self.duration_minutes = 4  # Run for 5-6 minutes
        self.click_count = 0
        self.successful_clicks = 0
        
    def setup_driver(self):
        """Set up the Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Enable headless mode for CI environment
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-gpu")  # Helps with Windows issues
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-popup-blocking")  # Allow popups
        
        # Add user agent to appear more human-like
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
        chrome_options.add_argument(f"user-agent={user_agent}")
        
        try:
            # Use Selenium 4's built-in driver manager
            print("Setting up Chrome driver...")
            self.driver = webdriver.Chrome(options=chrome_options)
            print("Browser successfully launched")
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
            raise
        
    def human_like_delay(self, min_seconds=1, max_seconds=5):
        """Wait for a random amount of time to simulate human behavior."""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
        
    def move_mouse_randomly(self):
        """Move the mouse to random positions on the page to simulate human behavior."""
        try:
            actions = ActionChains(self.driver)
            viewport_width = self.driver.execute_script("return window.innerWidth")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            # Random movement points (keeping within 80% of viewport to avoid edge issues)
            max_x = int(viewport_width * 0.8)
            max_y = int(viewport_height * 0.8)
            
            points = [(random.randint(10, max_x), random.randint(10, max_y)) for _ in range(2)]
            
            for x, y in points:
                actions.move_by_offset(x, y).perform()
                self.human_like_delay(0.5, 1)
                # Move back to center to avoid going off-screen
                actions.move_to_element(self.driver.find_element(By.TAG_NAME, "body")).perform()
        except Exception as e:
            print(f"Error during mouse movement: {e}")
            # Reset mouse position as a fallback
            try:
                actions = ActionChains(self.driver)
                actions.move_to_element(self.driver.find_element(By.TAG_NAME, "body")).perform()
            except:
                pass
            
    def scroll_randomly(self):
        """Scroll the page randomly to simulate human reading behavior."""
        try:
            viewport_height = self.driver.execute_script("return window.innerHeight")
            page_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Perform a few random scrolls
            scroll_count = random.randint(1, 3)
            for i in range(scroll_count):
                # Decide whether to scroll up or down (80% down, 20% up if not at the top)
                current_scroll_position = self.driver.execute_script("return window.pageYOffset")
                scroll_direction = 1  # Default: scroll down
                
                if current_scroll_position > 0 and random.random() < 0.2:
                    scroll_direction = -1  # Scroll up 20% of the time if not at the top
                
                scroll_amount = random.randint(int(viewport_height * 0.3), int(viewport_height * 0.8))
                self.driver.execute_script(f"window.scrollBy(0, {scroll_direction * scroll_amount});")
                self.human_like_delay(0.8, 2)
                
                # After scrolling, pause to "read" content
                self.human_like_delay(1, 3)
        except Exception as e:
            print(f"Error during scrolling: {e}")
   
    def is_element_clickable(self, element):
        """Check if an element is actually clickable."""
        try:
            # Check if element is displayed and has dimensions
            if not element.is_displayed():
                return False
                
            # Check if element has size (not zero width/height)
            size = element.size
            if size['width'] == 0 or size['height'] == 0:
                return False
                
            # Get element location
            location = element.location
            viewport_width = self.driver.execute_script("return window.innerWidth")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            # Check if element is within viewport
            scroll_x = self.driver.execute_script("return window.pageXOffset")
            scroll_y = self.driver.execute_script("return window.pageYOffset")
            
            element_x = location['x'] - scroll_x
            element_y = location['y'] - scroll_y
            
            if (element_x < 0 or element_y < 0 or 
                element_x > viewport_width or element_y > viewport_height):
                # Element is outside viewport
                return False
                
            return True
        except (StaleElementReferenceException, WebDriverException):
            return False
            
    def switch_to_iframe_recursively(self, iframe_index=0, max_depth=5, current_depth=0):
        """Recursively switch to iframes to find ad content."""
        if current_depth >= max_depth:
            return False
            
        try:
            # Switch back to main content first
            self.driver.switch_to.default_content()
            
            # Get all iframes in the current document
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            
            # If no iframes or index out of bounds, return
            if not iframes or iframe_index >= len(iframes):
                return False
                
            # Switch to the iframe at the specified index
            self.driver.switch_to.frame(iframes[iframe_index])
            print(f"Switched to iframe {iframe_index}")
            
            # Try to find ads in this iframe
            found_ads = self.find_and_click_ads(in_iframe=True)
            
            if found_ads:
                return True
                
            # If no ads found, try recursively checking nested iframes
            nested_iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            
            for i in range(len(nested_iframes)):
                if self.switch_to_iframe_recursively(i, max_depth, current_depth + 1):
                    return True
                    
            # Switch back to parent frame before returning
            self.driver.switch_to.parent_frame()
            return False
            
        except Exception as e:
            print(f"Error while switching to iframe: {e}")
            # Switch back to main content in case of error
            self.driver.switch_to.default_content()
            return False
            
    def find_ad_elements(self):
        """Find potential ad elements on the page."""
        # Common ad selectors (high priority)
        high_priority_selectors = [
            "[id*='google_ads']", 
            "[class*='adsense']", 
            "[id*='adsense']",
            "[class*='ad-unit']",
            "[id*='ad-unit']",
            "[data-ad-client]",
            "[data-ad-slot]",
            ".ad", 
            ".advertisement", 
            ".banner", 
            "[id*='banner']", 
            "[class*='banner']",
            "[id*='ad']", 
            "[class*='ad']", 
            "iframe[src*='ad']", 
            "iframe[id*='ad']",
            "iframe[src*='doubleclick']",
            "iframe[src*='googlead']",
            "div[aria-label*='Advertisement']"
        ]
        
        # Secondary selectors (generic clickable elements that might be ads)
        secondary_selectors = [
            ".social-bar", 
            "[class*='social']", 
            ".share-buttons", 
            "[class*='share']",
            "a[target='_blank']", 
            "a[rel='nofollow']", 
            "[onclick*='window.open']",
            "a img", # Images inside links are often ads
            "button:not([disabled])",
            "[role='button']",
            "a.external"
        ]
        
        # Combine selectors with priority
        all_elements = []
        
        # First check high priority selectors
        for selector in high_priority_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if self.is_element_clickable(element):
                        all_elements.append({"element": element, "selector": selector, "priority": "high"})
            except Exception as e:
                continue
                
        # Then check secondary selectors
        for selector in secondary_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if self.is_element_clickable(element):
                        all_elements.append({"element": element, "selector": selector, "priority": "low"})
            except Exception as e:
                continue
                
        return all_elements
           
    def find_and_click_ads(self, in_iframe=False):
        """Find various types of ad elements and click on them."""
        # Reset return value
        clicked = False
        
        try:
            # Find potential ad elements
            ad_elements = self.find_ad_elements()
            
            if not ad_elements:
                if not in_iframe:
                    print("No eligible ad elements found in the main document")
                return False
                
            # Sort elements by priority (high first)
            ad_elements.sort(key=lambda x: 0 if x["priority"] == "high" else 1)
            
            # Try clicking on random elements, preferring high priority ones
            for i in range(min(3, len(ad_elements))):
                # Get a random element with bias towards high priority
                if i == 0 and any(elem["priority"] == "high" for elem in ad_elements):
                    # Only choose from high priority elements
                    high_priority_elements = [elem for elem in ad_elements if elem["priority"] == "high"]
                    element_data = random.choice(high_priority_elements)
                else:
                    # Choose from any element
                    element_data = random.choice(ad_elements)
                    ad_elements.remove(element_data)  # Don't select the same element twice
                
                element = element_data["element"]
                selector = element_data["selector"]
                
                # Try to scroll element into view
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", element)
                    self.human_like_delay(1, 2)
                except Exception as e:
                    print(f"Error scrolling to element: {e}")
                    continue
                
                # Try to perform a human-like click
                try:
                    self.click_count += 1
                    print(f"Attempting to click {selector} element (attempt #{self.click_count})")
                    
                    # Hover over the element first
                    try:
                        actions = ActionChains(self.driver)
                        actions.move_to_element(element).perform()
                        self.human_like_delay(0.5, 1)
                    except Exception as hover_error:
                        print(f"Hover failed: {hover_error}")
                    
                    # Click the element
                    element.click()
                    print("✓ Click successful! ✓")
                    self.successful_clicks += 1
                    self.human_like_delay(1.5, 3)
                    
                    # Handle any new windows/tabs that opened
                    self.handle_new_windows()
                    
                    # Return after successful click to allow page to change
                    clicked = True
                    break
                    
                except (ElementNotInteractableException, StaleElementReferenceException) as e:
                    print(f"Could not interact with element: {e}")
                    # Try JavaScript click as fallback
                    try:
                        self.driver.execute_script("arguments[0].click();", element)
                        print("✓ JavaScript click successful! ✓")
                        self.successful_clicks += 1
                        self.human_like_delay(1.5, 3)
                        self.handle_new_windows()
                        clicked = True
                        break
                    except Exception as js_e:
                        print(f"JavaScript click failed: {js_e}")
            
            if not clicked and not in_iframe:
                print("Could not click any elements in the main document")
                
            return clicked
                
        except Exception as e:
            print(f"Error processing ad elements: {e}")
            return False
        
    def handle_new_windows(self):
        """Check for and close any new browser tabs/windows."""
        try:
            current_handles = self.driver.window_handles
            
            if len(current_handles) > 1:
                print(f"Detected {len(current_handles) - 1} new windows/tabs")
                
                # Switch back to main window first to ensure it's not closed
                self.driver.switch_to.window(self.main_window)
                
                # Close all other windows/tabs
                for handle in current_handles:
                    if handle != self.main_window:
                        self.driver.switch_to.window(handle)
                        print("Closing new tab/window")
                        self.human_like_delay(1, 2)
                        
                        # Take an action on the new page before closing (shows more human-like behavior)
                        try:
                            self.driver.execute_script("window.scrollBy(0, 100);")
                            self.human_like_delay(0.5, 1)
                        except:
                            pass
                            
                        self.driver.close()
                        
                # Switch back to main window
                self.driver.switch_to.window(self.main_window)
        except Exception as e:
            print(f"Error handling new windows: {e}")
            # Try to get back to the main window
            try:
                self.driver.switch_to.window(self.main_window)
            except:
                pass
    
    def check_iframes_for_ads(self):
        """Systematically check iframes for ads."""
        try:
            # Switch to main content first
            self.driver.switch_to.default_content()
            
            # Find all iframes
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            
            if not iframes:
                print("No iframes found on the page")
                return False
                
            print(f"Found {len(iframes)} iframes to check")
            
            # Try each iframe
            for i in range(min(len(iframes), 5)):  # Limit to 5 iframes to avoid excessive checking
                try:
                    self.driver.switch_to.default_content()
                    self.driver.switch_to.frame(iframes[i])
                    print(f"Checking iframe {i+1}/{min(len(iframes), 5)}")
                    
                    if self.find_and_click_ads(in_iframe=True):
                        print(f"Successfully clicked an ad in iframe {i+1}")
                        # Switch back to main content
                        self.driver.switch_to.default_content()
                        return True
                        
                except Exception as e:
                    print(f"Error checking iframe {i+1}: {e}")
                    
            # Switch back to main content
            self.driver.switch_to.default_content()
            return False
            
        except Exception as e:
            print(f"Error checking iframes: {e}")
            # Switch back to main content
            self.driver.switch_to.default_content()
            return False
    
    def run(self):
        """Main method to run the ad clicker."""
        try:
            # Navigate to the target website
            print("Navigating to the target website...")
            self.driver.get("https://ai-art-fake.onrender.com")
            self.human_like_delay(5, 8)  # Wait longer for page to fully load
            
            # Store the main window handle
            self.main_window = self.driver.current_window_handle
            
            # Set start time
            self.start_time = datetime.now()
            end_time = self.start_time + timedelta(minutes=self.duration_minutes)
            
            print(f"Starting ad clicking session at {self.start_time.strftime('%H:%M:%S')}")
            print(f"Will run until {end_time.strftime('%H:%M:%S')}")
            
            # Click cycle interval counter
            cycle_count = 0
            
            # Main loop
            while datetime.now() < end_time:
                cycle_count += 1
                print(f"\n--- Cycle {cycle_count} ---")
                
                # Occasionally refresh the page to get new ads (25% chance)
                if cycle_count > 1 and random.random() < 0.25:
                    print("Refreshing the page to get new ads...")
                    self.driver.refresh()
                    self.human_like_delay(5, 8)
                
                # Simulate human-like browsing
                self.move_mouse_randomly()
                self.scroll_randomly()
                
                # Try to find and click ads in the main document
                main_click_success = self.find_and_click_ads()
                
                # If no success in main document, try iframes
                if not main_click_success:
                    iframe_success = self.check_iframes_for_ads()
                    if not iframe_success:
                        print("No clickable ads found in this cycle")
                
                # Print stats
                elapsed = (datetime.now() - self.start_time).total_seconds() / 60
                print(f"Stats: {self.successful_clicks} successful clicks out of {self.click_count} attempts ({elapsed:.1f} minutes elapsed)")
                
                # Wait a bit before the next action
                self.human_like_delay(2, 5)
            
            elapsed_time = datetime.now() - self.start_time
            print(f"\nSession completed after {elapsed_time.total_seconds() / 60:.2f} minutes")
            print(f"Final stats: {self.successful_clicks} successful clicks out of {self.click_count} attempts")
            success_rate = (self.successful_clicks / self.click_count * 100) if self.click_count > 0 else 0
            print(f"Success rate: {success_rate:.1f}%")
        
        except Exception as e:
            print(f"An error occurred during execution: {e}")
        
        finally:
            # Clean up
            print("Closing browser...")
            try:
                self.driver.quit()
                print("Browser closed successfully")
            except Exception as e:
                print(f"Error closing browser: {e}")
            print("Session ended.")

if __name__ == "__main__":
    try:
        print("Starting Ad Clicker...")
        ad_clicker = AdClicker()
        ad_clicker.run()
    except Exception as e:
        print(f"Fatal error: {e}")