import time
from celery import Celery

celery_app = Celery(
    "gadget_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery_app.task(bind=True)
def recalculate_market_stats(self, marketplace_id: int):
    for progress in range(1, 101, 25):
        time.sleep(3)
        self.update_state(state='PROCESSING', meta={'progress_percent': progress})

    return {
        "status": "success",
        "marketplace_id": marketplace_id,
        "message": "Статистика цен успешно пересчитана"
    }
