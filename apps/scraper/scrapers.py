import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin, urlparse
from email.utils import parsedate_to_datetime
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
from django.conf import settings
from apps.opportunities.models import University, Opportunity
from .models import Source
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
        date_string = re.sub(r"\s+", " ", date_string)
        date_string = re.sub(r"(?i)\b(deadline|due|closes|closing date|apply by)\b[:\s-]*", "", date_string).strip()
        
        # Common date formats
        formats = [
            '%B %d, %Y',  # January 1, 2024
            '%b %d, %Y',   # Jan 1, 2024
            '%Y-%m-%d',    # 2024-01-01
            '%m/%d/%Y',    # 01/01/2024
            '%d/%m/%Y',    # 01/01/2024
            '%B %d %Y',    # January 1 2024
            '%d %B %Y',    # 1 January 2024
            '%d %b %Y',    # 1 Jan 2024
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_string, fmt)
                if timezone.is_naive(dt):
                    dt = timezone.make_aware(dt, timezone.get_current_timezone())
                return dt
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

    def extract_deadline_from_text(self, text):
        if not text:
            return None
        blob = re.sub(r"\s+", " ", text)
        lower = blob.lower()
        if any(term in lower for term in ["rolling", "open until filled", "no deadline"]):
            return None

        patterns = [
            r'(?i)(?:deadline|due|closes|closing date|apply by)[:\s-]*([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})',
            r'(?i)(?:deadline|due|closes|closing date|apply by)[:\s-]*(\d{1,2}/\d{1,2}/\d{4})',
            r'(?i)(?:deadline|due|closes|closing date|apply by)[:\s-]*(\d{4}-\d{2}-\d{2})',
            r'(?i)\b([A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})\b',
            r'(?i)\b(\d{1,2}/\d{1,2}/\d{4})\b',
            r'(?i)\b(\d{4}-\d{2}-\d{2})\b',
        ]
        for pattern in patterns:
            match = re.search(pattern, blob)
            if not match:
                continue
            dt = self.parse_date(match.group(1))
            if dt:
                return dt
        return None

    def extract_best_description(self, soup):
        selectors = ["article", "main", ".content", ".entry-content", ".post-content", ".job-description", ".description"]
        for selector in selectors:
            block = soup.select_one(selector)
            if block:
                text = block.get_text(" ", strip=True)
                if len(text) > 120:
                    return text[:2000]

        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        paragraphs = [p for p in paragraphs if len(p) > 40]
        if paragraphs:
            return " ".join(paragraphs[:6])[:2000]
        return ""

    def fetch_detail_and_enrich(self, url, fallback_title, fallback_description):
        soup = self.get_soup(url)
        if not soup:
            return fallback_title, fallback_description, None

        title_elem = soup.find(["h1", "h2"])
        title = title_elem.get_text(" ", strip=True)[:500] if title_elem else fallback_title
        description = self.extract_best_description(soup) or fallback_description

        text_blob = soup.get_text(" ", strip=True)[:12000]
        deadline = self.extract_deadline_from_text(text_blob)

        # Sometimes deadlines are in metadata.
        if not deadline:
            for meta_name in ("article:published_time", "article:modified_time", "date"):
                meta = soup.find("meta", attrs={"property": meta_name}) or soup.find("meta", attrs={"name": meta_name})
                if meta and meta.get("content"):
                    try:
                        dt = parsedate_to_datetime(meta["content"])
                        if timezone.is_naive(dt):
                            dt = timezone.make_aware(dt, timezone.get_current_timezone())
                        deadline = dt
                        break
                    except Exception:
                        continue

        return title, description[:2000], deadline

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
                    url = urljoin(source_url, url)

                    desc_elem = item.find(['p', 'div'], class_=['description', 'content', 'summary', 'field-content'])
                    description = desc_elem.get_text(strip=True) if desc_elem else item.get_text(" ", strip=True)[:400]
                    context_text = item.get_text(" ", strip=True)
                    deadline = self.extract_deadline_from_text(context_text)
                    title, description, detail_deadline = self.fetch_detail_and_enrich(url, title, description)
                    if detail_deadline:
                        deadline = detail_deadline

                    # Avoid fake identical deadlines across all opportunities.
                    if not deadline:
                        continue

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

        # Fallback: mine relevant links when block selectors are not present.
        if not opportunities:
            opportunities = self.extract_from_links(soup, source_url)
        return opportunities

    def extract_from_links(self, soup, source_url):
        opportunities = []
        seen = set()
        keywords = (
            "opportun", "intern", "research", "fellowship", "scholarship", "grant",
            "job", "career", "program", "summer", "lab", "assistant", "postdoc",
            "conference", "workshop", "application", "competition", "challenge",
            "hackathon",
        )
        parsed_source = urlparse(source_url)

        for link in soup.find_all("a", href=True):
            href = (link.get("href") or "").strip()
            text = link.get_text(" ", strip=True)
            if not href or not text or len(text) < 6:
                continue

            absolute_url = urljoin(source_url, href)
            parsed_link = urlparse(absolute_url)
            if parsed_link.scheme not in {"http", "https"}:
                continue
            if parsed_link.netloc and parsed_source.netloc and parsed_source.netloc not in parsed_link.netloc:
                # Keep extraction mostly source-local to reduce noise.
                continue

            blob = f"{text} {absolute_url}".lower()
            if not any(k in blob for k in keywords):
                continue

            key = (text.lower(), absolute_url.lower())
            if key in seen:
                continue
            seen.add(key)

            parent = link.find_parent(["li", "article", "div", "section"])
            context_text = parent.get_text(" ", strip=True) if parent else text
            description = context_text[:400]
            title, description, deadline = self.fetch_detail_and_enrich(absolute_url, text[:500], description)
            if not deadline:
                deadline = self.extract_deadline_from_text(context_text)
            if not deadline:
                continue
            opportunity_type = self.determine_type(text, description)

            opportunities.append({
                "title": title[:500],
                "description": description,
                "deadline": deadline,
                "url": absolute_url,
                "source_url": source_url,
                "opportunity_type": opportunity_type,
            })

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
                    if not deadline:
                        deadline = self.extract_deadline_from_text(item.get_text(" ", strip=True))

                    title, description, detail_deadline = self.fetch_detail_and_enrich(url, title, description)
                    if detail_deadline:
                        deadline = detail_deadline
                    if not deadline:
                        continue
                    
                    opp = {
                        'title': title,
                        'description': description,
                        'deadline': deadline,
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
        self.driver = None

    def _ensure_driver(self):
        if self.driver:
            return True

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
            return True
        except Exception as e:
            logger.error(f"Error initializing Chrome driver: {str(e)}")
            self.driver = None
            return False
        
    def scrape_dynamic(self, url, wait_for_element=None, scroll=False):
        if not self._ensure_driver():
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


class UnstopScraper(BaseScraper):
    def scrape_source(self, listing_url):
        opportunities = []
        soup = self.get_soup(listing_url)
        if not soup:
            return opportunities

        # Unstop often serves card-based listings and nested links.
        opportunities.extend(self.parse_generic_page(soup, listing_url, urlparse(listing_url).netloc))
        return opportunities


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
        self.source_scrapers = {
            "unstop": UnstopScraper(),
        }
        self.dynamic_scraper = DynamicContentScraper()

    def _resolve_source_university(self, source):
        if source.university:
            return source.university
        code = f"src_{source.code}"[:50]
        uni, _ = University.objects.get_or_create(
            code=code,
            defaults={
                "name": f"{source.name} (External)",
                "website": source.base_url,
                "opportunities_url": source.listing_url,
                "is_ivy_league": False,
                "active": True,
            },
        )
        source.university = uni
        source.save(update_fields=["university", "updated_at"])
        return uni

    def _save_opportunity(self, university, opp_data):
        if not opp_data.get("deadline"):
            return None, False

        deadline = opp_data["deadline"]
        if not getattr(settings, "USE_TZ", False) and timezone.is_aware(deadline):
            deadline = timezone.make_naive(deadline, timezone.get_current_timezone())

        external_url = opp_data.get("url", "") or ""
        source_url = opp_data.get("source_url", "") or ""
        hash_string = f"{opp_data['title']}{university.id}{external_url}{source_url}"
        source_hash = hashlib.sha256(hash_string.encode()).hexdigest()

        opportunity, created = Opportunity.objects.update_or_create(
            source_hash=source_hash,
            defaults={
                "title": opp_data["title"],
                "description": opp_data["description"],
                "deadline": deadline,
                "external_url": external_url,
                "opportunity_type": opp_data.get("opportunity_type", "workshop"),
                "university": university,
                "source_url": source_url,
            },
        )
        return opportunity, created

    def scrape_all(self):
        """Scrape all active universities + configured external sources."""
        all_opportunities = []

        for university in University.objects.filter(active=True):
            scraper = self.scrapers.get(university.code, BaseScraper())
            try:
                logger.info(f"Scraping {university.name}...")
                
                opportunities = []

                # Always include the DB-configured opportunities URL first.
                if university.opportunities_url:
                    try:
                        source_url = university.opportunities_url
                        soup = scraper.get_soup(source_url)
                        if soup:
                            base_domain = urlparse(source_url).netloc
                            opportunities.extend(
                                scraper.parse_generic_page(soup, source_url, base_domain)
                            )
                    except Exception as e:
                        logger.error(
                            f"Error scraping configured URL for {university.code}: {str(e)}"
                        )

                # If DB URL is configured, treat it as the source of truth.
                # Hardcoded fallbacks are used only when no DB URL is provided.
                if not university.opportunities_url and hasattr(scraper, "scrape"):
                    opportunities.extend(scraper.scrape())
                
                for opp_data in opportunities:
                    try:
                        opportunity, created = self._save_opportunity(university, opp_data)
                        
                        if opportunity and created:
                            all_opportunities.append(opportunity)
                            logger.info(f"New opportunity: {opportunity.title}")
                            
                    except Exception as e:
                        logger.error(f"Error saving opportunity: {str(e)}")
                        continue
                
                # Update last scraped time
                university.last_scraped = timezone.now()
                university.save()
                
            except Exception as e:
                logger.error(f"Error scraping {university.code}: {str(e)}")
                continue

        for source in Source.objects.filter(active=True):
            try:
                logger.info(f"Scraping source {source.name}...")
                scraper = self.source_scrapers.get(source.code, BaseScraper())
                opportunities = []

                if hasattr(scraper, "scrape_source"):
                    opportunities = scraper.scrape_source(source.listing_url)
                else:
                    soup = scraper.get_soup(source.listing_url)
                    if soup:
                        opportunities = scraper.parse_generic_page(
                            soup, source.listing_url, urlparse(source.listing_url).netloc
                        )

                source_university = self._resolve_source_university(source)
                for opp_data in opportunities:
                    try:
                        opportunity, created = self._save_opportunity(source_university, opp_data)
                        if opportunity and created:
                            all_opportunities.append(opportunity)
                            logger.info(f"New source opportunity: {opportunity.title}")
                    except Exception as e:
                        logger.error(f"Error saving source opportunity: {str(e)}")
                        continue

                source.last_scraped = timezone.now()
                source.save(update_fields=["last_scraped", "updated_at"])
            except Exception as e:
                logger.error(f"Error scraping source {source.code}: {str(e)}")
                continue
                
        return all_opportunities
