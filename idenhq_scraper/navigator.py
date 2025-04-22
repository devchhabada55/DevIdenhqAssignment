import asyncio
from playwright.async_api import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

from auth import Authenticator
from config import Config

class Navigator:
    def __init__(self):  # Remove the config parameter
        self.config = Config()  # Create config internally like Authenticator does
        self.auth = Authenticator()
    
    
    async def navigate_challenge_flow(self, page):
        """Handles sequence: Launch -> Start Journey -> Continue Search -> Inventory Button -> Verify Grid."""
        try:
            current_url = page.url
            print(f"--- Starting Challenge Navigation Flow ---")
            print(f"Starting challenge navigation flow from: {current_url}")
            
            # --- Step 1: Launch Challenge (if on Instructions page) ---
            if self.config.INSTRUCTIONS_URL_PART in current_url:
                print("On instructions page, attempting to click Launch Challenge...")
                if not await self.auth.click_element(page, self.config.LAUNCH_CHALLENGE_SELECTOR, "Launch Challenge"):
                    return False
                try:
                    await page.wait_for_url(f"**{self.config.CHALLENGE_URL_PART}", timeout=self.config.LONG_TIMEOUT)
                    print(f"Navigated successfully to URL containing '{self.config.CHALLENGE_URL_PART}'.")
                except PlaywrightTimeoutError:
                    print(f"Warning: Navigation to '{self.config.CHALLENGE_URL_PART}' URL timed out after launch. Checking current URL and elements.")
                    if self.config.CHALLENGE_URL_PART not in page.url:
                        print(f"Still not on challenge URL. Current URL: {page.url}")
                        if not await self.auth.wait_for_element_robust(page, self.config.START_JOURNEY_SELECTOR):
                            await page.screenshot(path="debug_failed_navigate_post_launch.png")
                            print("Error: Could not find Start Journey button after Launch Challenge timeout and wrong URL.")
                            return False
                        else:
                            print("Found Start Journey button despite navigation timeout/wrong URL. Proceeding cautiously.")
                    else:
                        print("URL contains challenge part now. Proceeding.")
            
            elif self.config.CHALLENGE_URL_PART in current_url:
                print("Already on challenge page, skipping Launch Challenge.")
            else:
                if await page.locator(self.config.LAUNCH_CHALLENGE_SELECTOR).first.is_visible(timeout=self.config.SHORT_TIMEOUT):
                    print(f"On unexpected page ({current_url}) but Launch button found. Attempting launch...")
                    if not await self.auth.click_element(page, self.config.LAUNCH_CHALLENGE_SELECTOR, "Launch Challenge"): 
                        return False
                    try:
                        await page.wait_for_url(f"**{self.config.CHALLENGE_URL_PART}", timeout=self.config.LONG_TIMEOUT)
                        print(f"Navigated successfully to URL containing '{self.config.CHALLENGE_URL_PART}'.")
                    except PlaywrightTimeoutError:
                        print("Warning: Navigation timeout after launching from unexpected page. Checking elements.")
                        if not await self.auth.wait_for_element_robust(page, self.config.START_JOURNEY_SELECTOR): 
                            return False
                        else: 
                            print("Found Start Journey button despite nav timeout.")
                else:
                    print(f"Error: Not on expected page ({self.config.INSTRUCTIONS_URL_PART} or {self.config.CHALLENGE_URL_PART}) and Launch button not found. Current URL: {page.url}")
                    await page.screenshot(path="debug_wrong_page_start_challenge_flow.png")
                    return False
            
            # --- Verify we are now on the Challenge Page ---
            if self.config.CHALLENGE_URL_PART not in page.url:
                try:
                    await page.wait_for_url(f"**{self.config.CHALLENGE_URL_PART}", timeout=self.config.SHORT_TIMEOUT)
                except PlaywrightTimeoutError:
                    print(f"Error: Failed to confirm navigation to challenge page. Current URL: {page.url}")
                    await page.screenshot(path="debug_not_on_challenge_page_final.png")
                    return False
            print(f"Confirmed on challenge page: {page.url}")
            
            # --- Step 2: Click Start Journey ---
            if not await self.auth.wait_for_element_robust(page, self.config.START_JOURNEY_SELECTOR): 
                return False
            if not await self.auth.click_element(page, self.config.START_JOURNEY_SELECTOR, "Start Journey"): 
                return False
            
            # --- Step 3: Click Continue Search ---
            if not await self.auth.wait_for_element_robust(page, self.config.CONTINUE_SEARCH_SELECTOR): 
                return False
            if not await self.auth.click_element(page, self.config.CONTINUE_SEARCH_SELECTOR, "Continue Search"): 
                return False
            
            # --- Step 4: Click Inventory Section Button ---
            print("Waiting for the 'Inventory Section' button...")
            if not await self.auth.wait_for_element_robust(page, self.config.INVENTORY_BUTTON_SELECTOR):
                await page.screenshot(path="debug_failed_find_inventory_button.png")
                return False
            if not await self.auth.click_element(page, self.config.INVENTORY_BUTTON_SELECTOR, "Inventory Section Button"):
                return False
            
            # Add a wait to ensure page loads completely
            await asyncio.sleep(3.0)
            
            # --- Step 5: Wait for Product Cards to be visible ---
            # First wait for the page to be stable
            await page.wait_for_load_state('networkidle', timeout=self.config.LONG_TIMEOUT)
            
            # Take a screenshot of the current state for debugging
            await page.screenshot(path="debug_after_inventory_click.png")
            
            # Wait for any product cards to be visible
            print(f"Waiting for product cards to be visible using selector: {self.config.PRODUCT_CARD_SELECTOR}")
            try:
                card_locator = page.locator(self.config.PRODUCT_CARD_SELECTOR).first
                await card_locator.wait_for(state="visible", timeout=self.config.LONG_TIMEOUT)
                print("Product card is visible!")
                await page.screenshot(path="debug_product_card_visible.png")
                return True
            except PlaywrightTimeoutError:
                print("Failed to find any product cards.")
                await page.screenshot(path="debug_no_product_cards.png")
                return False
        
        except PlaywrightError as e:
            if "closed" in str(e).lower():
                print(f"Critical Error in challenge flow: Page or context closed unexpectedly. {e}")
            else:
                print(f"A Playwright error occurred during the challenge navigation flow: {e}")
            try:
                if page and not page.is_closed():
                    await page.screenshot(path="debug_challenge_flow_playwright_error.png")
            except Exception: 
                pass
            return False
        except Exception as e:
            print(f"An unexpected error occurred during the challenge navigation flow: {e}")
            try:
                if page and not page.is_closed():
                    await page.screenshot(path="debug_challenge_flow_unexpected_error.png")
            except Exception: 
                pass
            return False