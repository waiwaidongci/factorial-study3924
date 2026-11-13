import random,json
from sqlalchemy import select,func
from src.config.database import Base,engine,Session
from src.models import User,FactorStudy,TrialCell,TrialReading,FactorRun,FollowupPlan
from src.utils.security import hash_password
from src.services.run_service import execute_run

def seed():
    Base.metadata.create_all(engine);rng=random.Random(117)
    with Session() as db:
        for role,name in [('admin','陶焙 · 实验负责人'),('analyst','梁衡 · 材料分析员'),('viewer','程砚 · 工艺观察员')]:
            if not db.scalar(select(User).where(User.email==f'{role}@beiheng.demo')):db.add(User(email=f'{role}@beiheng.demo',name=name,role=role,password_hash=hash_password('Beiheng2026!')))
        levels_a=['1180','1220','1260'];levels_b=['薄釉','厚釉']
        for index,(code,name,means) in enumerate([('BH-INT','窑程A · 交互线索',[[49,56],[58,59],[65,60]]),('BH-ADD','窑程B · 加性对照',[[50,55],[58,63],[65,70]]),('BH-CONST','窑程C · 常量边界',[[42,42],[42,42],[42,42]])]):
            study=db.scalar(select(FactorStudy).where(FactorStudy.code==code))
            if not study:
                study=FactorStudy(code=code,name=name,a_levels=levels_a,b_levels=levels_b,source_file=f'bh-kiln-{code.lower()}.csv',note='3温度×2釉层，每格20个随机独立陶瓷试片，响应为抗折强度MPa；非重复测量。');db.add(study);db.flush()
                for i,a in enumerate(levels_a):
                    for j,b in enumerate(levels_b):
                        cell=TrialCell(study_id=study.id,temperature=a,glaze=b);db.add(cell);db.flush()
                        for k in range(20):db.add(TrialReading(study_id=study.id,cell_id=cell.id,specimen_code=f'BH{index+1}-{i+1}{j+1}-{k+1:02d}',strength_mpa=42. if index==2 else round(rng.gauss(means[i][j],1.8),5)))
                db.commit()
            runname=code+' · 预设全家族分析'
            if not db.scalar(select(FactorRun).where(FactorRun.name==runname)):
                run=FactorRun(name=runname,study_id=study.id,alpha=.05,contrast_family='all_simple_pairwise',status='queued');db.add(run);db.commit();execute_run(db,run.id)
        run=db.scalar(select(FactorRun).where(FactorRun.name=='BH-INT · 预设全家族分析'))
        if run and run.status=='completed' and not db.scalar(select(FollowupPlan).where(FollowupPlan.title=='中温段釉层差异的独立复烧')):
            db.add(FollowupPlan(title='中温段釉层差异的独立复烧',run_id=run.id,contrast_index=8,action='围绕1220°C薄釉与厚釉条件，重新随机分配独立试片并记录窑位与配料批次。',verification='另批试片复烧并保持独立观测；先核对残差与同方差前提，不把单个显著对比直接作为量产定论。',status='approved',approved_by='admin@beiheng.demo'))
        db.commit();print(json.dumps({m.__tablename__:db.scalar(select(func.count()).select_from(m)) for m in (User,FactorStudy,TrialCell,TrialReading,FactorRun,FollowupPlan)},ensure_ascii=False))
if __name__=='__main__':seed()
