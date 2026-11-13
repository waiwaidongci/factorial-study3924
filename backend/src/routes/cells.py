from fastapi import APIRouter,Depends
from src.config.database import get_db
from src.utils.auth import current_user
from src.schemas.cell import CellSummary
from src.controllers.cell_controller import list_cells
router=APIRouter(prefix='/cells')
@router.get('',response_model=list[CellSummary])
def index(study_id:int,db=Depends(get_db),user=Depends(current_user)):return list_cells(db,study_id)
