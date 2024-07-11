import unittest
from bq_schema_sync.schema_sync import SchemaSync


class TestSchemaSync(unittest.TestCase):

    def setUp(self):
        self.schema_sync = SchemaSync(
            project_id='modified-antler-202212',
            dataset_id='monitoring_reporting',
            table_id='infrastructure',
            schema_path='../schemas/example_schema.yaml'
        )

    def test_load_schema(self):
        schema = self.schema_sync.load_schema()
        self.assertIsInstance(schema, dict)
        self.assertIn('fields', schema)

    def test_compare_schemas(self):
        differences = self.schema_sync.compare_schemas()
        self.assertIsInstance(differences, dict)


if __name__ == '__main__':
    unittest.main()
