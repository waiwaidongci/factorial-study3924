from sqlalchemy import String,ForeignKey,Double,UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column
from src.config.database import Base
class TrialReading(Base):
    __tablename__='trial_readings'
    __table_args__=(UniqueConstraint('study_id','specimen_code'),)
    id:Mapped[int]=mapped_column(primary_key=True)
    study_id:Mapped[int]=mapped_column(ForeignKey('factor_studies.id'))
    cell_id:Mapped[int]=mapped_column(ForeignKey('trial_cells.id'))
    specimen_code:Mapped[str]=mapped_column(String(80))
    strength_mpa:Mapped[float]=mapped_column(Double)
