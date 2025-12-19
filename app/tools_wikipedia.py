"""
Wikipedia tools for the research agent.

Provides search and summary functions using the Wikipedia API.
No API key required - uses the public MediaWiki API.
"""

import urllib.parse
import urllib.request
import json
from typing import Optional


# Wikipedia API base URL
WIKI_API_URL = "https://en.wikipedia.org/w/api.php"


def wikipedia_search(query: str, limit: int = 5) -> list[str]:
    """
    Search Wikipedia for articles matching the query.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return (default: 5)
    
    Returns:
        List of article titles matching the query
    """
    params = {
        "action": "opensearch",
        "search": query,
        "limit": limit,
        "namespace": 0,
        "format": "json"
    }
    
    url = f"{WIKI_API_URL}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            # OpenSearch returns [query, [titles], [descriptions], [urls]]
            if len(data) >= 2:
                return data[1]
            return []
    except Exception as e:
        print(f"Wikipedia search error: {e}")
        return []


def wikipedia_summary(title: str, sentences: int = 5) -> Optional[str]:
    """
    Get a summary/extract of a Wikipedia article.
    
    Args:
        title: The exact title of the Wikipedia article
        sentences: Number of sentences to extract (default: 5)
    
    Returns:
        Article summary text, or None if not found
    """
    params = {
        "action": "query",
        "titles": title,
        "prop": "extracts",
        "exintro": True,  # Only get intro section
        "explaintext": True,  # Plain text, not HTML
        "exsentences": sentences,
        "format": "json"
    }
    
    url = f"{WIKI_API_URL}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            
            for page_id, page_data in pages.items():
                if page_id != "-1":  # -1 means page not found
                    return page_data.get("extract", "")
            
            return None
    except Exception as e:
        print(f"Wikipedia summary error: {e}")
        return None


# Tool definitions for LLM function calling (if using OpenAI tools feature)
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "wikipedia_search",
            "description": "Search Wikipedia for articles matching a query. Returns a list of article titles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find Wikipedia articles"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wikipedia_summary",
            "description": "Get the summary/introduction of a Wikipedia article by its exact title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The exact title of the Wikipedia article"
                    }
                },
                "required": ["title"]
            }
        }
    }
]

