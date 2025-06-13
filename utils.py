import io
import base64
import uuid
import numpy as np
import cv2
import matplotlib.pyplot as plt
from PIL import datetime
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RPImage, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os
import requests
from io import BytesIO
import json

try:
    import pydicom
    PYDICOM_AVAILABLE = True
except ImportError:
    PYDICOM_AVAILABLE = False

try:
    import nibabel as nib
    NIBABEL_AVAILABLE = True
except ImportError:
    NIBABEL_AVAILABLE = False

try:
    from Bio import Entrez
    Entrez.email = "subhashkr855@gmail.com"
    BIOPYTNON_AVAILABLE = True
except ImportError:
    BIOPYTNON_AVAILABLE = False


def process_file(upload_file):
    """Process different file types (images, DICOM, NIfTI)"""
    file_extension = upload_file.name.split('.')[-1].lower()

    if file_extension in ['jpg', 'jpeg', 'png']:

        image = Image.open(upload_file)
        return {"type": "image", "data": image, "array": np.array(image)}
    
    elif file_extension in ['dcm'] and PYDICOM_AVAILABLE:
        try:
            bytes_data = upload_file.getvalues()
            with io.BytesIO(bytes_data) as dcm_bytes:
                dicom = pydicom.dcmread(dcm_bytes)
                image_array = dicom.pixel_array

                #Convert to 8-bit for display
                image_array = ((image_array - image_array.min())/(image_array.max() - image_array.min()) * 255).astype(np.uint8))

                return {
                    "type": "dicom",
                    "data": Image.fromarray(image_array),
                    "array": image_array,
                    "metadata": {
                        "PatientID": getattr(dicom, "PatientID", "Unknown"),
                        "StudyDate": getattr(dicom, "StudyDate", "Unknown"),
                        "Modality": getattr(dicom, "Modality", "Unknown")
                    }
                }
            
        except Exception as e:
            print(f"Enter processing DICOM: {e}")
            return None
        
    elif file_extension in ['nii', 'nii.gz'] and NIBABEL_AVAILABLE:
        try:
            bytes_data = upload_file.getvalue()
            with io.BytesIO(bytes_data) as nii_bytes:
                temp_path = f"temp_{uuid.uuid4()}.nii.gz"
                with open(temp_path, "wb") as f:
                    f.write(nii_bytes.read())

                    nii_img = nib.load(temp_path)
                    nii_data = nii_img.get_fdata()

                    #make a middle slice for preview
                    middle_slice = nii_data.shape[2] // 2
                    image_array = nii_data[:, :, middle_slice]

                    #Normalize for display
                    image_array = ((image_array - image_array.min())/(image_array.max() - image_array.min()) * 255).astype(np.uint8))

                    # Clean up temp file
                    os.remove(temp_path)

                    return {
                        "type": "nifti",
                        "data": Image.fromarray(image_array),
                        "array": image_array,
                        "metadata": {
                            "Dimensions": nii_data.shape,
                            "Voxel Size": nii_img.header.get_zooms()
                        }
                    }

        except Exception as e:
            print(f"Error Processing NIFTI: {e}")
            return None
            

    elif file_extension in ['dcm', 'nii', 'nii.gz']:
        return {
            "type": "image",
            "data": Image.new('RGB', (400, 400), color='gray'),
            "array": np.zeros((400, 400, 3), dtype=np.uint8),
            "metadata": {
                "Warning": "Reuired libraries not installed for this file type",
                "Missing": "Install pydicom or nibabel to process thia file"
            }
        }

    else:
        return None


def analyze_image(image_data, api_key,enable_xai=True):
    """Analyze image and return results(mock implementaion)"""

    if isinstance(image_data, Image.Image):
        image_array = np.array(image_data)
    else:
        image_array = image_data

    analysis = """
    **Radiological Analysis**

    The image shows a chest X-ray with apparent bilateral pulmonary infiltrates, predominantly in the lower labes. There is evidence of ground-glass opacities and possible consolidation in the right lower labe. The cardiac silhouette appears mildly enlarged. No pneumothorax or pleural effusion is visible.

    **Impression:**
    1. Bilateral pulmonary infiltrates, consistent with atypical pneumonia
    2. Consider viral etiology (e.g., COVID-19) in appropriate clinical context
    3. Mild cardiomegaly
    4. Recommend clinical correlation and follow-up imaging as appropriate
    """

    finding = [
        "Bilateral pulmonary infiltrates",
    ]