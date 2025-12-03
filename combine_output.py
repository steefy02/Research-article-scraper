"""
Combine all platform result files into a single master file
Removes duplicates based on article titles
"""

import os
import re
from typing import List, Dict, Set


def parse_article_from_text(text_block: str) -> Dict:
    """Parse an article entry from a text block"""
    article = {
        'title': '',
        'authors': '',
        'year': '',
        'doi': '',
        'url': '',
        'journal': '',
        'bibtex': '',
        'platform': '',
        'keywords': []
    }
    
    lines = text_block.split('\n')
    
    # Extract title (first non-empty line after the article number)
    for line in lines:
        line = line.strip()
        if line.startswith('[') and ']' in line:
            title = line.split(']', 1)[1].strip()
            article['title'] = title
            break
    
    # Extract other fields
    bibtex_lines = []
    in_bibtex = False
    
    for line in lines:
        line_stripped = line.strip()
        
        if line_stripped.startswith('Authors:'):
            article['authors'] = line_stripped.replace('Authors:', '').strip()
        elif line_stripped.startswith('Publication Date:'):
            article['year'] = line_stripped.replace('Publication Date:', '').strip()
        elif line_stripped.startswith('Journal/Venue:'):
            journal = line_stripped.replace('Journal/Venue:', '').strip()
            article['journal'] = journal if journal != 'N/A' else ''
        elif line_stripped.startswith('DOI:'):
            doi = line_stripped.replace('DOI:', '').strip()
            article['doi'] = doi if doi != 'N/A' else ''
        elif line_stripped.startswith('URL:'):
            url = line_stripped.replace('URL:', '').strip()
            article['url'] = url if url != 'N/A' else ''
        elif line_stripped.startswith('BibTeX Citation:'):
            in_bibtex = True
        elif in_bibtex:
            if line_stripped.startswith('@'):
                bibtex_lines.append(line_stripped)
            elif line_stripped and not line_stripped.startswith('-'):
                bibtex_lines.append(line_stripped)
            elif line_stripped.startswith('-' * 10):
                break
    
    article['bibtex'] = '\n'.join(bibtex_lines)
    
    return article


def parse_platform_file(filepath: str) -> Dict[str, List[Dict]]:
    """
    Parse a platform file and return articles organized by keyword
    
    Returns:
        Dictionary mapping keywords to lists of articles
    """
    if not os.path.exists(filepath):
        print(f"Warning: File not found: {filepath}")
        return {}
    
    # Extract platform name from filename
    platform_name = os.path.basename(filepath).replace('.txt', '').replace('_', ' ').title()
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    articles_by_keyword = {}
    current_keyword = None
    
    # Split content by keyword sections
    sections = re.split(r'={100}\nKEYWORD: (.+?)\n={100}', content)
    
    # Parse each section
    for i in range(1, len(sections), 2):
        if i + 1 < len(sections):
            keyword = sections[i].strip().lower()
            section_content = sections[i + 1]
            
            # Split section into individual articles
            article_blocks = re.split(r'-{100}\n\[\d+\]', section_content)
            
            articles = []
            for block in article_blocks[1:]:  # Skip first empty split
                if block.strip():
                    article = parse_article_from_text(f"[1] {block}")
                    if article['title']:
                        article['platform'] = platform_name
                        article['keywords'] = [keyword]
                        articles.append(article)
            
            if keyword not in articles_by_keyword:
                articles_by_keyword[keyword] = []
            articles_by_keyword[keyword].extend(articles)
    
    return articles_by_keyword


def merge_article_data(article1: Dict, article2: Dict) -> Dict:
    """Merge data from two articles with the same title, keeping the most complete information"""
    merged = article1.copy()
    
    # Merge keywords
    keywords_set = set(merged.get('keywords', []))
    keywords_set.update(article2.get('keywords', []))
    merged['keywords'] = sorted(list(keywords_set))
    
    # Keep non-empty values
    for key in ['authors', 'year', 'doi', 'url', 'bibtex']:
        if not merged.get(key) and article2.get(key):
            merged[key] = article2[key]
    
    # Add platform info if from different platforms
    if 'platforms' not in merged:
        merged['platforms'] = [merged.get('platform', '')]
    if article2.get('platform') and article2['platform'] not in merged['platforms']:
        merged['platforms'].append(article2['platform'])
    
    return merged


def combine_all_results(input_dir: str = "./results", output_file: str = "./results/combined_all_platforms.txt"):
    """
    Combine all platform result files into a single master file
    Removes duplicates based on article titles
    """
    print("=" * 100)
    print("COMBINING ALL PLATFORM RESULTS")
    print("=" * 100)
    
    # Get all .txt files from the results directory
    if not os.path.exists(input_dir):
        print(f"\nError: Directory '{input_dir}' not found!")
        return
    
    txt_files = [f for f in os.listdir(input_dir) if f.endswith('.txt') and f != 'combined_all_platforms.txt']
    
    if not txt_files:
        print(f"\nNo .txt files found in '{input_dir}'")
        return
    
    print(f"\nFound {len(txt_files)} platform files:")
    for filename in txt_files:
        print(f"  • {filename}")
    
    # Parse all files
    all_articles_by_keyword = {}
    all_articles = []
    
    print("\nParsing files...")
    for filename in txt_files:
        filepath = os.path.join(input_dir, filename)
        print(f"  Processing {filename}...")
        
        articles_by_keyword = parse_platform_file(filepath)
        
        for keyword, articles in articles_by_keyword.items():
            if keyword not in all_articles_by_keyword:
                all_articles_by_keyword[keyword] = []
            all_articles_by_keyword[keyword].extend(articles)
            all_articles.extend(articles)
    
    print(f"\nTotal articles before deduplication: {len(all_articles)}")
    
    # Remove duplicates based on title (case-insensitive)
    print("\nRemoving duplicates...")
    unique_articles = {}
    
    for article in all_articles:
        title_key = article['title'].lower().strip()
        
        if title_key in unique_articles:
            # Merge with existing article
            unique_articles[title_key] = merge_article_data(unique_articles[title_key], article)
        else:
            unique_articles[title_key] = article
    
    unique_articles_list = list(unique_articles.values())
    print(f"Total unique articles after deduplication: {len(unique_articles_list)}")
    
    # Organize unique articles by keyword
    unique_by_keyword = {}
    for article in unique_articles_list:
        for keyword in article.get('keywords', ['uncategorized']):
            if keyword not in unique_by_keyword:
                unique_by_keyword[keyword] = []
            unique_by_keyword[keyword].append(article)
    
    # Sort articles within each keyword by year (descending)
    for keyword in unique_by_keyword:
        unique_by_keyword[keyword].sort(
            key=lambda x: (
                int(x['year']) if str(x['year']).isdigit() else 0
            ),
            reverse=True
        )
    
    # Write combined results
    print(f"\nWriting combined results to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write("COMBINED RESULTS FROM ALL PLATFORMS\n")
        f.write("=" * 100 + "\n\n")
        f.write(f"Total unique articles: {len(unique_articles_list)}\n")
        f.write(f"Keywords: {len(unique_by_keyword)}\n")
        f.write(f"Platform files processed: {len(txt_files)}\n\n")
        
        # Write articles organized by keyword
        for keyword in sorted(unique_by_keyword.keys()):
            articles = unique_by_keyword[keyword]
            
            f.write(f"\n{'=' * 100}\n")
            f.write(f"KEYWORD: {keyword.upper()}\n")
            f.write(f"{'=' * 100}\n")
            f.write(f"Unique articles: {len(articles)}\n\n")
            
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
                
                # Show all platforms where this article was found
                platforms = article.get('platforms', [article.get('platform', 'Unknown')])
                f.write(f"Found in: {', '.join(platforms)}\n")
                
                # Show all keywords this article matches
                keywords = article.get('keywords', [])
                if len(keywords) > 1:
                    f.write(f"Also matches keywords: {', '.join([k for k in keywords if k != keyword])}\n")
                
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
        
        # Add statistics section at the end
        f.write(f"\n\n{'=' * 100}\n")
        f.write("STATISTICS\n")
        f.write(f"{'=' * 100}\n\n")
        
        f.write(f"Total unique articles: {len(unique_articles_list)}\n")
        f.write(f"Total keywords: {len(unique_by_keyword)}\n\n")
        
        f.write("Articles per keyword:\n")
        for keyword in sorted(unique_by_keyword.keys()):
            f.write(f"  • {keyword}: {len(unique_by_keyword[keyword])} articles\n")
    
    print("\n" + "=" * 100)
    print("COMBINATION COMPLETE!")
    print("=" * 100)
    print(f"\nCombined file saved: {output_file}")
    print(f"Total unique articles: {len(unique_articles_list)}")
    print(f"Keywords: {len(unique_by_keyword)}")
    
    # Print summary statistics
    print("\nArticles per keyword:")
    for keyword in sorted(unique_by_keyword.keys()):
        print(f"  • {keyword}: {len(unique_by_keyword[keyword])} articles")


if __name__ == "__main__":
    combine_all_results()