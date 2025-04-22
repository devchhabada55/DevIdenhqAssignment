class Config:
    # --- Files ---
    SESSION_FILE = "session.json"
    OUTPUT_FILE = "product_data.json"
    
    # --- URLs ---
    BASE_URL = "https://hiring.idenhq.com"
    INSTRUCTIONS_URL_PART = "/instructions"
    CHALLENGE_URL_PART = "/challenge"
    
    # --- Credentials ---
    CREDENTIALS = {
        "username": "chhabadadev@gmail.com",
        "password": "EynKbIKc"
    }
    
    # --- Timeouts ---
    DEFAULT_TIMEOUT = 30000  # 30 seconds (in ms)
    LONG_TIMEOUT = 45000     # 45 seconds for potentially slower operations
    SHORT_TIMEOUT = 5000     # 5 seconds for quick checks
    
    # --- Selectors ---
    # Login Page
    LOGIN_USERNAME_SELECTOR = 'input[name="username"], input[type="email"], input[placeholder*="email" i]'
    LOGIN_PASSWORD_SELECTOR = 'input[name="password"], input[type="password"]'
    LOGIN_SUBMIT_SELECTOR = 'button[type="submit"], input[type="submit"], button:has-text("Login"), button:has-text("Sign in")'
    
    # Instructions Page (/instructions)
    LAUNCH_CHALLENGE_SELECTOR = "button:has-text('Launch Challenge')"
    
    # Challenge Page Flow
    START_JOURNEY_SELECTOR = "button:has-text('Start Journey'), a:has-text('Start Journey')"
    CONTINUE_SEARCH_SELECTOR = "button:has-text('Continue Search')"
    INVENTORY_BUTTON_SELECTOR = "button:has-text('Inventory Section')"
    
    # Inventory Page / Final Target
    PRODUCT_INVENTORY_SELECTOR = "div.space-y-6"
    PRODUCT_CARD_SELECTOR = "div.rounded-lg.border.bg-card.text-card-foreground.shadow-sm"
    
    # Pagination
    NEXT_PAGE_SELECTOR = "button:has-text('Next'), a:has-text('Next')"
    PAGINATION_SELECTOR = "nav[aria-label='pagination'], div.pagination"