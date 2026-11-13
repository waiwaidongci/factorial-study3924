from datetime import datetime
from sqlalchemy import String,ForeignKey,DateTime
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
class FollowupPlan(Base):
    __tablename__='followup_plans'
    id:Mapped[int]=mapped_column(primary_key=True)
    title:Mapped[str]=mapped_column(String(160),unique=True)
    run_id:Mapped[int]=mapped_column(ForeignKey('factor_runs.id'))
    contrast_index:Mapped[int]
    action:Mapped[str]=mapped_column(String(1200))
    verification:Mapped[str]=mapped_column(String(1200))
    status:Mapped[str]=mapped_column(String(20),default='draft')
    approved_by:Mapped[str]=mapped_column(String(160),default='')
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
