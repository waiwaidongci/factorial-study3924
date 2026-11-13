from datetime import datetime
from sqlalchemy import String,ForeignKey,Double,JSON,DateTime
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
class FactorRun(Base):
    __tablename__='factor_runs'
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(160),unique=True)
    study_id:Mapped[int]=mapped_column(ForeignKey('factor_studies.id'))
    alpha:Mapped[float]=mapped_column(Double,default=.05)
    contrast_family:Mapped[str]=mapped_column(String(40),default='all_simple_pairwise')
    status:Mapped[str]=mapped_column(String(20),default='queued')
    result:Mapped[dict]=mapped_column(JSON,default=dict)
    error:Mapped[str]=mapped_column(String(600),default='')
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
