import os
import click
import shutil

@click.command()
@click.argument('project_name')
def init(project_name):
    """Scaffold a new DCVPG user project."""
    
    if os.path.exists(project_name):
        click.echo(f"Error: Directory '{project_name}' already exists.")
        return

    # Scaffold directories
    dirs = [
        "contracts/services",
        "contracts/_schema",
        "custom_connectors",
        "custom_rules",
        "pipelines/airflow",
        "pipelines/prefect",
        "pipelines/dagster",
        "tests",
        ".github/workflows"
    ]
    
    for d in dirs:
        os.makedirs(os.path.join(project_name, d), exist_ok=True)
        # Add __init__.py for Python modules
        if "custom" in d or "pipelines" in d:
             open(os.path.join(project_name, d, "__init__.py"), "w").close()

    # Base path of framework templates
    # In a real package, this would use pkg_resources or importlib.resources
    # We map relative to cli currently
    script_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(script_dir, "../../templates")
    config_dir = os.path.join(script_dir, "../../config")
    
    # 1. dcvpg.config.yaml
    src_config = os.path.join(templates_dir, "dcvpg.config.yaml.template")
    if os.path.exists(src_config):
        dest_config = os.path.join(project_name, "dcvpg.config.yaml")
        # Replace template name placeholder
        with open(src_config, "r") as f:
            content = f.read().replace("my-data-platform", project_name)
        with open(dest_config, "w") as f:
            f.write(content)

    # 2. Add an example contract
    src_contract = os.path.join(templates_dir, "contract.yaml.template")
    if os.path.exists(src_contract):
        shutil.copy(src_contract, os.path.join(project_name, "contracts/services/example_contract.yaml"))

    # 3. Add JSON schema to _schema folder to help IDEs
    src_schema = os.path.join(config_dir, "contract.schema.json")
    if os.path.exists(src_schema):
         shutil.copy(src_schema, os.path.join(project_name, "contracts/_schema/contract.schema.json"))
         
    # 4. Custom module templates
    src_conn = os.path.join(templates_dir, "custom_connector.py.template")
    src_rule = os.path.join(templates_dir, "custom_rule.py.template")
    if os.path.exists(src_conn): shutil.copy(src_conn, os.path.join(project_name, "custom_connectors/example_connector.py"))
    if os.path.exists(src_rule): shutil.copy(src_rule, os.path.join(project_name, "custom_rules/example_rule.py"))

    # 5. Orchestrator DAG / flow templates
    src_airflow = os.path.join(templates_dir, "airflow_dag.py.template")
    src_prefect = os.path.join(templates_dir, "prefect_flow.py.template")
    if os.path.exists(src_airflow):
        shutil.copy(src_airflow, os.path.join(project_name, "pipelines/airflow/example_dag.py"))
    if os.path.exists(src_prefect):
        shutil.copy(src_prefect, os.path.join(project_name, "pipelines/prefect/example_flow.py"))

    # 6. GitHub Actions CI workflow
    src_workflow = os.path.join(templates_dir, "github_workflow.yml.template")
    if os.path.exists(src_workflow):
        shutil.copy(src_workflow, os.path.join(project_name, ".github/workflows/validate_contracts.yml"))

    # Print success output
    click.echo(f"\n✅ Created project: {project_name}/\n")
    click.echo("  ✅ dcvpg.config.yaml          (master config — edit this first)")
    click.echo("  ✅ contracts/                 (put your contract YAMLs here)")
    click.echo("  ✅ contracts/_schema/         (JSON Schema for YAML validation)")
    click.echo("  ✅ custom_connectors/         (extend for your proprietary sources)")
    click.echo("  ✅ custom_rules/              (extend for your business-specific rules)")
    click.echo("\nNext steps:")
    click.echo(f"  1. cd {project_name}")
    click.echo("  2. Edit dcvpg.config.yaml — add your data source connections")
    click.echo("  3. Run: dcvpg generate --source <your-db-connection> --table <table_name>")
    click.echo("  4. Review the generated contract YAML in contracts/services/")
    click.echo("  5. Run: dcvpg validate --all")
    click.echo("  6. Add DataContractValidatorOperator to your first pipeline")
