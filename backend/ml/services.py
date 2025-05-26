"""
Services for the ml app.
"""

import logging
import os
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.conf import settings
from .models import MLModel, ModelPrediction

logger = logging.getLogger(__name__)


class SchemaRecognitionModel:
    """Service for schema recognition."""
    
    def __init__(self):
        """Initialize the schema recognition model."""
        self.model = self._load_model()
        self.vectorizer = TfidfVectorizer(
            analyzer='word',
            token_pattern=r'[a-zA-Z0-9_]+',
            ngram_range=(1, 2),
            stop_words='english',
            lowercase=True
        )
    
    def _load_model(self):
        """Load the model from file."""
        try:
            # In a real implementation, this would load a trained model
            # For now, we'll just return None
            return None
        except Exception as e:
            logger.error(f"Error loading schema recognition model: {str(e)}")
            return None
    
    def predict(self, schema_data):
        """Predict entity types from schema data."""
        # In a real implementation, this would use the loaded model
        # For now, we'll just use a simple heuristic approach
        
        predictions = []
        
        for entity in schema_data:
            entity_name = entity.get('name', '').lower()
            fields = entity.get('fields', [])
            
            # Simple heuristic based on entity name
            entity_type = 'unknown'
            confidence = 0.5
            
            if 'patient' in entity_name or 'person' in entity_name or 'client' in entity_name:
                entity_type = 'person'
                confidence = 0.9
            elif 'medication' in entity_name or 'prescription' in entity_name or 'drug' in entity_name:
                entity_type = 'medication'
                confidence = 0.9
            elif 'appointment' in entity_name or 'visit' in entity_name or 'schedule' in entity_name:
                entity_type = 'appointment'
                confidence = 0.9
            elif 'address' in entity_name or 'location' in entity_name:
                entity_type = 'address'
                confidence = 0.9
            elif 'provider' in entity_name or 'doctor' in entity_name or 'caregiver' in entity_name:
                entity_type = 'provider'
                confidence = 0.9
            
            predictions.append({
                'entity_name': entity.get('name'),
                'entity_type': entity_type,
                'confidence': confidence
            })
        
        return predictions


class FieldMappingModel:
    """Service for field mapping."""
    
    def __init__(self):
        """Initialize the field mapping model."""
        self.model = self._load_model()
        self.vectorizer = TfidfVectorizer(
            analyzer='word',
            token_pattern=r'[a-zA-Z0-9_]+',
            ngram_range=(1, 2),
            stop_words='english',
            lowercase=True
        )
    
    def _load_model(self):
        """Load the model from file."""
        try:
            # In a real implementation, this would load a trained model
            # For now, we'll just return None
            return None
        except Exception as e:
            logger.error(f"Error loading field mapping model: {str(e)}")
            return None
    
    def predict(self, source_fields, target_fields):
        """Predict field mappings between source and target fields."""
        # In a real implementation, this would use the loaded model
        # For now, we'll just use cosine similarity between field names
        
        source_texts = [f"{field.get('name', '')} {field.get('type', '')}" for field in source_fields]
        target_texts = [f"{field.get('name', '')} {field.get('type', '')}" for field in target_fields]
        
        # Compute similarity matrix
        all_texts = source_texts + target_texts
        tfidf_matrix = self.vectorizer.fit_transform(all_texts)
        
        source_vectors = tfidf_matrix[:len(source_texts)]
        target_vectors = tfidf_matrix[len(source_texts):]
        
        similarity_matrix = cosine_similarity(source_vectors, target_vectors)
        
        # Create mappings based on similarity
        mappings = []
        
        for i, source_field in enumerate(source_fields):
            best_match_idx = np.argmax(similarity_matrix[i])
            best_match_score = similarity_matrix[i][best_match_idx]
            
            if best_match_score > 0.3:  # Threshold for considering a match
                target_field = target_fields[best_match_idx]
                
                mappings.append({
                    'source_field': source_field.get('name'),
                    'target_field': target_field.get('name'),
                    'confidence': float(best_match_score)
                })
        
        return mappings


class DataQualityModel:
    """Service for data quality enhancement."""
    
    def __init__(self):
        """Initialize the data quality model."""
        self.model = self._load_model()
    
    def _load_model(self):
        """Load the model from file."""
        try:
            # In a real implementation, this would load a trained model
            # For now, we'll just return None
            return None
        except Exception as e:
            logger.error(f"Error loading data quality model: {str(e)}")
            return None
    
    def enhance(self, data, field_type):
        """Enhance data quality for a specific field type."""
        # In a real implementation, this would use the loaded model
        # For now, we'll just return the original data
        return data
