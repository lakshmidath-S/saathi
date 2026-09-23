import requests

RAPIDAPI_KEY = "your_key_here"  # free tier, 100 calls/day

def query_vehicle(reg_number: str) -> dict:
    url = "https://rto-vehicle-information-verification-india.p.rapidapi.com/api/v1/rc/vehicleinfo"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "Content-Type": "application/json"
    }
    r = requests.post(url, json={"reg_no": reg_number}, headers=headers)
    return r.json()

def query_challan(reg_number: str) -> dict:
    # eChallan public endpoint
    url = f"https://echallan.parivahan.gov.in/index/accused-challan"
    # returns challan status
    pass
