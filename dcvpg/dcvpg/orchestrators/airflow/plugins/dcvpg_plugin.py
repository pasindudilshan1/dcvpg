"""
DCVPG Airflow Plugin — registers the DCVPGValidateOperator and supporting sensors
as first-class Airflow components discoverable by the Airflow plugin manager.
"""
from __future__ import annotations

from airflow.plugins_manager import AirflowPlugin

from dcvpg.orchestrators.airflow.operators.contract_validator import DCVPGValidateOperator


class DCVPGPlugin(AirflowPlugin):
    """
    Airflow plugin that exposes DCVPG components in the Airflow UI and
    makes the custom operator importable via the standard Airflow plugin
    discovery mechanism.

    Drop this file (or the whole dcvpg package) into your Airflow
    ``$AIRFLOW_HOME/plugins/`` directory, or install the dcvpg Python
    package into the Airflow environment — the plugin manager will pick it
    up automatically.
    """

    name = "dcvpg"

    # Expose the operator so users can import it as:
    #   from airflow.operators.dcvpg import DCVPGValidateOperator
    operators = [DCVPGValidateOperator]

    # Future: sensors, hooks, macros, etc.
    sensors = []
    hooks = []
    macros = []
    flask_blueprints = []
    menu_links = []
    appbuilder_views = []
    appbuilder_menu_items = []
