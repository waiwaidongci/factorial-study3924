from datetime import datetime
from sqlalchemy import String,JSON,DateTime
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
class FactorStudy(Base):
    __tablename__='factor_studies'
    id:Mapped[int]=mapped_column(primary_key=True)
    code:Mapped[str]=mapped_column(String(60),unique=True)
    name:Mapped[str]=mapped_column(String(160))
    a_levels:Mapped[list]=mapped_column(JSON)
    b_levels:Mapped[list]=mapped_column(JSON)
    source_file:Mapped[str]=mapped_column(String(160))
    note:Mapped[str]=mapped_column(String(600),default='')
    created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
