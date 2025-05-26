"""
Advanced data profiling service for comprehensive data analysis.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
import re
from collections import Counter
import json

logger = logging.getLogger(__name__)


class DataProfiler:
    """Comprehensive data profiling service."""
    
    def __init__(self):
        """Initialize the data profiler."""
        self.profile_cache = {}
        
    def profile_dataset(self, df: pd.DataFrame, sample_size: Optional[int] = None) -> Dict[str, Any]:
        """Generate comprehensive data profile for a dataset."""
        
        # Sample data if dataset is large
        if sample_size and len(df) > sample_size:
            df_sample = df.sample(n=sample_size, random_state=42)
            logger.info(f"Sampling {sample_size} rows from {len(df)} total rows")
        else:
            df_sample = df
        
        profile = {
            'dataset_info': self._get_dataset_info(df, df_sample),
            'column_profiles': self._profile_columns(df_sample),
            'data_types': self._analyze_data_types(df_sample),
            'relationships': self._analyze_relationships(df_sample),
            'patterns': self._detect_patterns(df_sample),
            'quality_metrics': self._calculate_quality_metrics(df_sample),
            'statistical_summary': self._generate_statistical_summary(df_sample),
            'recommendations': []
        }
        
        # Generate recommendations
        profile['recommendations'] = self._generate_profiling_recommendations(profile)
        
        return profile
    
    def _get_dataset_info(self, df_full: pd.DataFrame, df_sample: pd.DataFrame) -> Dict[str, Any]:
        """Get basic dataset information."""
        return {
            'total_rows': len(df_full),
            'total_columns': len(df_full.columns),
            'sample_rows': len(df_sample),
            'memory_usage_mb': float(df_full.memory_usage(deep=True).sum() / 1024 / 1024),
            'column_names': list(df_full.columns),
            'shape': df_full.shape,
            'size': df_full.size
        }
    
    def _profile_columns(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Profile each column individually."""
        column_profiles = {}
        
        for col in df.columns:
            column_profiles[col] = self._profile_single_column(df[col])
        
        return column_profiles
    
    def _profile_single_column(self, series: pd.Series) -> Dict[str, Any]:
        """Profile a single column."""
        profile = {
            'name': series.name,
            'dtype': str(series.dtype),
            'non_null_count': int(series.count()),
            'null_count': int(series.isnull().sum()),
            'null_percentage': float(series.isnull().sum() / len(series) * 100),
            'unique_count': int(series.nunique()),
            'unique_percentage': float(series.nunique() / len(series) * 100),
            'memory_usage': int(series.memory_usage(deep=True))
        }
        
        # Type-specific profiling
        if series.dtype in ['int64', 'float64', 'int32', 'float32']:
            profile.update(self._profile_numeric_column(series))
        elif series.dtype == 'object':
            profile.update(self._profile_text_column(series))
        elif series.dtype == 'datetime64[ns]':
            profile.update(self._profile_datetime_column(series))
        elif series.dtype == 'bool':
            profile.update(self._profile_boolean_column(series))
        
        return profile
    
    def _profile_numeric_column(self, series: pd.Series) -> Dict[str, Any]:
        """Profile numeric column."""
        numeric_series = series.dropna()
        
        if len(numeric_series) == 0:
            return {'profile_type': 'numeric', 'error': 'No non-null values'}
        
        profile = {
            'profile_type': 'numeric',
            'min': float(numeric_series.min()),
            'max': float(numeric_series.max()),
            'mean': float(numeric_series.mean()),
            'median': float(numeric_series.median()),
            'std': float(numeric_series.std()),
            'variance': float(numeric_series.var()),
            'skewness': float(numeric_series.skew()),
            'kurtosis': float(numeric_series.kurtosis()),
            'quartiles': {
                'q1': float(numeric_series.quantile(0.25)),
                'q2': float(numeric_series.quantile(0.5)),
                'q3': float(numeric_series.quantile(0.75))
            },
            'percentiles': {
                'p5': float(numeric_series.quantile(0.05)),
                'p95': float(numeric_series.quantile(0.95)),
                'p99': float(numeric_series.quantile(0.99))
            }
        }
        
        # Detect outliers
        Q1 = profile['quartiles']['q1']
        Q3 = profile['quartiles']['q3']
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        outliers = numeric_series[(numeric_series < lower_bound) | (numeric_series > upper_bound)]
        profile['outliers'] = {
            'count': len(outliers),
            'percentage': float(len(outliers) / len(numeric_series) * 100),
            'lower_bound': float(lower_bound),
            'upper_bound': float(upper_bound)
        }
        
        # Check if values are integers
        if all(numeric_series == numeric_series.astype(int)):
            profile['is_integer'] = True
        else:
            profile['is_integer'] = False
        
        return profile
    
    def _profile_text_column(self, series: pd.Series) -> Dict[str, Any]:
        """Profile text column."""
        text_series = series.dropna().astype(str)
        
        if len(text_series) == 0:
            return {'profile_type': 'text', 'error': 'No non-null values'}
        
        # Calculate text statistics
        lengths = text_series.str.len()
        
        profile = {
            'profile_type': 'text',
            'min_length': int(lengths.min()),
            'max_length': int(lengths.max()),
            'mean_length': float(lengths.mean()),
            'median_length': float(lengths.median()),
            'std_length': float(lengths.std()),
            'empty_strings': int((text_series == '').sum()),
            'whitespace_only': int(text_series.str.strip().eq('').sum())
        }
        
        # Most common values
        value_counts = text_series.value_counts().head(10)
        profile['most_common'] = [
            {'value': str(val), 'count': int(count)} 
            for val, count in value_counts.items()
        ]
        
        # Pattern detection
        profile['patterns'] = self._detect_text_patterns(text_series)
        
        # Character analysis
        profile['character_analysis'] = self._analyze_characters(text_series)
        
        return profile
    
    def _profile_datetime_column(self, series: pd.Series) -> Dict[str, Any]:
        """Profile datetime column."""
        dt_series = series.dropna()
        
        if len(dt_series) == 0:
            return {'profile_type': 'datetime', 'error': 'No non-null values'}
        
        profile = {
            'profile_type': 'datetime',
            'min_date': dt_series.min().isoformat(),
            'max_date': dt_series.max().isoformat(),
            'date_range_days': (dt_series.max() - dt_series.min()).days,
            'most_common_year': int(dt_series.dt.year.mode().iloc[0]),
            'most_common_month': int(dt_series.dt.month.mode().iloc[0]),
            'most_common_day_of_week': int(dt_series.dt.dayofweek.mode().iloc[0])
        }
        
        # Time component analysis
        if dt_series.dt.time.nunique() > 1:
            profile['has_time_component'] = True
            profile['most_common_hour'] = int(dt_series.dt.hour.mode().iloc[0])
        else:
            profile['has_time_component'] = False
        
        # Frequency analysis
        date_counts = dt_series.value_counts()
        profile['duplicate_dates'] = {
            'count': int((date_counts > 1).sum()),
            'percentage': float((date_counts > 1).sum() / len(date_counts) * 100)
        }
        
        return profile
    
    def _profile_boolean_column(self, series: pd.Series) -> Dict[str, Any]:
        """Profile boolean column."""
        bool_series = series.dropna()
        
        if len(bool_series) == 0:
            return {'profile_type': 'boolean', 'error': 'No non-null values'}
        
        true_count = bool_series.sum()
        false_count = len(bool_series) - true_count
        
        return {
            'profile_type': 'boolean',
            'true_count': int(true_count),
            'false_count': int(false_count),
            'true_percentage': float(true_count / len(bool_series) * 100),
            'false_percentage': float(false_count / len(bool_series) * 100)
        }
    
    def _analyze_data_types(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze data types and suggest improvements."""
        type_analysis = {
            'current_types': {},
            'suggested_types': {},
            'type_distribution': {},
            'conversion_recommendations': []
        }
        
        # Current types
        for col in df.columns:
            type_analysis['current_types'][col] = str(df[col].dtype)
        
        # Type distribution
        type_counts = df.dtypes.value_counts()
        type_analysis['type_distribution'] = {
            str(dtype): int(count) for dtype, count in type_counts.items()
        }
        
        # Suggest type optimizations
        for col in df.columns:
            current_type = df[col].dtype
            suggested_type = self._suggest_optimal_type(df[col])
            
            if suggested_type != str(current_type):
                type_analysis['suggested_types'][col] = suggested_type
                type_analysis['conversion_recommendations'].append({
                    'column': col,
                    'current_type': str(current_type),
                    'suggested_type': suggested_type,
                    'reason': self._get_conversion_reason(df[col], suggested_type)
                })
        
        return type_analysis
    
    def _suggest_optimal_type(self, series: pd.Series) -> str:
        """Suggest optimal data type for a series."""
        if series.dtype == 'object':
            # Try to convert to numeric
            try:
                numeric_series = pd.to_numeric(series, errors='coerce')
                if numeric_series.notna().sum() / len(series) > 0.8:  # 80% convertible
                    if all(numeric_series.dropna() == numeric_series.dropna().astype(int)):
                        return 'int64'
                    else:
                        return 'float64'
            except:
                pass
            
            # Try to convert to datetime
            try:
                datetime_series = pd.to_datetime(series, errors='coerce')
                if datetime_series.notna().sum() / len(series) > 0.8:
                    return 'datetime64[ns]'
            except:
                pass
            
            # Check if it's categorical
            if series.nunique() / len(series) < 0.1:  # Less than 10% unique values
                return 'category'
        
        elif series.dtype in ['int64', 'float64']:
            # Check if we can downcast
            if series.dtype == 'int64':
                if series.min() >= -128 and series.max() <= 127:
                    return 'int8'
                elif series.min() >= -32768 and series.max() <= 32767:
                    return 'int16'
                elif series.min() >= -2147483648 and series.max() <= 2147483647:
                    return 'int32'
            elif series.dtype == 'float64':
                if series.min() >= np.finfo(np.float32).min and series.max() <= np.finfo(np.float32).max:
                    return 'float32'
        
        return str(series.dtype)
    
    def _get_conversion_reason(self, series: pd.Series, suggested_type: str) -> str:
        """Get reason for type conversion suggestion."""
        if suggested_type in ['int8', 'int16', 'int32']:
            return "Memory optimization - values fit in smaller integer type"
        elif suggested_type == 'float32':
            return "Memory optimization - values fit in 32-bit float"
        elif suggested_type == 'category':
            return "Memory optimization - low cardinality suggests categorical data"
        elif suggested_type in ['int64', 'float64']:
            return "Type correction - values are numeric but stored as text"
        elif suggested_type == 'datetime64[ns]':
            return "Type correction - values are dates but stored as text"
        else:
            return "Type optimization recommended"
    
    def _analyze_relationships(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze relationships between columns."""
        relationships = {
            'correlations': {},
            'potential_keys': [],
            'functional_dependencies': [],
            'duplicate_columns': []
        }
        
        # Correlation analysis for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr()
            
            # Find high correlations
            high_corr_pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_value = corr_matrix.iloc[i, j]
                    if abs(corr_value) > 0.7:  # High correlation threshold
                        high_corr_pairs.append({
                            'column1': corr_matrix.columns[i],
                            'column2': corr_matrix.columns[j],
                            'correlation': float(corr_value)
                        })
            
            relationships['correlations'] = high_corr_pairs
        
        # Identify potential keys
        for col in df.columns:
            if df[col].nunique() == len(df):  # Unique values
                relationships['potential_keys'].append(col)
        
        # Find duplicate columns
        for i, col1 in enumerate(df.columns):
            for col2 in df.columns[i+1:]:
                if df[col1].equals(df[col2]):
                    relationships['duplicate_columns'].append([col1, col2])
        
        return relationships
    
    def _detect_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect common patterns in the data."""
        patterns = {
            'naming_conventions': self._analyze_naming_conventions(df.columns),
            'value_patterns': {},
            'format_patterns': {}
        }
        
        # Analyze value patterns for text columns
        for col in df.select_dtypes(include=['object']).columns:
            patterns['value_patterns'][col] = self._detect_text_patterns(df[col].dropna())
        
        return patterns
    
    def _analyze_naming_conventions(self, column_names: List[str]) -> Dict[str, Any]:
        """Analyze column naming conventions."""
        conventions = {
            'snake_case': 0,
            'camelCase': 0,
            'PascalCase': 0,
            'kebab-case': 0,
            'UPPER_CASE': 0,
            'mixed': 0
        }
        
        for name in column_names:
            if re.match(r'^[a-z]+(_[a-z]+)*$', name):
                conventions['snake_case'] += 1
            elif re.match(r'^[a-z]+([A-Z][a-z]*)*$', name):
                conventions['camelCase'] += 1
            elif re.match(r'^[A-Z][a-z]*([A-Z][a-z]*)*$', name):
                conventions['PascalCase'] += 1
            elif re.match(r'^[a-z]+(-[a-z]+)*$', name):
                conventions['kebab-case'] += 1
            elif re.match(r'^[A-Z]+(_[A-Z]+)*$', name):
                conventions['UPPER_CASE'] += 1
            else:
                conventions['mixed'] += 1
        
        # Determine dominant convention
        dominant_convention = max(conventions, key=conventions.get)
        
        return {
            'conventions': conventions,
            'dominant_convention': dominant_convention,
            'consistency_score': conventions[dominant_convention] / len(column_names)
        }
    
    def _detect_text_patterns(self, series: pd.Series) -> Dict[str, Any]:
        """Detect patterns in text data."""
        if len(series) == 0:
            return {}
        
        text_series = series.astype(str)
        
        patterns = {
            'email_like': 0,
            'phone_like': 0,
            'url_like': 0,
            'numeric_only': 0,
            'alpha_only': 0,
            'alphanumeric': 0,
            'contains_special_chars': 0,
            'all_caps': 0,
            'all_lowercase': 0,
            'title_case': 0
        }
        
        # Pattern matching
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        phone_pattern = r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$'
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        
        for value in text_series:
            if re.match(email_pattern, value):
                patterns['email_like'] += 1
            elif re.match(phone_pattern, value):
                patterns['phone_like'] += 1
            elif re.match(url_pattern, value):
                patterns['url_like'] += 1
            elif value.isdigit():
                patterns['numeric_only'] += 1
            elif value.isalpha():
                patterns['alpha_only'] += 1
            elif value.isalnum():
                patterns['alphanumeric'] += 1
            
            if any(char in value for char in '!@#$%^&*()_+-=[]{}|;:,.<>?'):
                patterns['contains_special_chars'] += 1
            
            if value.isupper():
                patterns['all_caps'] += 1
            elif value.islower():
                patterns['all_lowercase'] += 1
            elif value.istitle():
                patterns['title_case'] += 1
        
        # Convert to percentages
        total_count = len(text_series)
        for pattern_type in patterns:
            patterns[pattern_type] = {
                'count': patterns[pattern_type],
                'percentage': patterns[pattern_type] / total_count * 100
            }
        
        return patterns
    
    def _analyze_characters(self, series: pd.Series) -> Dict[str, Any]:
        """Analyze character usage in text data."""
        all_text = ' '.join(series.astype(str))
        
        return {
            'total_characters': len(all_text),
            'unique_characters': len(set(all_text)),
            'character_frequency': dict(Counter(all_text).most_common(20)),
            'has_unicode': any(ord(char) > 127 for char in all_text),
            'has_digits': any(char.isdigit() for char in all_text),
            'has_punctuation': any(not char.isalnum() and not char.isspace() for char in all_text)
        }
    
    def _calculate_quality_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate overall data quality metrics."""
        total_cells = df.size
        missing_cells = df.isnull().sum().sum()
        
        return {
            'completeness': 1 - (missing_cells / total_cells),
            'consistency': self._calculate_consistency_score(df),
            'validity': self._calculate_validity_score(df),
            'uniqueness': self._calculate_uniqueness_score(df)
        }
    
    def _calculate_consistency_score(self, df: pd.DataFrame) -> float:
        """Calculate consistency score."""
        # Simplified consistency calculation
        # In practice, this would be more sophisticated
        return 0.85  # Placeholder
    
    def _calculate_validity_score(self, df: pd.DataFrame) -> float:
        """Calculate validity score."""
        # Simplified validity calculation
        return 0.90  # Placeholder
    
    def _calculate_uniqueness_score(self, df: pd.DataFrame) -> float:
        """Calculate uniqueness score."""
        uniqueness_scores = []
        for col in df.columns:
            if len(df[col]) > 0:
                uniqueness_scores.append(df[col].nunique() / len(df[col]))
        
        return np.mean(uniqueness_scores) if uniqueness_scores else 0.0
    
    def _generate_statistical_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate statistical summary."""
        return {
            'numeric_summary': df.describe().to_dict() if len(df.select_dtypes(include=[np.number]).columns) > 0 else {},
            'categorical_summary': self._summarize_categorical_columns(df),
            'missing_data_summary': self._summarize_missing_data(df)
        }
    
    def _summarize_categorical_columns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Summarize categorical columns."""
        categorical_summary = {}
        
        for col in df.select_dtypes(include=['object', 'category']).columns:
            categorical_summary[col] = {
                'unique_count': df[col].nunique(),
                'most_frequent': df[col].mode().iloc[0] if len(df[col].mode()) > 0 else None,
                'frequency': df[col].value_counts().head(5).to_dict()
            }
        
        return categorical_summary
    
    def _summarize_missing_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Summarize missing data patterns."""
        missing_summary = {}
        
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            missing_summary[col] = {
                'missing_count': int(missing_count),
                'missing_percentage': float(missing_count / len(df) * 100)
            }
        
        return missing_summary
    
    def _generate_profiling_recommendations(self, profile: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on profiling results."""
        recommendations = []
        
        # Data quality recommendations
        quality_metrics = profile.get('quality_metrics', {})
        if quality_metrics.get('completeness', 1) < 0.9:
            recommendations.append("Address missing data issues to improve completeness")
        
        # Type optimization recommendations
        type_analysis = profile.get('data_types', {})
        if type_analysis.get('conversion_recommendations'):
            recommendations.append("Consider optimizing data types to reduce memory usage")
        
        # Relationship recommendations
        relationships = profile.get('relationships', {})
        if relationships.get('duplicate_columns'):
            recommendations.append("Remove duplicate columns to reduce redundancy")
        
        if relationships.get('correlations'):
            recommendations.append("Review highly correlated columns for potential feature engineering")
        
        return recommendations
