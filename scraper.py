#!/usr/bin/env python3
"""
Ukraine Combat Data Scraper
Fetches daily combat engagement data from Ukrainian General Staff reports.
Parses Ukrinform articles and extracts engagement counts per operational direction.

Run manually: python scraper.py
Or via GitHub Actions: scheduled daily at 8pm Kyiv time
"""

import json
import re
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from pathlib import Path

# Configuration
OUTPUT_FILE = "combat-data.json"
UKRINFORM_URL = "https://www.ukrinform.net/rubric-ato"

# Mapping of direction names (various spellings) to canonical names
DIRECTION_ALIASES = {
    # Pokrovsk
    'pokrovsk': 'pokrovsk',
    # Kostiantynivka  
    'kostiantynivka': 'kostiantynivka',
    'kostyantynivka': 'kostiantynivka',
    'konstantynivka': 'kostiantynivka',
    # Oleksandrivka
    'oleksandrivka': 'oleksandrivka',
    'alexandrivka': 'oleksandrivka',
    # Lyman
    'lyman': 'lyman',
    # Sloviansk
    'sloviansk': 'sloviansk',
    'slovyansk': 'sloviansk',
    'slavyansk': 'sloviansk',
    # Huliaipole
    'huliaipole': 'huliaipole',
    'gulyaipole': 'huliaipole',
    # Orikhiv
    'orikhiv': 'orikhiv',
    'orekhov': 'orikhiv',
    # Kupiansk
    'kupiansk': 'kupiansk',
    'kupyansk': 'kupiansk',
    # Kramatorsk
    'kramatorsk': 'kramatorsk',
    # Kursk
    'kursk': 'kursk',
    # Kharkiv North / Slobozhansky
    'kharkiv': 'kharkiv_north',
    'slobozhansky': 'kharkiv_north',
    'slobozhansk': 'kharkiv_north',
    'northern-slobozhansky': 'kharkiv_north',
    'northern slobozhansky': 'kharkiv_north',
    'north-slobozhansky': 'kharkiv_north',
    'southern-slobozhansky': 'kharkiv_north',
    'southern slobozhansky': 'kharkiv_north',
    # Kherson / Prydniprovskyi
    'kherson': 'kherson',
    'prydniprovskyi': 'kherson',
    'prydniprovsky': 'kherson',
    'dnipro': 'kherson',
    # Toretsk
    'toretsk': 'toretsk',
    # Siversk
    'siversk': 'siversk',
}

# Direction display names and approximate coordinates
DIRECTION_CONFIG = {
    'pokrovsk': {
        'displayName': 'Pokrovsk',
        'coords': [48.28, 37.18],
        'polygon': [[48.45, 36.90], [48.50, 37.50], [48.20, 37.60], [48.05, 37.20], [48.15, 36.85]]
    },
    'kostiantynivka': {
        'displayName': 'Kostiantynivka',
        'coords': [48.52, 37.70],
        'polygon': [[48.65, 37.45], [48.70, 37.95], [48.45, 38.00], [48.35, 37.60], [48.50, 37.40]]
    },
    'oleksandrivka': {
        'displayName': 'Oleksandrivka',
        'coords': [47.95, 36.70],
        'polygon': [[48.10, 36.50], [48.10, 36.95], [47.85, 37.00], [47.75, 36.65], [47.90, 36.45]]
    },
    'lyman': {
        'displayName': 'Lyman',
        'coords': [48.98, 37.81],
        'polygon': [[49.15, 37.50], [49.20, 38.10], [49.00, 38.25], [48.80, 38.00], [48.85, 37.55]]
    },
    'sloviansk': {
        'displayName': 'Sloviansk',
        'coords': [48.85, 37.58],
        'polygon': [[48.95, 37.35], [49.00, 37.75], [48.80, 37.85], [48.70, 37.50], [48.80, 37.30]]
    },
    'huliaipole': {
        'displayName': 'Huliaipole',
        'coords': [47.65, 36.25],
        'polygon': [[47.85, 35.90], [47.85, 36.50], [47.55, 36.60], [47.40, 36.20], [47.55, 35.85]]
    },
    'orikhiv': {
        'displayName': 'Orikhiv',
        'coords': [47.56, 35.78],
        'polygon': [[47.75, 35.50], [47.75, 36.00], [47.45, 36.05], [47.35, 35.65], [47.50, 35.45]]
    },
    'kupiansk': {
        'displayName': 'Kupiansk',
        'coords': [49.71, 37.62],
        'polygon': [[49.90, 37.30], [49.95, 37.90], [49.70, 38.00], [49.50, 37.70], [49.55, 37.25]]
    },
    'kramatorsk': {
        'displayName': 'Kramatorsk',
        'coords': [48.72, 37.55],
        'polygon': [[48.82, 37.40], [48.85, 37.70], [48.65, 37.75], [48.58, 37.50], [48.68, 37.35]]
    },
    'kursk': {
        'displayName': 'Kursk (RU)',
        'coords': [51.40, 35.20],
        'polygon': [[51.65, 34.60], [51.70, 35.60], [51.35, 35.80], [51.10, 35.30], [51.25, 34.70]]
    },
    'kharkiv_north': {
        'displayName': 'Kharkiv (N)',
        'coords': [50.05, 36.45],
        'polygon': [[50.25, 36.10], [50.30, 36.80], [50.05, 36.95], [49.85, 36.55], [49.95, 36.15]]
    },
    'kherson': {
        'displayName': 'Kherson',
        'coords': [46.65, 32.62],
        'polygon': [[46.85, 32.20], [46.90, 33.00], [46.55, 33.10], [46.40, 32.60], [46.55, 32.15]]
    },
    'toretsk': {
        'displayName': 'Toretsk',
        'coords': [48.40, 37.85],
        'polygon': [[48.55, 37.65], [48.55, 38.05], [48.30, 38.10], [48.25, 37.75], [48.40, 37.60]]
    },
    'siversk': {
        'displayName': 'Siversk',
        'coords': [48.87, 38.08],
        'polygon': [[49.00, 37.90], [49.05, 38.30], [48.80, 38.35], [48.72, 38.00], [48.85, 37.85]]
    }
}


def get_heat_level(engagements: int) -> str:
    """Determine heat level based on engagement count."""
    if engagements >= 30:
        return 'extreme'
    elif engagements >= 15:
        return 'high'
    elif engagements >= 8:
        return 'medium'
    elif engagements >= 3:
        return 'low'
    else:
        return 'quiet'


def parse_engagement_count(text: str) -> dict:
    """
    Parse engagement counts from General Staff report text.
    Returns dict mapping direction -> count
    """
    results = {}
    text_lower = text.lower()
    
    # Patterns to match engagement counts
    # "In the Pokrovsk direction, the enemy made 43 attempts"
    # "Pokrovsk direction – 43 attacks"
    # "43 combat engagements in the Pokrovsk direction"
    patterns = [
        # "In the X direction, ... made/conducted/carried out N attacks/attempts/engagements"
        r'(?:in\s+the\s+)?(\w+(?:[-\s]\w+)?)\s+direction[,:\s]+.*?(?:made|conducted|carried out|recorded)\s+(\d+)\s+(?:attack|attempt|assault|engagement|offensive)',
        # "X direction – N attacks"
        r'(\w+(?:[-\s]\w+)?)\s+direction\s*[-–:]\s*(\d+)\s+(?:attack|attempt|assault|engagement)',
        # "N attacks in the X direction"
        r'(\d+)\s+(?:attack|attempt|assault|engagement)s?\s+(?:in\s+the\s+)?(\w+(?:[-\s]\w+)?)\s+direction',
        # "X direction ... repelled N enemy attacks"
        r'(\w+(?:[-\s]\w+)?)\s+direction.*?repelled\s+(\d+)\s+(?:enemy\s+)?(?:attack|assault)',
        # "X – N" in lists
        r'(\w+(?:[-\s]\w+)?)\s*[-–]\s*(\d+)(?:\s+attack)?',
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            groups = match.groups()
            # Handle both orderings (direction-count and count-direction)
            if groups[0].isdigit():
                count, direction = int(groups[0]), groups[1]
            else:
                direction, count = groups[0], int(groups[1])
            
            # Clean up direction name
            direction = direction.strip().replace('-', '_').replace(' ', '_')
            
            # Map to canonical name
            canonical = None
            for alias, canon in DIRECTION_ALIASES.items():
                if alias in direction or direction in alias:
                    canonical = canon
                    break
            
            if canonical and canonical in DIRECTION_CONFIG:
                # Keep highest count if multiple matches
                if canonical not in results or count > results[canonical]:
                    results[canonical] = count
    
    return results


def fetch_latest_report() -> tuple[str, str]:
    """
    Fetch the latest General Staff report from Ukrinform.
    Returns (article_text, article_url)
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Fetch the ATO/war news page
    response = requests.get(UKRINFORM_URL, headers=headers, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for General Staff report links
    keywords = ['combat engagement', 'general staff', 'combat clash', 'enemy attack']
    
    for article in soup.find_all('a', href=True):
        title = article.get_text().lower()
        if any(kw in title for kw in keywords):
            url = article['href']
            if not url.startswith('http'):
                url = 'https://www.ukrinform.net' + url
            
            # Fetch the article
            article_response = requests.get(url, headers=headers, timeout=30)
            article_response.raise_for_status()
            
            article_soup = BeautifulSoup(article_response.text, 'html.parser')
            
            # Extract article text
            article_body = article_soup.find('div', class_='newsText')
            if article_body:
                return article_body.get_text(), url
    
    return None, None


def fetch_casualty_data() -> dict:
    """
    Fetch Russian casualty data from available APIs.
    """
    try:
        # Try the russian-casualties.in.ua API
        response = requests.get(
            'https://russian-casualties.in.ua/api/v1/data/json/daily',
            timeout=10
        )
        if response.ok:
            data = response.json()
            if data and len(data) > 0:
                latest = data[-1]  # Most recent entry
                return {
                    'russia': {
                        'total': latest.get('personnel', 0),
                        'daily': latest.get('personnel_daily', 0),
                        'source': 'Ukrainian General Staff'
                    },
                    'ukraine': {
                        'total': 400000,  # Last official estimate
                        'daily': None,
                        'source': 'Zelensky (Jan 2025)'
                    }
                }
    except Exception as e:
        print(f"Warning: Could not fetch casualty data: {e}")
    
    # Fallback to static data
    return {
        'russia': {
            'total': 1167570,
            'daily': 1120,
            'source': 'Ukrainian General Staff'
        },
        'ukraine': {
            'total': 400000,
            'daily': None,
            'source': 'Zelensky (Jan 2025)'
        }
    }


def load_existing_data() -> dict:
    """Load existing combat data if available."""
    try:
        with open(OUTPUT_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def build_combat_data(engagement_counts: dict, source_url: str = None) -> dict:
    """Build the full combat data structure."""
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    
    # Build front sectors
    front_sectors = []
    for direction_id, config in DIRECTION_CONFIG.items():
        count = engagement_counts.get(direction_id, 0)
        front_sectors.append({
            'name': direction_id,
            'displayName': config['displayName'],
            'coords': config['coords'],
            'combatEngagements': count,
            'heat': get_heat_level(count),
            'polygon': config['polygon']
        })
    
    # Sort by engagement count (highest first)
    front_sectors.sort(key=lambda x: x['combatEngagements'], reverse=True)
    
    total_engagements = sum(engagement_counts.values())
    
    return {
        'date': today,
        'source': 'Ukrainian General Staff',
        'sourceUrl': source_url,
        'totalEngagements': total_engagements,
        'lastUpdate': datetime.now(timezone.utc).isoformat(),
        'frontSectors': front_sectors,
        'casualties': fetch_casualty_data()
    }


def main():
    print(f"Ukraine Combat Data Scraper")
    print(f"Running at: {datetime.now(timezone.utc).isoformat()}")
    print("-" * 50)
    
    # Try to fetch latest report
    print("Fetching latest General Staff report...")
    article_text, article_url = fetch_latest_report()
    
    if article_text:
        print(f"Found report: {article_url}")
        engagement_counts = parse_engagement_count(article_text)
        print(f"Parsed engagements: {engagement_counts}")
    else:
        print("Warning: Could not fetch report, using fallback data")
        # Load existing data as fallback
        existing = load_existing_data()
        if existing:
            engagement_counts = {
                sector['name']: sector['combatEngagements']
                for sector in existing.get('frontSectors', [])
            }
        else:
            # Hardcoded fallback based on recent data
            engagement_counts = {
                'pokrovsk': 35,
                'kostiantynivka': 20,
                'oleksandrivka': 14,
                'lyman': 10,
                'huliaipole': 8,
                'sloviansk': 6,
                'kupiansk': 5,
                'orikhiv': 4,
                'kramatorsk': 3,
                'kursk': 2,
                'kharkiv_north': 2,
                'kherson': 1
            }
    
    # Build output
    combat_data = build_combat_data(engagement_counts, article_url)
    
    # Save to file
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(combat_data, f, indent=2)
    
    print(f"\nSaved to {OUTPUT_FILE}")
    print(f"Total engagements: {combat_data['totalEngagements']}")
    print(f"Active fronts: {len([s for s in combat_data['frontSectors'] if s['combatEngagements'] > 0])}")
    
    # Print summary
    print("\nFront Activity:")
    for sector in combat_data['frontSectors'][:5]:
        print(f"  {sector['displayName']}: {sector['combatEngagements']} ({sector['heat']})")


if __name__ == '__main__':
    main()
