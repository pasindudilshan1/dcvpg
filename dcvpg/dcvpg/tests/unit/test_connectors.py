"""Unit tests for all data source connectors (mocked)."""
import pandas as pd
from unittest.mock import MagicMock, patch


class TestFileConnector:
    def test_connect_csv(self, tmp_path):
        from dcvpg.engine.connectors.file_connector import FileConnector
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("id,name\n1,Alice\n2,Bob\n")
        conn = FileConnector()
        conn.connect({"file_type": "csv"})
        df = conn.fetch_batch(source=str(csv_file), batch_id="test")
        assert len(df) == 2
        assert "id" in df.columns

    def test_connect_json(self, tmp_path):
        import json
        from dcvpg.engine.connectors.file_connector import FileConnector
        json_file = tmp_path / "data.json"
        records = [{"id": 1, "val": "a"}, {"id": 2, "val": "b"}]
        # Write as newline-delimited JSON (JSONL) — the format FileConnector expects
        json_file.write_text("\n".join(json.dumps(r) for r in records))
        conn = FileConnector()
        conn.connect({"file_type": "json"})
        df = conn.fetch_batch(source=str(json_file), batch_id="test")
        assert len(df) == 2

    def test_fetch_sample(self, tmp_path):
        from dcvpg.engine.connectors.file_connector import FileConnector
        csv_file = tmp_path / "big.csv"
        rows = "id,value\n" + "\n".join(f"{i},{i*2}" for i in range(200))
        csv_file.write_text(rows)
        conn = FileConnector()
        conn.connect({"file_type": "csv"})
        df = conn.fetch_sample(source=str(csv_file), sample_rows=50)
        assert len(df) <= 50


class TestPostgresConnector:
    def test_connect_builds_engine(self):
        from dcvpg.engine.connectors.postgres_connector import PostgresConnector
        conn = PostgresConnector()
        # connect() should not raise if sqlalchemy is available;
        # we mock the create_engine call to avoid needing a real DB
        with patch("dcvpg.engine.connectors.postgres_connector.create_engine") as mock_engine:
            mock_engine.return_value = MagicMock()
            conn.connect({
                "host": "localhost", "port": 5432,
                "name": "testdb", "user": "user", "password": "pass"
            })
            assert mock_engine.called

    def test_fetch_batch_returns_dataframe(self):
        from dcvpg.engine.connectors.postgres_connector import PostgresConnector
        conn = PostgresConnector()
        mock_engine = MagicMock()
        conn.engine = mock_engine
        with patch("pandas.read_sql") as mock_read_sql:
            mock_read_sql.return_value = pd.DataFrame({"id": [1, 2, 3]})
            df = conn.fetch_batch(source="orders", batch_id="test-123")
            assert len(df) == 3
            assert "id" in df.columns


class TestSchemaInference:
    def test_infer_schema_from_dataframe(self):
        from dcvpg.engine.reporting.schema_diff import infer_schema_from_dataframe
        df = pd.DataFrame({
            "id": pd.array([1, 2, 3], dtype="int64"),
            "name": ["a", "b", "c"],
            "price": [1.1, 2.2, 3.3],
            "active": [True, False, True],
        })
        schema = infer_schema_from_dataframe(df)
        fields = {f["field"]: f["type"] for f in schema}
        assert fields["id"] == "integer"
        assert fields["name"] == "string"
        assert fields["price"] == "float"
        assert fields["active"] == "boolean"


class TestSchemaDiff:
    def test_no_drift(self):
        from dcvpg.engine.reporting.schema_diff import compute_schema_diff
        schema = [{"field": "id", "type": "integer"}, {"field": "name", "type": "string"}]
        result = compute_schema_diff(schema, schema)
        assert result["has_drift"] is False
        assert result["added_fields"] == []
        assert result["removed_fields"] == []
        assert result["type_changed"] == {}

    def test_added_field(self):
        from dcvpg.engine.reporting.schema_diff import compute_schema_diff
        contract = [{"field": "id", "type": "integer"}]
        live = [{"field": "id", "type": "integer"}, {"field": "new_col", "type": "string"}]
        result = compute_schema_diff(contract, live)
        assert result["has_drift"] is True
        assert "new_col" in result["added_fields"]

    def test_removed_field(self):
        from dcvpg.engine.reporting.schema_diff import compute_schema_diff
        contract = [{"field": "id", "type": "integer"}, {"field": "old_col", "type": "string"}]
        live = [{"field": "id", "type": "integer"}]
        result = compute_schema_diff(contract, live)
        assert result["has_drift"] is True
        assert "old_col" in result["removed_fields"]

    def test_type_changed(self):
        from dcvpg.engine.reporting.schema_diff import compute_schema_diff
        contract = [{"field": "age", "type": "integer"}]
        live = [{"field": "age", "type": "string"}]
        result = compute_schema_diff(contract, live)
        assert result["has_drift"] is True
        assert "age" in result["type_changed"]
        assert result["type_changed"]["age"]["contract_type"] == "integer"
        assert result["type_changed"]["age"]["live_type"] == "string"
