"""
NHS-Compliant Encryption Module

Advanced encryption utilities meeting NHS Digital Security and Protection Toolkit requirements.
"""

import os
import base64
import hashlib
import secrets
import logging
from typing import Union, Tuple, Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class NHSEncryption:
    """
    NHS-compliant encryption service implementing DSPT requirements.
    
    Features:
    - AES-256 encryption for data at rest
    - RSA-4096 for key exchange
    - PBKDF2 for key derivation
    - Secure key management
    - Audit logging for all operations
    """
    
    # NHS DSPT encryption standards
    AES_KEY_SIZE = 32  # 256 bits
    RSA_KEY_SIZE = 4096
    PBKDF2_ITERATIONS = 100000
    SALT_SIZE = 32
    
    def __init__(self):
        """Initialize NHS encryption service."""
        self.backend = default_backend()
        self._validate_configuration()
    
    def _validate_configuration(self):
        """Validate encryption configuration meets NHS requirements."""
        required_settings = [
            'NHS_ENCRYPTION_MASTER_KEY',
            'NHS_ENCRYPTION_KEY_ROTATION_DAYS',
        ]
        
        for setting in required_settings:
            if not hasattr(settings, setting):
                raise ImproperlyConfigured(f"Missing required setting: {setting}")
    
    def generate_key(self) -> bytes:
        """Generate a new AES-256 encryption key."""
        key = secrets.token_bytes(self.AES_KEY_SIZE)
        logger.info("Generated new AES-256 encryption key")
        return key
    
    def derive_key_from_password(self, password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """
        Derive encryption key from password using PBKDF2.
        
        Args:
            password: Password to derive key from
            salt: Optional salt (generated if not provided)
            
        Returns:
            Tuple of (derived_key, salt)
        """
        if salt is None:
            salt = secrets.token_bytes(self.SALT_SIZE)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.AES_KEY_SIZE,
            salt=salt,
            iterations=self.PBKDF2_ITERATIONS,
            backend=self.backend
        )
        
        key = kdf.derive(password.encode('utf-8'))
        logger.info("Derived encryption key from password using PBKDF2")
        return key, salt
    
    def encrypt_data(self, data: Union[str, bytes], key: Optional[bytes] = None) -> Dict[str, str]:
        """
        Encrypt data using AES-256-GCM.
        
        Args:
            data: Data to encrypt
            key: Encryption key (uses master key if not provided)
            
        Returns:
            Dictionary containing encrypted data and metadata
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        if key is None:
            key = self._get_master_key()
        
        # Generate random IV
        iv = secrets.token_bytes(12)  # 96 bits for GCM
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=self.backend
        )
        
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        # Prepare result
        result = {
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
            'iv': base64.b64encode(iv).decode('utf-8'),
            'tag': base64.b64encode(encryptor.tag).decode('utf-8'),
            'algorithm': 'AES-256-GCM',
            'key_id': self._get_key_id(key),
        }
        
        logger.info(f"Encrypted data using AES-256-GCM (size: {len(data)} bytes)")
        return result
    
    def decrypt_data(self, encrypted_data: Dict[str, str], key: Optional[bytes] = None) -> bytes:
        """
        Decrypt data encrypted with AES-256-GCM.
        
        Args:
            encrypted_data: Dictionary containing encrypted data and metadata
            key: Decryption key (uses master key if not provided)
            
        Returns:
            Decrypted data as bytes
        """
        if key is None:
            key = self._get_master_key()
        
        try:
            ciphertext = base64.b64decode(encrypted_data['ciphertext'])
            iv = base64.b64decode(encrypted_data['iv'])
            tag = base64.b64decode(encrypted_data['tag'])
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(key),
                modes.GCM(iv, tag),
                backend=self.backend
            )
            
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            logger.info(f"Decrypted data using AES-256-GCM (size: {len(plaintext)} bytes)")
            return plaintext
            
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise ValueError("Failed to decrypt data - invalid key or corrupted data")
    
    def encrypt_file(self, file_path: str, output_path: Optional[str] = None, key: Optional[bytes] = None) -> str:
        """
        Encrypt a file using AES-256-GCM.
        
        Args:
            file_path: Path to file to encrypt
            output_path: Path for encrypted file (defaults to file_path + '.enc')
            key: Encryption key (uses master key if not provided)
            
        Returns:
            Path to encrypted file
        """
        if output_path is None:
            output_path = file_path + '.enc'
        
        if key is None:
            key = self._get_master_key()
        
        # Read file
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # Encrypt data
        encrypted_data = self.encrypt_data(data, key)
        
        # Write encrypted file with metadata
        with open(output_path, 'w') as f:
            import json
            json.dump(encrypted_data, f)
        
        logger.info(f"Encrypted file: {file_path} -> {output_path}")
        return output_path
    
    def decrypt_file(self, encrypted_file_path: str, output_path: Optional[str] = None, key: Optional[bytes] = None) -> str:
        """
        Decrypt a file encrypted with encrypt_file.
        
        Args:
            encrypted_file_path: Path to encrypted file
            output_path: Path for decrypted file
            key: Decryption key (uses master key if not provided)
            
        Returns:
            Path to decrypted file
        """
        if output_path is None:
            output_path = encrypted_file_path.replace('.enc', '')
        
        if key is None:
            key = self._get_master_key()
        
        # Read encrypted file
        with open(encrypted_file_path, 'r') as f:
            import json
            encrypted_data = json.load(f)
        
        # Decrypt data
        decrypted_data = self.decrypt_data(encrypted_data, key)
        
        # Write decrypted file
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
        
        logger.info(f"Decrypted file: {encrypted_file_path} -> {output_path}")
        return output_path
    
    def generate_rsa_keypair(self) -> Tuple[bytes, bytes]:
        """
        Generate RSA-4096 key pair for key exchange.
        
        Returns:
            Tuple of (private_key_pem, public_key_pem)
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=self.RSA_KEY_SIZE,
            backend=self.backend
        )
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        logger.info("Generated RSA-4096 key pair")
        return private_pem, public_pem
    
    def rsa_encrypt(self, data: bytes, public_key_pem: bytes) -> bytes:
        """Encrypt data using RSA public key."""
        public_key = serialization.load_pem_public_key(public_key_pem, backend=self.backend)
        
        ciphertext = public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        logger.info(f"RSA encrypted data (size: {len(data)} bytes)")
        return ciphertext
    
    def rsa_decrypt(self, ciphertext: bytes, private_key_pem: bytes) -> bytes:
        """Decrypt data using RSA private key."""
        private_key = serialization.load_pem_private_key(
            private_key_pem, 
            password=None, 
            backend=self.backend
        )
        
        plaintext = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        logger.info(f"RSA decrypted data (size: {len(plaintext)} bytes)")
        return plaintext
    
    def hash_data(self, data: Union[str, bytes], algorithm: str = 'SHA256') -> str:
        """
        Hash data using specified algorithm.
        
        Args:
            data: Data to hash
            algorithm: Hash algorithm (SHA256, SHA512)
            
        Returns:
            Hex-encoded hash
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        if algorithm == 'SHA256':
            hash_obj = hashlib.sha256(data)
        elif algorithm == 'SHA512':
            hash_obj = hashlib.sha512(data)
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")
        
        return hash_obj.hexdigest()
    
    def _get_master_key(self) -> bytes:
        """Get the master encryption key."""
        master_key_b64 = getattr(settings, 'NHS_ENCRYPTION_MASTER_KEY', None)
        if not master_key_b64:
            raise ImproperlyConfigured("NHS_ENCRYPTION_MASTER_KEY not configured")
        
        try:
            return base64.b64decode(master_key_b64)
        except Exception as e:
            raise ImproperlyConfigured(f"Invalid NHS_ENCRYPTION_MASTER_KEY: {str(e)}")
    
    def _get_key_id(self, key: bytes) -> str:
        """Generate a key ID for tracking purposes."""
        return hashlib.sha256(key).hexdigest()[:16]


class PatientDataEncryption(NHSEncryption):
    """Specialized encryption for patient data with additional safeguards."""
    
    def encrypt_patient_data(self, patient_data: Dict[str, Any], nhs_number: str) -> Dict[str, str]:
        """
        Encrypt patient data with NHS Number as additional entropy.
        
        Args:
            patient_data: Patient data to encrypt
            nhs_number: NHS Number for additional security
            
        Returns:
            Encrypted patient data
        """
        # Serialize patient data
        import json
        data_json = json.dumps(patient_data, sort_keys=True)
        
        # Derive key using NHS Number as salt
        nhs_salt = hashlib.sha256(nhs_number.encode()).digest()
        master_key = self._get_master_key()
        
        # Combine master key with NHS-derived salt
        combined_key = hashlib.pbkdf2_hmac(
            'sha256',
            master_key,
            nhs_salt,
            self.PBKDF2_ITERATIONS,
            self.AES_KEY_SIZE
        )
        
        # Encrypt with combined key
        encrypted_data = self.encrypt_data(data_json, combined_key)
        encrypted_data['nhs_number_hash'] = self.hash_data(nhs_number)
        
        logger.info(f"Encrypted patient data for NHS Number: {nhs_number[:3]}***{nhs_number[-3:]}")
        return encrypted_data
    
    def decrypt_patient_data(self, encrypted_data: Dict[str, str], nhs_number: str) -> Dict[str, Any]:
        """
        Decrypt patient data using NHS Number.
        
        Args:
            encrypted_data: Encrypted patient data
            nhs_number: NHS Number for decryption
            
        Returns:
            Decrypted patient data
        """
        # Verify NHS Number matches
        nhs_hash = self.hash_data(nhs_number)
        if encrypted_data.get('nhs_number_hash') != nhs_hash:
            raise ValueError("NHS Number does not match encrypted data")
        
        # Derive key using NHS Number as salt
        nhs_salt = hashlib.sha256(nhs_number.encode()).digest()
        master_key = self._get_master_key()
        
        # Combine master key with NHS-derived salt
        combined_key = hashlib.pbkdf2_hmac(
            'sha256',
            master_key,
            nhs_salt,
            self.PBKDF2_ITERATIONS,
            self.AES_KEY_SIZE
        )
        
        # Decrypt with combined key
        decrypted_json = self.decrypt_data(encrypted_data, combined_key)
        
        # Parse JSON
        import json
        patient_data = json.loads(decrypted_json.decode('utf-8'))
        
        logger.info(f"Decrypted patient data for NHS Number: {nhs_number[:3]}***{nhs_number[-3:]}")
        return patient_data


# Global encryption instance
nhs_encryption = NHSEncryption()
patient_encryption = PatientDataEncryption()
