import os
import hashlib
import requests
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app

def hash_password(password):
    """Generate a hashed password using Werkzeug's security functions"""
    return generate_password_hash(password)

def verify_password(hashed_password, password):
    """Verify a password against a hash using Werkzeug's security functions"""
    return check_password_hash(hashed_password, password)

def generate_safe_filename(filename):
    """Generate a secure filename with a hash to avoid collisions"""
    # Get file extension
    name, extension = os.path.splitext(filename)
    # Create a unique hash based on filename + timestamp
    hash_obj = hashlib.md5((name + str(os.urandom(8))).encode('utf-8'))
    hashed_name = hash_obj.hexdigest()
    # Combine hash with original extension
    return f"{hashed_name}{extension}"

def save_file(file, upload_folder):
    """Save a file to the upload folder with a secure filename"""
    if file:
        # Secure the filename to prevent any malicious paths
        original_filename = secure_filename(file.filename)
        # Generate a safe filename to avoid collisions
        safe_filename = generate_safe_filename(original_filename)
        # Create full path
        file_path = os.path.join(upload_folder, safe_filename)
        # Save the file
        file.save(file_path)
        # Return the filename and path
        return original_filename, safe_filename, file_path
    return None, None, None

def enhance_image_with_stable_diffusion(input_path, output_path):
    """Enhance an image using a local Stable Diffusion model"""
    try:
        url = current_app.config['STABLE_DIFFUSION_API_URL']
        with open(input_path, 'rb') as img_file:
            files = {'image': img_file}
            data = {
                'prompt': 'vector line art, clean lines, minimalist style',
                'negative_prompt': 'blur, pixelated, low quality',
                'steps': 30,
                'guidance_scale': 7.5
            }
            response = requests.post(url, files=files, data=data)
            
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
        else:
            return False
    except Exception as e:
        print(f"Error enhancing image with Stable Diffusion: {str(e)}")
        return False

def enhance_image_with_ollama(input_path, output_path):
    """Enhance an image using the Ollama model for vector-line art"""
    try:
        url = current_app.config['OLLAMA_API_URL']
        model = current_app.config['OLLAMA_MODEL']
        
        # Read the image file as binary
        with open(input_path, 'rb') as img_file:
            img_data = img_file.read()
        
        # Base64 encode the image
        import base64
        img_base64 = base64.b64encode(img_data).decode('utf-8')
        
        # Prepare the payload
        payload = {
            'model': model,
            'prompt': 'Convert this image to vector-line art style:',
            'images': [img_base64],
            'stream': False
        }
        
        # Send request to Ollama API
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            # Process the response - this will depend on how Ollama returns the enhanced image
            # For now, let's assume it returns a base64 encoded image
            if 'image' in data:
                img_data = base64.b64decode(data['image'])
                with open(output_path, 'wb') as f:
                    f.write(img_data)
                return True
            else:
                return False
        else:
            return False
    except Exception as e:
        print(f"Error enhancing image with Ollama: {str(e)}")
        return False
