import os
import json
import asyncio
from playwright.async_api import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
from config import Config
class Authenticator:
    def __init__(self):
        self.config = Config()
    
    async def wait_for_element_robust(self, page, selector, timeout=None, state="visible"):
        """Waits for an element using locator with specific state and timeout."""
        if timeout is None:
            timeout = self.config.DEFAULT_TIMEOUT
            
        print(f"Waiting for selector '{selector}' to be {state} (timeout: {timeout/1000}s)...")
        try:
            await page.locator(selector).first.wait_for(state=state, timeout=timeout)
            print(f"Selector '{selector}' found and is {state}.")
            return True
        except PlaywrightTimeoutError:
            print(f"Timeout waiting for selector '{selector}' after {timeout/1000} seconds.")
            return False
        except PlaywrightError as e:
            if "closed" in str(e).lower():
                print(f"Error waiting for selector '{selector}': Page or context closed. {e}")
            else:
                print(f"Playwright error waiting for selector '{selector}': {e}")
            return False
        except Exception as e:
            print(f"Unexpected error waiting for selector '{selector}': {e}")
            return False
    
    async def click_element(self, page, selector, description, timeout=None):
        """Clicks an element with robust waiting and error handling."""
        if timeout is None:
            timeout = self.config.DEFAULT_TIMEOUT
            
        print(f"Attempting to click '{description}' (selector: {selector})...")
        try:
            element = page.locator(selector).first
            await element.wait_for(state="visible", timeout=timeout)
            print(f"Element '{description}' visible.")
            await asyncio.sleep(0.2)
            
            if await element.is_enabled(timeout=self.config.SHORT_TIMEOUT):
                print(f"Element '{description}' enabled.")
                await element.click(timeout=self.config.SHORT_TIMEOUT*2)
                print(f"Successfully clicked '{description}'.")
                try:
                    if not page.is_closed():
                        await page.screenshot(path=f"debug_after_click_{description.replace(' ', '_').lower()}.png")
                except PlaywrightError as screen_err:
                    print(f"Warning: Could not take screenshot after clicking {description}: {screen_err}")
                await asyncio.sleep(1.0)
                return True
            else:
                print(f"Error: Element '{description}' found but is not enabled.")
                if not page.is_closed(): 
                    await page.screenshot(path=f"debug_failed_click_{description.replace(' ', '_').lower()}_disabled.png")
                return False
        except PlaywrightTimeoutError as e:
            print(f"Timeout error during action for '{description}': {e}")
            if not page.is_closed(): 
                await page.screenshot(path=f"debug_failed_click_{description.replace(' ', '_').lower()}_timeout.png")
            return False
        except PlaywrightError as e:
            if "closed" in str(e).lower():
                print(f"Playwright error clicking '{description}': Page or context closed. {e}")
            else:
                print(f"Playwright error clicking '{description}': {e}")
            try:
                if not page.is_closed(): 
                    await page.screenshot(path=f"debug_failed_click_{description.replace(' ', '_').lower()}_playwright_error.png")
            except Exception: 
                pass
            return False
        except Exception as e:
            print(f"Unexpected error clicking '{description}': {e}")
            try:
                if not page.is_closed(): 
                    await page.screenshot(path=f"debug_failed_click_{description.replace(' ', '_').lower()}_unexpected_error.png")
            except Exception: 
                pass
            return False
    
    async def login(self, browser):
        """Logs in, verifies landing on instructions page, saves session."""
        context = None
        page = None
        print("Attempting new login...")
        try:
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()
            print(f"Navigating to {self.config.BASE_URL}...")
            await page.goto(self.config.BASE_URL, wait_until="domcontentloaded", timeout=self.config.LONG_TIMEOUT)
            print("Page loaded. Looking for login fields.")
            await page.screenshot(path="debug_login_page_initial.png")
            
            if not await self.wait_for_element_robust(page, self.config.LOGIN_USERNAME_SELECTOR):
                raise Exception("Login username field not found.")
            if not await self.wait_for_element_robust(page, self.config.LOGIN_PASSWORD_SELECTOR):
                raise Exception("Login password field not found.")
            
            await page.locator(self.config.LOGIN_USERNAME_SELECTOR).first.fill(self.config.CREDENTIALS["username"])
            await page.locator(self.config.LOGIN_PASSWORD_SELECTOR).first.fill(self.config.CREDENTIALS["password"])
            print("Credentials filled.")
            await page.screenshot(path="debug_login_fields_filled.png")
            
            if not await self.click_element(page, self.config.LOGIN_SUBMIT_SELECTOR, "Login Submit Button"):
                print("Login submit click failed. Trying password field Enter keypress...")
                await page.locator(self.config.LOGIN_PASSWORD_SELECTOR).first.press('Enter')
                await asyncio.sleep(1)
            
            print("Waiting for navigation or Launch button after login submission...")
            try:
                await page.wait_for_load_state('networkidle', timeout=self.config.LONG_TIMEOUT)
                if self.config.INSTRUCTIONS_URL_PART in page.url:
                    print(f"Successfully navigated to URL containing '{self.config.INSTRUCTIONS_URL_PART}'.")
                else:
                    print(f"Did not navigate to '{self.config.INSTRUCTIONS_URL_PART}' URL directly. Checking for '{self.config.LAUNCH_CHALLENGE_SELECTOR}'. Current URL: {page.url}")
                    if not await self.wait_for_element_robust(page, self.config.LAUNCH_CHALLENGE_SELECTOR):
                        await page.screenshot(path="debug_login_failed_no_nav_no_button.png")
                        raise PlaywrightTimeoutError(f"Login failed: Neither navigated to '{self.config.INSTRUCTIONS_URL_PART}' nor found '{self.config.LAUNCH_CHALLENGE_SELECTOR}' after submission.")
                    else:
                        print(f"Found '{self.config.LAUNCH_CHALLENGE_SELECTOR}', assuming login successful despite slow navigation.")
            except PlaywrightTimeoutError:
                print(f"Timeout waiting for page idle or navigation after login. Checking for '{self.config.LAUNCH_CHALLENGE_SELECTOR}'.")
                if not await self.wait_for_element_robust(page, self.config.LAUNCH_CHALLENGE_SELECTOR):
                    await page.screenshot(path="debug_login_failed_timeout_no_button.png")
                    raise PlaywrightTimeoutError(f"Login failed: Timeout after submission and '{self.config.LAUNCH_CHALLENGE_SELECTOR}' not found.")
                else:
                    print(f"Found '{self.config.LAUNCH_CHALLENGE_SELECTOR}' after timeout, assuming login successful.")
            
            if not await self.wait_for_element_robust(page, self.config.LAUNCH_CHALLENGE_SELECTOR, timeout=self.config.SHORT_TIMEOUT):
                await page.screenshot(path="debug_login_success_but_no_button_final.png")
                raise Exception(f"Login likely succeeded but couldn't find '{self.config.LAUNCH_CHALLENGE_SELECTOR}' reliably.")
            
            print("Authentication successful (verified by presence of Launch Challenge button).")
            await page.screenshot(path="debug_login_successful.png")
            
            storage_state = await context.storage_state()
            with open(self.config.SESSION_FILE, "w") as f:
                json.dump(storage_state, f, indent=2)
            print(f"Session saved to {self.config.SESSION_FILE}")
            
            return context
        
        except Exception as e:
            print(f"Authentication failed - Error during login: {e}")
            if page and not page.is_closed():
                try: await page.screenshot(path="debug_login_failed_error.png")
                except Exception: pass
            if page and not page.is_closed():
                try: await page.close()
                except Exception: pass
            if context:
                try: await context.close()
                except Exception: pass
            return None
    
    async def load_session(self, browser):
        """Loads session, verifies landing on instructions or challenge page."""
        if not os.path.exists(self.config.SESSION_FILE):
            print("Session file not found.")
            return None
        
        context = None
        page = None
        print("Found existing session file, attempting to load and validate...")
        try:
            with open(self.config.SESSION_FILE, "r") as f:
                storage_state = json.load(f)
            if not storage_state or 'cookies' not in storage_state or 'origins' not in storage_state:
                print("Session file content is invalid.")
                os.remove(self.config.SESSION_FILE)
                print("Removed invalid session file.")
                return None
            
            context = await browser.new_context(storage_state=storage_state, ignore_https_errors=True)
            page = await context.new_page()
            print(f"Navigating to {self.config.BASE_URL + self.config.INSTRUCTIONS_URL_PART} with loaded session...")
            await page.goto(self.config.BASE_URL + self.config.INSTRUCTIONS_URL_PART, 
                          wait_until="domcontentloaded", 
                          timeout=self.config.LONG_TIMEOUT)
            print("Page loaded with session. Validating...")
            await page.screenshot(path="debug_session_load_page.png")
            
            current_url = page.url
            on_instructions = self.config.INSTRUCTIONS_URL_PART in current_url
            on_challenge = self.config.CHALLENGE_URL_PART in current_url
            
            can_launch = await self.wait_for_element_robust(page, self.config.LAUNCH_CHALLENGE_SELECTOR)
            
            if on_instructions and can_launch:
                print("Session valid: On instructions page and Launch button found.")
            elif on_challenge:
                print("Session valid: Loaded directly onto challenge page.")
            elif can_launch:
                print(f"Session valid: Not on instructions page (URL: {current_url}), but Launch button found.")
            else:
                print(f"Session invalid or expired (URL: {current_url}, Launch button not found).")
                await page.screenshot(path="debug_session_invalid.png")
                raise Exception("Session validation failed")
            
            print("Session validation successful.")
            await page.screenshot(path="debug_session_valid.png")
            return context
        
        except Exception as e:
            print(f"Session loading/validation failed: {e}")
            if page and not page.is_closed():
                try: await page.screenshot(path="debug_session_load_failed.png")
                except Exception: pass
            if page and not page.is_closed():
                try: await page.close()
                except Exception: pass
            if context:
                try: await context.close()
                except Exception: pass
            if os.path.exists(self.config.SESSION_FILE):
                try:
                    os.remove(self.config.SESSION_FILE)
                    print(f"Removed potentially invalid session file: {self.config.SESSION_FILE}")
                except OSError as remove_err:
                    print(f"Warning: Could not remove session file {self.config.SESSION_FILE}: {remove_err}")
            return None