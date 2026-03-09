import sys
import os

# Add framework to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from config.config_loader import load_config
from engine.registry import ContractRegistry
from engine.validator import Validator
from engine.connectors.file_connector import FileConnector

def main():
    config_path = os.path.join(os.path.dirname(__file__), 'dcvpg.config.yaml')
    # Generate a dummy config and contract on the fly for the standalone example
    create_dummy_files()
    
    # 1. Load config
    config = load_config(config_path)
    
    # 2. Get the contract definition
    registry = ContractRegistry(config.contracts.directory)
    contract_spec = registry.get_contract('users_raw')
    
    # 3. Connect to source (FileConnector used here for simplicity)
    conn_config = next((c for c in config.connections if c.name == 'local_csvs'), None)
    connector = FileConnector()
    connector.connect(conn_config.model_dump())
    
    # 4. Fetch the batch
    print("Fetching batch from users.csv...")
    df = connector.fetch_batch(source='users.csv', batch_id='run-001')
    
    # 5. Validate the batch
    print("Validating batch against users_raw contract...")
    engine = Validator(contract_spec, custom_rules_dir=None)
    report = engine.validate_batch(df, pipeline_name="standalone_users_pipeline")
    
    # 6. Check results
    if report.status == "FAILED":
        print(f"PIPELINE HALTED: Found {report.violations_count} contract violations!")
        for v in report.violation_details:
             print(f" -> Field: {v.field} | Violation: {v.violation_type} | Expected: {v.expected_value}")
    else:
        print("PIPELINE PASSED. Proceeding to target warehouse.")

def create_dummy_files():
    # Setup dummy directory layout
    os.makedirs('examples/standalone_project/contracts', exist_ok=True)
    os.makedirs('examples/standalone_project/data', exist_ok=True)
    
    # Write dummy CSV
    with open('examples/standalone_project/data/users.csv', 'w') as f:
        f.write("id,email,age,status\n1,alice@example.com,25,active\n2,bob,30,pending\n3,charlie@example.com,15,active\n")
        
    # Write config
    with open('examples/standalone_project/dcvpg.config.yaml', 'w') as f:
        f.write('''project:
  name: standalone_demo
  team: de
  environment: dev
contracts:
  directory: ./examples/standalone_project/contracts
connections:
  - name: local_csvs
    type: file
    path: ./examples/standalone_project/data
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
        
    # Write contract (using some quality rules to trigger a failure intentionally)
    with open('examples/standalone_project/contracts/users_raw.yaml', 'w') as f:
        f.write('''contract:
  name: users_raw
  version: "1.0"
  owner_team: DE
  source_owner: BE
  source_connection: local_csvs
  schema:
    - field: id
      type: integer
      nullable: false
    - field: email
      type: string
      format: email
    - field: age
      type: integer
      min: 18
    - field: status
      type: string
      allowed_values: [active, pending, suspended]
''')

if __name__ == "__main__":
    main()
