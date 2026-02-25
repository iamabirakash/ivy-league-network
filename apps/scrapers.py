import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import logging
from typing import Dict, List, Optional
import hashlib
from django.utils import timezone
from apps.opportunities.models import University, Opportunity
import re

logger = logging.getLogger(__name__)


class BaseScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def get_soup(self, url):
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def parse_date(self, date_string):
        """Parse various date formats"""
        if not date_string:
            return None
        
        date_string = date_string.strip()
        
        # Common date formats
        formats = [
            '%B %d, %Y',  # January 1, 2024
            '%b %d, %Y',   # Jan 1, 2024
            '%Y-%m-%d',    # 2024-01-01
            '%m/%d/%Y',    # 01/01/2024
            '%d/%m/%Y',    # 01/01/2024
            '%B %d %Y',    # January 1 2024
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_string}")
        return None

    def determine_type(self, title, description):
        """Determine opportunity type from title/description."""
        text = f"{title} {description}".lower()
        if any(word in text for word in ['intern', 'internship']):
            return 'internship'
        if any(word in text for word in ['research', 'lab', 'scientist']):
            return 'research'
        if any(word in text for word in ['scholarship', 'financial aid']):
            return 'scholarship'
        if any(word in text for word in ['hackathon', 'hack']):
            return 'hackathon'
        if any(word in text for word in ['workshop', 'training']):
            return 'workshop'
        if any(word in text for word in ['conference', 'symposium']):
            return 'conference'
        if any(word in text for word in ['fellowship']):
            return 'fellowship'
        if any(word in text for word in ['course', 'class']):
            return 'course'
        if any(word in text for word in ['job', 'career', 'position']):
            return 'job'
        return 'workshop'

    def parse_generic_page(self, soup, source_url, base_domain):
        opportunities = []
        selectors = [
            ('div', 'opportunity-item'),
            ('article', 'post'),
            ('div', 'job-listing'),
            ('li', 'opportunity'),
            ('div', 'views-row'),
            ('article', None),
        ]

        seen = set()
        for tag, class_name in selectors:
            items = soup.find_all(tag, class_=class_name) if class_name else soup.find_all(tag)
            for item in items:
                try:
                    title_elem = item.find(['h1', 'h2', 'h3', 'h4', 'a'])
                    if not title_elem:
                        continue
                    title = title_elem.get_text(strip=True)
                    if len(title) < 8 or title.lower() in seen:
                        continue
                    seen.add(title.lower())

                    link_elem = item.find('a', href=True)
                    url = link_elem['href'] if link_elem else source_url
                    if url.startswith('/'):
                        url = f"https://{base_domain}{url}"

                    desc_elem = item.find(['p', 'div'], class_=['description', 'content', 'summary', 'field-content'])
                    description = desc_elem.get_text(strip=True) if desc_elem else item.get_text(" ", strip=True)[:400]
                    deadline = timezone.now() + timezone.timedelta(days=30)

                    opportunities.append({
                        'title': title,
                        'description': description,
                        'deadline': deadline,
                        'url': url,
                        'source_url': source_url,
                        'opportunity_type': self.determine_type(title, description),
                    })
                except Exception as exc:
                    logger.error("Generic parsing failed: %s", exc)
                    continue
        return opportunities


class HarvardScraper(BaseScraper):
    def scrape(self):
        """Scrape Harvard opportunities"""
        opportunities = []
        urls = [
            'https://harvard.edu/opportunities/',
            'https://seas.harvard.edu/students/opportunities',
            'https://college.harvard.edu/academics/research-opportunities',
            'https://hr.harvard.edu/jobs',
        ]
        
        for url in urls:
            try:
                soup = self.get_soup(url)
                if soup:
                    opps = self.parse_harvard_page(soup, url)
                    opportunities.extend(opps)
                time.sleep(1)  # Be respectful
            except Exception as e:
                logger.error(f"Error scraping Harvard URL {url}: {str(e)}")
                continue
                
        return opportunities
    
    def parse_harvard_page(self, soup, source_url):
        opportunities = []
        
        # Try different selectors based on page structure
        selectors = [
            ('div', 'opportunity-item'),
            ('article', 'post'),
            ('div', 'job-listing'),
            ('li', 'opportunity'),
        ]
        
        for tag, class_name in selectors:
            items = soup.find_all(tag, class_=class_name)
            for item in items:
                try:
                    title_elem = item.find(['h2', 'h3', 'h4', 'a'])
                    title = title_elem.text.strip() if title_elem else "No Title"
                    
                    # Find link
                    link_elem = item.find('a', href=True)
                    url = link_elem['href'] if link_elem else source_url
                    if url.startswith('/'):
                        url = f"https://harvard.edu{url}"
                    
                    # Find description
                    desc_elem = item.find(['p', 'div'], class_=['description', 'content', 'summary'])
                    description = desc_elem.text.strip() if desc_elem else ""
                    
                    # Find deadline
                    deadline_elem = item.find(text=re.compile(r'deadline|due|closes', re.I))
                    deadline = None
                    if deadline_elem:
                        deadline_text = deadline_elem.parent.text if deadline_elem.parent else deadline_elem
                        deadline = self.parse_date(deadline_text)
                    
                    opp = {
                        'title': title,
                        'description': description,
                        'deadline': deadline or timezone.now() + timezone.timedelta(days=30),  # Default 30 days
                        'url': url,
                        'source_url': source_url,
                        'opportunity_type': self.determine_type(title, description),
                    }
                    opportunities.append(opp)
                except Exception as e:
                    logger.error(f"Error parsing Harvard opportunity: {str(e)}")
                    continue
        
        return opportunities
    

class YaleScraper(BaseScraper):
    def scrape(self):
        """Scrape Yale opportunities"""
        opportunities = []
        urls = [
            'https://yale.edu/opportunities/',
            'https://seas.yale.edu/students/opportunities',
        ]
        
        for url in urls:
            try:
                soup = self.get_soup(url)
                if soup:
                    opps = self.parse_yale_page(soup, url)
                    opportunities.extend(opps)
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error scraping Yale URL {url}: {str(e)}")
                continue
        
        return opportunities
    
    def parse_yale_page(self, soup, source_url):
        return self.parse_generic_page(soup, source_url, "yale.edu")


class PrincetonScraper(BaseScraper):
    def scrape(self):
        """Scrape Princeton opportunities"""
        opportunities = []
        urls = [
            'https://princeton.edu/opportunities/',
            'https://gradschool.princeton.edu/opportunities',
        ]
        
        for url in urls:
            try:
                soup = self.get_soup(url)
                if soup:
                    opps = self.parse_princeton_page(soup, url)
                    opportunities.extend(opps)
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error scraping Princeton URL {url}: {str(e)}")
                continue
        
        return opportunities
    
    def parse_princeton_page(self, soup, source_url):
        return self.parse_generic_page(soup, source_url, "princeton.edu")


class ColumbiaScraper(BaseScraper):
    def scrape(self):
        """Scrape Columbia opportunities"""
        opportunities = []
        urls = [
            'https://columbia.edu/opportunities/',
            'https://engineering.columbia.edu/students/opportunities',
        ]
        
        for url in urls:
            try:
                soup = self.get_soup(url)
                if soup:
                    opps = self.parse_columbia_page(soup, url)
                    opportunities.extend(opps)
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error scraping Columbia URL {url}: {str(e)}")
                continue
        
        return opportunities
    
    def parse_columbia_page(self, soup, source_url):
        return self.parse_generic_page(soup, source_url, "columbia.edu")


class CornellScraper(BaseScraper):
    def scrape(self):
        """Scrape Cornell opportunities"""
        opportunities = []
        urls = [
            'https://cornell.edu/opportunities/',
            'https://engineering.cornell.edu/students/opportunities',
        ]
        
        for url in urls:
            try:
                soup = self.get_soup(url)
                if soup:
                    opps = self.parse_cornell_page(soup, url)
                    opportunities.extend(opps)
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error scraping Cornell URL {url}: {str(e)}")
                continue
        
        return opportunities
    
    def parse_cornell_page(self, soup, source_url):
        return self.parse_generic_page(soup, source_url, "cornell.edu")


class DartmouthScraper(BaseScraper):
    def scrape(self):
        """Scrape Dartmouth opportunities"""
        opportunities = []
        urls = [
            'https://dartmouth.edu/opportunities/',
            'https://engineering.dartmouth.edu/students/opportunities',
        ]
        
        for url in urls:
            try:
                soup = self.get_soup(url)
                if soup:
                    opps = self.parse_dartmouth_page(soup, url)
                    opportunities.extend(opps)
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error scraping Dartmouth URL {url}: {str(e)}")
                continue
        
        return opportunities
    
    def parse_dartmouth_page(self, soup, source_url):
        return self.parse_generic_page(soup, source_url, "dartmouth.edu")


class BrownScraper(BaseScraper):
    def scrape(self):
        """Scrape Brown opportunities"""
        opportunities = []
        urls = [
            'https://brown.edu/opportunities/',
            'https://engineering.brown.edu/students/opportunities',
        ]
        
        for url in urls:
            try:
                soup = self.get_soup(url)
                if soup:
                    opps = self.parse_brown_page(soup, url)
                    opportunities.extend(opps)
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error scraping Brown URL {url}: {str(e)}")
                continue
        
        return opportunities
    
    def parse_brown_page(self, soup, source_url):
        return self.parse_generic_page(soup, source_url, "brown.edu")


class PennScraper(BaseScraper):
    def scrape(self):
        """Scrape UPenn opportunities"""
        opportunities = []
        urls = [
            'https://upenn.edu/opportunities/',
            'https://seas.upenn.edu/students/opportunities',
        ]
        
        for url in urls:
            try:
                soup = self.get_soup(url)
                if soup:
                    opps = self.parse_penn_page(soup, url)
                    opportunities.extend(opps)
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error scraping Penn URL {url}: {str(e)}")
                continue
        
        return opportunities
    
    def parse_penn_page(self, soup, source_url):
        return self.parse_generic_page(soup, source_url, "upenn.edu")


class DynamicContentScraper(BaseScraper):
    """For websites with JavaScript-rendered content"""
    
    def __init__(self):
        super().__init__()
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
        except Exception as e:
            logger.error(f"Error initializing Chrome driver: {str(e)}")
            self.driver = None
        
    def scrape_dynamic(self, url, wait_for_element=None, scroll=False):
        if not self.driver:
            logger.error("Chrome driver not initialized")
            return None
            
        try:
            self.driver.get(url)
            
            if wait_for_element:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element))
                )
            
            if scroll:
                # Scroll to load dynamic content
                last_height = self.driver.execute_script("return document.body.scrollHeight")
                while True:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
            
            time.sleep(2)  # Allow for dynamic content to load
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            return soup
        except Exception as e:
            logger.error(f"Error in dynamic scraping of {url}: {str(e)}")
            return None
    
    def __del__(self):
        if hasattr(self, 'driver') and self.driver:
            self.driver.quit()


class ScraperManager:
    def __init__(self):
        self.scrapers = {
            'harvard': HarvardScraper(),
            'yale': YaleScraper(),
            'princeton': PrincetonScraper(),
            'columbia': ColumbiaScraper(),
            'cornell': CornellScraper(),
            'dartmouth': DartmouthScraper(),
            'brown': BrownScraper(),
            'upenn': PennScraper(),
        }
        self.dynamic_scraper = DynamicContentScraper()
        
    def scrape_all(self):
        """Scrape all Ivy League universities"""
        all_opportunities = []
        
        for university_code, scraper in self.scrapers.items():
            try:
                university = University.objects.get(code=university_code)
                logger.info(f"Scraping {university.name}...")
                
                opportunities = scraper.scrape()
                
                for opp_data in opportunities:
                    try:
                        # Create or update opportunity
                        hash_string = f"{opp_data['title']}{university.id}"
                        source_hash = hashlib.sha256(hash_string.encode()).hexdigest()
                        
                        opportunity, created = Opportunity.objects.update_or_create(
                            source_hash=source_hash,
                            defaults={
                                'title': opp_data['title'],
                                'description': opp_data['description'],
                                'deadline': opp_data.get('deadline', timezone.now() + timezone.timedelta(days=30)),
                                'external_url': opp_data.get('url', ''),
                                'opportunity_type': opp_data.get('opportunity_type', 'workshop'),
                                'university': university,
                                'source_url': opp_data.get('source_url', ''),
                            }
                        )
                        
                        if created:
                            all_opportunities.append(opportunity)
                            logger.info(f"New opportunity: {opportunity.title}")
                            
                    except Exception as e:
                        logger.error(f"Error saving opportunity: {str(e)}")
                        continue
                
                # Update last scraped time
                university.last_scraped = timezone.now()
                university.save()
                
            except University.DoesNotExist:
                logger.error(f"University with code {university_code} not found in database")
                continue
            except Exception as e:
                logger.error(f"Error scraping {university_code}: {str(e)}")
                continue
                
        return all_opportunities
