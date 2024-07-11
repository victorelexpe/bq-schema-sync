import argparse
import yaml
import logging
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError
from bq_schema_sync.schema_sync import SchemaSync

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_config():
    template_config = {
        'project_id': 'your-gcp-project-id',
        'dataset_id': 'your-dataset-id',
        'table_id': 'your-table-id',
        # 'service_account_key_path': '/path/to/service-account-key.json',
        'schema': {
            'fields': [
                {'name': 'id', 'type': 'STRING', 'mode': 'REQUIRED', 'description': 'Unique identifier'},
                {'name': 'created_at', 'type': 'TIMESTAMP', 'mode': 'NULLABLE', 'description': 'Record creation timestamp'}
            ]
        }
    }

    with open('config.yaml', 'w') as file:
        yaml.dump(template_config, file, default_flow_style=False)
    logger.info("Template config.yaml created successfully.")

def validate_config(config):
    required_fields = ['project_id', 'dataset_id', 'table_id', 'schema']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required configuration field: {field}")

    if 'fields' not in config['schema']:
        raise ValueError("Missing 'fields' in schema configuration")

def main():
    parser = argparse.ArgumentParser(description='BigQuery Schema Sync Tool')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    subparsers = parser.add_subparsers(dest='command')

    # Initialize config command
    subparsers.add_parser('init', help='Initialize configuration file')

    # Compare schemas command
    compare_parser = subparsers.add_parser('compare', help='Compare schemas')
    compare_parser.add_argument('--config', type=str, required=True, help='Path to the config file')
    compare_parser.add_argument('--dry-run', action='store_true', help='Enable dry run mode')

    # Apply changes command
    apply_parser = subparsers.add_parser('apply', help='Apply schema changes')
    apply_parser.add_argument('--config', type=str, required=True, help='Path to the config file')
    apply_parser.add_argument('--dry-run', action='store_true', help='Enable dry run mode')

    # Generate migration script command
    generate_parser = subparsers.add_parser('generate-script', help='Generate migration script')
    generate_parser.add_argument('--config', type=str, required=True, help='Path to the config file')
    generate_parser.add_argument('--output', type=str, required=True, help='Path to the output SQL file')

    # Validate schema command
    validate_parser = subparsers.add_parser('validate', help='Validate schema')
    validate_parser.add_argument('--config', type=str, required=True, help='Path to the config file')

    # Save schema version command
    save_version_parser = subparsers.add_parser('save-version', help='Save the current schema version')
    save_version_parser.add_argument('--config', type=str, required=True, help='Path to the config file')
    save_version_parser.add_argument('--description', type=str, required=True, help='Description of the schema change')

    # List schema versions command
    list_versions_parser = subparsers.add_parser('list-versions', help='List all saved schema versions')
    list_versions_parser.add_argument('--config', type=str, required=True, help='Path to the config file')

    # Apply schema version command
    apply_version_parser = subparsers.add_parser('apply-version', help='Apply a specific schema version')
    apply_version_parser.add_argument('--config', type=str, required=True, help='Path to the config file')
    apply_version_parser.add_argument('--version', type=int, required=True, help='Version number to apply')

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    try:
        if args.command is None:
            parser.print_help()
        elif args.command == 'init':
            init_config()
        else:
            with open(args.config, 'r') as file:
                config = yaml.safe_load(file)

            try:
                validate_config(config)
            except ValueError as e:
                logger.error(e)
                return

            client_kwargs = {}
            if 'service_account_key_path' in config:
                client_kwargs['credentials'] = bigquery.Credentials.from_service_account_file(
                    config['service_account_key_path']
                )

            client = bigquery.Client(project=config['project_id'], **client_kwargs)

            schema_sync = SchemaSync(
                project_id=config['project_id'],
                dataset_id=config['dataset_id'],
                table_id=config['table_id'],
                schema=config['schema'],
                client=client,
                dry_run=args.dry_run
            )

            if args.command == 'compare':
                differences = schema_sync.compare_schemas()
                logger.info("Schema Differences: %s", differences)
            elif args.command == 'apply':
                schema_sync.apply_changes()
                if args.dry_run:
                    logger.info("Dry run mode: No changes applied.")
                else:
                    logger.info("Schema changes applied successfully.")
            elif args.command == 'generate-script':
                schema_sync.generate_migration_script(args.output)
                logger.info("Migration script generated at %s", args.output)
            elif args.command == 'validate':
                schema_sync.validate_schema()
                logger.info("Schema validated successfully.")
            elif args.command == 'save-version':
                schema_sync.save_version(args.description)
                logger.info("Schema version saved successfully.")
            elif args.command == 'list-versions':
                versions = schema_sync.list_versions()
                for version in versions:
                    print(f"Version: {version['version']}, Timestamp: {version['timestamp']}, Description: {version['description']}")
            elif args.command == 'apply-version':
                schema_sync.apply_version(args.version)
                logger.info(f"Schema version {args.version} applied successfully.")
            else:
                parser.print_help()
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
    except yaml.YAMLError as e:
        logger.error(f"Error parsing configuration file: {e}")
    except GoogleAPIError as e:
        logger.error(f"Google API error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    main()
