import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils import clean_text, truncate_text
import time
import re
from urllib.parse import urljoin, urlparse

class WebCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def extract_seo_elements(self, soup, url):
        """Extract comprehensive SEO elements"""
        seo_data = {
            'title': soup.title.string.strip() if soup.title else '',
            'meta_description': '',
            'meta_keywords': '',
            'canonical_url': '',
            'robots_meta': '',
            'og_tags': {},
            'twitter_cards': {},
            'schema_markup': False,
            'alt_texts': [],
            'internal_links': 0,
            'external_links': 0
        }
        
        # Meta tags
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            seo_data['meta_description'] = meta_desc.get('content', '')
            
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            seo_data['meta_keywords'] = meta_keywords.get('content', '')
            
        # Canonical URL
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        if canonical:
            seo_data['canonical_url'] = canonical.get('href', '')
            
        # Robots meta
        robots = soup.find('meta', attrs={'name': 'robots'})
        if robots:
            seo_data['robots_meta'] = robots.get('content', '')
            
        # Open Graph tags
        og_tags = soup.find_all('meta', attrs={'property': re.compile(r'^og:')})
        for tag in og_tags:
            property_name = tag.get('property', '').replace('og:', '')
            seo_data['og_tags'][property_name] = tag.get('content', '')
            
        # Twitter Cards
        twitter_tags = soup.find_all('meta', attrs={'name': re.compile(r'^twitter:')})
        for tag in twitter_tags:
            name = tag.get('name', '').replace('twitter:', '')
            seo_data['twitter_cards'][name] = tag.get('content', '')
            
        # Schema markup detection
        schema_scripts = soup.find_all('script', attrs={'type': 'application/ld+json'})
        seo_data['schema_markup'] = len(schema_scripts) > 0
        
        # Alt texts for images
        images = soup.find_all('img')
        seo_data['alt_texts'] = [img.get('alt', '') for img in images]
        
        # Link analysis
        domain = urlparse(url).netloc
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            if href.startswith('http'):
                link_domain = urlparse(href).netloc
                if link_domain == domain:
                    seo_data['internal_links'] += 1
                else:
                    seo_data['external_links'] += 1
        
        return seo_data
    
    def extract_performance_indicators(self, soup, response=None):
        """Extract performance-related indicators"""
        perf_data = {
            'page_size_bytes': 0,
            'total_requests': 1,  # At least the main page
            'css_files': 0,
            'js_files': 0,
            'image_files': 0,
            'external_resources': 0,
            'inline_styles': 0,
            'inline_scripts': 0
        }
        
        if response:
            perf_data['page_size_bytes'] = len(response.content)
            
        # CSS files
        css_links = soup.find_all('link', attrs={'rel': 'stylesheet'})
        perf_data['css_files'] = len(css_links)
        
        # JavaScript files
        js_scripts = soup.find_all('script', src=True)
        perf_data['js_files'] = len(js_scripts)
        
        # Images
        images = soup.find_all('img', src=True)
        perf_data['image_files'] = len(images)
        
        # Inline styles and scripts
        inline_styles = soup.find_all('style')
        perf_data['inline_styles'] = len(inline_styles)
        
        inline_scripts = soup.find_all('script', src=False)
        perf_data['inline_scripts'] = len(inline_scripts)
        
        # Count external resources
        all_resources = css_links + js_scripts + images
        for resource in all_resources:
            src = resource.get('href') or resource.get('src', '')
            if src and src.startswith('http'):
                perf_data['external_resources'] += 1
                
        perf_data['total_requests'] = perf_data['css_files'] + perf_data['js_files'] + perf_data['image_files'] + 1
        
        return perf_data
    
    def extract_ux_elements(self, soup):
        """Extract UX-related elements"""
        ux_data = {
            'has_search': False,
            'has_breadcrumbs': False,
            'nav_elements': 0,
            'cta_buttons': 0,
            'form_elements': 0,
            'video_elements': 0,
            'social_links': 0,
            'contact_info': False,
            'mobile_meta': False
        }
        
        # Search functionality
        search_inputs = soup.find_all('input', attrs={'type': 'search'}) + \
                       soup.find_all('input', attrs={'name': re.compile(r'search', re.I)})
        ux_data['has_search'] = len(search_inputs) > 0
        
        # Breadcrumbs (common patterns)
        breadcrumb_indicators = soup.find_all(attrs={'class': re.compile(r'breadcrumb', re.I)}) + \
                               soup.find_all(attrs={'id': re.compile(r'breadcrumb', re.I)})
        ux_data['has_breadcrumbs'] = len(breadcrumb_indicators) > 0
        
        # Navigation elements
        nav_elements = soup.find_all('nav') + soup.find_all(attrs={'role': 'navigation'})
        ux_data['nav_elements'] = len(nav_elements)
        
        # CTA buttons (common patterns)
        cta_patterns = ['btn', 'button', 'cta', 'call-to-action', 'subscribe', 'buy', 'purchase']
        cta_elements = []
        for pattern in cta_patterns:
            cta_elements.extend(soup.find_all(attrs={'class': re.compile(pattern, re.I)}))
        ux_data['cta_buttons'] = len(set(cta_elements))  # Remove duplicates
        
        # Forms
        forms = soup.find_all('form')
        ux_data['form_elements'] = len(forms)
        
        # Video elements
        videos = soup.find_all(['video', 'iframe'])
        ux_data['video_elements'] = len(videos)
        
        # Social media links
        social_patterns = ['facebook', 'twitter', 'instagram', 'linkedin', 'youtube', 'tiktok']
        social_links = []
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href'].lower()
            if any(social in href for social in social_patterns):
                social_links.append(link)
        ux_data['social_links'] = len(social_links)
        
        # Contact information
        contact_patterns = ['contact', 'email', 'phone', 'tel:', 'mailto:']
        contact_elements = []
        for pattern in contact_patterns:
            contact_elements.extend(soup.find_all(string=re.compile(pattern, re.I)))
            contact_elements.extend(soup.find_all('a', href=re.compile(pattern, re.I)))
        ux_data['contact_info'] = len(contact_elements) > 0
        
        # Mobile viewport meta
        viewport_meta = soup.find('meta', attrs={'name': 'viewport'})
        ux_data['mobile_meta'] = viewport_meta is not None
        
        return ux_data
    
    def crawl_static(self, url):
        """Enhanced static crawling with comprehensive data extraction"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements for clean text
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Basic data structure
            data = {
                'title': soup.title.string.strip() if soup.title else '',
                'meta_description': '',
                'headings': {},
                'text_content': '',
                'links': [],
                'images': [],
                'forms': []
            }
            
            # Extract comprehensive data
            seo_data = self.extract_seo_elements(soup, url)
            perf_data = self.extract_performance_indicators(soup, response)
            ux_data = self.extract_ux_elements(soup)
            
            # Merge all data
            data.update({
                'seo_elements': seo_data,
                'performance_indicators': perf_data,
                'ux_elements': ux_data
            })
            
            # Original extractions (enhanced)
            # Meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                data['meta_description'] = meta_desc.get('content', '')
            
            # Headings with better structure
            for i in range(1, 7):
                headings = soup.find_all(f'h{i}')
                data['headings'][f'h{i}'] = [clean_text(h.get_text()) for h in headings]
            
            # Text content
            data['text_content'] = clean_text(soup.get_text())
            
            # Links with more details
            links = soup.find_all('a', href=True)
            data['links'] = [
                {
                    'text': clean_text(link.get_text()), 
                    'href': link['href'],
                    'title': link.get('title', ''),
                    'is_external': link['href'].startswith('http') and urlparse(url).netloc not in link['href']
                } 
                for link in links[:30]  # Increased limit
            ]
            
            # Images with more details
            images = soup.find_all('img', src=True)
            data['images'] = [
                {
                    'alt': img.get('alt', ''), 
                    'src': img['src'],
                    'title': img.get('title', ''),
                    'loading': img.get('loading', ''),
                    'width': img.get('width', ''),
                    'height': img.get('height', '')
                } 
                for img in images[:15]  # Increased limit
            ]
            
            # Forms with more details
            forms = soup.find_all('form')
            data['forms'] = [
                {
                    'action': form.get('action', ''), 
                    'method': form.get('method', 'get'),
                    'input_count': len(form.find_all('input')),
                    'has_validation': 'required' in str(form)
                } 
                for form in forms
            ]
            
            return data
            
        except Exception as e:
            raise Exception(f"Error crawling {url}: {str(e)}")
    
    def crawl_dynamic(self, url):
        """Enhanced dynamic crawling (fallback)"""
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
            
            # Extract comprehensive data (similar to static method)
            data = {
                'title': driver.title,
                'text_content': clean_text(soup.get_text()),
                'dynamic': True,
                'seo_elements': self.extract_seo_elements(soup, url),
                'ux_elements': self.extract_ux_elements(soup)
            }
            
            return data
            
        except Exception as e:
            raise Exception(f"Error crawling dynamic content: {str(e)}")
        finally:
            if driver:
                driver.quit()
    
    def crawl_website(self, url):
        """Enhanced main crawling method"""
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