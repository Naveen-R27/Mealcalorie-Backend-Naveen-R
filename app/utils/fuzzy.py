from rapidfuzz import fuzz, process

def best_match(query: str, candidates: list[str], limit=1):
    results = process.extract(query, candidates, scorer=fuzz.WRatio, limit=limit)
    return results
