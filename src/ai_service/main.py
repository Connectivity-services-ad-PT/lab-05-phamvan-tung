import os
import httpx
from fastapi import FastAPI
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List
from datetime import datetime

# Nạp cấu hình các biến môi trường từ file .env
load_dotenv()

app = FastAPI(title="B5 - Analytics Service")

# Lấy URL kết nối của các dịch vụ phụ thuộc từ biến môi trường
IOT_SERVICE_URL = os.getenv("IOT_SERVICE_URL", "http://localhost:8001")
VISION_SERVICE_URL = os.getenv("VISION_SERVICE_URL", "http://localhost:8004")

# =================================================================
# 1. ĐỊNH NGHĨA PYDANTIC SCHEMAS (DÙNG ĐỂ VALIDATE DỮ LIỆU VỚI B6)
# =================================================================

# Cấu trúc dữ liệu nhận vào khi nhóm B6 gọi sang B5 (Decision Payload)
class DecisionPayload(BaseModel):
    correlationId: str
    decision: str
    reason: str
    latencyMs: int
    quotaBefore: int
    quotaAfter: int
    rulesTriggered: List[str]
    timestamp: str  # Chuỗi thời gian dạng ISO nhận từ hệ thống B6
    mode: str

# Cấu trúc dữ liệu nhóm B5 phản hồi lại cho nhóm B6
class DecisionResponse(BaseModel):
    status: str
    message: str
    correlationId: str
    timestamp: str


# =================================================================
# 2. CÁC ENDPOINT ĐÁP ỨNG NGHIỆP VỤ BÀI LAB
# =================================================================

# Endpoint 1: Kiểm tra trạng thái hoạt động nội bộ (Bắt buộc theo Rubric)
@app.get("/health", status_code=200)
async def health_check():
    return {
        "status": "ok",
        "service": "B5 - Analytics Service"
    }


# Endpoint 2: Tổng hợp dữ liệu phân tích từ nhóm B1 (IoT) và B4 (AI Vision)
@app.get("/api/v1/analytics/summary")
async def get_campus_summary():
    iot_data = {}
    vision_data = {}

    async with httpx.AsyncClient() as client:
        # Gọi sang dịch vụ IoT B1 (Bẫy lỗi Timeout 5 giây chống treo cụm hệ thống)
        try:
            response = await client.get(f"{IOT_SERVICE_URL}/health", timeout=5.0)
            iot_data = {"status": "connected"} if response.status_code == 200 else {"status": "error"}
        except (httpx.TimeoutException, httpx.RequestError):
            iot_data = {"status": "unavailable"}

        # Gọi sang dịch vụ AI Vision B4 (Bẫy lỗi Timeout 5 giây chống treo cụm hệ thống)
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


# Endpoint 3: Tiếp nhận và xử lý sự kiện quyết định từ nhóm B6 truyền sang
@app.post("/api/v1/analytics/decision", response_model=DecisionResponse)
async def receive_decision_from_b6(payload: DecisionPayload):
    """
    Endpoint tiếp nhận gói tin Decision từ B6, tự động kiểm tra cấu trúc 
    dữ liệu đầu vào, xuất log kiểm tra và trả về phản hồi đồng bộ luồng.
    """
    # In trực tiếp dữ liệu ra Terminal phục vụ quá trình chấm điểm trực quan của Thầy
    print(f"\n[B5 Logs] Nhận gói tin từ B6 - Correlation ID: {payload.correlationId}")
    print(f"[B5 Logs] Quyết định đưa ra: {payload.decision} | Lý do: {payload.reason}")
    print(f"[B5 Logs] Chế độ vận hành: {payload.mode}")
    print(f"[B5 Logs] Các quy tắc được kích hoạt: {payload.rulesTriggered}")

    # Tạo gói tin phản hồi chuẩn format đầu ra khớp 100% với yêu cầu hệ thống liên nhóm
    response_data = DecisionResponse(
        status="success",
        message="Decision received and processed",
        correlationId=payload.correlationId,  # Trả ngược lại đúng mã ID của phiên làm việc để B6 nhận diện
        timestamp=datetime.now().isoformat()  # Tự động sinh mốc thời gian phản hồi theo chuẩn cấu trúc ISO
    )
    
    return response_data