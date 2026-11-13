import csv,io
from sqlalchemy import select
from fastapi import HTTPException
from src.models import FactorRun,FollowupPlan
from src.constants.enums import RunStatus,PlanStatus
def list_plans(db):return db.scalars(select(FollowupPlan).order_by(FollowupPlan.id.desc())).all()
def create_plan(db,data):
    run=db.get(FactorRun,data.run_id)
    if not run or run.status!=RunStatus.COMPLETED:raise HTTPException(422,'请选择已完成分析')
    if data.contrast_index>len(run.result['contrasts']):raise HTTPException(422,'对比索引不属于固定家族')
    if db.scalar(select(FollowupPlan).where(FollowupPlan.title==data.title)):raise HTTPException(409,'提案标题已存在')
    item=FollowupPlan(**data.model_dump(),status=PlanStatus.DRAFT);db.add(item);db.commit();return item
def approve_plan(db,id,user):
    item=db.get(FollowupPlan,id)
    if not item:raise HTTPException(404,'后续实验提案不存在')
    item.status=PlanStatus.APPROVED;item.approved_by=user.email;db.commit();return item
def export_plan(db,id):
    item=db.get(FollowupPlan,id)
    if not item:raise HTTPException(404,'提案不存在')
    if item.status!=PlanStatus.APPROVED:raise HTTPException(409,'负责人审批后才能交付')
    run=db.get(FactorRun,item.run_id);out=io.StringIO();out.write('\ufeff');writer=csv.writer(out)
    writer.writerow(['row_type','term','df','SS','F','p_raw','p_holm','difference','ci_low','ci_high','selected_followup','plan_title','action','verification','fingerprint'])
    def safe(v):
        v=str(v);return "'"+v if v.startswith(('=','+','-','@','\t','\r')) else v
    tail=[safe(item.title),safe(item.action),safe(item.verification),run.result['fingerprint']]
    for r in run.result['anova']:writer.writerow(['ANOVA',r['label'],r['df'],r['ss'],r['f'],r['p'],'','','','','',*tail])
    for r in run.result['contrasts']:writer.writerow(['simple_effect',safe(f"{r['condition_factor']}={r['condition']}：{r['left']}−{r['right']}"),run.result['df_error'],'','',r['p_raw'],r['p_holm'],r['estimate'],r['ci_low'],r['ci_high'],r['index']==item.contrast_index,*tail])
    return out.getvalue()
