import streamlit as st
from streamlit_tags import st_tags_sidebar
import pandas as pd
import json
from datetime import datetime

# Importing functions from scraper.py
from scraper import fetch_html_selenium, save_raw_data, format_data, save_formatted_data, calculate_price, clean_html

# Initialize Streamlit app
st.set_page_config(page_title="Universal Web Scraper")
st.title("Universal Web Scraper 🦑")

# Sidebar components
st.sidebar.title("Web Scraper Settings")
model_selection = st.sidebar.selectbox(
    "Select Model",
    options=["babbage-002", "gpt-4o-mini", "gpt-4o-mini-2024-07-18", "gpt-3.5-turbo-0125", "gpt-3.5-turbo-1106"],
    index=0
)

# Accept multiple URLs
url_input = st.sidebar.text_area("Enter URLs (separated by newlines)")

st.sidebar.markdown("---")

# Initialize variables to store token and cost information
input_tokens = output_tokens = total_cost = 0  # Default values

# Function to perform scraping for each URL
def perform_scrape(url):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Fetch raw HTML
    raw_html = fetch_html_selenium(url)

    # Clean HTML (removes headers, footers, classes, etc.)
    cleaned_html = clean_html(raw_html)
    raw_html_file_path = save_raw_data(cleaned_html, timestamp)

    # Extract and format data
    formatted_data = format_data(cleaned_html)

    # Prepare structured job posting JSON data
    if formatted_data:
        job_data = json.dumps(formatted_data.dict())

        # Calculate token usage and cost
        input_tokens, output_tokens, total_cost = calculate_price(cleaned_html, json.dumps(job_data, indent=4), model=model_selection)
        
        return job_data, input_tokens, output_tokens, total_cost, raw_html_file_path
    else:
        return None, 0, 0, 0, raw_html_file_path

# Button to trigger scraping
if st.sidebar.button("Scrape URLs"):
    with st.spinner('Please wait... Data is being scraped.'):

        urls = url_input.splitlines()
        results = []

        for url in urls:
            try:
                st.write(f"Scraping URL: {url}")
                job_data, input_tokens, output_tokens, total_cost, raw_html_file_path = perform_scrape(url)
                
                if job_data:
                    results.append((job_data, input_tokens, output_tokens, total_cost, raw_html_file_path))
                else:
                    st.write(f"Failed to extract data from {url}")
            except Exception as e:
                st.write(f"Error scraping {url}: {e}")
        
        # Store results in session state
        st.session_state['results'] = results
        st.session_state['perform_scrape'] = True

# Display the results
if st.session_state.get('perform_scrape'):
    for idx, (job_data, input_tokens, output_tokens, total_cost, raw_html_file_path) in enumerate(st.session_state['results']):
        st.write(f"## Scraped Data for URL {idx + 1}")
        
        # Display raw HTML file path
        # st.write(f"Raw HTML data saved to: **{raw_html_file_path}**")
        
        # Display formatted job data
        st.write("### Formatted Data:")
        st.json(job_data)

        # Display token usage and cost
        st.sidebar.markdown(f"## Token Usage for URL {idx + 1}")
        st.sidebar.markdown(f"**Input Tokens:** {input_tokens}")
        st.sidebar.markdown(f"**Output Tokens:** {output_tokens}")
        st.sidebar.markdown(f"**Total Cost:** :green-background[***${total_cost:.4f}***]")
        
        # Download buttons for each URL
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                f"Download JSON for URL {idx + 1}",
                data=json.dumps(job_data, indent=4),
                file_name=f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_job_data.json"
            )
        with col2:
            df = pd.DataFrame([job_data])  # Wrap job_data in a list to create a DataFrame
            st.download_button(
                f"Download CSV for URL {idx + 1}",
                data=df.to_csv(index=False),
                file_name=f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_job_data.csv"
            )
        # with col3:
        #     st.download_button(
        #     f"Download Markdown for URL {idx + 1}",
        #     data=cleaned_html,  # Use cleaned_html which contains the raw HTML content
        #     file_name=f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_job_data.md"
        # )
