"""
Services for the analyzer app.
"""
import json
import logging
# import pandas as pd  # Commented out temporarily
from django.db import transaction
from .models import DataSource, Entity, Field

logger = logging.getLogger(__name__)

class DataSourceAnalyzer:
    """Service for analyzing data sources."""

    def __init__(self, data_source_id):
        """Initialize with a data source ID."""
        self.data_source = DataSource.objects.get(id=data_source_id)

    def analyze(self):
        """Analyze the data source and extract schema information."""
        logger.info(f"Starting analysis for data source: {self.data_source.name}")

        try:
            # Connect to the data source based on its type
            if self.data_source.source_type == 'csv':
                return self._analyze_csv()
            elif self.data_source.source_type == 'database':
                return self._analyze_database()
            elif self.data_source.source_type == 'api':
                return self._analyze_api()
            else:
                raise ValueError(f"Unsupported data source type: {self.data_source.source_type}")
        except Exception as e:
            logger.error(f"Error analyzing data source {self.data_source.name}: {str(e)}")
            raise

    def _analyze_csv(self):
        """Analyze a CSV data source."""
        try:
            # Parse connection string to get file path
            file_path = self.data_source.connection_string

            # For now, we'll create a mock entity without actually reading the CSV
            # since pandas is not installed
            with transaction.atomic():
                # Create entity for the CSV file
                entity = Entity.objects.create(
                    data_source=self.data_source,
                    name=file_path.split('/')[-1].split('.')[0],
                    original_name=file_path.split('/')[-1],
                    description=f"CSV file: {file_path}",
                    record_count=0  # Mock value
                )

                # Create some mock fields
                mock_fields = [
                    {"name": "id", "data_type": "integer", "sample_values": [1, 2, 3, 4, 5]},
                    {"name": "name", "data_type": "string", "sample_values": ["John", "Jane", "Bob", "Alice", "Tom"]},
                    {"name": "age", "data_type": "integer", "sample_values": [25, 30, 35, 40, 45]},
                    {"name": "email", "data_type": "string", "sample_values": ["john@example.com", "jane@example.com"]}
                ]

                for field_data in mock_fields:
                    Field.objects.create(
                        entity=entity,
                        name=field_data["name"],
                        original_name=field_data["name"],
                        data_type=field_data["data_type"],
                        is_nullable=False,
                        sample_values=json.dumps(field_data["sample_values"])
                    )

                return entity

            # In a real implementation with pandas, we would:
            # 1. Read the CSV file: df = pd.read_csv(file_path)
            # 2. Extract column names, data types, and sample values
            # 3. Create fields for each column

        except Exception as e:
            logger.error(f"Error analyzing CSV file: {str(e)}")
            raise

    def _analyze_database(self):
        """Analyze a database data source."""
        # This would connect to the database using SQLAlchemy
        # and extract schema information
        # For now, we'll just raise a NotImplementedError
        raise NotImplementedError("Database analysis not yet implemented")

    def _analyze_api(self):
        """Analyze an API data source."""
        # This would make API requests and analyze the response structure
        # For now, we'll just raise a NotImplementedError
        raise NotImplementedError("API analysis not yet implemented")


class SchemaAnalyzer:
    """Service for analyzing and comparing schemas."""

    def compare_entities(self, source_entity_id, target_entity_id):
        """Compare two entities and suggest mappings."""
        source_entity = Entity.objects.get(id=source_entity_id)
        target_entity = Entity.objects.get(id=target_entity_id)

        source_fields = Field.objects.filter(entity=source_entity)
        target_fields = Field.objects.filter(entity=target_entity)

        # Simple field matching based on name similarity
        mappings = []

        for source_field in source_fields:
            best_match = None
            best_score = 0

            for target_field in target_fields:
                # Calculate similarity score
                score = self._calculate_similarity(source_field.name, target_field.name)

                if score > best_score and score > 0.7:  # Threshold for a good match
                    best_score = score
                    best_match = target_field

            if best_match:
                mappings.append({
                    'source_field': source_field,
                    'target_field': best_match,
                    'confidence': best_score
                })

        return mappings

    def _calculate_similarity(self, str1, str2):
        """Calculate string similarity using a simple algorithm."""
        # Convert to lowercase for case-insensitive comparison
        str1 = str1.lower()
        str2 = str2.lower()

        # Exact match
        if str1 == str2:
            return 1.0

        # One is a substring of the other
        if str1 in str2 or str2 in str1:
            return 0.8

        # Levenshtein distance (simplified)
        # In a real implementation, we would use a proper Levenshtein distance algorithm
        # or a library like fuzzywuzzy
        return 0.5  # Default similarity for demonstration
