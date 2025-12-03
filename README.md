# Research Paper Scraper - Multi-Keyword System

This system scrapes research papers from multiple academic platforms, organizing results by platform and keyword, with automatic deduplication.

## Files Overview

1. **scraper.py** - Core scraper module (can be used for any keywords/topics)
2. **search_multiple_keywords.py** - Main script that searches multiple keywords across all platforms
3. **combine_output.py** - Combines all platform files and removes duplicates

## Features

- ✅ Searches 6 academic platforms: arXiv, DBLP, Semantic Scholar, OpenAlex, CrossRef, CORE
- ✅ Supports multiple search keywords
- ✅ Organizes results by platform and keyword
- ✅ Removes duplicates based on article titles
- ✅ Includes complete metadata:
  - Title
  - Authors
  - Publication date
  - Journal/Venue/Conference name
  - DOI (when available)
  - URL/Link to article
  - BibTeX citation with journal field
- ✅ Smart query fallback strategies for maximum results

## Requirements

```bash
pip install requests beautifulsoup4 lxml
```

## Quick Start

### Step 1: Configure Your Search Keywords

Edit `search_multiple_keywords.py` and modify the keyword list:

```python
search_keywords = [
    "dark patterns",
    "deceptive design",
    "user interface manipulation",
    "persuasive design ethics",
    "malicious interface design",
    "cookie consent manipulation",
    "subscription cancellation UX",
]
```

### Step 2: Run the Search

```bash
python search_multiple_keywords.py
```

This will:

- Search all 6 platforms for each keyword
- Save results to `./results/` directory
- Create one file per platform:
  - `arxiv.txt`
  - `dblp.txt`
  - `semantic_scholar.txt`
  - `openalex.txt`
  - `crossref.txt`
  - `core.txt`

### Step 3: Combine Results

```bash
python combine_output.py
```

This will:

- Parse all platform files
- Remove duplicates
- Merge articles found across multiple platforms
- Create `./results/combined_all_platforms.txt`

## Output Format

### Platform Files (e.g., arxiv.txt)

```
==================================================================================================
ARXIV - RESEARCH ARTICLES
==================================================================================================

Total unique articles: 45
Search keywords: 7

==================================================================================================
KEYWORD: DARK PATTERNS
==================================================================================================
Articles found: 12

----------------------------------------------------------------------------------------------------
[1] Understanding Dark Patterns in E-commerce
----------------------------------------------------------------------------------------------------

Authors: John Doe, Jane Smith, Bob Johnson
Publication Date: 2023-05-15
Journal/Venue: ACM Conference on Human Factors in Computing Systems (CHI)
DOI: 10.1234/example.doi
URL: https://arxiv.org/abs/2305.12345

BibTeX Citation:
@article{doe2023understanding,
  title={Understanding Dark Patterns in E-commerce},
  author={John Doe, Jane Smith, Bob Johnson},
  year={2023},
  journal={ACM Conference on Human Factors in Computing Systems (CHI)},
  doi={10.1234/example.doi},
  url={https://arxiv.org/abs/2305.12345},
  note={Source: arXiv}
}
```

### Combined File (combined_all_platforms.txt)

Similar format but includes:

- All unique articles from all platforms
- Shows which platforms each article was found on
- Shows which keywords each article matches
- Complete statistics at the end

## Customization Options

### Modify Number of Articles Per Platform

In `search_multiple_keywords.py`:

```python
search_multiple_keywords(
    search_keywords=search_keywords,
    max_articles_per_platform=15,  # ← Change this number
    cs_category="cs"
)
```

### Change arXiv Category

Available categories:

- `"cs"` - All of Computer Science
- `"cs.AI"` - Artificial Intelligence
- `"cs.LG"` - Machine Learning
- `"cs.CV"` - Computer Vision
- `"cs.CL"` - Computation and Language (NLP)
- `"cs.CR"` - Cryptography and Security
- `"cs.DB"` - Databases
- `"cs.SE"` - Software Engineering

```python
search_multiple_keywords(
    search_keywords=search_keywords,
    max_articles_per_platform=15,
    cs_category="cs.AI"  # ← Change category here
)
```

### Use Scraper for Single Keyword Search

You can also use the scraper directly:

```python
from scraper import CSResearchScraper

scraper = CSResearchScraper()

# Search single platform
articles = scraper.scrape_arxiv("machine learning", max_articles=20, category="cs.AI")

# Or search all platforms
articles = scraper.search_all_platforms("dark patterns", max_articles_per_platform=10)
```

## Output Directory Structure

```
./results/
├── arxiv.txt
├── dblp.txt
├── semantic_scholar.txt
├── openalex.txt
├── crossref.txt
├── core.txt
└── combined_all_platforms.txt
```

## Tips

1. **Rate Limiting**: The scraper includes automatic delays between requests (1-2 seconds) to be respectful to APIs
2. **Large Searches**: If searching many keywords, the process may take several minutes
3. **Network Issues**: If a platform fails, the scraper continues with other platforms
4. **Duplicates**: Articles are considered duplicates if they have the same title (case-insensitive)

## Troubleshooting

### Getting 0 results from arXiv (or other platforms)

**Possible causes:**

1. **Network connectivity**: Ensure you have internet access
   - Test: Try accessing https://arxiv.org in your browser
2. **Firewall/proxy blocking**: Some networks block API access

   - Solution: Try from a different network or configure proxy settings

3. **Query too restrictive**: arXiv's category + keyword combination might be too specific

   - The scraper now uses multiple fallback strategies automatically
   - It tries:
     1. Category + keyword (most restrictive)
     2. Category + keyword in title/abstract
     3. Category wildcard + keyword
     4. Keyword only (no category restriction)

4. **Rate limiting**: If you've made too many requests

   - Solution: Wait 5-10 minutes before trying again
   - The scraper includes automatic delays to prevent this

5. **API temporarily down**: Sometimes platforms have outages
   - Solution: Try again later or skip that platform

**Quick test:**

```python
from scraper import CSResearchScraper

scraper = CSResearchScraper()

# Test arXiv with a common term
articles = scraper.scrape_arxiv("neural networks", max_articles=5, category="cs")
print(f"Found {len(articles)} articles")

# Test without category restriction
articles = scraper.scrape_arxiv("neural networks", max_articles=5, category=None)
print(f"Found {len(articles)} articles (no category)")
```

### No articles found

- Check your internet connection
- Try different keywords
- Some platforms may temporarily block requests (wait a few minutes)

### Missing DOIs or URLs

- Not all articles have DOIs
- The scraper gets what's available from each platform

### Parsing errors in combine_output.py

- Make sure platform files are in the correct format
- Check that files are in the `./results/` directory

## Requirements

Install required packages:

```bash
pip install requests beautifulsoup4 lxml
```

**System Requirements:**

- Python 3.7+
- Internet connection with access to academic APIs
- No firewall blocking research platform domains

## License

Free to use and modify for research purposes.
