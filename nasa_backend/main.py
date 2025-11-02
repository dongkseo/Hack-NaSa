from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import os
import firebase_admin
from firebase_admin import credentials, messaging



TOKEN_FILE = "tokens.json"


def load_tokens():
    """JSON 파일에서 토큰 로드"""
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

active_tokens = load_tokens()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # Startup
    print("🚀 Bluetooth Hybrid API Server Starting...")
    # Firebase Admin 초기화
    if not firebase_admin._apps:
        cred = credentials.Certificate("nasa-2b926-588694529dd9.json")
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin initialized")
    yield
    # Shutdown
    print("🛑 Bluetooth Hybrid API Server Shutting down...")

app = FastAPI(
    title="Bluetooth Hybrid Control API",
    description="macOS Bluetooth 장치 및 미디어 제어 REST API (v2)",
    version="2.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FCMRequest(BaseModel):
    token: str
    user_id: str = "default"

class SendMessageRequest(BaseModel):
    user_id: str
    title: str
    body: str
    data_message: Optional[dict] = None


def save_tokens(tokens):
    """토큰을 JSON 파일에 저장"""
    with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)
    print(f"✅ Tokens saved to {TOKEN_FILE}")

active_tokens = load_tokens()

@app.post("/api/fcm/register-token")
async def register_token(request: FCMRequest):
    """토큰 등록 (메모리에만 저장)"""
    active_tokens[request.user_id] = request.token
    print(f"Token registered: {request.user_id} -> {request.token[:20]}...")
    save_tokens(active_tokens)
    return {"message": "Token registered"}

@app.post("/api/fcm/send-to-user")
async def send_to_user(request: SendMessageRequest):
    """메모리의 토큰으로 즉시 전송"""
    print(f"User ID: {request.user_id}")
    print(f"Title: {request.title}")
    print(f"Body: {request.body}")
    
    token = active_tokens.get(request.user_id)
    if not token:
        return {"error": "No token found for user"}
    
    # Firebase Admin SDK를 사용한 메시지 전송
    message = messaging.Message(
        notification=messaging.Notification(
            title=request.title,
            body=request.body,
        ),
        data=request.data_message if request.data_message else {},
        token=token
    )
    
    try:
        response = messaging.send(message)
        print(f"✅ Successfully sent message: {response}")
        return {"status": "sent", "message_id": response}
    except Exception as e:
        print(f"❌ Error sending message: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/api/fcm/tokens")
async def get_all_tokens():
    """현재 등록된 모든 토큰 조회"""
    if not active_tokens:
        return {
            "total_users": 0,
            "message": "No tokens registered",
            "users": []
        }
    
    return {
        "total_users": len(active_tokens),
        "users": list(active_tokens.keys()),
        "tokens": active_tokens  # 전체 토큰 목록
    }

@app.get("/api/fcm/tokens/{user_id}")
async def get_user_token(user_id: str):
    """특정 사용자의 토큰 조회"""
    token = active_tokens.get(user_id)
    
    if not token:
        return {
            "error": f"No token found for user: {user_id}",
            "user_id": user_id
        }
    
    return {
        "user_id": user_id,
        "token": token,
        "token_preview": f"{token[:20]}...{token[-10:]}"  # 앞뒤 일부만 표시
    }

import api.bluetooth  # noqa