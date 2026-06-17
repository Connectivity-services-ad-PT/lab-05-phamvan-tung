import os
import httpx
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="B5 - Analytics Service")

IOT_SERVICE_URL = os.getenv("IOT_SERVICE_URL", "http://localhost:8001")
VISION_SERVICE_URL = os.getenv("VISION_SERVICE_URL", "http://localhost:8004")

# Endpoint /health bắt buộc theo yêu cầu của thầy
@app.get("/health", status_code=200)
async def health_check():
    return {
        "status": "ok",
        "service": "B5 - Analytics Service"
    }

# Endpoint tổng hợp dữ liệu từ các nhóm đối tác
@app.get("/api/v1/analytics/summary")
async def get_campus_summary():
    iot_data = {}
    vision_data = {}

    async with httpx.AsyncClient() as client:
        # Gọi sang IoT B1 (Timeout 5 giây chống treo)
        try:
            response = await client.get(f"{IOT_SERVICE_URL}/health", timeout=5.0)
            iot_data = {"status": "connected"} if response.status_code == 200 else {"status": "error"}
        except (httpx.TimeoutException, httpx.RequestError):
            iot_data = {"status": "unavailable"}

        # Gọi sang AI Vision B4 (Timeout 5 giây chống treo)
        try:
            response = await client.get(f"{VISION_SERVICE_URL}/health", timeout=5.0)
            vision_data = {"status": "connected"} if response.status_code == 200 else {"status": "error"}
        except (httpx.TimeoutException, httpx.RequestError):
            vision_data = {"status": "unavailable"}

    return {
        "analytics_target": "Smart Campus Operations",
        "dependencies": {"B1_iot": iot_data, "B4_vision": vision_data},
        "summary": {"total_energy_kwh": 4550, "campus_population": 1500}
    }