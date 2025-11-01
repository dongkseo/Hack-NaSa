"""
Prediction Endpoints

예측 처리 WebSocket 엔드포인트
"""
import json
import time
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from app.core.dependencies import PredictionSvc, ConnectionRepo
from app.schemas.prediction import PredictionRequest, PredictionResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/predictions")
async def websocket_prediction_endpoint(
    websocket: WebSocket,
    prediction_service: PredictionSvc,
    connection_repo: ConnectionRepo
):
    """
    예측 WebSocket 엔드포인트

    Windows 클라이언트로부터 실시간 예측 결과를 수신하고 처리

    **프로토콜:**
    - Client → Server: PredictionRequest (JSON)
    - Server → Client: PredictionResponse (JSON)

    **Example Request:**
    ```json
    {
        "type": "prediction",
        "detected_action": 1,
        "confidence": 0.85,
        "timestamp": 1699876543.123
    }
    ```

    **Example Response:**
    ```json
    {
        "status": "success",
        "timestamp": 1699876543.456,
        "message": "Processed 2 actions",
        "actions_taken": ["speaker:alert", "phone:notify"]
    }
    ```
    """
    # 연결 수락
    await connection_repo.connect_client(websocket)
    logger.info("Client connected to WebSocket")

    try:
        while True:
            # 메시지 수신
            data = await websocket.receive_text()

            try:
                message_dict = json.loads(data)

                # Pydantic 스키마로 검증
                prediction_request = PredictionRequest(**message_dict)

                logger.info(
                    f"Received prediction: action={prediction_request.detected_action}, "
                    f"confidence={prediction_request.confidence:.2%}"
                )

                # 서비스를 통해 비즈니스 로직 실행
                result = await prediction_service.process_prediction(
                    detected_action=prediction_request.detected_action,
                    confidence=prediction_request.confidence,
                    timestamp=prediction_request.timestamp,
                    metadata=prediction_request.metadata
                )

                # 응답 생성 및 전송
                response = PredictionResponse(
                    status=result["status"],
                    timestamp=time.time(),
                    message=result["message"],
                    actions_taken=result.get("actions_taken", []),
                    prediction_info=result.get("prediction_info")
                )

                await websocket.send_json(response.model_dump())
                logger.debug(f"Sent response: {response.status}")

            except ValidationError as e:
                # 입력 검증 실패
                logger.error(f"Validation error: {e}")
                error_response = PredictionResponse(
                    status="error",
                    timestamp=time.time(),
                    message="Invalid request format",
                    actions_taken=[]
                )
                await websocket.send_json(error_response.model_dump())

            except json.JSONDecodeError as e:
                # JSON 파싱 실패
                logger.error(f"JSON decode error: {e}")
                error_response = PredictionResponse(
                    status="error",
                    timestamp=time.time(),
                    message="Invalid JSON format",
                    actions_taken=[]
                )
                await websocket.send_json(error_response.model_dump())

    except WebSocketDisconnect:
        logger.info("Client disconnected normally")
        connection_repo.disconnect_client(websocket)

    except Exception as e:
        logger.exception(f"Unexpected WebSocket error: {e}")
        connection_repo.disconnect_client(websocket)
