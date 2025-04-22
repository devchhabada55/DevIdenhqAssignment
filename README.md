# IdenhQ Product Scraper

A robust asynchronous web scraper designed to extract product data from the IdenhQ hiring challenge using Playwright.

## Overview

This project implements an automated solution for navigating a multi-step web challenge, authenticating, and systematically extracting product inventory data. It features session management, robust error handling, comprehensive logging, and modular architecture.

## Features

- **Authentication Management**: Handles login and session persistence
- **Robust Navigation**: Navigates through a multi-step challenge flow
- **Comprehensive Scraping**: Extracts detailed product information 
- **Pagination and Infinite Scroll**: Supports both standard pagination and infinite scroll interfaces
- **Error Recovery**: Employs defensive programming with robust error handling
- **Debug Screenshots**: Automatically captures screenshots at critical steps for debugging
- **Progress Tracking**: Periodically saves scraping progress

## Requirements

- Python 3.8+
- Playwright
- AsyncIO

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd idenhq-scraper
   ```

2. Install dependencies:
   ```bash
   pip install playwright asyncio
   ```

3. Install Playwright browsers:
   ```bash
   playwright install
   ```

## Configuration

The scraper is configured through the `Config` class in `config.py`:

- **URLs**: Base URL and path segments
- **Credentials**: Login credentials
- **Timeouts**: Default, short, and long timeouts (in milliseconds)
- **Selectors**: CSS selectors for important page elements
- **File Paths**: Session storage and output file locations

Modify these settings as needed for your specific requirements.

## Project Structure

- **main.py**: Entry point and orchestration logic
- **auth.py**: Authentication and session management
- **navigator.py**: Page navigation logic
- **scraper.py**: Product data extraction
- **config.py**: Configuration settings

## Usage

Run the scraper:

```bash
python main.py
```

The script will:
1. Attempt to load an existing session
2. If no valid session exists, perform a new login
3. Navigate through the challenge flow
4. Extract product data
5. Save results to `product_data.json`

## Architecture

### Authenticator

Handles login processes and session management:
- Login attempt with credentials
- Session storage and verification
- Robust element interaction

### Navigator

Manages the challenge flow navigation:
- Step-by-step page progression
- Element validation
- Error handling and recovery

### ProductScraper

Extracts product information:
- Supports both pagination and infinite scroll
- Handles partial page loads
- Progressive data extraction
- Periodic progress saving

## Debugging

Debug screenshots are automatically captured during execution:
- `debug_login_page_initial.png`: Initial login page
- `debug_session_load_page.png`: State after session load
- `debug_after_page_[N].png`: State after processing each page
- Various other debug points during execution

## Output Format

Data is saved to `product_data.json` as an array of product objects with fields:
- `name`: Product name
- `id`: Product ID
- `category`: Product category
- Various additional product details (price, rating, stock, etc.)

Example:
```json
[
  {
    "name": "Premium Bluetooth Headphones",
    "id": "PRD-123456",
    "category": "Electronics",
    "price": "$149.99",
    "rating": "4.7",
    "stock": "In Stock"
  },
  ...
]
```

## Error Handling

The scraper implements comprehensive error handling:
- Timeout management
- Page and context closure detection
- Screenshot capture at failure points
- Progressive data saving to preserve progress

## License

[Specify your license here]

## Author

[Your name or organization]
