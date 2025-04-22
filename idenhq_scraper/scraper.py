import asyncio
import json
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from config import Config
class ProductScraper:
    def __init__(self):  # Make sure this doesn't take any parameters
        self.config = Config()
        
    async def scroll_to_load_more(self, page):
        """Scrolls to the bottom of the page to trigger loading more items."""
        print("Scrolling to load more items...")
        try:
            # Get count before scrolling
            before_count = await page.locator(self.config.PRODUCT_CARD_SELECTOR).count()
            
            # Execute scroll to bottom
            await page.evaluate("""
                window.scrollTo({
                    top: document.body.scrollHeight,
                    behavior: 'smooth'
                });
            """)
            
            # Wait for potential new content to load
            await asyncio.sleep(3)
            
            # Check if more items loaded
            after_count = await page.locator(self.config.PRODUCT_CARD_SELECTOR).count()
            
            print(f"Cards before scroll: {before_count}, after scroll: {after_count}")
            return after_count > before_count
        
        except Exception as e:
            print(f"Error during scroll operation: {e}")
            return False
    
    async def scrape_product_data(self, page):
        """Scrapes data from product cards on the inventory page with pagination or infinite scroll handling."""
        products_data = []
        print("\n--- Starting Scraping ---")
        try:
            # Wait for the page to stabilize
            await page.wait_for_load_state('networkidle', timeout=self.config.DEFAULT_TIMEOUT)
            await asyncio.sleep(2)  # Give extra time for any JavaScript to execute
            
            # Take a screenshot of the initial state
            await page.screenshot(path="debug_scrape_initial_state.png")
            
            # Check if pagination exists
            has_pagination = await page.locator(self.config.PAGINATION_SELECTOR).count() > 0
            print(f"Pagination detected: {has_pagination}")
            
            page_num = 1
            total_cards_processed = 0
            more_content_available = True
            
            # Continue until no more content can be loaded
            while more_content_available:
                print(f"\n--- Processing Page {page_num} ---")
                
                # Ensure product cards are loaded
                try:
                    await page.locator(self.config.PRODUCT_CARD_SELECTOR).first.wait_for(state="visible", timeout=self.config.LONG_TIMEOUT)
                except PlaywrightTimeoutError:
                    print(f"No cards found on page {page_num}. Taking screenshot.")
                    await page.screenshot(path=f"debug_no_cards_page_{page_num}.png")
                    more_content_available = False
                    break
                
                # Sometimes we need to wait a bit more for all cards to render
                await asyncio.sleep(1)
                
                # Count cards on current view
                card_locators = page.locator(self.config.PRODUCT_CARD_SELECTOR)
                count = await card_locators.count()
                print(f"Found {count} product cards on current view.")
                
                if count == 0:
                    print("Warning: No cards found on current view. Taking screenshot.")
                    await page.screenshot(path=f"debug_no_cards_page_{page_num}.png")
                    more_content_available = False
                    break
                    
                # Track if we found any new cards in this iteration
                new_cards_found = False
                processed_on_this_page = 0
                
                # Process visible cards
                for i in range(count):
                    card = card_locators.nth(i)
                    
                    # Check if we've already processed this card (by position)
                    if i < (total_cards_processed - processed_on_this_page):
                        continue
                        
                    new_cards_found = True
                    product_info = {}
                    print(f"Processing Card {total_cards_processed+1} (Page {page_num}, Card {i+1}/{count})...")
                    
                    try:
                        # Try to scroll the card into view
                        try:
                            await card.scroll_into_view_if_needed(timeout=self.config.SHORT_TIMEOUT)
                        except Exception as scroll_err:
                            print(f"Non-critical: Couldn't scroll card into view: {scroll_err}")
                        
                        # Extract Name (h3)
                        try:
                            product_info["name"] = (await card.locator("h3").first.text_content(timeout=self.config.SHORT_TIMEOUT) or "").strip()
                        except Exception as e:
                            print(f"Error extracting name: {e}")
                            product_info["name"] = "Unknown"
        
                        # Extract ID (p.text-muted-foreground.font-mono)
                        try:
                            id_text = (await card.locator("p.text-xs.text-muted-foreground.font-mono").first.text_content(timeout=self.config.SHORT_TIMEOUT) or "").strip()
                            product_info["id"] = id_text.replace("ID:", "").strip()
                        except Exception as e:
                            print(f"Error extracting ID: {e}")
                            product_info["id"] = "Unknown"
        
                        # Extract Category (div.rounded-full...)
                        try:
                            product_info["category"] = (await card.locator("div[class*='rounded-full'][class*='bg-primary']").first.text_content(timeout=self.config.SHORT_TIMEOUT) or "").strip()
                        except Exception as e:
                            print(f"Error extracting category: {e}")
                            product_info["category"] = "Unknown"
        
                        # Extract details from Definition List (dl > div > dt/dd)
                        try:
                            details_rows = card.locator("dl > div.flex.items-center.justify-between")
                            details_count = await details_rows.count()
        
                            for j in range(details_count):
                                row = details_rows.nth(j)
                                label_loc = row.locator("dt.text-muted-foreground")
                                value_loc = row.locator("dd.font-medium")
        
                                label = (await label_loc.first.text_content(timeout=self.config.SHORT_TIMEOUT) or "").strip().replace(':', '')
                                value = (await value_loc.first.text_content(timeout=self.config.SHORT_TIMEOUT) or "").strip()
        
                                # Special handling for Rating (nested span)
                                if label == "Rating":
                                    # Try to find the rating directly
                                    rating_span = value_loc.locator("span.ml-1.text-sm.text-muted-foreground")
                                    if await rating_span.count() > 0:
                                        value = (await rating_span.first.text_content(timeout=self.config.SHORT_TIMEOUT) or "").strip()
                                    # If rating not found in span, try to extract the numeric value from the text
                                    elif value and any(c.isdigit() for c in value):
                                        import re
                                        # Extract numeric part using regex
                                        match = re.search(r'(\d+\.\d+)', value)
                                        if match:
                                            value = match.group(1)
        
                                if label:  # Only add if label is found
                                    key = label.lower().replace(' ', '_').replace('(', '').replace(')', '')
                                    product_info[key] = value
                        except Exception as details_err:
                            print(f"Error extracting details: {details_err}")
        
                        # Extract Last Updated from the footer if it exists
                        try:
                            footer_loc = card.locator("div.items-center.p-6.pt-2.border-t > span")
                            if await footer_loc.count() > 0:
                                footer_text = (await footer_loc.first.text_content(timeout=self.config.SHORT_TIMEOUT) or "").strip()
                                if footer_text.startswith("Updated:"):
                                    product_info["footer_last_updated"] = footer_text.replace("Updated:", "").strip()
                        except Exception as footer_err:
                            print(f"Error extracting footer: {footer_err}")
                        
                        products_data.append(product_info)
                        total_cards_processed += 1
                        processed_on_this_page += 1
                        print(f"Card processed: {product_info.get('name', 'N/A')}. Total: {total_cards_processed}")
                        
                        # Periodically save progress
                        if total_cards_processed % 100 == 0:
                            print(f"Saving progress: {total_cards_processed} cards processed so far...")
                            with open(self.config.OUTPUT_FILE, 'w') as f:
                                json.dump(products_data, f, indent=2)
                    
                    except Exception as card_err:
                        print(f"Error processing card: {card_err}")
                        await page.screenshot(path=f"debug_card_error_page{page_num}_card{i+1}.png")
                
                # Save state before attempting next page navigation
                await page.screenshot(path=f"debug_after_page_{page_num}.png")
                
                # Check if we found any new cards on this page
                if not new_cards_found:
                    print("No new cards found on this page. This may indicate we've already processed all cards.")
                    more_content_available = False
                    break
                    
                # Determine how to navigate to next page/batch
                next_page_exists = await page.locator(self.config.NEXT_PAGE_SELECTOR).count() > 0
                
                if has_pagination and next_page_exists:
                    # If pagination exists, click next page button
                    print("Clicking Next Page button...")
                    next_button = page.locator(self.config.NEXT_PAGE_SELECTOR).first
                    try:
                        await next_button.wait_for(state="visible", timeout=self.config.SHORT_TIMEOUT)
                        await next_button.click(timeout=self.config.SHORT_TIMEOUT*2)
                        await page.wait_for_load_state('networkidle', timeout=self.config.LONG_TIMEOUT)
                        print("Successfully clicked Next Page button.")
                    except Exception as e:
                        print(f"Failed to click Next Page button: {e}. Trying infinite scroll approach.")
                        # If clicking fails, try scrolling to bottom as fallback
                        more_content_loaded = await self.scroll_to_load_more(page)
                        if not more_content_loaded:
                            print("No more cards could be loaded through scrolling. Ending scrape.")
                            more_content_available = False
                else:
                    # If no pagination or next button, try infinite scroll
                    print("No pagination detected or no Next button. Scrolling to load more...")
                    more_content_loaded = await self.scroll_to_load_more(page)
                    if not more_content_loaded:
                        print("No more cards could be loaded through scrolling. Ending scrape.")
                        more_content_available = False
                        break
                
                # Increment page counter for tracking
                page_num += 1
                
                # Avoid endless loop - safety mechanism in case detection of new content fails
                if page_num > 500:  # Increased but still reasonable limit
                    print("Reached maximum page safety limit (500). Stopping to prevent infinite loop.")
                    break
            
            print(f"\n--- Scraping Finished. Successfully processed {len(products_data)} products. ---")
            return products_data

        except Exception as e:
            print(f"An error occurred during scraping: {e}")
            try:
                if not page.is_closed(): 
                    await page.screenshot(path="debug_scrape_error.png")
            except Exception: pass
            # Return partial results if any
            return products_data