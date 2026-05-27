import asyncio
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List

from . import models, schemas
from .database import engine, get_db_session

from celery.result import AsyncResult
from .worker import recalculate_market_stats

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Gadget Price Tracker API")

@app.post("/marketplaces/", response_model=schemas.MarketplaceResponse, status_code=status.HTTP_201_CREATED)
def register_new_marketplace(store: schemas.MarketplaceCreate, db: Session = Depends(get_db_session)):
    db_store = models.Marketplace(**store.model_dump())
    db.add(db_store)
    db.commit()
    db.refresh(db_store)
    return db_store

@app.get("/marketplaces/", response_model=List[schemas.MarketplaceResponse])
def fetch_all_marketplaces(db: Session = Depends(get_db_session)):
    return db.query(models.Marketplace).all()

@app.post("/gadgets/", response_model=schemas.GadgetResponse, status_code=status.HTTP_201_CREATED)
def add_new_gadget(gadget: schemas.GadgetCreate, db: Session = Depends(get_db_session)):
    db_gadget = models.Gadget(**gadget.model_dump())
    db.add(db_gadget)
    db.commit()
    db.refresh(db_gadget)
    return db_gadget

@app.get("/gadgets/", response_model=List[schemas.GadgetResponse])
def browse_gadgets(limit: int = 100, db: Session = Depends(get_db_session)):
    return db.query(models.Gadget).limit(limit).all()

@app.get("/gadgets/{target_id}", response_model=schemas.GadgetResponse)
def retrieve_gadget_details(target_id: int, db: Session = Depends(get_db_session)):
    item = db.query(models.Gadget).filter(models.Gadget.id == target_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Гаджет с запрошенным ID не обнаружен в базе")
    return item

@app.put("/gadgets/{target_id}", response_model=schemas.GadgetResponse)
def rewrite_gadget_info(target_id: int, payload: schemas.GadgetUpdate, db: Session = Depends(get_db_session)):
    item = db.query(models.Gadget).filter(models.Gadget.id == target_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Невозможно обновить: гаджет не найден")
    
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    
    db.commit()
    db.refresh(item)
    return item

@app.patch("/gadgets/{target_id}/price", response_model=schemas.GadgetResponse)
def adjust_gadget_price(target_id: int, payload: schemas.GadgetPartialUpdate, db: Session = Depends(get_db_session)):
    item = db.query(models.Gadget).filter(models.Gadget.id == target_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Товар не найден для изменения цены")
    
    if payload.current_price is not None:
        item.current_price = payload.current_price
        
    db.commit()
    db.refresh(item)
    return item

@app.delete("/gadgets/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_gadget_from_catalog(target_id: int, db: Session = Depends(get_db_session)):
    item = db.query(models.Gadget).filter(models.Gadget.id == target_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Удаление отменено: объект отсутствует")
    
    db.delete(item)
    db.commit()
    return None

@app.post("/gadgets/{target_id}/prices", response_model=schemas.PriceHistoryResponse)
def log_price_change(target_id: int, record: schemas.PriceHistoryCreate, db: Session = Depends(get_db_session)):
    if not db.query(models.Gadget).filter(models.Gadget.id == target_id).first():
        raise HTTPException(status_code=404, detail="Нельзя добавить цену несуществующему гаджету")

    new_record = models.PriceHistory(gadget_id=target_id, **record.model_dump())
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record

@app.get("/gadgets/{target_id}/prices", response_model=List[schemas.PriceHistoryResponse])
def get_price_timeline(target_id: int, db: Session = Depends(get_db_session)):
    return db.query(models.PriceHistory).filter(models.PriceHistory.gadget_id == target_id).all()

@app.post("/tasks/recalc-stats/{market_id}", tags=["Background Tasks"])
def trigger_stats_recalculation(market_id: int):
    task = recalculate_market_stats.delay(market_id)
    return {
        "task_id": task.id, 
        "status": "Задание успешно добавлено в фоновую очередь"
    }

@app.get("/tasks/{task_id}", tags=["Background Tasks"])
def check_task_status(task_id: str):
    task_result = AsyncResult(task_id, app=recalculate_market_stats.app)
    
    response = {
        "task_id": task_id,
        "current_state": task_result.state,
    }
    
    if task_result.state == 'PROCESSING':
        response['details'] = task_result.info
    elif task_result.state == 'SUCCESS':
        response['result'] = task_result.result
    elif task_result.state == 'FAILURE':
        response['error'] = str(task_result.info)
        
    return response

@app.websocket("/ws/tasks/{task_id}")
async def websocket_task_status(websocket: WebSocket, task_id: str):
    await websocket.accept()
    try:
        while True:
            task_result = AsyncResult(task_id, app=recalculate_market_stats.app)
            
            message = {
                "task_id": task_id,
                "status": task_result.state,
            }
            
            if task_result.state == 'PROCESSING':
                message["progress"] = task_result.info.get("progress_percent", 0)
            elif task_result.state == 'SUCCESS':
                message["result"] = task_result.result
            elif task_result.state == 'FAILURE':
                message["error"] = str(task_result.info)
            
            await websocket.send_json(message)
            
            if task_result.state in ['SUCCESS', 'FAILURE']:
                break
                
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        print(f"Клиент отключился от сокета (задача {task_id})")
    finally:
        if websocket.client_state.name != "DISCONNECTED":
            await websocket.close()
