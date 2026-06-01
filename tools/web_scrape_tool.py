# c:\Users\mshas\OneDrive\Desktop\SUNDAY\tools\web_scrape_tool.py
"""
Web Scrape Tool for SUNDAY.
Fetches and parses plain text, headings, and links from websites without external dependencies.
"""
import requests
from html.parser import HTMLParser
from tools.base_tool import BaseTool

class CleanTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_blocks = []
        self.extracted_links = []
        self.in_script_or_style = False
        self.page_title = ""
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.in_script_or_style = True
        elif tag == "title":
            self.in_title = True
        elif tag == "a":
            # Extract links safely
            for attr, val in attrs:
                if attr == "href" and val.startswith("http"):
                    self.extracted_links.append(val)

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.in_script_or_style = False
        elif tag == "title":
            self.in_title = False

    def handle_data(self, data):
        cleaned = data.strip()
        if not cleaned:
            return
            
        if self.in_title:
            self.page_title = cleaned
        elif not self.in_script_or_style:
            self.text_blocks.append(cleaned)

    def get_clean_text(self) -> str:
        return "\n".join(self.text_blocks)

    def get_links(self) -> list:
        # De-duplicate links while preserving order
        seen = set()
        unique_links = []
        for link in self.extracted_links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
        return unique_links[:20]  # Cap to top 20 links for context limits


class WebScrapeTool(BaseTool):
    def __init__(self):
        super().__init__("web_scrape", 1, "Directly extracts clean text and links from a website URL")

    def execute(self, parameters: dict, context: dict = None) -> dict:
        url = parameters.get("url", parameters.get("site", ""))
        if not url:
            return {"success": False, "message": "No website URL provided for scraping"}

        if not url.startswith("http"):
            url = f"https://{url}"

        # Standard desktop User-Agent to avoid generic request blocks
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            print(f"[SCRAPER] Fetching and parsing: {url}...")
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "message": f"Website returned error HTTP status: {response.status_code}"
                }

            parser = CleanTextExtractor()
            parser.feed(response.text)
            
            clean_text = parser.get_clean_text()
            title = parser.page_title if parser.page_title else "Web Scrape Result"
            links = parser.get_links()
            
            print(f"[SCRAPER] Scraped success. Title: '{title}' | Text Length: {len(clean_text)}")
            
            return {
                "success": True,
                "title": title,
                "text": clean_text[:12000],  # Capped for context limits
                "links": links,
                "message": f"Scraped site '{title}' successfully (extracted {len(clean_text)} characters)."
            }
            
        except Exception as e:
            print(f"[SCRAPER] [ERROR] Failed to scrape website: {e}")
            return {
                "success": False,
                "message": f"Failed to scrape webpage: {str(e)}"
            }
