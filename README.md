# Job-Scraper

Here is a `README.md` file for your `Universal Web Scraper` project:

```markdown
# Universal Web Scraper 🦑

This project is a **Universal Web Scraper** built using Python, Selenium, BeautifulSoup, and OpenAI's GPT-based models. It provides an easy-to-use Streamlit interface for scraping job postings or other data from multiple URLs. The scraper can clean, format, and export the data into structured JSON and CSV formats, with insights on token usage and API cost.

## Features

- **Multiple URL Input:** Accepts a list of URLs for scraping.
- **HTML Cleaning:** Cleans raw HTML by removing headers, footers, and unnecessary classes.
- **Data Formatting:** Formats the cleaned HTML data into structured JSON using GPT models.
- **Token & Cost Calculation:** Provides insights on input/output tokens used and the total API cost.
- **Downloadable Outputs:** Allows users to download the results in both JSON and CSV formats.
- **Supports Multiple Models:** Allows users to select from different OpenAI GPT models (e.g., `babbage-002`, `gpt-4o-mini`, etc.).

## Installation

### Prerequisites

- Python 3.8+
- Pip package manager

### Clone the Repository

```bash
git clone https://github.com/your-username/universal-web-scraper.git
cd universal-web-scraper
```

### Install the Dependencies

```bash
pip install -r requirements.txt
```

### Set Up Environment Variables

Create a `.env` file in the root directory and add your OpenAI API key:

```bash
OPENAI_API_KEY=your_openai_api_key
```

## Usage

To start the Streamlit app, run the following command in your terminal:

```bash
streamlit run streamlit_app.py
```

### Using the Web Scraper

1. Enter the URLs you want to scrape into the "URLs" field in the sidebar (separated by newlines).
2. Select the GPT model you want to use for formatting the scraped data.
3. Click the "Scrape URLs" button to start the scraping process.
4. View the results for each URL, including formatted data, token usage, and cost estimation.
5. Download the structured data in JSON or CSV format.

## Project Structure

```
├── scraper.py               # Contains functions for fetching, cleaning, and formatting data
├── streamlit_app.py          # Main Streamlit app file
├── requirements.txt          # List of dependencies
├── README.md                 # Project documentation
└── .env                      # Environment variables (not included in the repo)
```

## Functionality

- **fetch_html_selenium:** Fetches the raw HTML content from the provided URLs using Selenium.
- **clean_html:** Cleans the raw HTML by removing unwanted elements like headers, footers, and classes.
- **format_data:** Formats the cleaned HTML using OpenAI GPT models to create structured JSON data.
- **calculate_price:** Calculates the API token usage and the estimated cost based on input/output token count.
- **save_raw_data/save_formatted_data:** Saves the raw and formatted data to local files.

## Screenshots

### Web Scraper Interface

![web_scraper_interface](path_to_screenshot_1.png)

### Results Display

![results_display](path_to_screenshot_2.png)

## Contributing

If you would like to contribute to this project, feel free to open a pull request or issue on GitHub. Contributions and suggestions are welcome!


```

### Instructions:
- Update the GitHub link in the "Clone the Repository" section.
- Add paths to screenshots in the "Screenshots" section if you have any, or remove that part if not needed.
  
Let me know if you need further modifications!
