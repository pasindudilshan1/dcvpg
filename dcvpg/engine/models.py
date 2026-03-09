from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class FieldSpec(BaseModel):
    field: str
    type: str
    nullable: bool = True
    unique: bool = False
    min: Optional[float] = None
    max: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    format: Optional[str] = None
    allowed_values: Optional[List[Any]] = None
    description: Optional[str] = None

class CustomRuleSpec(BaseModel):
    rule: str
    params: Optional[Dict[str, Any]] = None

class ContractSpec(BaseModel):
    name: str
    version: str
    owner_team: str
    source_owner: str
    source_connection: str
    source_table: Optional[str] = None
    schema_fields: List[FieldSpec] = Field(..., alias="schema")
    description: Optional[str] = None
    sla_freshness_hours: Optional[int] = None
    pipeline_tags: Optional[List[str]] = None
    row_count_min: Optional[int] = None
    row_count_max: Optional[int] = None
    custom_rules: Optional[List[CustomRuleSpec]] = None

class ContractSpecWrapper(BaseModel):
    contract: ContractSpec

class ValidationResult(BaseModel):
    passed: bool
    field: Optional[str] = None
    violation_type: Optional[str] = None
    rows_affected: Optional[int] = None
    sample_values: Optional[List[Any]] = None
    expected_value: Optional[str] = None

class ValidationReport(BaseModel):
    pipeline_name: str
    contract_name: str
    contract_version: str
    status: str
    rows_processed: int
    violations_count: int
    duration_ms: int
    violation_details: List[ValidationResult]

class QuarantineEvent(BaseModel):
    pipeline_name: str
    contract_name: str
    contract_version: str
    batch_id: str
    violation_type: str
    affected_field: str
    expected_value: Optional[str] = None
    actual_sample: Optional[str] = None
    rows_affected: int
    total_rows: int
