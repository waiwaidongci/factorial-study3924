from enum import StrEnum
class Role(StrEnum):
    ADMIN='admin'
    ANALYST='analyst'
    VIEWER='viewer'
class RunStatus(StrEnum):
    QUEUED='queued'
    RUNNING='running'
    COMPLETED='completed'
    FAILED='failed'
class PlanStatus(StrEnum):
    DRAFT='draft'
    APPROVED='approved'
CONTRAST_FAMILY='all_simple_pairwise'
