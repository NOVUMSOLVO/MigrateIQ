"""
Services for the mapping_engine app.
"""

import logging
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from analyzer.models import Entity, Field
from .models import Mapping, FieldMapping, MappingRule

logger = logging.getLogger(__name__)


class MappingEngine:
    """Service for generating mappings between source and target schemas."""
    
    def __init__(self):
        """Initialize the mapping engine."""
        self.vectorizer = TfidfVectorizer(
            analyzer='word',
            token_pattern=r'[a-zA-Z0-9_]+',
            ngram_range=(1, 2),
            stop_words='english',
            lowercase=True
        )
    
    def generate_entity_mappings(self, source_entities, target_entities):
        """Generate mappings between source and target entities."""
        mappings = []
        
        # Extract entity names and descriptions
        source_texts = [f"{entity.name} {entity.description}" for entity in source_entities]
        target_texts = [f"{entity.name} {entity.description}" for entity in target_entities]
        
        # Compute similarity matrix
        all_texts = source_texts + target_texts
        tfidf_matrix = self.vectorizer.fit_transform(all_texts)
        
        source_vectors = tfidf_matrix[:len(source_texts)]
        target_vectors = tfidf_matrix[len(source_texts):]
        
        similarity_matrix = cosine_similarity(source_vectors, target_vectors)
        
        # Create mappings based on similarity
        for i, source_entity in enumerate(source_entities):
            best_match_idx = np.argmax(similarity_matrix[i])
            best_match_score = similarity_matrix[i][best_match_idx]
            
            if best_match_score > 0.3:  # Threshold for considering a match
                target_entity = target_entities[best_match_idx]
                
                # Create mapping
                mapping = Mapping(
                    source_entity=source_entity,
                    target_entity=target_entity,
                    confidence_score=float(best_match_score)
                )
                mappings.append(mapping)
        
        return mappings
    
    def generate_field_mappings(self, entity_mapping):
        """Generate mappings between fields of mapped entities."""
        field_mappings = []
        
        source_entity = entity_mapping.source_entity
        target_entity = entity_mapping.target_entity
        
        source_fields = Field.objects.filter(entity=source_entity)
        target_fields = Field.objects.filter(entity=target_entity)
        
        # Apply predefined rules first
        rules = MappingRule.objects.all().order_by('-priority')
        rule_applied = set()
        
        for source_field in source_fields:
            for rule in rules:
                if self._apply_rule(rule, source_field, target_fields, entity_mapping, field_mappings):
                    rule_applied.add(source_field.id)
                    break
        
        # For remaining fields, use similarity-based matching
        remaining_source_fields = [f for f in source_fields if f.id not in rule_applied]
        remaining_target_fields = list(target_fields)
        
        if remaining_source_fields and remaining_target_fields:
            # Extract field names and descriptions
            source_texts = [f"{field.name} {field.data_type}" for field in remaining_source_fields]
            target_texts = [f"{field.name} {field.data_type}" for field in remaining_target_fields]
            
            # Compute similarity matrix
            all_texts = source_texts + target_texts
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
            
            source_vectors = tfidf_matrix[:len(source_texts)]
            target_vectors = tfidf_matrix[len(source_texts):]
            
            similarity_matrix = cosine_similarity(source_vectors, target_vectors)
            
            # Create field mappings based on similarity
            for i, source_field in enumerate(remaining_source_fields):
                best_match_idx = np.argmax(similarity_matrix[i])
                best_match_score = similarity_matrix[i][best_match_idx]
                
                if best_match_score > 0.3:  # Threshold for considering a match
                    target_field = remaining_target_fields[best_match_idx]
                    
                    # Create field mapping
                    field_mapping = FieldMapping(
                        mapping=entity_mapping,
                        source_field=source_field,
                        target_field=target_field,
                        confidence_score=float(best_match_score)
                    )
                    field_mappings.append(field_mapping)
        
        return field_mappings
    
    def _apply_rule(self, rule, source_field, target_fields, entity_mapping, field_mappings):
        """Apply a mapping rule to a source field."""
        if rule.rule_type == 'EXACT_MATCH':
            # Exact match rule
            for target_field in target_fields:
                if source_field.name.lower() == target_field.name.lower():
                    field_mapping = FieldMapping(
                        mapping=entity_mapping,
                        source_field=source_field,
                        target_field=target_field,
                        confidence_score=1.0
                    )
                    field_mappings.append(field_mapping)
                    return True
        
        elif rule.rule_type == 'SYNONYM':
            # Synonym rule
            source_pattern = rule.source_pattern.lower()
            target_pattern = rule.target_pattern.lower()
            
            if source_field.name.lower() == source_pattern:
                for target_field in target_fields:
                    if target_field.name.lower() == target_pattern:
                        field_mapping = FieldMapping(
                            mapping=entity_mapping,
                            source_field=source_field,
                            target_field=target_field,
                            confidence_score=0.9
                        )
                        field_mappings.append(field_mapping)
                        return True
        
        elif rule.rule_type == 'PATTERN':
            # Pattern matching rule
            source_pattern = re.compile(rule.source_pattern, re.IGNORECASE)
            target_pattern = re.compile(rule.target_pattern, re.IGNORECASE)
            
            if source_pattern.match(source_field.name):
                for target_field in target_fields:
                    if target_pattern.match(target_field.name):
                        field_mapping = FieldMapping(
                            mapping=entity_mapping,
                            source_field=source_field,
                            target_field=target_field,
                            confidence_score=0.8
                        )
                        field_mappings.append(field_mapping)
                        return True
        
        return False
