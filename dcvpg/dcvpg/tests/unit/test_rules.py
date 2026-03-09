import pandas as pd
from engine.rules.schema_rules import SchemaPresenceRule
from engine.rules.quality_rules import NullabilityRule, RangeRule

def test_schema_presence():
    rule = SchemaPresenceRule()
    df = pd.DataFrame({'id': [1, 2], 'name': ['Alice', 'Bob']})
    
    # Passing case
    res1 = rule.validate(df, 'name', {})
    assert res1.passed is True
    
    # Failing case
    res2 = rule.validate(df, 'age', {})
    assert res2.passed is False
    assert res2.violation_type == "FIELD_MISSING"

def test_nullability_rule():
    rule = NullabilityRule()
    df = pd.DataFrame({'id': [1, 2], 'name': ['Alice', None]})
    
    # Nullable is True (default) -> Pass
    res1 = rule.validate(df, 'name', {'nullable': True})
    assert res1.passed is True
    
    # Nullable is False -> Fail because of "None"
    res2 = rule.validate(df, 'name', {'nullable': False})
    assert res2.passed is False
    assert res2.violation_type == "NULLABILITY_VIOLATION"
    assert res2.rows_affected == 1
    
    # Nullable is False, but data has no nulls -> Pass
    res3 = rule.validate(df, 'id', {'nullable': False})
    assert res3.passed is True

def test_range_rule():
    rule = RangeRule()
    df = pd.DataFrame({'age': [25, 30, 45]})
    
    res1 = rule.validate(df, 'age', {'min': 18, 'max': 60})
    assert res1.passed is True
    
    res2 = rule.validate(df, 'age', {'min': 30})
    assert res2.passed is False
    assert res2.rows_affected == 1 # 25 fails
    
    res3 = rule.validate(df, 'age', {'max': 40})
    assert res3.passed is False
    assert res3.rows_affected == 1 # 45 fails
