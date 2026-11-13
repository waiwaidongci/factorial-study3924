from fastapi import APIRouter,Depends
from src.config.database import get_db
from src.utils.auth import current_user,editor
from src.schemas.study import StudyInput
from src.controllers.study_controller import list_studies,create_study
router=APIRouter(prefix='/studies')
@router.get('')
def index(db=Depends(get_db),user=Depends(current_user)):return list_studies(db)
@router.post('',status_code=201)
def create(data:StudyInput,db=Depends(get_db),user=Depends(editor)):return create_study(db,data)
