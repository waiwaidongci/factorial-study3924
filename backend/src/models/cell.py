from sqlalchemy import String,ForeignKey,UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
class TrialCell(Base):
    __tablename__='trial_cells'
    __table_args__=(UniqueConstraint('study_id','temperature','glaze'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    study_id:Mapped[int]=mapped_column(ForeignKey('factor_studies.id'))
    temperature:Mapped[str]=mapped_column(String(40))
    glaze:Mapped[str]=mapped_column(String(40))
