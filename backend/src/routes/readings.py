from fastapi import APIRouter,Depends,Query
from src.config.database import get_db
from src.utils.auth import current_user
from src.controllers.reading_controller import list_readings
router=APIRouter(prefix='/readings')
@router.get('')
def index(study_id:int,cell_id:int|None=None,offset:int=Query(default=0,ge=0),limit:int=Query(default=20,ge=1,le=200),db=Depends(get_db),user=Depends(current_user)):return list_readings(db,study_id,cell_id,offset,limit)
