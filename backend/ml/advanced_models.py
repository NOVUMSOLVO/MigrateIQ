"""
Advanced ML models for data migration and quality assessment.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import joblib
import logging
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class AdvancedSchemaRecognitionModel:
    """Advanced ML model for schema recognition and entity classification."""
    
    def __init__(self):
        """Initialize the advanced schema recognition model."""
        self.model = None
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # Entity type patterns
        self.entity_patterns = {
            'person': [
                r'(first|last|full)_?name', r'email', r'phone', r'address',
                r'birth_?date', r'age', r'gender', r'ssn', r'employee_?id'
            ],
            'organization': [
                r'company', r'organization', r'department', r'division',
                r'office', r'branch', r'subsidiary'
            ],
            'product': [
                r'product', r'item', r'sku', r'barcode', r'category',
                r'brand', r'model', r'price', r'cost'
            ],
            'transaction': [
                r'transaction', r'order', r'payment', r'invoice',
                r'amount', r'total', r'tax', r'discount'
            ],
            'location': [
                r'address', r'city', r'state', r'country', r'zip',
                r'postal', r'latitude', r'longitude', r'region'
            ],
            'temporal': [
                r'date', r'time', r'timestamp', r'created', r'updated',
                r'modified', r'start', r'end', r'duration'
            ]
        }
    
    def extract_features(self, schema_data: List[Dict[str, Any]]) -> np.ndarray:
        """Extract features from schema data."""
        features = []
        
        for entity in schema_data:
            entity_features = []
            
            # Basic entity features
            entity_name = entity.get('name', '').lower()
            fields = entity.get('fields', [])
            
            # Entity name features
            entity_features.extend([
                len(entity_name),
                entity_name.count('_'),
                entity_name.count(' '),
                len(fields)
            ])
            
            # Field-based features
            field_names = [f.get('name', '').lower() for f in fields]
            field_types = [f.get('type', '').lower() for f in fields]
            
            # Pattern matching features
            for entity_type, patterns in self.entity_patterns.items():
                pattern_matches = 0
                for pattern in patterns:
                    for field_name in field_names:
                        if re.search(pattern, field_name):
                            pattern_matches += 1
                entity_features.append(pattern_matches)
            
            # Data type distribution
            type_counts = {}
            for field_type in field_types:
                type_counts[field_type] = type_counts.get(field_type, 0) + 1
            
            # Common data types
            common_types = ['string', 'integer', 'float', 'boolean', 'date', 'timestamp']
            for data_type in common_types:
                entity_features.append(type_counts.get(data_type, 0))
            
            features.append(entity_features)
        
        return np.array(features)
    
    def train(self, training_data: List[Dict[str, Any]], labels: List[str]):
        """Train the schema recognition model."""
        try:
            # Extract features
            X = self.extract_features(training_data)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train model
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            self.model.fit(X_scaled, labels)
            
            self.is_trained = True
            logger.info("Schema recognition model trained successfully")
            
        except Exception as e:
            logger.error(f"Failed to train schema recognition model: {str(e)}")
            raise
    
    def predict(self, schema_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Predict entity types and confidence scores."""
        if not self.is_trained:
            logger.warning("Model not trained, using heuristic approach")
            return self._heuristic_prediction(schema_data)
        
        try:
            # Extract features
            X = self.extract_features(schema_data)
            X_scaled = self.scaler.transform(X)
            
            # Make predictions
            predictions = self.model.predict(X_scaled)
            probabilities = self.model.predict_proba(X_scaled)
            
            results = []
            for i, entity in enumerate(schema_data):
                result = {
                    'entity_name': entity.get('name'),
                    'predicted_type': predictions[i],
                    'confidence': float(np.max(probabilities[i])),
                    'all_probabilities': {
                        class_name: float(prob) 
                        for class_name, prob in zip(self.model.classes_, probabilities[i])
                    }
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            return self._heuristic_prediction(schema_data)
    
    def _heuristic_prediction(self, schema_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback heuristic prediction when model is not available."""
        results = []
        
        for entity in schema_data:
            entity_name = entity.get('name', '').lower()
            fields = entity.get('fields', [])
            
            # Simple pattern matching
            best_match = 'unknown'
            best_score = 0
            
            for entity_type, patterns in self.entity_patterns.items():
                score = 0
                for pattern in patterns:
                    if re.search(pattern, entity_name):
                        score += 2
                    for field in fields:
                        field_name = field.get('name', '').lower()
                        if re.search(pattern, field_name):
                            score += 1
                
                if score > best_score:
                    best_score = score
                    best_match = entity_type
            
            confidence = min(best_score / 10.0, 1.0)
            
            results.append({
                'entity_name': entity.get('name'),
                'predicted_type': best_match,
                'confidence': confidence,
                'all_probabilities': {best_match: confidence}
            })
        
        return results


class DataQualityAssessmentModel:
    """Advanced model for data quality assessment."""
    
    def __init__(self):
        """Initialize the data quality assessment model."""
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.clustering_model = DBSCAN(eps=0.5, min_samples=5)
        
    def assess_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive data quality assessment."""
        quality_report = {
            'overall_score': 0.0,
            'completeness': self._assess_completeness(df),
            'consistency': self._assess_consistency(df),
            'accuracy': self._assess_accuracy(df),
            'validity': self._assess_validity(df),
            'uniqueness': self._assess_uniqueness(df),
            'anomalies': self._detect_anomalies(df),
            'recommendations': []
        }
        
        # Calculate overall score
        scores = [
            quality_report['completeness']['score'],
            quality_report['consistency']['score'],
            quality_report['accuracy']['score'],
            quality_report['validity']['score'],
            quality_report['uniqueness']['score']
        ]
        quality_report['overall_score'] = np.mean(scores)
        
        # Generate recommendations
        quality_report['recommendations'] = self._generate_recommendations(quality_report)
        
        return quality_report
    
    def _assess_completeness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess data completeness."""
        total_cells = df.size
        missing_cells = df.isnull().sum().sum()
        completeness_ratio = 1 - (missing_cells / total_cells)
        
        column_completeness = {}
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            column_completeness[col] = {
                'missing_count': int(missing_count),
                'missing_percentage': float(missing_count / len(df) * 100),
                'completeness_score': float(1 - missing_count / len(df))
            }
        
        return {
            'score': float(completeness_ratio),
            'missing_cells': int(missing_cells),
            'total_cells': int(total_cells),
            'column_details': column_completeness
        }
    
    def _assess_consistency(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess data consistency."""
        consistency_issues = []
        consistency_score = 1.0
        
        for col in df.columns:
            if df[col].dtype == 'object':
                # Check for inconsistent formatting
                unique_values = df[col].dropna().unique()
                
                # Check for case inconsistencies
                case_variants = {}
                for value in unique_values:
                    if isinstance(value, str):
                        lower_value = value.lower()
                        if lower_value in case_variants:
                            case_variants[lower_value].append(value)
                        else:
                            case_variants[lower_value] = [value]
                
                case_issues = {k: v for k, v in case_variants.items() if len(v) > 1}
                if case_issues:
                    consistency_issues.append({
                        'column': col,
                        'issue_type': 'case_inconsistency',
                        'details': case_issues
                    })
                    consistency_score -= 0.1
        
        return {
            'score': max(0.0, consistency_score),
            'issues': consistency_issues
        }
    
    def _assess_accuracy(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess data accuracy using statistical methods."""
        accuracy_issues = []
        accuracy_score = 1.0
        
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                # Check for outliers using IQR method
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)][col]
                if len(outliers) > 0:
                    accuracy_issues.append({
                        'column': col,
                        'issue_type': 'outliers',
                        'outlier_count': len(outliers),
                        'outlier_percentage': len(outliers) / len(df) * 100
                    })
                    accuracy_score -= 0.05
        
        return {
            'score': max(0.0, accuracy_score),
            'issues': accuracy_issues
        }
    
    def _assess_validity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess data validity against expected formats."""
        validity_issues = []
        validity_score = 1.0
        
        # Common validation patterns
        patterns = {
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'phone': r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$',
            'url': r'^https?://[^\s/$.?#].[^\s]*$',
            'ip_address': r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
        }
        
        for col in df.columns:
            if df[col].dtype == 'object':
                col_lower = col.lower()
                
                # Check if column name suggests a specific format
                for pattern_name, pattern in patterns.items():
                    if pattern_name in col_lower:
                        invalid_count = 0
                        for value in df[col].dropna():
                            if isinstance(value, str) and not re.match(pattern, value):
                                invalid_count += 1
                        
                        if invalid_count > 0:
                            validity_issues.append({
                                'column': col,
                                'expected_format': pattern_name,
                                'invalid_count': invalid_count,
                                'invalid_percentage': invalid_count / len(df.dropna()) * 100
                            })
                            validity_score -= 0.1
        
        return {
            'score': max(0.0, validity_score),
            'issues': validity_issues
        }
    
    def _assess_uniqueness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess data uniqueness."""
        uniqueness_report = {}
        overall_uniqueness = 1.0
        
        for col in df.columns:
            total_count = len(df[col].dropna())
            unique_count = len(df[col].dropna().unique())
            uniqueness_ratio = unique_count / total_count if total_count > 0 else 0
            
            duplicates = df[col].duplicated().sum()
            
            uniqueness_report[col] = {
                'uniqueness_ratio': float(uniqueness_ratio),
                'duplicate_count': int(duplicates),
                'unique_count': int(unique_count),
                'total_count': int(total_count)
            }
            
            # Penalize columns with low uniqueness (except for categorical columns)
            if uniqueness_ratio < 0.5 and unique_count > 10:
                overall_uniqueness -= 0.1
        
        return {
            'score': max(0.0, overall_uniqueness),
            'column_details': uniqueness_report
        }
    
    def _detect_anomalies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect anomalies in the dataset."""
        anomalies = {}
        
        # Select numeric columns for anomaly detection
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) > 0:
            try:
                # Prepare data for anomaly detection
                X = df[numeric_cols].fillna(df[numeric_cols].median())
                
                # Detect anomalies
                anomaly_labels = self.anomaly_detector.fit_predict(X)
                anomaly_indices = np.where(anomaly_labels == -1)[0]
                
                anomalies = {
                    'anomaly_count': len(anomaly_indices),
                    'anomaly_percentage': len(anomaly_indices) / len(df) * 100,
                    'anomaly_indices': anomaly_indices.tolist()
                }
                
            except Exception as e:
                logger.error(f"Anomaly detection failed: {str(e)}")
                anomalies = {'error': str(e)}
        
        return anomalies
    
    def _generate_recommendations(self, quality_report: Dict[str, Any]) -> List[str]:
        """Generate data quality improvement recommendations."""
        recommendations = []
        
        # Completeness recommendations
        if quality_report['completeness']['score'] < 0.9:
            recommendations.append("Consider implementing data validation rules to reduce missing values")
        
        # Consistency recommendations
        if quality_report['consistency']['score'] < 0.9:
            recommendations.append("Standardize data formats and implement data entry guidelines")
        
        # Accuracy recommendations
        if quality_report['accuracy']['score'] < 0.9:
            recommendations.append("Review outliers and implement data validation ranges")
        
        # Validity recommendations
        if quality_report['validity']['score'] < 0.9:
            recommendations.append("Implement format validation for structured data fields")
        
        # Uniqueness recommendations
        if quality_report['uniqueness']['score'] < 0.9:
            recommendations.append("Review duplicate records and implement deduplication processes")
        
        # Anomaly recommendations
        anomalies = quality_report.get('anomalies', {})
        if anomalies.get('anomaly_percentage', 0) > 5:
            recommendations.append("Investigate anomalous records for potential data quality issues")
        
        return recommendations
