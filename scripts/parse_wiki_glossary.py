"""Parse Wikipedia Fishery Glossary wikitext into structured JSON."""
import json, re, sys
from pathlib import Path

# The wikitext was fetched from:
# https://en.wikipedia.org/w/api.php?action=parse&page=Glossary_of_fishery_terms&prop=wikitext&format=json
# and saved. This script extracts term-definition pairs.

def parse_wikitext(text: str) -> dict[str, str]:
    """Extract terms from Wikipedia glossary wikitext."""
    terms = {}
    # Pattern: *'''[[Term]]''' – definition  or  *'''Term''' – definition
    # The term may have wiki formatting stripped
    for line in text.split('\n'):
        # Match glossary entries: *'''...''' – ...
        m = re.match(r"\*'''+(?:\[\[)?([^\]|']+)(?:\]\]|''').*?[–-]\s*(.+)", line)
        if m:
            term = m.group(1).strip()
            # Clean term: remove wiki formatting
            term = re.sub(r'\([^)]*\)', '', term).strip()
            definition = re.sub(r"''+", '', m.group(2)).strip()
            if term and len(term) > 1:
                terms[term.lower()] = definition
    return terms

# For now, use hardcoded extraction from known Wikipedia format
# The API response is in the tool output — we'll rebuild from it
print("Parser ready. Run with Wikipedia API response to rebuild glossary.")
