"""
Multi-keyword research scraper
Searches all platforms for multiple keywords and organizes results by platform
"""

import os
import time
import random
from scraper import CSResearchScraper
from typing import List, Dict


def remove_duplicates(articles: List[Dict]) -> List[Dict]:
    """Remove duplicate articles based on title (case-insensitive)"""
    seen_titles = set()
    unique_articles = []
    
    for article in articles:
        title_lower = article['title'].lower().strip()
        if title_lower not in seen_titles:
            seen_titles.add(title_lower)
            unique_articles.append(article)
    
    return unique_articles


def save_platform_results(platform_name: str, articles_by_keyword: Dict[str, List[Dict]], output_dir: str = "./results"):
    """
    Save results for a single platform, organized by keyword
    
    Args:
        platform_name: Name of the platform (e.g., "arXiv", "DBLP")
        articles_by_keyword: Dictionary mapping keywords to lists of articles
        output_dir: Directory to save results
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Remove duplicates within each keyword
    for keyword in articles_by_keyword:
        articles_by_keyword[keyword] = remove_duplicates(articles_by_keyword[keyword])
    
    # Count total unique articles across all keywords
    all_articles = []
    for articles in articles_by_keyword.values():
        all_articles.extend(articles)
    unique_articles = remove_duplicates(all_articles)
    
    filename = os.path.join(output_dir, f"{platform_name.lower().replace(' ', '_')}.txt")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"{'=' * 100}\n")
        f.write(f"{platform_name.upper()} - RESEARCH ARTICLES\n")
        f.write(f"{'=' * 100}\n\n")
        f.write(f"Total unique articles: {len(unique_articles)}\n")
        f.write(f"Search keywords: {len(articles_by_keyword)}\n\n")
        
        # Write articles organized by keyword
        for keyword, articles in articles_by_keyword.items():
            if not articles:
                continue
                
            f.write(f"\n{'=' * 100}\n")
            f.write(f"KEYWORD: {keyword.upper()}\n")
            f.write(f"{'=' * 100}\n")
            f.write(f"Articles found: {len(articles)}\n\n")
            
            for i, article in enumerate(articles, 1):
                f.write(f"\n{'-' * 100}\n")
                f.write(f"[{i}] {article['title']}\n")
                f.write(f"{'-' * 100}\n\n")
                
                f.write(f"Authors: {article.get('authors', 'N/A')}\n")
                f.write(f"Publication Date: {article.get('year', 'N/A')}\n")
                
                # Add journal/venue information
                if article.get('journal'):
                    f.write(f"Journal/Venue: {article['journal']}\n")
                else:
                    f.write(f"Journal/Venue: N/A\n")
                
                if article.get('doi'):
                    f.write(f"DOI: {article['doi']}\n")
                else:
                    f.write(f"DOI: N/A\n")
                
                if article.get('url'):
                    f.write(f"URL: {article['url']}\n")
                else:
                    f.write(f"URL: N/A\n")
                
                f.write(f"\nBibTeX Citation:\n")
                f.write(f"{article.get('bibtex', 'N/A')}\n")
    
    print(f"✓ Saved {len(unique_articles)} unique articles to {filename}")


def search_multiple_keywords(search_keywords: List[str], max_articles_per_platform: int = 15, cs_category: str = "cs"):
    """
    Search all platforms for multiple keywords and save results organized by platform
    
    Args:
        search_keywords: List of keywords to search for
        max_articles_per_platform: Number of articles to retrieve per platform per keyword
        cs_category: arXiv CS category (cs, cs.AI, cs.LG, cs.CV, etc.)
    """
    scraper = CSResearchScraper()
    
    # Dictionary to store results: platform -> keyword -> articles
    results_by_platform = {
        'arXiv': {},
        'DBLP': {},
        'Semantic Scholar': {},
        'OpenAlex': {},
        'CrossRef': {},
        'CORE': {}
    }
    
    # Initialize keyword lists for each platform
    for platform in results_by_platform:
        for keyword in search_keywords:
            results_by_platform[platform][keyword] = []
    
    print("=" * 100)
    print(f"SEARCHING {len(search_keywords)} KEYWORDS ACROSS 6 PLATFORMS")
    print("=" * 100)
    print(f"\nKeywords:")
    for i, keyword in enumerate(search_keywords, 1):
        print(f"  {i}. {keyword}")
    print(f"\nMax articles per platform per keyword: {max_articles_per_platform}")
    print("=" * 100)
    
    # Search each keyword across all platforms
    for keyword_idx, keyword in enumerate(search_keywords, 1):
        print(f"\n\n{'#' * 100}")
        print(f"KEYWORD {keyword_idx}/{len(search_keywords)}: '{keyword}'")
        print(f"{'#' * 100}\n")
        
        # DBLP
        print(f"  → Searching DBLP...")
        try:
            dblp_results = scraper.scrape_dblp(keyword, max_articles_per_platform)
            results_by_platform['DBLP'][keyword].extend(dblp_results)
            print(f"    Found {len(dblp_results)} articles")
        except Exception as e:
            print(f"    Error: {e}")
        time.sleep(random.uniform(1, 2))
        
        # arXiv
        print(f"  → Searching arXiv...")
        try:
            arxiv_results = scraper.scrape_arxiv(keyword, max_articles_per_platform, cs_category)
            results_by_platform['arXiv'][keyword].extend(arxiv_results)
            print(f"    Found {len(arxiv_results)} articles")
        except Exception as e:
            print(f"    Error: {e}")
        time.sleep(random.uniform(1, 2))
        
        # Semantic Scholar
        print(f"  → Searching Semantic Scholar...")
        try:
            semantic_results = scraper.scrape_semantic_scholar(keyword, max_articles_per_platform)
            results_by_platform['Semantic Scholar'][keyword].extend(semantic_results)
            print(f"    Found {len(semantic_results)} articles")
        except Exception as e:
            print(f"    Error: {e}")
        time.sleep(random.uniform(1, 2))
        
        # OpenAlex
        print(f"  → Searching OpenAlex...")
        try:
            openalex_results = scraper.scrape_openalex(keyword, max_articles_per_platform)
            results_by_platform['OpenAlex'][keyword].extend(openalex_results)
            print(f"    Found {len(openalex_results)} articles")
        except Exception as e:
            print(f"    Error: {e}")
        time.sleep(random.uniform(1, 2))
        
        # CrossRef
        print(f"  → Searching CrossRef...")
        try:
            crossref_results = scraper.scrape_crossref(keyword, max_articles_per_platform)
            results_by_platform['CrossRef'][keyword].extend(crossref_results)
            print(f"    Found {len(crossref_results)} articles")
        except Exception as e:
            print(f"    Error: {e}")
        time.sleep(random.uniform(1, 2))
        
        # CORE
        print(f"  → Searching CORE...")
        try:
            core_results = scraper.scrape_core(keyword, max_articles_per_platform)
            results_by_platform['CORE'][keyword].extend(core_results)
            print(f"    Found {len(core_results)} articles")
        except Exception as e:
            print(f"    Error: {e}")
        time.sleep(random.uniform(1, 2))
    
    # Save results for each platform
    print("\n\n" + "=" * 100)
    print("SAVING RESULTS BY PLATFORM")
    print("=" * 100 + "\n")
    
    for platform, keywords_data in results_by_platform.items():
        save_platform_results(platform, keywords_data)
    
    print("\n" + "=" * 100)
    print("ALL SEARCHES COMPLETE!")
    print("=" * 100)
    print("\nGenerated files in ./results/ directory:")
    for platform in results_by_platform.keys():
        filename = f"{platform.lower().replace(' ', '_')}.txt"
        print(f"  • {filename}")


if __name__ == "__main__":
    # Define your search keywords here
    search_keywords = [
        "dark patterns",
        "deceptive design",
        "user interface manipulation",
        "persuasive design ethics",
        "malicious interface design",
        "cookie consent manipulation",
        "subscription cancellation UX",
    ]
    
    # Run the search
    search_multiple_keywords(
        search_keywords=search_keywords,
        max_articles_per_platform=15,
        cs_category="cs"
    )