"""
Enhanced ML Models for MigrateIQ
Advanced machine learning capabilities for data migration and analysis.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import joblib
import json
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class MLPrediction:
    """ML prediction result."""
    prediction: Any
    confidence: float
    explanation: str
    metadata: Dict[str, Any]
    timestamp: datetime


@dataclass
class DataQualityMetrics:
    """Data quality assessment metrics."""
    completeness: float
    consistency: float
    accuracy: float
    validity: float
    uniqueness: float
    overall_score: float
    issues: List[str]
    recommendations: List[str]


class AdvancedSchemaMapper:
    """Advanced ML-powered schema mapping."""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.similarity_threshold = 0.7
        self.trained = False
        
    def train_on_mappings(self, historical_mappings: List[Dict[str, Any]]):
        """Train the model on historical mapping data."""
        try:
            # Extract field names and descriptions
            source_fields = []
            target_fields = []
            
            for mapping in historical_mappings:
                source_fields.append(f"{mapping.get('source_field', '')} {mapping.get('source_description', '')}")
                target_fields.append(f"{mapping.get('target_field', '')} {mapping.get('target_description', '')}")
            
            # Fit vectorizer on all field data
            all_fields = source_fields + target_fields
            self.vectorizer.fit(all_fields)
            self.trained = True
            
            logger.info(f"Schema mapper trained on {len(historical_mappings)} mappings")
            
        except Exception as e:
            logger.error(f"Failed to train schema mapper: {e}")
            raise
    
    def suggest_mappings(self, 
                        source_schema: List[Dict[str, str]], 
                        target_schema: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Suggest field mappings between source and target schemas."""
        if not self.trained:
            logger.warning("Schema mapper not trained. Using basic similarity.")
        
        suggestions = []
        
        # Prepare source and target field descriptions
        source_descriptions = [
            f"{field.get('name', '')} {field.get('description', '')} {field.get('type', '')}"
            for field in source_schema
        ]
        
        target_descriptions = [
            f"{field.get('name', '')} {field.get('description', '')} {field.get('type', '')}"
            for field in target_schema
        ]
        
        if self.trained:
            # Use trained vectorizer
            source_vectors = self.vectorizer.transform(source_descriptions)
            target_vectors = self.vectorizer.transform(target_descriptions)
        else:
            # Fallback to basic vectorization
            all_descriptions = source_descriptions + target_descriptions
            self.vectorizer.fit(all_descriptions)
            source_vectors = self.vectorizer.transform(source_descriptions)
            target_vectors = self.vectorizer.transform(target_descriptions)
        
        # Calculate similarity matrix
        similarity_matrix = cosine_similarity(source_vectors, target_vectors)
        
        # Find best matches
        for i, source_field in enumerate(source_schema):
            similarities = similarity_matrix[i]
            best_match_idx = np.argmax(similarities)
            best_similarity = similarities[best_match_idx]
            
            if best_similarity >= self.similarity_threshold:
                target_field = target_schema[best_match_idx]
                
                suggestions.append({
                    'source_field': source_field,
                    'target_field': target_field,
                    'confidence': float(best_similarity),
                    'mapping_type': self._determine_mapping_type(source_field, target_field),
                    'transformation_needed': self._needs_transformation(source_field, target_field),
                    'explanation': f"High similarity ({best_similarity:.2f}) between field names and descriptions"
                })
        
        return sorted(suggestions, key=lambda x: x['confidence'], reverse=True)
    
    def _determine_mapping_type(self, source_field: Dict, target_field: Dict) -> str:
        """Determine the type of mapping needed."""
        source_type = source_field.get('type', '').lower()
        target_type = target_field.get('type', '').lower()
        
        if source_type == target_type:
            return 'direct'
        elif 'int' in source_type and 'string' in target_type:
            return 'type_conversion'
        elif 'date' in source_type or 'date' in target_type:
            return 'date_transformation'
        else:
            return 'complex'
    
    def _needs_transformation(self, source_field: Dict, target_field: Dict) -> bool:
        """Check if transformation is needed."""
        return (
            source_field.get('type') != target_field.get('type') or
            source_field.get('format') != target_field.get('format')
        )


class DataQualityAnalyzer:
    """Advanced data quality analysis using ML."""
    
    def __init__(self):
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.pattern_analyzer = None
        
    def analyze_data_quality(self, data: pd.DataFrame) -> DataQualityMetrics:
        """Comprehensive data quality analysis."""
        metrics = {}
        issues = []
        recommendations = []
        
        # Completeness analysis
        completeness = self._analyze_completeness(data)
        metrics['completeness'] = completeness
        if completeness < 0.9:
            issues.append(f"Data completeness is low ({completeness:.2%})")
            recommendations.append("Investigate and address missing data")
        
        # Consistency analysis
        consistency = self._analyze_consistency(data)
        metrics['consistency'] = consistency
        if consistency < 0.8:
            issues.append(f"Data consistency issues detected ({consistency:.2%})")
            recommendations.append("Standardize data formats and values")
        
        # Accuracy analysis (anomaly detection)
        accuracy = self._analyze_accuracy(data)
        metrics['accuracy'] = accuracy
        if accuracy < 0.85:
            issues.append(f"Potential accuracy issues detected ({accuracy:.2%})")
            recommendations.append("Review and validate data accuracy")
        
        # Validity analysis
        validity = self._analyze_validity(data)
        metrics['validity'] = validity
        if validity < 0.9:
            issues.append(f"Data validity issues found ({validity:.2%})")
            recommendations.append("Implement data validation rules")
        
        # Uniqueness analysis
        uniqueness = self._analyze_uniqueness(data)
        metrics['uniqueness'] = uniqueness
        if uniqueness < 0.95:
            issues.append(f"Duplicate data detected ({uniqueness:.2%})")
            recommendations.append("Remove or consolidate duplicate records")
        
        # Calculate overall score
        overall_score = np.mean(list(metrics.values()))
        
        return DataQualityMetrics(
            completeness=completeness,
            consistency=consistency,
            accuracy=accuracy,
            validity=validity,
            uniqueness=uniqueness,
            overall_score=overall_score,
            issues=issues,
            recommendations=recommendations
        )
    
    def _analyze_completeness(self, data: pd.DataFrame) -> float:
        """Analyze data completeness."""
        total_cells = data.size
        non_null_cells = data.count().sum()
        return non_null_cells / total_cells if total_cells > 0 else 0.0
    
    def _analyze_consistency(self, data: pd.DataFrame) -> float:
        """Analyze data consistency."""
        consistency_scores = []
        
        for column in data.columns:
            if data[column].dtype == 'object':
                # Check format consistency for text columns
                values = data[column].dropna().astype(str)
                if len(values) > 0:
                    # Simple pattern consistency check
                    patterns = values.apply(lambda x: len(x)).value_counts()
                    most_common_pattern_ratio = patterns.iloc[0] / len(values) if len(patterns) > 0 else 1.0
                    consistency_scores.append(most_common_pattern_ratio)
            else:
                # For numeric columns, check for reasonable ranges
                consistency_scores.append(1.0)  # Simplified for now
        
        return np.mean(consistency_scores) if consistency_scores else 1.0
    
    def _analyze_accuracy(self, data: pd.DataFrame) -> float:
        """Analyze data accuracy using anomaly detection."""
        try:
            # Select numeric columns for anomaly detection
            numeric_data = data.select_dtypes(include=[np.number])
            
            if numeric_data.empty or len(numeric_data) < 10:
                return 1.0  # Not enough data for analysis
            
            # Fit anomaly detector
            self.anomaly_detector.fit(numeric_data.fillna(0))
            
            # Predict anomalies
            anomaly_predictions = self.anomaly_detector.predict(numeric_data.fillna(0))
            
            # Calculate accuracy as percentage of normal data
            normal_data_ratio = np.sum(anomaly_predictions == 1) / len(anomaly_predictions)
            return normal_data_ratio
            
        except Exception as e:
            logger.warning(f"Accuracy analysis failed: {e}")
            return 1.0
    
    def _analyze_validity(self, data: pd.DataFrame) -> float:
        """Analyze data validity."""
        validity_scores = []
        
        for column in data.columns:
            column_data = data[column].dropna()
            
            if column_data.empty:
                validity_scores.append(0.0)
                continue
            
            if 'email' in column.lower():
                # Email validation
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                valid_emails = column_data.astype(str).str.match(email_pattern).sum()
                validity_scores.append(valid_emails / len(column_data))
            
            elif 'phone' in column.lower():
                # Phone validation (basic)
                phone_pattern = r'^[\+]?[1-9][\d]{0,15}$'
                valid_phones = column_data.astype(str).str.match(phone_pattern).sum()
                validity_scores.append(valid_phones / len(column_data))
            
            elif data[column].dtype in ['int64', 'float64']:
                # Numeric validation (check for reasonable ranges)
                finite_values = np.isfinite(column_data).sum()
                validity_scores.append(finite_values / len(column_data))
            
            else:
                # Default validity (non-empty strings)
                valid_values = (column_data.astype(str).str.len() > 0).sum()
                validity_scores.append(valid_values / len(column_data))
        
        return np.mean(validity_scores) if validity_scores else 1.0
    
    def _analyze_uniqueness(self, data: pd.DataFrame) -> float:
        """Analyze data uniqueness."""
        if data.empty:
            return 1.0
        
        # Check for duplicate rows
        total_rows = len(data)
        unique_rows = len(data.drop_duplicates())
        
        return unique_rows / total_rows


class PredictiveMigrationPlanner:
    """ML-powered migration planning and optimization."""
    
    def __init__(self):
        self.performance_predictor = RandomForestClassifier(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.trained = False
    
    def train_performance_predictor(self, historical_migrations: List[Dict[str, Any]]):
        """Train the performance prediction model."""
        try:
            # Extract features and targets
            features = []
            targets = []
            
            for migration in historical_migrations:
                feature_vector = [
                    migration.get('data_size_gb', 0),
                    migration.get('num_tables', 0),
                    migration.get('num_fields', 0),
                    migration.get('complexity_score', 0),
                    migration.get('source_db_load', 0),
                    migration.get('target_db_load', 0),
                    migration.get('network_bandwidth', 0)
                ]
                features.append(feature_vector)
                
                # Target: success (1) or failure (0)
                targets.append(1 if migration.get('status') == 'success' else 0)
            
            if len(features) < 10:
                logger.warning("Insufficient training data for performance predictor")
                return
            
            # Scale features and train model
            features_scaled = self.scaler.fit_transform(features)
            self.performance_predictor.fit(features_scaled, targets)
            self.trained = True
            
            logger.info(f"Performance predictor trained on {len(features)} migrations")
            
        except Exception as e:
            logger.error(f"Failed to train performance predictor: {e}")
            raise
    
    def predict_migration_success(self, migration_params: Dict[str, Any]) -> MLPrediction:
        """Predict migration success probability."""
        if not self.trained:
            return MLPrediction(
                prediction=0.5,
                confidence=0.0,
                explanation="Model not trained",
                metadata={},
                timestamp=datetime.now()
            )
        
        try:
            # Extract features
            feature_vector = [[
                migration_params.get('data_size_gb', 0),
                migration_params.get('num_tables', 0),
                migration_params.get('num_fields', 0),
                migration_params.get('complexity_score', 0),
                migration_params.get('source_db_load', 0),
                migration_params.get('target_db_load', 0),
                migration_params.get('network_bandwidth', 0)
            ]]
            
            # Scale and predict
            feature_vector_scaled = self.scaler.transform(feature_vector)
            success_probability = self.performance_predictor.predict_proba(feature_vector_scaled)[0][1]
            
            # Get feature importance for explanation
            feature_names = [
                'data_size_gb', 'num_tables', 'num_fields', 'complexity_score',
                'source_db_load', 'target_db_load', 'network_bandwidth'
            ]
            
            feature_importance = dict(zip(feature_names, self.performance_predictor.feature_importances_))
            most_important = max(feature_importance, key=feature_importance.get)
            
            explanation = f"Success probability: {success_probability:.2%}. Most influential factor: {most_important}"
            
            return MLPrediction(
                prediction=success_probability,
                confidence=max(success_probability, 1 - success_probability),
                explanation=explanation,
                metadata={
                    'feature_importance': feature_importance,
                    'model_type': 'RandomForestClassifier'
                },
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return MLPrediction(
                prediction=0.5,
                confidence=0.0,
                explanation=f"Prediction failed: {e}",
                metadata={},
                timestamp=datetime.now()
            )
    
    def optimize_migration_plan(self, migration_params: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize migration plan based on ML insights."""
        recommendations = []
        optimizations = {}
        
        # Analyze data size and suggest chunking
        data_size = migration_params.get('data_size_gb', 0)
        if data_size > 100:
            chunk_size = min(10, data_size / 10)
            recommendations.append(f"Consider chunking data into {chunk_size}GB batches")
            optimizations['chunk_size_gb'] = chunk_size
        
        # Analyze complexity and suggest parallel processing
        complexity = migration_params.get('complexity_score', 0)
        if complexity > 7:
            recommendations.append("High complexity detected. Consider parallel processing")
            optimizations['parallel_workers'] = min(4, migration_params.get('num_tables', 1))
        
        # Network optimization
        bandwidth = migration_params.get('network_bandwidth', 0)
        if bandwidth < 100:  # Less than 100 Mbps
            recommendations.append("Low bandwidth detected. Schedule during off-peak hours")
            optimizations['schedule_off_peak'] = True
        
        return {
            'recommendations': recommendations,
            'optimizations': optimizations,
            'estimated_duration_hours': self._estimate_duration(migration_params, optimizations),
            'risk_level': self._assess_risk_level(migration_params)
        }
    
    def _estimate_duration(self, params: Dict[str, Any], optimizations: Dict[str, Any]) -> float:
        """Estimate migration duration."""
        base_duration = params.get('data_size_gb', 0) * 0.1  # 0.1 hours per GB baseline
        
        # Apply optimizations
        if optimizations.get('parallel_workers', 1) > 1:
            base_duration /= optimizations['parallel_workers'] * 0.7  # 70% efficiency
        
        if optimizations.get('chunk_size_gb'):
            base_duration *= 1.1  # 10% overhead for chunking
        
        return max(0.5, base_duration)  # Minimum 30 minutes
    
    def _assess_risk_level(self, params: Dict[str, Any]) -> str:
        """Assess migration risk level."""
        risk_score = 0
        
        if params.get('data_size_gb', 0) > 1000:
            risk_score += 2
        if params.get('complexity_score', 0) > 8:
            risk_score += 2
        if params.get('num_tables', 0) > 100:
            risk_score += 1
        
        if risk_score >= 4:
            return 'high'
        elif risk_score >= 2:
            return 'medium'
        else:
            return 'low'
