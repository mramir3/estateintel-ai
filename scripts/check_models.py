import urllib.request
import json

def check_openrouter():
    url = "https://openrouter.ai/api/v1/models"
    req = urllib.request.Request(url, headers={"User-Agent": "EstateIntel/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = data.get("data", [])
            print(f"Total models available on OpenRouter: {len(models)}")
            free_models = [
                m for m in models 
                if m.get("id", "").endswith(":free") 
                or (str(m.get("pricing", {}).get("prompt", "1")) == "0" and str(m.get("pricing", {}).get("completion", "1")) == "0")
            ]
            print(f"Total free models found: {len(free_models)}\n")
            for m in free_models:
                print(f"ID: {m.get('id'):<45} | Context: {m.get('context_length'):<7} | Name: {m.get('name')}")
    except Exception as e:
        print("Error checking models:", e)

if __name__ == "__main__":
    check_openrouter()
