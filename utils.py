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
                image_array = ((image_array - image_array.min()/(image_array.max() - image_array.min()) * 255).astype(np.uint8))

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
                    
            