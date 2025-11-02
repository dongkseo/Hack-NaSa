"""
Connection Repository

WebSocket 연결 관리 Repository
"""
import logging
from datetime import datetime
from typing import List
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionRepository:
    """
    WebSocket 연결 관리 Repository

    연결 상태를 관리하고 통계를 수집
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.total_messages = 0
        self.last_message_time: datetime = None
        self.connected_at: datetime = None

    async def connect_client(self, websocket: WebSocket) -> None:
        """
        클라이언트 연결

        Args:
            websocket: WebSocket 연결
        """
        await websocket.accept()
        self.active_connections.append(websocket)

        if not self.connected_at:
            self.connected_at = datetime.now()

        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect_client(self, websocket: WebSocket) -> None:
        """
        클라이언트 연결 해제

        Args:
            websocket: WebSocket 연결
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        logger.info(f"Client disconnected. Remaining: {len(self.active_connections)}")

    def update_stats(self) -> None:
        """통계 업데이트"""
        self.total_messages += 1
        self.last_message_time = datetime.now()

    def get_connection_count(self) -> int:
        """현재 연결 수 조회"""
        return len(self.active_connections)

    def is_connected(self) -> bool:
        """연결 여부 확인"""
        return len(self.active_connections) > 0

    def get_stats(self) -> dict:
        """통계 조회"""
        uptime = None
        if self.connected_at:
            uptime_delta = datetime.now() - self.connected_at
            hours, remainder = divmod(int(uptime_delta.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime = f"{hours:02}:{minutes:02}:{seconds:02}"

        return {
            "active_connections": len(self.active_connections),
            "total_messages": self.total_messages,
            "last_message_time": self.last_message_time.isoformat() if self.last_message_time else None,
            "is_connected": self.is_connected(),
            "uptime": uptime,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None
        }

    def reset_stats(self) -> None:
        """통계 초기화"""
        self.total_messages = 0
        self.last_message_time = None
        self.connected_at = None if not self.is_connected() else self.connected_at
