import requests
from requests.exceptions import ReadTimeout, RequestException
import os

API_BASE = os.getenv("OFF_API_URL", "https://world.openfoodfacts.org")


def get_product_by_barcode(barcode: str) -> dict:
    url = f"{API_BASE}/api/v0/product/{barcode}.json"
    res = requests.get(url, timeout=5)
    res.raise_for_status()
    return res.json()


def search_products(query: str, page_size: int = 25, page: int = 1) -> list:
    params = {
        "search_terms": query,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": page_size,
        "page": page,
    }

    try:
        res = requests.get(
            f"{API_BASE}/cgi/search.pl",
            params=params,
            timeout=5  # čak i smanji timeout
        )
        res.raise_for_status()
        return res.json().get("products", [])

    except (ReadTimeout, RequestException) as e:
        print("⚠️ OpenFoodFacts timeout:", e)
        return []   # ⬅️ KRITIČNO: ne pucaj aplikaciju




def build_meal_plan(limit_kcal: int = 1200, vegan=False, max_sugar=None) -> list[dict]:
    """Generate a simple meal idea using OpenFoodFacts data"""
    params = {
        "search_terms": "meal",
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 100,
    }
    res = requests.get(f"{API_BASE}/cgi/search.pl", params=params, timeout=10)
    res.raise_for_status()
    products = res.json().get("products", [])

    filtered = []
    total_kcal = 0
    for p in products:
        nutr = p.get("nutriments", {})
        kcal = nutr.get("energy-kcal_100g")
        sugar = nutr.get("sugars_100g")
        if not kcal:
            continue
        if max_sugar is not None and sugar and sugar > max_sugar:
            continue
        if vegan and "vegan" not in " ".join(p.get("labels_tags", [])):
            continue
        if total_kcal + kcal <= limit_kcal:
            filtered.append(p)
            total_kcal += kcal
        if len(filtered) >= 4:
            break
    return filtered
