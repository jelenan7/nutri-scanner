import os
import requests
from requests.exceptions import ReadTimeout, RequestException

API_BASE = os.getenv("OFF_API_URL", "https://world.openfoodfacts.net")

HEADERS = {
    "User-Agent": "NutriScanner/1.0 (nikcevicj7@gmail.com)"
}


def extract_display_image(product: dict) -> str | None:
    if not product:
        return None

    selected_images = product.get("selected_images", {}) or {}
    front = selected_images.get("front", {}) or {}
    display = front.get("display", {}) or {}

    if display.get("en"):
        return display.get("en")
    if display.get("fr"):
        return display.get("fr")

    return (
        product.get("image_front_url")
        or product.get("image_url")
        or product.get("image_front_small_url")
    )


def get_product_by_barcode(barcode: str) -> dict:
    url = f"{API_BASE}/api/v2/product/{barcode}"
    params = {
        "fields": ",".join([
            "code",
            "product_name",
            "generic_name",
            "brands",
            "quantity",
            "nutriments",
            "labels_tags",
            "countries_tags",
            "nutrition_grades",
            "nova_group",
            "ecoscore_grade",
            "ingredients_text",
            "allergens",
            "allergens_tags",
            "selected_images",
            "image_front_url",
            "image_url",
            "image_front_small_url"
        ])
    }

    try:
        res = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=10
        )
        res.raise_for_status()
        data = res.json()

        product = data.get("product")
        if product:
            product["display_image"] = extract_display_image(product)

        return data

    except (ReadTimeout, RequestException) as e:
        print("⚠️ OFF product fetch error:", e)
        return {
            "status": 0,
            "product": None
        }


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
            headers=HEADERS,
            timeout=10
        )
        res.raise_for_status()
        data = res.json()
        products = data.get("products", [])

        for product in products:
            product["display_image"] = extract_display_image(product)

        return products

    except (ReadTimeout, RequestException) as e:
        print("⚠️ OFF search error:", e)
        return []


def build_meal_plan(limit_kcal: int = 1200, vegan: bool = False, max_sugar: float = None) -> list[dict]:
    params = {
        "search_terms": "meal",
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": 100,
        "page": 1,
    }

    try:
        res = requests.get(
            f"{API_BASE}/cgi/search.pl",
            params=params,
            headers=HEADERS,
            timeout=10
        )
        res.raise_for_status()
        products = res.json().get("products", [])

    except (ReadTimeout, RequestException) as e:
        print("⚠️ OFF meal plan error:", e)
        return []

    filtered = []
    total_kcal = 0.0

    for p in products:
        nutr = p.get("nutriments", {}) or {}
        labels = p.get("labels_tags", []) or []

        kcal = nutr.get("energy-kcal_100g")
        sugar = nutr.get("sugars_100g")

        try:
            kcal = float(kcal)
        except (TypeError, ValueError):
            continue

        try:
            sugar = float(sugar) if sugar is not None else None
        except (TypeError, ValueError):
            sugar = None

        if max_sugar is not None:
            if sugar is None or sugar > max_sugar:
                continue

        if vegan and "en:vegan" not in labels:
            continue

        if total_kcal + kcal <= limit_kcal:
            p["display_image"] = extract_display_image(p)
            filtered.append(p)
            total_kcal += kcal

        if len(filtered) >= 4:
            break

    return filtered
