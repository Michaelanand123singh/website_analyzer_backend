import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import clean_text, truncate_text
import time

class WebCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def crawl_static(self, url):
        """Crawl static content using requests + BeautifulSoup"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            data = {
                'title': soup.title.string if soup.title else '',
                'meta_description': '',
                'headings': {},
                'text_content': '',
                'links': [],
                'images': [],
                'forms': []
            }
            
            # Meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                data['meta_description'] = meta_desc.get('content', '')
            
            # Headings
            for i in range(1, 7):
                headings = soup.find_all(f'h{i}')
                data['headings'][f'h{i}'] = [clean_text(h.get_text()) for h in headings]
            
            # Text content
            data['text_content'] = clean_text(soup.get_text())
            
            # Links
            links = soup.find_all('a', href=True)
            data['links'] = [{'text': clean_text(link.get_text()), 'href': link['href']} 
                           for link in links[:20]]  # Limit to 20 links
            
            # Images
            images = soup.find_all('img', src=True)
            data['images'] = [{'alt': img.get('alt', ''), 'src': img['src']} 
                            for img in images[:10]]  # Limit to 10 images
            
            # Forms
            forms = soup.find_all('form')
            data['forms'] = [{'action': form.get('action', ''), 'method': form.get('method', 'get')} 
                           for form in forms]
            
            return data
            
        except Exception as e:
            raise Exception(f"Error crawling {url}: {str(e)}")
    
    def crawl_dynamic(self, url):
        """Crawl dynamic content using Selenium (fallback)"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = None
        try:
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Similar extraction as static method
            data = {
                'title': driver.title,
                'text_content': clean_text(soup.get_text()),
                'dynamic': True
            }
            
            return data
            
        except Exception as e:
            raise Exception(f"Error crawling dynamic content: {str(e)}")
        finally:
            if driver:
                driver.quit()
    
    def crawl_website(self, url):
        """Main crawling method"""
        try:
            # Try static crawling first
            return self.crawl_static(url)
        except Exception as e:
            # Fallback to dynamic crawling
            print(f"Static crawling failed: {e}")
            try:
                return self.crawl_dynamic(url)
            except Exception as e2:
                raise Exception(f"Both crawling methods failed: {e2}")