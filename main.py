from fastapi import FastAPI
import requests

app = FastAPI()
API_KEY = "rigour-ip-checking-service"

@app.get("/")
def read_root():
    return {"message": "IP Checker API is working!"}

@app.post("/ip-check")
async def ip_check(payload: dict):
    project_id = payload.get("project_id")
    respondent_id = payload.get("respondent_id")
    ip_address = payload.get("ip_address")

    # Make IP geolocation request
    geo_response = requests.get(f"http://ip-api.com/json/{ip_address}")
    geo_data = geo_response.json()

    # Extract desired fields, default to "Unknown" if missing
    country = geo_data.get("country", "Unknown")
    country_code = geo_data.get("countryCode", "Unknown")
    region = geo_data.get("region", "Unknown")
    region_name = geo_data.get("regionName", "Unknown")
    city = geo_data.get("city", "Unknown")

    return {
        "project_id": project_id,
        "respondent_id": respondent_id,
        "ip_address": ip_address,
        "country": country,
        "countryCode": country_code,
        "region": region,
        "regionName": region_name,
        "city": city
    }
