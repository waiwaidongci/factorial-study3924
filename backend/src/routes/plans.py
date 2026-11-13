from fastapi import APIRouter,Depends,Response
from src.config.database import get_db
from src.utils.auth import current_user,editor,admin
from src.schemas.plan import PlanInput
from src.controllers.plan_controller import list_plans,create_plan,approve_plan,export_plan
router=APIRouter(prefix='/plans')
@router.get('')
def index(db=Depends(get_db),user=Depends(current_user)):return list_plans(db)
@router.post('',status_code=201)
def create(data:PlanInput,db=Depends(get_db),user=Depends(editor)):return create_plan(db,data)
@router.patch('/{id}/approve')
def approve(id:int,db=Depends(get_db),user=Depends(admin)):return approve_plan(db,id,user)
@router.get('/{id}/export')
def export(id:int,db=Depends(get_db),user=Depends(current_user)):return Response(export_plan(db,id),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':f'attachment; filename="factorial-plan-{id}.csv"'})
