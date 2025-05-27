"""
Disaster Recovery and Rollback Module

NHS-compliant disaster recovery and rollback capabilities for data migration.
"""

import os
import json
import logging
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from django.db import transaction, connection
from django.conf import settings
from django.utils import timezone
from django.core.management import call_command
from django.core.serializers import serialize, deserialize
from core.models import AuditLog
from orchestrator.models import MigrationJob
from nhs_compliance.models import CQCAuditTrail, PatientSafetyIncident

logger = logging.getLogger(__name__)


class DisasterRecoveryManager:
    """
    NHS-compliant disaster recovery manager with rollback capabilities.
    
    Features:
    - Automated backup creation before migration
    - Point-in-time recovery
    - Data integrity verification
    - Rollback with audit trails
    - Patient safety incident tracking
    """
    
    def __init__(self, migration_job: MigrationJob):
        """Initialize disaster recovery manager."""
        self.migration_job = migration_job
        self.backup_dir = self._get_backup_directory()
        self.recovery_log = []
    
    def _get_backup_directory(self) -> str:
        """Get backup directory for this migration job."""
        backup_root = getattr(settings, 'NHS_BACKUP_ROOT', '/var/backups/migrateiq')
        job_backup_dir = os.path.join(
            backup_root,
            f"job_{self.migration_job.id}_{self.migration_job.created_at.strftime('%Y%m%d_%H%M%S')}"
        )
        os.makedirs(job_backup_dir, exist_ok=True)
        return job_backup_dir
    
    def create_pre_migration_backup(self) -> Dict[str, Any]:
        """
        Create comprehensive backup before migration starts.
        
        Returns:
            Backup metadata
        """
        backup_timestamp = timezone.now()
        backup_id = f"backup_{backup_timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Creating pre-migration backup: {backup_id}")
        
        try:
            # Create backup metadata
            backup_metadata = {
                'backup_id': backup_id,
                'migration_job_id': self.migration_job.id,
                'timestamp': backup_timestamp.isoformat(),
                'backup_type': 'pre_migration',
                'components': [],
            }
            
            # Backup database
            db_backup_path = self._backup_database(backup_id)
            if db_backup_path:
                backup_metadata['components'].append({
                    'type': 'database',
                    'path': db_backup_path,
                    'size': os.path.getsize(db_backup_path),
                })
            
            # Backup source data
            source_backup_path = self._backup_source_data(backup_id)
            if source_backup_path:
                backup_metadata['components'].append({
                    'type': 'source_data',
                    'path': source_backup_path,
                    'size': self._get_directory_size(source_backup_path),
                })
            
            # Backup configuration
            config_backup_path = self._backup_configuration(backup_id)
            if config_backup_path:
                backup_metadata['components'].append({
                    'type': 'configuration',
                    'path': config_backup_path,
                    'size': os.path.getsize(config_backup_path),
                })
            
            # Save backup metadata
            metadata_path = os.path.join(self.backup_dir, f"{backup_id}_metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(backup_metadata, f, indent=2, default=str)
            
            # Create audit trail
            self._create_audit_trail(
                'BACKUP_CREATED',
                f"Pre-migration backup created: {backup_id}",
                backup_metadata
            )
            
            logger.info(f"Pre-migration backup completed: {backup_id}")
            return backup_metadata
            
        except Exception as e:
            logger.error(f"Failed to create pre-migration backup: {str(e)}")
            self._create_safety_incident(
                'BACKUP_FAILURE',
                f"Failed to create pre-migration backup: {str(e)}",
                'HIGH'
            )
            raise
    
    def _backup_database(self, backup_id: str) -> Optional[str]:
        """Backup database using pg_dump or equivalent."""
        try:
            db_config = settings.DATABASES['default']
            backup_file = os.path.join(self.backup_dir, f"{backup_id}_database.sql")
            
            if db_config['ENGINE'] == 'django.db.backends.postgresql':
                # PostgreSQL backup
                import subprocess
                cmd = [
                    'pg_dump',
                    '-h', db_config.get('HOST', 'localhost'),
                    '-p', str(db_config.get('PORT', 5432)),
                    '-U', db_config['USER'],
                    '-d', db_config['NAME'],
                    '-f', backup_file,
                    '--verbose',
                    '--no-password'
                ]
                
                env = os.environ.copy()
                env['PGPASSWORD'] = db_config['PASSWORD']
                
                result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info(f"Database backup created: {backup_file}")
                    return backup_file
                else:
                    logger.error(f"Database backup failed: {result.stderr}")
                    return None
            
            else:
                # Django fixtures backup (fallback)
                call_command('dumpdata', '--output', backup_file, '--format', 'json')
                logger.info(f"Django fixtures backup created: {backup_file}")
                return backup_file
                
        except Exception as e:
            logger.error(f"Database backup failed: {str(e)}")
            return None
    
    def _backup_source_data(self, backup_id: str) -> Optional[str]:
        """Backup source data files."""
        try:
            source_data_dir = getattr(settings, 'MIGRATION_SOURCE_DATA_DIR', None)
            if not source_data_dir or not os.path.exists(source_data_dir):
                logger.warning("No source data directory to backup")
                return None
            
            backup_dir = os.path.join(self.backup_dir, f"{backup_id}_source_data")
            shutil.copytree(source_data_dir, backup_dir)
            
            logger.info(f"Source data backup created: {backup_dir}")
            return backup_dir
            
        except Exception as e:
            logger.error(f"Source data backup failed: {str(e)}")
            return None
    
    def _backup_configuration(self, backup_id: str) -> Optional[str]:
        """Backup migration configuration."""
        try:
            config_data = {
                'migration_job': {
                    'id': self.migration_job.id,
                    'name': self.migration_job.name,
                    'source_config': self.migration_job.source_config,
                    'target_config': self.migration_job.target_config,
                    'mapping_config': getattr(self.migration_job, 'mapping_config', {}),
                },
                'system_settings': {
                    'debug': settings.DEBUG,
                    'database_config': {
                        'engine': settings.DATABASES['default']['ENGINE'],
                        'name': settings.DATABASES['default']['NAME'],
                    },
                },
                'backup_timestamp': timezone.now().isoformat(),
            }
            
            config_file = os.path.join(self.backup_dir, f"{backup_id}_config.json")
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)
            
            logger.info(f"Configuration backup created: {config_file}")
            return config_file
            
        except Exception as e:
            logger.error(f"Configuration backup failed: {str(e)}")
            return None
    
    def initiate_rollback(self, backup_id: str, reason: str) -> Dict[str, Any]:
        """
        Initiate rollback to a previous backup.
        
        Args:
            backup_id: ID of backup to restore
            reason: Reason for rollback
            
        Returns:
            Rollback result
        """
        rollback_timestamp = timezone.now()
        rollback_id = f"rollback_{rollback_timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        logger.warning(f"Initiating rollback: {rollback_id} (backup: {backup_id})")
        
        try:
            # Load backup metadata
            metadata_path = os.path.join(self.backup_dir, f"{backup_id}_metadata.json")
            if not os.path.exists(metadata_path):
                raise FileNotFoundError(f"Backup metadata not found: {backup_id}")
            
            with open(metadata_path, 'r') as f:
                backup_metadata = json.load(f)
            
            rollback_result = {
                'rollback_id': rollback_id,
                'backup_id': backup_id,
                'timestamp': rollback_timestamp.isoformat(),
                'reason': reason,
                'status': 'in_progress',
                'steps_completed': [],
                'errors': [],
            }
            
            # Create safety incident for rollback
            self._create_safety_incident(
                'SYSTEM_ROLLBACK',
                f"System rollback initiated: {reason}",
                'HIGH'
            )
            
            # Step 1: Stop migration processes
            self._stop_migration_processes()
            rollback_result['steps_completed'].append('migration_processes_stopped')
            
            # Step 2: Restore database
            if self._restore_database(backup_id, backup_metadata):
                rollback_result['steps_completed'].append('database_restored')
            else:
                rollback_result['errors'].append('database_restore_failed')
            
            # Step 3: Restore source data
            if self._restore_source_data(backup_id, backup_metadata):
                rollback_result['steps_completed'].append('source_data_restored')
            else:
                rollback_result['errors'].append('source_data_restore_failed')
            
            # Step 4: Verify data integrity
            integrity_check = self._verify_data_integrity()
            if integrity_check['passed']:
                rollback_result['steps_completed'].append('data_integrity_verified')
            else:
                rollback_result['errors'].append('data_integrity_check_failed')
                rollback_result['integrity_issues'] = integrity_check['issues']
            
            # Determine final status
            if not rollback_result['errors']:
                rollback_result['status'] = 'completed'
                logger.info(f"Rollback completed successfully: {rollback_id}")
            else:
                rollback_result['status'] = 'completed_with_errors'
                logger.error(f"Rollback completed with errors: {rollback_result['errors']}")
            
            # Create audit trail
            self._create_audit_trail(
                'ROLLBACK_COMPLETED',
                f"System rollback completed: {rollback_id}",
                rollback_result
            )
            
            return rollback_result
            
        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            rollback_result = {
                'rollback_id': rollback_id,
                'backup_id': backup_id,
                'timestamp': rollback_timestamp.isoformat(),
                'reason': reason,
                'status': 'failed',
                'error': str(e),
            }
            
            self._create_safety_incident(
                'ROLLBACK_FAILURE',
                f"System rollback failed: {str(e)}",
                'CRITICAL'
            )
            
            return rollback_result
    
    def _stop_migration_processes(self):
        """Stop all running migration processes."""
        try:
            # Update migration job status
            self.migration_job.status = 'CANCELLED'
            self.migration_job.save()
            
            # Stop Celery tasks (if using Celery)
            try:
                from celery import current_app
                current_app.control.revoke(
                    self.migration_job.celery_task_id,
                    terminate=True
                )
            except ImportError:
                pass
            
            logger.info("Migration processes stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop migration processes: {str(e)}")
    
    def _restore_database(self, backup_id: str, backup_metadata: Dict[str, Any]) -> bool:
        """Restore database from backup."""
        try:
            # Find database backup component
            db_component = None
            for component in backup_metadata['components']:
                if component['type'] == 'database':
                    db_component = component
                    break
            
            if not db_component:
                logger.error("No database backup found")
                return False
            
            backup_file = db_component['path']
            if not os.path.exists(backup_file):
                logger.error(f"Database backup file not found: {backup_file}")
                return False
            
            db_config = settings.DATABASES['default']
            
            if db_config['ENGINE'] == 'django.db.backends.postgresql':
                # PostgreSQL restore
                import subprocess
                cmd = [
                    'psql',
                    '-h', db_config.get('HOST', 'localhost'),
                    '-p', str(db_config.get('PORT', 5432)),
                    '-U', db_config['USER'],
                    '-d', db_config['NAME'],
                    '-f', backup_file,
                    '--quiet'
                ]
                
                env = os.environ.copy()
                env['PGPASSWORD'] = db_config['PASSWORD']
                
                result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info("Database restored successfully")
                    return True
                else:
                    logger.error(f"Database restore failed: {result.stderr}")
                    return False
            
            else:
                # Django fixtures restore (fallback)
                call_command('loaddata', backup_file)
                logger.info("Database restored from Django fixtures")
                return True
                
        except Exception as e:
            logger.error(f"Database restore failed: {str(e)}")
            return False
    
    def _restore_source_data(self, backup_id: str, backup_metadata: Dict[str, Any]) -> bool:
        """Restore source data from backup."""
        try:
            # Find source data backup component
            source_component = None
            for component in backup_metadata['components']:
                if component['type'] == 'source_data':
                    source_component = component
                    break
            
            if not source_component:
                logger.warning("No source data backup found")
                return True  # Not an error if no source data
            
            backup_dir = source_component['path']
            source_data_dir = getattr(settings, 'MIGRATION_SOURCE_DATA_DIR', None)
            
            if not source_data_dir:
                logger.warning("No source data directory configured")
                return True
            
            if os.path.exists(source_data_dir):
                shutil.rmtree(source_data_dir)
            
            shutil.copytree(backup_dir, source_data_dir)
            logger.info("Source data restored successfully")
            return True
            
        except Exception as e:
            logger.error(f"Source data restore failed: {str(e)}")
            return False
    
    def _verify_data_integrity(self) -> Dict[str, Any]:
        """Verify data integrity after restore."""
        integrity_result = {
            'passed': True,
            'issues': [],
            'checks_performed': [],
        }
        
        try:
            # Check database connectivity
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            integrity_result['checks_performed'].append('database_connectivity')
            
            # Check critical tables exist
            critical_tables = ['auth_user', 'core_tenant', 'orchestrator_migrationjob']
            with connection.cursor() as cursor:
                for table in critical_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    if count >= 0:  # Table exists and is accessible
                        integrity_result['checks_performed'].append(f'table_{table}')
            
            # Check migration job status
            try:
                job = MigrationJob.objects.get(id=self.migration_job.id)
                if job:
                    integrity_result['checks_performed'].append('migration_job_accessible')
            except MigrationJob.DoesNotExist:
                integrity_result['passed'] = False
                integrity_result['issues'].append('migration_job_not_found')
            
            logger.info(f"Data integrity check completed: {integrity_result}")
            
        except Exception as e:
            integrity_result['passed'] = False
            integrity_result['issues'].append(f"integrity_check_error: {str(e)}")
            logger.error(f"Data integrity check failed: {str(e)}")
        
        return integrity_result
    
    def _create_audit_trail(self, category: str, description: str, details: Dict[str, Any]):
        """Create CQC audit trail entry."""
        try:
            from nhs_compliance.models import NHSOrganization
            
            # Get NHS organization (assuming one per tenant)
            nhs_org = NHSOrganization.objects.filter(
                tenant=self.migration_job.tenant
            ).first()
            
            if nhs_org:
                CQCAuditTrail.objects.create(
                    organization=nhs_org,
                    category='SYSTEM_CHANGE',
                    severity='HIGH',
                    event_description=description,
                    technical_details=details,
                    system_component='disaster_recovery',
                    patient_data_affected=True,  # Assume patient data is involved
                )
        except Exception as e:
            logger.error(f"Failed to create audit trail: {str(e)}")
    
    def _create_safety_incident(self, incident_type: str, description: str, severity: str):
        """Create patient safety incident record."""
        try:
            from nhs_compliance.models import NHSOrganization
            
            # Get NHS organization
            nhs_org = NHSOrganization.objects.filter(
                tenant=self.migration_job.tenant
            ).first()
            
            if nhs_org:
                PatientSafetyIncident.objects.create(
                    organization=nhs_org,
                    incident_date=timezone.now(),
                    incident_type=incident_type,
                    incident_description=description,
                    harm_level='NO_HARM',  # Default, should be assessed
                    reported_by=None,  # System-generated
                )
        except Exception as e:
            logger.error(f"Failed to create safety incident: {str(e)}")
    
    def _get_directory_size(self, directory: str) -> int:
        """Get total size of directory in bytes."""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total_size += os.path.getsize(filepath)
        return total_size
