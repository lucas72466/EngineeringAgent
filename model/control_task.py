from typing import List, Optional
from pydantic import BaseModel, Field


class TaskSpecs(BaseModel):
    id: Optional[int] = Field(None, description="ID")
    num: List[float] = Field(..., description="Numerator")
    den: List[float] = Field(..., description="Denominator")
    tau: Optional[float] = Field(None, description="Time delay (tau), optional")
    phase_margin_min: float = Field(..., description="Minimum phase margin")
    settling_time_min: float = Field(..., description="Minimum settling time (seconds)")
    settling_time_max: float = Field(..., description="Maximum settling time (seconds)")
    steadystate_error_max: float = Field(..., description="Maximum steady-state error")
    scenario: str = Field(..., description="Scenario")

    def __init__(self, **data):
        super().__init__(**data)

    def __getitem__(self, key: str):
        # to support TaskSpecs['key'] operation
        return getattr(self, key)

    def validate_task(self):
        pass

    def construct_thresholds(self):
        thresholds = {
            'phase_margin': {'min': self.phase_margin_min,
                             'message': f'Phase margin should be at least {self.phase_margin_min} degrees.'},
            'settling_time_min': {'min': self.settling_time_min,
                                  'message': f'Settling time should be at least {self.settling_time_min} sec.'},
            'settling_time_max': {'max': self.settling_time_max,
                                  'message': f'Settling time should be at most {self.settling_time_max} sec.'},
            'steadystate_error': {'max': self.steadystate_error_max,
                                  'message': f'Steady state error should be at most {self.steadystate_error_max}.'}
        }

        return thresholds


class TaskDesignResult(BaseModel):
    parameters: dict = Field(..., description="output parameters")
    performance: dict = Field(..., description="output performance")
    conversation_round: int = Field(..., description="conversation round")


class FinalTaskDesignResult(BaseModel):
    used_agent: str = Field(..., description="used agent")
    is_success: bool = Field(..., description="final design success or not")
    design_history: List[TaskDesignResult] = Field(..., description="design history")
