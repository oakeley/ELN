import hashlib
import hmac
import base64
import time
import json
from datetime import datetime
import os
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from flask import current_app, session

class DigitalSignature:
    def __init__(self):
        """Initialize the digital signature system"""
        # In a production environment, you'd store these keys securely
        # For this example, we'll generate keys on initialization
        self.private_key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys', 'private_key.pem')
        self.public_key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys', 'public_key.pem')
        
        # Create keys directory if it doesn't exist
        os.makedirs(os.path.dirname(self.private_key_path), exist_ok=True)
        
        # Generate or load keys
        self._load_or_generate_keys()
    
    def _load_or_generate_keys(self):
        """Load existing keys or generate new ones if they don't exist"""
        try:
            if os.path.exists(self.private_key_path) and os.path.exists(self.public_key_path):
                # Load existing keys
                with open(self.private_key_path, "rb") as key_file:
                    self.private_key = serialization.load_pem_private_key(
                        key_file.read(),
                        password=None,
                        backend=default_backend()
                    )
                
                with open(self.public_key_path, "rb") as key_file:
                    self.public_key = serialization.load_pem_public_key(
                        key_file.read(),
                        backend=default_backend()
                    )
                
                print("Loaded existing signature keys")
            else:
                # Generate new key pair
                self.private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=2048,
                    backend=default_backend()
                )
                self.public_key = self.private_key.public_key()
                
                # Save private key
                pem = self.private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                )
                with open(self.private_key_path, 'wb') as f:
                    f.write(pem)
                
                # Save public key
                pem = self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                with open(self.public_key_path, 'wb') as f:
                    f.write(pem)
                
                print("Generated new signature keys")
        except Exception as e:
            print(f"Error managing signature keys: {str(e)}")
            # Fallback to simple HMAC if key generation fails
            self.private_key = None
            self.public_key = None
    
    def create_timestamp(self):
        """Create a secure timestamp with current time"""
        timestamp = datetime.utcnow().isoformat()
        return timestamp
    
    def create_signature(self, username, timestamp, additional_data=None):
        """
        Create a digital signature using RSA
        
        Args:
            username: The username doing the signing
            timestamp: The timestamp of the signature
            additional_data: Any additional data to include in the signature
            
        Returns:
            Dictionary with signature information
        """
        # Create the data to sign
        data = {
            'username': username,
            'timestamp': timestamp,
            'data': additional_data
        }
        
        # Convert to JSON string
        data_json = json.dumps(data, sort_keys=True)
        
        try:
            if self.private_key:
                # Create RSA signature
                signature = self.private_key.sign(
                    data_json.encode('utf-8'),
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
                
                # Base64 encode for storage and display
                signature_b64 = base64.b64encode(signature).decode('utf-8')
                
                return {
                    'username': username,
                    'timestamp': timestamp,
                    'data': additional_data,
                    'signature': signature_b64,
                    'algorithm': 'RSA-PSS',
                    'verification': f"To verify: Use RSA-PSS with SHA-256"
                }
            else:
                # Fallback to HMAC
                # In a real application, you'd use a secure key stored in an environment variable
                secret_key = current_app.config.get('SECRET_KEY', 'fallback-secret').encode('utf-8')
                
                # Create HMAC signature
                signature = hmac.new(
                    secret_key,
                    data_json.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                
                return {
                    'username': username,
                    'timestamp': timestamp,
                    'data': additional_data,
                    'signature': signature,
                    'algorithm': 'HMAC-SHA256',
                    'verification': f"To verify: Use HMAC with SHA-256"
                }
        except Exception as e:
            print(f"Error creating signature: {str(e)}")
            # Return a simple fallback
            return {
                'username': username,
                'timestamp': timestamp,
                'data': additional_data,
                'signature': "signature-generation-failed",
                'algorithm': 'none',
                'error': str(e)
            }
    
    def verify_signature(self, data, signature_b64):
        """
        Verify a digital signature
        
        Args:
            data: The original data that was signed (as JSON string)
            signature_b64: The base64-encoded signature
            
        Returns:
            Boolean indicating if signature is valid
        """
        try:
            if self.public_key:
                # Decode the signature
                signature = base64.b64decode(signature_b64)
                
                # Verify the signature
                self.public_key.verify(
                    signature,
                    data.encode('utf-8'),
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
                
                # If no exception was raised, signature is valid
                return True
            else:
                # Fallback to HMAC verification
                secret_key = current_app.config.get('SECRET_KEY', 'fallback-secret').encode('utf-8')
                
                expected_signature = hmac.new(
                    secret_key,
                    data.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                
                return signature_b64 == expected_signature
        except Exception as e:
            print(f"Signature verification failed: {str(e)}")
            return False
    
    def format_signature_for_display(self, signature_data):
        """Format signature data for display in documents"""
        username = signature_data.get('username', 'Unknown User')
        timestamp = signature_data.get('timestamp', 'Unknown Time')
        algorithm = signature_data.get('algorithm', 'Unknown')
        signature = signature_data.get('signature', 'Invalid')[:16] + '...'  # Show only part of the signature
        
        return f"Signed by {username} at {timestamp} using {algorithm} [{signature}]"
    
    def format_signature_for_latex(self, signature_data):
        """Format signature data for inclusion in LaTeX documents"""
        username = self.tex_escape(signature_data.get('username', 'Unknown User'))
        timestamp = self.tex_escape(signature_data.get('timestamp', 'Unknown Time'))
        algorithm = self.tex_escape(signature_data.get('algorithm', 'Unknown'))
        signature = self.tex_escape(signature_data.get('signature', 'Invalid')[:16] + '...')
        
        return f"""\\begin{{center}}
\\framebox{{
\\begin{{minipage}}{{0.8\\textwidth}}
\\textbf{{Digital Signature}}\\\\
Signed by: {username}\\\\
Date and Time: {timestamp}\\\\
Method: {algorithm}\\\\
Signature: {signature}\\\\
\\end{{minipage}}
}}
\\end{{center}}"""
    
    @staticmethod
    def tex_escape(text):
        """Escape special LaTeX characters"""
        if text is None:
            return ""
        
        conv = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\^{}',
            '\\': r'\textbackslash{}',
            '<': r'\textless{}',
            '>': r'\textgreater{}',
        }
        regex = re.compile('|'.join(re.escape(key) for key in sorted(conv.keys(), key=lambda item: -len(item))))
        return regex.sub(lambda match: conv[match.group()], text)
