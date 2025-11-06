import httpx
from app.config import settings
from app.utils.fuzzy import best_match

class USDAClient:
    BASE = "https://api.nal.usda.gov/fdc/v1/foods/search"
    def __init__(self, api_key: str, http_client: httpx.AsyncClient | None = None):
        self.api_key = api_key
        self._client = http_client or httpx.AsyncClient(timeout=10)

    async def search(self, query: str, page_size: int = 10):
        params = {"api_key": self.api_key, "query": query, "pageSize": page_size}
        r = await self._client.get(self.BASE, params=params)
        r.raise_for_status()
        return r.json()

    async def close(self):
        await self._client.aclose()

class CaloriesService:
    def __init__(self, usda_client: USDAClient, cache=None):
        self.usda = usda_client
        self.cache = cache

    def _extract_energy(self, food_item: dict):
        """Try multiple places to extract energy (kcal) and serving info:
           - foodNutrients (nutrientNumber 208)
           - labelNutrients (if present)
           - foodPortions / servingSize / servingSizeUnit
           Returns tuple (calories_value, per_unit, unit_description)
           per_unit: 'serving' or '100g' or 'g' (value is per unit)
        """
        # 1) foodNutrients
        nutrients = food_item.get('foodNutrients', []) or []
        for n in nutrients:
            num = str(n.get('nutrientNumber') or n.get('nutrientId') or '')
            name = (n.get('nutrientName') or '').lower()
            if num == '208' or 'energy' in name:
                # value is commonly in kcal per the item measurement  USDA often uses per 100g or per serving depending on item
                value = n.get('value')
                unit_name = n.get('unitName') or n.get('nutrientUnitName') or ''
                return value, None, f"nutrient:{unit_name}"

        # 2) labelNutrients (some branded foods)
        label = food_item.get('labelNutrients') or {}
        if label:
            for k, v in label.items():
                if 'energy' in k.lower() or 'calor' in k.lower():
                    val = v.get('value') or v
                    return val, None, 'label'

        # 3) Check 'servingSize' fields
        ss = food_item.get('servingSize')
        ss_unit = food_item.get('servingSizeUnit')
        if ss and ss_unit:
            return None, 'serving', f"{ss} {ss_unit}"

        # 4) foodPortions: sometimes contains gram weights for portions
        portions = food_item.get('foodPortions') or []
        for p in portions:
            # look for gram amount and portion description
            if str(p.get('amount')).isdigit() or isinstance(p.get('gramWeight'), (int, float)):
                # We return info to indicate grams per portion
                gram = p.get('gramWeight')
                desc = p.get('portionDescription') or p.get('modifier') or ''
                if gram:
                    return None, 'g', f"{gram}g ({desc})"

        return None, None, ''

    async def get_calories(self, dish_name: str, servings: float):
        if servings <= 0:
            raise ValueError("Servings must be > 0")

        cache_key = f"cal:{dish_name.lower()}:{servings}"
        if self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                return cached

        data = await self.usda.search(dish_name, page_size=25)
        foods = data.get('foods', []) or []
        if not foods:
            raise LookupError("Dish not found")

        candidates = []
        id_map = {}
        for f in foods:
            name = f.get('description') or f.get('lowercaseDescription') or f.get('dataType') or ''
            candidates.append(name)
            id_map[name] = f

        match = best_match(dish_name, candidates, limit=1)
        if not match:
            chosen = foods[0]
        else:
            chosen_name, score, idx = match[0]
            chosen = id_map.get(chosen_name, foods[0])

        
        energy_val, per_unit, unit_desc = self._extract_energy(chosen)

        # If we got a direct energy value assume it's per 100g unless meta indicates per serving
        calories_per_serving = None
        if energy_val is not None:
            
            data_type = chosen.get('dataType', '').lower()
            if 'branded' in data_type or 'survey' in data_type or 'foundation' in data_type:
                calories_per_serving = float(energy_val)
            else:
                serving_size = chosen.get('servingSize')
                if serving_size:
                    calories_per_serving = float(energy_val)
                else:
                    
                    gram = None
                    portions = chosen.get('foodPortions') or []
                    for p in portions:
                        if p.get('gramWeight'):
                            gram = p.get('gramWeight')
                            break
                    if gram:
                        calories_per_serving = float(energy_val) * (gram / 100.0)
                    else:
                        calories_per_serving = float(energy_val)

        if calories_per_serving is None and per_unit in ('serving', 'g'):
            nutrients = chosen.get('foodNutrients', []) or []
            for n in nutrients:
                name = (n.get('nutrientName') or '').lower()
                if 'energy' in name or n.get('nutrientNumber') == 208:
                    val = n.get('value')
                    calories_per_serving = float(val)
                    break

        if calories_per_serving is None:
            raise LookupError("Calorie info not available for best match")

        total = calories_per_serving * servings

        result = {
            "dish_name": dish_name,
            "servings": servings,
            "calories_per_serving": round(calories_per_serving, 2),
            "total_calories": round(total, 2),
            "source": "USDA FoodData Central",
            "matched_item": chosen.get('description') or chosen.get('lowercaseDescription') or ''
        }

        if self.cache:
            await self.cache.set(cache_key, result, ex=60)

        return result
