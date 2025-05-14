import os
import json
import logging
from fastapi import FastAPI, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG)

app = FastAPI()

# API key setup
API_KEY = "rigour-ip-checking-service"
API_KEY_NAME = "x-api-key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# API key validation
async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key == API_KEY:
        return api_key
    raise HTTPException(status_code=403, detail="Invalid or missing API Key")

# Google Sheets logging function
def log_to_google_sheets(project_id, respondent_id, ip_address, country, country_code, region, region_name, city):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # Read credentials from the environment variable
    creds_json = os.getenv('GOOGLE_SHEET_CREDENTIALS')

    # Log the environment variable to verify if it's being read correctly
    if creds_json is None:
        logging.error("Google Sheets credentials not found in environment variable.")
        raise HTTPException(status_code=500, detail="Google Sheets credentials not found in environment variable")

    try:
        creds_dict = json.loads(creds_json)  # Parse the JSON string to a dictionary
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse Google Sheets credentials: {str(e)}")
        raise HTTPException(status_code=500, detail="Error parsing Google Sheets credentials")

    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
    except Exception as e:
        logging.error(f"Error authenticating with Google Sheets: {str(e)}")
        raise HTTPException(status_code=500, detail="Error authenticating with Google Sheets")

    try:
        sheet = client.open("Rigour IP address checking").sheet1
        timestamp = datetime.utcnow().isoformat()
        sheet.append_row([
            project_id,
            respondent_id,
            ip_address,
            country,
            country_code,
            region,
            region_name,
            city,
            timestamp
        ])
    except Exception as e:
        logging.error(f"Error appending data to Google Sheets: {str(e)}")
        raise HTTPException(status_code=500, detail="Error appending data to Google Sheets")

# 🧑‍💻 Root endpoint to check API health
@app.get("/")
def read_root():
    return {"message": "IP Checker API is working!"}

# 🌍 IP check and log endpoint
@app.post("/ip-check")
async def ip_check(payload: dict, api_key: str = Security(get_api_key)):
    project_id = payload.get("project_id")
    respondent_id = payload.get("respondent_id")
    ip_address = payload.get("ip_address")

    geo_response = requests.get(f"http://ip-api.com/json/{ip_address}")
    geo_data = geo_response.json()

    country = geo_data.get("country", "Unknown")
    country_code = geo_data.get("countryCode", "Unknown")
    region = geo_data.get("region", "Unknown")
    region_name = geo_data.get("regionName", "Unknown")
    city = geo_data.get("city", "Unknown")

    # Log to Google Sheets
    log_to_google_sheets(
        project_id,
        respondent_id,
        ip_address,
        country,
        country_code,
        region,
        region_name,
        city
    )

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
