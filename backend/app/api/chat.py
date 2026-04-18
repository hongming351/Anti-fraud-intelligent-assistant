from fastapi import APIRouter, BackgroundTasks
from app.services.risk_alert_service import RiskAlertService

router = APIRouter()

@router.post("/send_message")
async def send_message(
    request: MessageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    # ... 原有的对话逻辑 ...

    # 后台执行风险检测与短信联动
    background_tasks.add_task(
        RiskAlertService().process_user_message,
        current_user.id,
        request.message
    )

    return {"status": "ok"}