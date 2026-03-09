import pandas as pd
import os
import tempfile
from dcvpg.orchestrators.airflow.operators.contract_validator import DataContractValidatorOperator

# A minimal integration test using Airflow Operator without actually starting a DAG

def test_airflow_operator_integration():
    # Setup dummy directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create config
        config_path = os.path.join(temp_dir, 'dcvpg.config.yaml')
        contracts_dir = os.path.join(temp_dir, 'contracts')
        data_dir = os.path.join(temp_dir, 'data')
        os.makedirs(contracts_dir)
        os.makedirs(data_dir)
        
        with open(config_path, 'w') as f:
             f.write(f'''project:
  name: integration_test
  team: de
  environment: test
contracts:
  directory: {contracts_dir}
connections:
  - name: test_csv
    type: file
    path: {data_dir}
    file_type: csv
database:
  host: localhost
  port: 5432
  name: dcvpg
  user: user
  password: pass
alerting:
  default_severity_threshold: CRITICAL
''')
        
        # Create Contract
        contract_path = os.path.join(contracts_dir, 'test_contract.yaml')
        with open(contract_path, 'w') as f:
             f.write('''contract:
  name: test_contract
  version: "1.0"
  owner_team: DE
  source_owner: BE
  source_connection: test_csv
  source_table: test.csv
  schema:
    - field: id
      type: integer
      nullable: false
    - field: email
      type: string
''')
             
        # Create Data
        data_path = os.path.join(data_dir, 'test.csv')
        df = pd.DataFrame({'id': [1, 2], 'email': ['a@a.com', 'b@b.com']})
        df.to_csv(data_path, index=False)
        
        # Instantiate Operator
        operator = DataContractValidatorOperator(
             task_id='validate_test_contract',
             contract='test_contract',
             source_conn='test_csv',
             config_path=config_path,
             on_failure='quarantine_and_alert'
        )
        
        # Mock Airflow Context
        context = {
             'run_id': 'test-run-123'
        }
        
        # Execute (should pass and return dict)
        report_dict = operator.execute(context)
        
        assert report_dict['status'] == 'PASSED'
        assert report_dict['rows_processed'] == 2
        assert report_dict['violations_count'] == 0
