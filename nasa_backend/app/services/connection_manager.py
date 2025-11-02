# """
# WebSocket 연결 관리 서비스
# """
# from fastapi import WebSocket
# from typing import List
# from datetime import datetime
# from app.models.message import PredictionMessage, ResponseMessage, ConnectionInfo
# from app.services.action_mapper import action_mapper
# import time


# class ConnectionManager:
#     """WebSocket 연결을 관리하는 싱글톤 클래스"""

#     def __init__(self):
#         self.windows_clients: List[WebSocket] = []
#         self.connection_info = ConnectionInfo()

#     async def connect_windows(self, websocket: WebSocket):
#         """Windows 클라이언트 연결"""
#         await websocket.accept()
#         self.windows_clients.append(websocket)
#         self.connection_info.windows_connected = True
#         print(f"✅ Windows 클라이언트 연결됨 (총 {len(self.windows_clients)}개)")

#     def disconnect_windows(self, websocket: WebSocket):
#         """Windows 클라이언트 연결 해제"""
#         if websocket in self.windows_clients:
#             self.windows_clients.remove(websocket)
#         if len(self.windows_clients) == 0:
#             self.connection_info.windows_connected = False
#         print(f"❌ Windows 클라이언트 연결 해제 (남은 연결: {len(self.windows_clients)}개)")

#     async def process_prediction(self, message: PredictionMessage) -> ResponseMessage:
#         """Windows로부터 받은 행동 감지 결과 처리"""
#         self.connection_info.last_message_time = datetime.now().isoformat()
#         self.connection_info.total_messages += 1

#         print(f"📊 행동 감지 수신: ID={message.detected_action}, 신뢰도={message.confidence:.2%}")

#         # ActionMapper에게 처리 위임
#         actions_taken = await action_mapper.process_and_execute(
#             detected_action=message.detected_action,
#             confidence=message.confidence
#         )

#         result_message = f"Actions: {', '.join(actions_taken)}" if actions_taken else "No actions taken"

#         return ResponseMessage(
#             status="processed",
#             timestamp=time.time(),
#             message=result_message
#         )

#     def get_status(self) -> dict:
#         """현재 연결 상태 반환"""
#         return {
#             "windows_clients": len(self.windows_clients),
#             "connection_info": self.connection_info.model_dump(),
#             "timestamp": datetime.now().isoformat()
#         }


# # 싱글톤 인스턴스
# manager = ConnectionManager()