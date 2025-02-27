#!/usr/bin/env python
# coding: utf-8

#reportlab-4.3.1
#fake_useragent-2.0.3



import requests
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from fake_useragent import UserAgent
import time
import random


# In[2]:


# Define loan aggregator websites to scrape
LOAN_AGGREGATORS = [
    "https://www.bankbazaar.com/personal-loan.html",
    "https://www.paisabazaar.com/personal-loan/",
    "https://www.moneycontrol.com/personal-loan"
]

# Function to fetch and parse webpage content
def fetch_page_content(url):
    try:
        user_agent = UserAgent().random  # Random user-agent to avoid detection
        headers = {"User-Agent": user_agent}
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an error for HTTP issues
        
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

# Function to extract personal loan details
def extract_loan_info(soup):
    loan_info = []

    if soup:
        sections = soup.find_all(["h2", "h3", "p", "li"])  # Extract headings & paragraphs
        for section in sections:
            text = section.get_text(strip=True)
            if any(keyword in text.lower() for keyword in ["personal loan", "interest rate", "eligibility", "tenure", "loan amount"]):
                loan_info.append(text)

    return loan_info

# Function to save extracted text in a PDF
def save_to_pdf(loan_data, filename="data/personal_loan_info2.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    c.setFont("Helvetica", 12)
    y_position = 750  # Start position

    c.drawString(50, y_position, "Personal Loan Information from Aggregators")
    y_position -= 20  # Move down

    for url, info in loan_data.items():
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y_position, f"Source: {url}")
        y_position -= 15

        c.setFont("Helvetica", 10)
        for line in info:
            if y_position < 50:  # Move to new page if space runs out
                c.showPage()
                c.setFont("Helvetica", 10)
                y_position = 750

            c.drawString(50, y_position, line[:100])  # Limiting text width
            y_position -= 12

        y_position -= 10  # Extra spacing between sources

    c.save()
    print(f"✅ Data saved to {filename}")

# Main execution function
def scrape_personal_loan_info():
    loan_data = {}

    for url in LOAN_AGGREGATORS:
        print(f"Scraping: {url}")
        soup = fetch_page_content(url)
        time.sleep(random.uniform(2, 5))  # Random delay to avoid blocking

        if soup:
            extracted_info = extract_loan_info(soup)
            if extracted_info:
                loan_data[url] = extracted_info
            else:
                print(f"No relevant data found on {url}")

    if loan_data:
        save_to_pdf(loan_data)
    else:
        print("❌ No data extracted from any source.")

# Run the script
if __name__ == "__main__":
    scrape_personal_loan_info()


# In[ ]:




