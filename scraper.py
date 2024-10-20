import os
import time
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
from pydantic import BaseModel, Field, HttpUrl, field_validator
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
# from openai import OpenAI
import tiktoken
import openai

# Load environment variables
load_dotenv()

# Set up the Chrome WebDriver options
def setup_selenium():
    options = Options()
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    service = Service(r"C:\Users\ajoyd\Downloads\chromedriver-win64\chromedriver.exe")  
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# Fetch HTML using Selenium
def fetch_html_selenium(url: str) -> str:
    driver = setup_selenium()
    try:
        driver.get(url)
        time.sleep(5)  # Simulate user interaction delay
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        html = driver.page_source
        return html
    finally:
        driver.quit()

# Clean HTML content using BeautifulSoup
# Clean HTML content using BeautifulSoup and remove "Related Jobs" section
def clean_html(html_content: str) -> str:
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove irrelevant sections (style, footer, header, script)
    for element in soup.find_all(['style', 'footer', 'header', 'script', 'meta']):
        element.decompose()

    # Identify and remove the section below "Related Jobs" or similar keywords
    related_jobs_keywords = ["Related Jobs", "Recommended Jobs", "Similar Jobs"]
    
    # Find and remove the section containing related jobs
    for keyword in related_jobs_keywords:
        related_section = soup.find(lambda tag: tag.name == "section" and keyword.lower() in tag.get_text().lower())
        if related_section:
            # Remove everything after this section
            related_section.decompose()
            break  # Exit the loop after removing the first matching section

    # Remove all class attributes except for those containing 'description' as part of the class name
    for tag in soup.find_all(True):
        if 'class' in tag.attrs:
            tag_classes = tag.attrs['class']
            tag.attrs['class'] = [cls for cls in tag_classes if 'description' in cls]
            if not tag.attrs['class']:
                tag.attrs.pop('class', None)

    return str(soup)

# Define the pricing for models
pricing = {
    "gpt-4o-mini": {
        "input": 0.15 / 1_000_000,  # $0.150 per 1M input tokens
        "output": 0.60 / 1_000_000, # $0.600 per 1M output tokens
    },
    "gpt-4o-mini-2024-07-18": {
        "input": 0.15 / 1_000_000,  # $0.150 per 1M input tokens
        "output": 0.60 / 1_000_000, # $0.600 per 1M output tokens
    },
    "babbage-002": {
        "input": 0.4 / 1_000_000,  # $0.40 per 1M input tokens
        "output": 0.4 / 1_000_000,  # $0.40 per 1M output tokens
    },
    "gpt-3.5-turbo-0125": {
        "input": 0.5 / 1_000_000,  # $0.50 per 1M input tokens
        "output": 1.5 / 1_000_000,  # $1.50 per 1M output tokens
    },
    "gpt-3.5-turbo-1106": {
        "input": 1 / 1_000_000,  # $1 per 1M input tokens
        "output": 2 / 1_000_000,  # $2 per 1M output tokens
    },
}

model_used = "gpt-4o-mini"

# Save raw HTML data to a file
def save_raw_data(raw_data: str, timestamp: str, output_folder: str = 'output') -> str:
    os.makedirs(output_folder, exist_ok=True)
    raw_output_path = os.path.join(output_folder, f'rawData_{timestamp}.html')
    with open(raw_output_path, 'w', encoding='utf-8') as f:
        f.write(raw_data)
    print(f"Raw HTML data saved to {raw_output_path}")
    return raw_output_path

# Pydantic models for job postings
class Salary(BaseModel):
    min: Optional[int] = None
    max: Optional[int] = None
    currency: str = "USD"  
    period: str = "yearly"  

    @field_validator('min', 'max', mode='before')
    def validate_salary(cls, value):
        if value is not None and value < 0:
            raise ValueError('Salary cannot be negative')
        return value
    # Field validator to handle None values for currency and period
    @field_validator('currency', 'period', mode='before')
    def set_defaults(cls, value, info):
        if value is None:
            if info.field_name == 'currency':
                return 'USD'
            elif info.field_name == 'period':
                return 'yearly'
        return value

from dateutil import parser

def parse_date(date_str: str) -> Optional[str]:
    """
    Tries to parse various date formats and returns a date in 'YYYY-MM-DD' format.
    If the date cannot be parsed, returns None.
    """
    try:
        # Attempt to parse the date
        parsed_date = parser.parse(date_str).strftime("%Y-%m-%d")
        return parsed_date
    except (ValueError, OverflowError):
        if "ongoing" in date_str.lower():
            return None  # Handle special cases like 'Ongoing'
        return None  # Return None if the format is unrecognized

class Location(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "Unknown"  

class EducationalQualification(BaseModel):
    degree: Optional[str] = "Unspecified"
    field_of_study: Optional[str] = "General"  

class JobPosting(BaseModel):
    job_title: str
    company_name: str
    locations: List[Location]
    job_tags: List[str] = Field(default_factory=list)
    employment_type: str
    salary: Salary
    job_description: str
    responsibilities: List[str] = Field(default_factory=list)
    requirements: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    educational_qualifications: List[EducationalQualification] = Field(default_factory=list)
    date_posted: Optional[str] = None
    application_deadline: Optional[str] = None
    application_link: str 

    @field_validator('job_title', 'company_name', mode='before')
    def validate_mandatory_fields(cls, value, field):
        if not value or value.strip() == "":
            raise ValueError(f"{field.name} is a required field and cannot be empty")
        return value

    @field_validator('date_posted', 'application_deadline', mode='before')
    def validate_dates(cls, value):
        return parse_date(value) if value else value

class JobPostingsContainer(BaseModel):
    job_postings: List[JobPosting]
    metadata: Dict[str, Union[str, int]]

    @field_validator('job_postings', mode='before')
    def validate_job_postings(cls, value):
        if not value or len(value) == 0:
            raise ValueError("Job postings list cannot be empty")
        return value

# Function to convert relative date strings to absolute dates
def convert_relative_to_absolute(date_str: str) -> str:
    if "day" in date_str:
        days_ago = int(date_str.split()[0])
        return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    elif "week" in date_str:
        weeks_ago = int(date_str.split()[0])
        return (datetime.now() - timedelta(weeks=weeks_ago)).strftime("%Y-%m-%d")
    elif "month" in date_str:
        months_ago = int(date_str.split()[0])
        return (datetime.now() - timedelta(days=months_ago * 30)).strftime("%Y-%m-%d")
    
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError("Date should be in YYYY-MM-DD format")

# Extract and format data using OpenAI API
def format_data(data: str, model: str = "gpt-4o-mini") -> Optional[JobPostingsContainer]:
    openai.api_key=os.getenv('OPENAI_API_KEY')
    
    system_message = """
    You are an intelligent data extraction assistant. Your task is to extract structured job posting data from HTML content and convert it into JSON format.

    Output must match the following structure:
    {
        "job_postings": [
            {
                "job_title": "string",
                "company_name": "string",
                "locations": [
                    {
                        "city": "string",
                        "state": "string",
                        "country": "string"
                    }
                ],
                "job_tags": ["string"],  // Extract all the job tags correctly. Most job tags are present inside <a> tags.
                "employment_type": "string",  // Parse for employment types such as Full-Time, Part-Time, Contract, etc.
                "salary": {
                    "min": "integer",
                    "max": "integer",
                    "currency": "string",
                    "period": "string"  // e.g., "annual", "hourly", "monthly". If not provided, leave null.
                },
                "job_description": "string",  // Extract all text content from the <div> tag whose class name contains 'description'.
                                              // Ensure that you extract all textual content without omission, including:
                                              // - All child elements like <p>, <ul>, <li>, <h>, <span>, and other nested <div> tags.
                                              // - Make sure to handle any multi-level nesting and include all text within those tags.
                                              // - Convert all extracted content into clean, structured plain text.
                                              // - Maintain the hierarchy of the information: paragraphs, lists, headers, etc., should be clearly delineated in the output.
                                              // - Avoid truncation of long descriptions; ensure that all text is captured completely, no matter the length.
                                              // - Eliminate all HTML tags and provide the text in a readable format with proper line breaks and indentation.
                "responsibilities": ["string"],  // Extract from list items within sections labeled "Responsibilities".
                "requirements": ["string"],  // Extract from list items within sections labeled "Requirements" or "Qualifications".
                "skills": ["string"],  // Extract skills from whole content like Python, JavaScript, SQL, etc.
                "educational_qualifications": [
                    {
                        "degree": "string",  // e.g., Bachelor's, Master's. Leave null if not provided.
                        "field_of_study": "string"  // e.g., Computer Science. Leave null if not provided.
                    }
                ],
                "date_posted": "string",  // Extract exact posting date in YYYY-MM-DD format
                "application_deadline": "string",  // Extract exact deadline in YYYY-MM-DD format
                "application_link": "string"  // Extract URL link to apply
            }
        ],
        "metadata": {
            "scraping_timestamp": "string",  // Time when the data is scraped.
            "scraped_from": "string",  // URL from which the job posting is scraped.
            "source_type": "string",  // The type of website or platform (e.g., "job board", "company website").
            "scraper_version": "string",  // Version of the scraper.
            "data_format_version": "string",  // Version of the data format.
            "total_job_postings": "integer"  // The number of job postings extracted from the HTML.
        }
    }

    Additional Guidelines:
    - For "job_description", **capture all text from the <div> tag with a class name containing 'description'**. 
          - Ensure you account for deeply nested elements and extract all textual content, regardless of the depth of nesting.
          - If there are multiple paragraphs, bullet points, or lists, ensure they are all included without skipping any content.
          - The final output should be a clear, structured plain text representation, with appropriate formatting such as line breaks and indentation to maintain readability.
          - **Do not truncate or cut off** any part of the description, regardless of how long it is.
          - **Strip out all HTML tags** and provide only the pure textual information in a coherent format.
    - For "responsibilities" and "requirements", extract the text from list items under headings containing keywords such as "Responsibilities" or "Requirements".
    - For "job_tags", extract tags from <a> tags or any section labeled with "tags".
"""



        
    user_message = f"Extract the following information from the provided HTML content:\n\n{data}"
    
    try:
        completion = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "job_posting_schema",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "job_postings": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "job_title": {"type": "string"},
                                        "company_name": {"type": "string"},
                                        "locations": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "city": {"type": "string"},
                                                    "state": {"type": "string"},
                                                    "country": {"type": "string"}
                                                }
                                            }
                                        },
                                        "job_tags": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "employment_type": {"type": "string"},
                                        "salary": {
                                            "type": "object",
                                            "properties": {
                                                "min": {"type": "integer"},
                                                "max": {"type": "integer"},
                                                "currency": {"type": "string"},
                                                "period": {"type": "string"}
                                            }
                                        },
                                        "job_description": {"type": "string"},
                                        "responsibilities": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "requirements": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "skills": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "educational_qualifications": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "degree": {"type": "string"},
                                                    "field_of_study": {"type": "string"}
                                                }
                                            }
                                        },
                                        "date_posted": {"type": "string"},
                                        "application_deadline": {"type": "string"},
                                        "application_link": {"type": "string"}
                                    },
                                    "required": ["job_title", "company_name", "application_link"]
                                }
                            },
                            "metadata": {
                                "type": "object",
                                "properties": {
                                    "scraping_timestamp": {"type": "string"},
                                    "scraped_from": {"type": "string"},
                                    "source_type": {"type": "string"},
                                    "scraper_version": {"type": "string"},
                                    "data_format_version": {"type": "string"},
                                    "total_job_postings": {"type": "integer"}
                                }
                            }
                        },
                        "additionalProperties": False
                    }
                }
            }
        )
        
        response_content = completion.choices[0].message.content.strip()

        if response_content.startswith('```json'):
            response_content = response_content.replace('```json', '').replace('```', '').strip()
        
        if response_content.startswith('{'):
            formatted_data = JobPostingsContainer.parse_raw(response_content)
            
            return formatted_data
        else:
            print(f"Unexpected response format: {response_content}")
            return None
            
    except Exception as e:
        print(f"Error during API call: {e}")
        return None

# Save formatted data to JSON
def save_formatted_data(formatted_data, timestamp, output_folder='output'):
    os.makedirs(output_folder, exist_ok=True)
    formatted_data_dict = formatted_data.dict() if formatted_data else {}
    json_output_path = os.path.join(output_folder, f'sorted_data_{timestamp}.json')
    
    with open(json_output_path, 'w', encoding='utf-8') as f:
        json.dump(formatted_data_dict, f, indent=4)
    print(f"Formatted data saved to JSON at {json_output_path}")
    if formatted_data:
        print("Formatted data:", json.dumps(formatted_data_dict, indent=4))

# Calculate price based on input and output tokens
def calculate_price(input_text: str, output_text: str, model: str = "gpt-4o-mini") -> float:
    encoder = tiktoken.encoding_for_model(model)
    
    input_token_count = len(encoder.encode(input_text))
    output_token_count = len(encoder.encode(output_text))
    
    input_cost = input_token_count * pricing[model]["input"]
    output_cost = output_token_count * pricing[model]["output"]
    total_cost = input_cost + output_cost
    
    return input_token_count, output_token_count, total_cost

# Main function to execute the scraper
if __name__ == "__main__":
    # url = 'https://aijobs.ai/job/senior-software-engineer-semantic-scholar'  # Example URL
    # url = 'https://aijobs.ai/job/machine-learning-engineer-voice-cloning-and-speech-synthesis'  # Example URL
    # url = 'https://aijobs.ai/job/software-engineer-aiadas'
    # url = 'https://aijobs.ai/job/software-engineer-applied-engineering'
    # url = 'https://aijobs.ai/job/senior-software-engineer-ai-platform-6'
    url = 'https://aijobs.ai/job/lead-software-engineer-prog-data-scientist'
    
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        raw_html = fetch_html_selenium(url)
        cleaned_html = clean_html(raw_html)  # Cleaned HTML, no markdown conversion
        # print(cleaned_html)
        
        raw_file_path = save_raw_data(cleaned_html, timestamp)
        
        formatted_data = format_data(cleaned_html)  # Pass cleaned HTML directly to the LLM
        save_formatted_data(formatted_data, timestamp)
        
        if formatted_data:  # Only calculate price if formatted_data is not None
            formatted_data_text = json.dumps(formatted_data.dict()) 
            
            input_tokens, output_tokens, total_cost = calculate_price(cleaned_html, formatted_data_text, model=model_used)
            print(f"Input token count: {input_tokens}")
            print(f"Output token count: {output_tokens}")
            print(f"Estimated total cost: ${total_cost:.4f}")
        else:
            print("No formatted data to calculate cost.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
