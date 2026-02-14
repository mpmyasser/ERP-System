"""
QR Code Generator Module
========================
Generates QR codes for employee cards and barcodes
"""

import qrcode
import io
import base64


def generate_qr_code_base64(data: str) -> str:
    """
    Generates a QR code and returns it as a base64 encoded string.
    
    Args:
        data: The data to encode in the QR code (e.g., employee code)
        
    Returns:
        str: Base64 encoded PNG image string
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save image to a bytes buffer
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    
    # Encode buffer to base64
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str
