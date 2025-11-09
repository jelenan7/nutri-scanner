import os
import asyncio
import httpx
from dotenv import load_dotenv
from typing import Any, Dict, List, Optional

load_dotenv()

OFF_BASE = os.getenv("OFF_BASE", "https://world.openfoodfacts.org")
UA = os.getenv("OFF_USER_AGENT", "NutriScanner/1.0 (contact@example.com)")
COMMON_HEADERS = {"User-Agent": UA}

# Robusni timeouti + mali broj retry-a
TIMEOUT = httpx.Timeout(connect=5.0, read=25.0, write=10.0, pool=5.0)
RETRIES = 2

# Polja za /product v2 (stranica skeniranja)
FIELDS_PRODUCT = (
    "product_name,brands,nutriments,nutrition_grades,"
    "nutriscore_data,nova_group,allergens,ingredients_text,"
    "selected_images,code,countries,countries_tags"
)

async def _get_with_retry(url: str, params: Dict[str, Any]) -> httpx.Response:
    """GET sa malim exponential backoff-om za ReadTimeout."""
    for attempt in range(RETRIES + 1):
        try:
            async with httpx.AsyncClient(headers=COMMON_HEADERS, timeout=TIMEOUT) as client:
                r = await client.get(url, params=params)
                r.raise_for_status()
                return r
        except httpx.ReadTimeout:
            if attempt == RETRIES:
                raise
            await asyncio.sleep(0.5 * (2 ** attempt))  # 0.5s, 1.0s ...

# ----- /api/v2/product/{barcode}
async def get_product(barcode: str) -> Dict[str, Any]:
    url = f"{OFF_BASE}/api/v2/product/{barcode}"
    params = {"fields": FIELDS_PRODUCT}
    r = await _get_with_retry(url, params)
    data = r.json()
    if data.get("status") != 1:
        raise ValueError("Product not found")
    return data["product"]

# ----- /api/v2/search
async def search_products(
    category_en: Optional[str] = None,
    vegan: bool = False,
    max_sugars_100g: Optional[float] = None,
    page: int = 1,
    page_size: int = 24,
    sort_by: Optional[str] = "unique_scans_n",
    nutri_grades: Optional[List[str]] = None,
    only_cg: bool = False
) -> Dict[str, Any]:
    """
    OFF v2 search – lagana polja zbog brzih kartica.
    Uključujemo i nutriments da možemo prikazati šećere/energiju.
    """
    url = f"{OFF_BASE}/api/v2/search"
    params: Dict[str, Any] = {
        "fields": "code,product_name,brands,nutrition_grades,nova_group,countries_tags,selected_images,nutriments",
        "page": page,
        "page_size": page_size,
        "sort_by": sort_by or "unique_scans_n",
    }
    if category_en:
        params["categories_tags_en"] = category_en
    if vegan:
        params["labels_tags"] = "en:vegan"

    # ✅ Stabilniji server filter; ne forsira postojanje polja kao 'nutriments.sugars_100g'
    if max_sugars_100g is not None:
        params["sugars_100g<"] = max_sugars_100g

    if nutri_grades:
        params["nutrition_grades_tags"] = ",".join(g.lower() for g in nutri_grades)
    if only_cg:
        # OFF radi i sa 'countries_tags_en=montenegro'
        params["countries_tags_en"] = "montenegro"

    r = await _get_with_retry(url, params)
    return r.json()

# ----- helpers
def extract_image_url(product: Dict[str, Any]) -> Optional[str]:
    """Izaberi najbolju 'front' sliku iz selected_images."""
    sel = product.get("selected_images") or {}
    front = sel.get("front") or {}
    disp = front.get("display") or {}
    if isinstance(disp, dict):
        if "en" in disp and disp["en"]:
            return disp["en"]
        if disp:
            return next(iter(disp.values()))
    return None
