from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, List
from ..models import ValidationResult

class BaseRule(ABC):
    """
    Abstract base class for all rules in DCVPG (both core and custom user rules).
    Users extend this class and override the `validate` method.
    """

    def __init__(self):
        pass

    @abstractmethod
    def validate(self, data: pd.DataFrame, field: str, params: Dict[str, Any]) -> ValidationResult:
        """
        Executes the rule against the provided DataFrame.

        Args:
            data (pd.DataFrame): The incoming batch data.
            field (str): The column/field the rule applies to.
            params (dict): Parameters for this specific rule invocation.

        Returns:
            ValidationResult: The result indicating pass/fail and details of any violations.
        """
        pass
