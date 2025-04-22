import os
import json
import asyncio
import time
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
from config import Config
from navigator import Navigator
from scraper import ProductScraper
from auth import Authenticator # Import AuthManager from its module

async def main():
    """Main execution function for the IdenhQ scraper."""
    start_time = time.time()
    config = Config()
    
    # Clear old screenshots
    print("Clearing old debug screenshots...")
    for f in os.listdir("."):
        if f.startswith("debug_") and f.endswith(".png"):
            try: os.remove(f)
            except OSError: pass

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Set headless=False for debugging
        print("Browser launched.")
        context = None
        page = None

        try:
            # Initialize managers
            auth_manager = Authenticator() 
            navigator = Navigator()
            scraper = ProductScraper()
            
            # Try loading session first
            context = await auth_manager.load_session(browser)

            if not context:
                print("Could not load valid session, attempting new login.")
                context = await auth_manager.login(browser)

            if not context:
                print("Failed to establish a session. Exiting.")
                return

            print("Successfully obtained context.")
            # Use the first page if available, otherwise create new
            if context.pages:
                page = context.pages[0]
                print("Reusing existing page from context.")
                if config.INSTRUCTIONS_URL_PART not in page.url and config.CHALLENGE_URL_PART not in page.url:
                    print(f"Page is on unexpected URL: {page.url}. Navigating to instructions page.")
                    try:
                        await page.goto(config.BASE_URL + config.INSTRUCTIONS_URL_PART, wait_until="domcontentloaded", timeout=config.LONG_TIMEOUT)
                    except Exception as nav_err:
                        print(f"Failed to navigate reused page to instructions: {nav_err}")
                        print("Closing potentially bad reused page and creating a new one.")
                        await page.close()
                        page = await context.new_page()
                        await page.goto(config.BASE_URL + config.INSTRUCTIONS_URL_PART, wait_until="domcontentloaded", timeout=config.LONG_TIMEOUT)
            else:
                print("No existing page in context, creating new page.")
                page = await context.new_page()
                await page.goto(config.BASE_URL + config.INSTRUCTIONS_URL_PART, wait_until="domcontentloaded", timeout=config.LONG_TIMEOUT)

            print(f"Page ready at URL: {page.url}\n")

            # Set a longer default timeout for this complex scrape
            page.set_default_timeout(60000)  # 60 seconds

            # Navigate through the challenge
            if await navigator.navigate_challenge_flow(page):
                # Scrape data if navigation succeeded
                product_data = await scraper.scrape_product_data(page)

                if product_data:
                    print(f"\nSaving {len(product_data)} products to {config.OUTPUT_FILE}...")
                    with open(config.OUTPUT_FILE, 'w') as f:
                        json.dump(product_data, f, indent=2)
                    print("Data saved successfully.")
                else:
                    print("\nNo product data was scraped.")
            else:
                print("\n--- Challenge Navigation Flow Failed ---")
                print("Review debug screenshots and console output.")

        except Exception as e:
            print(f"\n--- An error occurred in the main execution block ---")
            print(f"Error: {e}")
            if page and not page.is_closed():
                await page.screenshot(path="debug_main_exception.png")
        finally:
            print("\nClosing browser...")
            if page and not page.is_closed():
                try: await page.close()
                except Exception as page_close_err: print(f"Error closing page: {page_close_err}")
            if context:
                try: await context.close()
                except Exception as context_close_err: print(f"Error closing context: {context_close_err}")
            if browser:
                try: await browser.close()
                except Exception as browser_close_err: print(f"Error closing browser: {browser_close_err}")

    end_time = time.time()
    print(f"Total execution time: {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(main())