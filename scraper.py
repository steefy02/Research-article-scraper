import requests
from bs4 import BeautifulSoup
import time
import random
from typing import List, Dict
import urllib.parse

class CSResearchScraper:
    """Scraper optimized for Computer Science research papers"""
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        self.session = requests.Session()
    
    def _get_headers(self):
        """Get headers for requests"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'application/json',
        }
    
    def _generate_bibtex(self, article: Dict) -> str:
        """Generate BibTeX citation from article data"""
        # Create a citation key
        first_author = article.get('authors', 'Unknown').split(',')[0].split()[-1].lower()
        year = str(article.get('year', 'n.d.')).replace('N/A', 'n.d.')
        title_word = article.get('title', '').split()[0].lower() if article.get('title') else 'untitled'
        cite_key = f"{first_author}{year}{title_word}"
        
        # Clean title
        title = article.get('title', '').replace('{', '').replace('}', '')
        
        bibtex = f"@article{{{cite_key},\n"
        bibtex += f"  title={{{title}}},\n"
        bibtex += f"  author={{{article.get('authors', 'Unknown')}}},\n"
        bibtex += f"  year={{{year}}},\n"
        
        # Add journal/venue if available
        if article.get('journal'):
            bibtex += f"  journal={{{article['journal']}}},\n"
        
        if article.get('doi'):
            bibtex += f"  doi={{{article['doi']}}},\n"
        
        if article.get('url'):
            bibtex += f"  url={{{article['url']}}},\n"
        
        bibtex += f"  note={{Source: {article.get('platform', 'Unknown')}}}\n"
        bibtex += "}"
        
        return bibtex
    
    def scrape_arxiv(self, keywords: str, max_articles: int = 10, category: str = "cs") -> List[Dict]:
        """        
        CS categories:
        - cs: All of Computer Science
        - cs.AI: Artificial Intelligence
        - cs.LG: Machine Learning
        - cs.CV: Computer Vision
        - cs.CL: Computation and Language (NLP)
        - cs.CR: Cryptography and Security
        - cs.DB: Databases
        - cs.SE: Software Engineering
        """
        articles = []
        search_query = urllib.parse.quote(keywords)
        category = "cs.HC"
        
        # Try multiple query strategies for better results
        urls_to_try = []
        
        if category:
            # Strategy 1: Search within category (most restrictive but most relevant)
            urls_to_try.append(
                f"https://export.arxiv.org/api/query?search_query=cat:{category}+AND+all:{search_query}&start=0&max_results={max_articles}&sortBy=submittedDate&sortOrder=descending"
            )
            # Strategy 2: Search in title/abstract within category
            urls_to_try.append(
                f"https://export.arxiv.org/api/query?search_query=cat:{category}+AND+(ti:{search_query}+OR+abs:{search_query})&start=0&max_results={max_articles}&sortBy=submittedDate&sortOrder=descending"
            )
            # Strategy 3: Just category with keywords in any field (more relaxed)
            urls_to_try.append(
                f"https://export.arxiv.org/api/query?search_query=cat:{category.replace(':', '%3A')}*+AND+all:{search_query}&start=0&max_results={max_articles}&sortBy=relevance"
            )
        
        # Strategy 4: Search all fields without category restriction (fallback)
        urls_to_try.append(
            f"https://export.arxiv.org/api/query?search_query=all:{search_query}&start=0&max_results={max_articles}&sortBy=relevance"
        )
        
        # Try each URL until we get results
        for url_idx, url in enumerate(urls_to_try):
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code == 403:
                    print("    Temporarily blocked - try again later")
                    return articles
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'xml')
                entries = soup.find_all('entry')
                
                if entries:
                    # Found results, break out of loop
                    break
                elif url_idx < len(urls_to_try) - 1:
                    # No results with this query, try next strategy
                    continue
            except Exception as e:
                if url_idx == len(urls_to_try) - 1:
                    print(f"    Error: {str(e)[:100]}")
                    return articles
                continue
        
        if not entries:
            return articles
        
        try:
            for entry in entries:
                title_tag = entry.find('title')
                if title_tag:
                    title = title_tag.get_text(strip=True).replace('\n', ' ')
                    
                    # Get authors
                    authors = []
                    for author in entry.find_all('author'):
                        name = author.find('name')
                        if name:
                            authors.append(name.get_text(strip=True))
                    
                    # Get publication date
                    published = entry.find('published')
                    pub_date = published.get_text(strip=True)[:10] if published else "N/A"
                    
                    # Get DOI if available
                    doi_tag = entry.find('arxiv:doi')
                    doi = doi_tag.get_text(strip=True) if doi_tag else None
                    
                    # Get arXiv ID and create URL
                    id_tag = entry.find('id')
                    url = id_tag.get_text(strip=True) if id_tag else None
                    
                    # Get journal reference if available
                    journal_ref = entry.find('arxiv:journal_ref')
                    journal = journal_ref.get_text(strip=True) if journal_ref else None
                    
                    article_data = {
                        'title': title,
                        'authors': ', '.join(authors),
                        'authors_list': authors,
                        'year': pub_date,
                        'doi': doi,
                        'url': url,
                        'journal': journal,
                        'platform': 'arXiv'
                    }
                    
                    article_data['bibtex'] = self._generate_bibtex(article_data)
                    articles.append(article_data)
        except Exception as e:
            print(f"    Error parsing results: {str(e)[:100]}")
        
        return articles
    
    def scrape_semantic_scholar(self, keywords: str, max_articles: int = 10) -> List[Dict]:
        articles = []
        search_query = urllib.parse.quote(keywords)
        # Add venue to the fields we request
        url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={search_query}&limit={max_articles}&fields=title,authors,year,externalIds,url,venue,publicationVenue"
        
        try:
            response = self.session.get(url, headers=self._get_headers(), timeout=15)
            response.raise_for_status()
            data = response.json()
            
            for paper in data.get('data', []):
                title = paper.get('title', '')
                authors = paper.get('authors', [])
                author_names = [a.get('name', '') for a in authors]
                year = paper.get('year', 'N/A')
                
                # Get DOI
                external_ids = paper.get('externalIds', {})
                doi = external_ids.get('DOI')
                
                # Get URL
                paper_url = paper.get('url', '')
                
                # Get venue/journal information
                venue = paper.get('venue', '')
                pub_venue = paper.get('publicationVenue', {})
                if not venue and pub_venue:
                    venue = pub_venue.get('name', '')
                
                if title:
                    article_data = {
                        'title': title,
                        'authors': ', '.join(author_names),
                        'authors_list': author_names,
                        'year': year,
                        'doi': doi,
                        'url': paper_url,
                        'journal': venue if venue else None,
                        'platform': 'Semantic Scholar'
                    }
                    
                    article_data['bibtex'] = self._generate_bibtex(article_data)
                    articles.append(article_data)
        except Exception as e:
            print(f"Error: {str(e)[:100]}")
        
        return articles
    
    def scrape_openalex(self, keywords: str, max_articles: int = 10) -> List[Dict]:
        articles = []
        search_query = urllib.parse.quote(keywords)
        url = f"https://api.openalex.org/works?search={search_query}&per_page={max_articles}"
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            for work in data.get('results', []):
                title = work.get('title', '')
                
                # Get authors
                authorships = work.get('authorships', [])
                authors = []
                for authorship in authorships:
                    author = authorship.get('author', {})
                    name = author.get('display_name', '')
                    if name:
                        authors.append(name)
                
                # Get year
                year = work.get('publication_year', 'N/A')
                
                # Get DOI
                doi = work.get('doi', '').replace('https://doi.org/', '') if work.get('doi') else None
                
                # Get URL
                work_url = work.get('id', '') or work.get('doi', '')
                
                # Get journal/venue information
                venue = None
                primary_location = work.get('primary_location', {})
                if primary_location:
                    source = primary_location.get('source', {})
                    if source:
                        venue = source.get('display_name', '')
                
                # Fallback to host venue if no primary location
                if not venue:
                    host_venue = work.get('host_venue', {})
                    if host_venue:
                        venue = host_venue.get('display_name', '')
                
                if title:
                    article_data = {
                        'title': title,
                        'authors': ', '.join(authors),
                        'authors_list': authors,
                        'year': year,
                        'doi': doi,
                        'url': work_url,
                        'journal': venue if venue else None,
                        'platform': 'OpenAlex'
                    }
                    
                    article_data['bibtex'] = self._generate_bibtex(article_data)
                    articles.append(article_data)
        except Exception as e:
            print(f"Error: {str(e)[:100]}")
        
        return articles
    
    def scrape_crossref(self, keywords: str, max_articles: int = 10) -> List[Dict]:
        articles = []
        search_query = urllib.parse.quote(keywords)
        url = f"https://api.crossref.org/works?query={search_query}&rows={max_articles}"
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            for item in data.get('message', {}).get('items', []):
                # Get title
                titles = item.get('title', [])
                title = titles[0] if titles else ''
                
                # Get authors
                authors_data = item.get('author', [])
                authors = []
                for author in authors_data:
                    given = author.get('given', '')
                    family = author.get('family', '')
                    name = f"{given} {family}".strip()
                    if name:
                        authors.append(name)
                
                # Get year
                date_parts = item.get('created', {}).get('date-parts', [[]])
                year = date_parts[0][0] if date_parts and date_parts[0] else 'N/A'
                
                # Get DOI
                doi = item.get('DOI')
                
                # Get URL
                work_url = item.get('URL', '') or (f"https://doi.org/{doi}" if doi else '')
                
                # Get journal/container information
                container_titles = item.get('container-title', [])
                journal = container_titles[0] if container_titles else None
                
                if title:
                    article_data = {
                        'title': title,
                        'authors': ', '.join(authors),
                        'authors_list': authors,
                        'year': year,
                        'doi': doi,
                        'url': work_url,
                        'journal': journal,
                        'platform': 'CrossRef'
                    }
                    
                    article_data['bibtex'] = self._generate_bibtex(article_data)
                    articles.append(article_data)
        except Exception as e:
            print(f"Error: {str(e)[:100]}")
        
        return articles
    
    def scrape_core(self, keywords: str, max_articles: int = 10) -> List[Dict]:
        articles = []
        search_query = urllib.parse.quote(keywords)
        url = f"https://api.core.ac.uk/v3/search/works?q={search_query}&limit={max_articles}"
        
        try:
            response = self.session.get(url, headers=self._get_headers(), timeout=15)
            response.raise_for_status()
            data = response.json()
            
            for result in data.get('results', []):
                title = result.get('title', '')
                
                # Get authors
                authors_list = result.get('authors', [])
                authors = []
                for author in authors_list:
                    if isinstance(author, dict):
                        name = author.get('name', '')
                    else:
                        name = str(author)
                    if name:
                        authors.append(name)
                
                # Get year
                year = result.get('yearPublished', 'N/A')
                
                # Get DOI
                doi = result.get('doi')
                
                # Get URL
                work_url = result.get('downloadUrl', '') or result.get('sourceFulltextUrls', [''])[0] if result.get('sourceFulltextUrls') else ''
                
                # Get journal/publisher information
                journal = result.get('publisher', '') or result.get('journals', [''])[0] if result.get('journals') else None
                
                if title:
                    article_data = {
                        'title': title,
                        'authors': ', '.join(authors),
                        'authors_list': authors,
                        'year': year,
                        'doi': doi,
                        'url': work_url,
                        'journal': journal if journal else None,
                        'platform': 'CORE'
                    }
                    
                    article_data['bibtex'] = self._generate_bibtex(article_data)
                    articles.append(article_data)
        except Exception as e:
            print(f"Error: {str(e)[:100]}")
        
        return articles
    
    def scrape_dblp(self, keywords: str, max_articles: int = 10) -> List[Dict]:
        articles = []
        search_query = urllib.parse.quote(keywords)
        url = f"https://dblp.org/search/publ/api?q={search_query}&format=json&h={max_articles}"
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            hits = data.get('result', {}).get('hits', {}).get('hit', [])
            
            for hit in hits:
                info = hit.get('info', {})
                
                title = info.get('title', '')
                
                # Get authors
                authors_data = info.get('authors', {}).get('author', [])
                if isinstance(authors_data, str):
                    authors_data = [authors_data]
                elif isinstance(authors_data, dict):
                    authors_data = [authors_data.get('text', '')]
                else:
                    authors_data = [a.get('text', a) if isinstance(a, dict) else str(a) for a in authors_data]
                
                authors = [a for a in authors_data if a]
                
                # Get year
                year = info.get('year', 'N/A')
                
                # Get DOI
                doi = info.get('doi')
                
                # Get URL
                work_url = info.get('ee', '')
                if isinstance(work_url, list):
                    work_url = work_url[0] if work_url else ''
                
                # Get venue information (conference or journal)
                venue = info.get('venue', '')
                
                if title:
                    article_data = {
                        'title': title,
                        'authors': ', '.join(authors),
                        'authors_list': authors,
                        'year': year,
                        'doi': doi,
                        'url': work_url,
                        'journal': venue if venue else None,
                        'platform': 'DBLP'
                    }
                    
                    article_data['bibtex'] = self._generate_bibtex(article_data)
                    articles.append(article_data)
        except Exception as e:
            print(f"Error: {str(e)[:100]}")
        
        return articles
    
    def search_all_platforms(self, keywords: str, max_articles_per_platform: int = 10, 
                           cs_category: str = "cs") -> List[Dict]:
        """
        Search across all CS-focused platforms
        
        Args:
            keywords: Search terms
            max_articles_per_platform: Number of articles per platform
            cs_category: arXiv CS category (cs, cs.AI, cs.LG, cs.CV, etc.)
        """
        all_articles = []
        
        print(f"Searching for: '{keywords}'")
        if cs_category:
            print(f"arXiv category: {cs_category}")
        print("\n" + "=" * 80)
        
        # DBLP - CS-specific bibliography
        print("\nSearching DBLP (CS Bibliography)...")
        dblp_results = self.scrape_dblp(keywords, max_articles_per_platform)
        all_articles.extend(dblp_results)
        print(f"Found {len(dblp_results)} articles")
        time.sleep(random.uniform(1, 2))
        
        # arXiv - Best for CS preprints
        print("\nSearching arXiv (CS Preprints)...")
        arxiv_results = self.scrape_arxiv(keywords, max_articles_per_platform, cs_category)
        all_articles.extend(arxiv_results)
        print(f"Found {len(arxiv_results)} articles")
        time.sleep(random.uniform(1, 2))
        
        # Semantic Scholar - AI-powered search
        print("\nSearching Semantic Scholar...")
        semantic_results = self.scrape_semantic_scholar(keywords, max_articles_per_platform)
        all_articles.extend(semantic_results)
        print(f"Found {len(semantic_results)} articles")
        time.sleep(random.uniform(1, 2))
        
        # OpenAlex - Comprehensive coverage
        print("\nSearching OpenAlex...")
        openalex_results = self.scrape_openalex(keywords, max_articles_per_platform)
        all_articles.extend(openalex_results)
        print(f"Found {len(openalex_results)} articles")
        time.sleep(random.uniform(1, 2))
        
        # CrossRef - Published papers
        print("\nSearching CrossRef...")
        crossref_results = self.scrape_crossref(keywords, max_articles_per_platform)
        all_articles.extend(crossref_results)
        print(f"Found {len(crossref_results)} articles")
        time.sleep(random.uniform(1, 2))
        
        # CORE - Open access papers
        print("\nSearching CORE (Open Access)...")
        core_results = self.scrape_core(keywords, max_articles_per_platform)
        all_articles.extend(core_results)
        print(f"Found {len(core_results)} articles")
        
        print("\n" + "=" * 80)
        print(f"Total: {len(all_articles)} articles found across {6} platforms")
        
        return all_articles