import qrcode
from io import BytesIO
from PIL import Image
from fastapi import HTTPException
from config import settings


def generate_qr_code(short_code: str) -> str:
    """Generate QR code for a short URL"""
    try:
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # Add URL to QR code
        url = f"{settings.BASE_URL}/{short_code}"
        qr.add_data(url)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 string
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        # Return base64 string (simplified - in practice you might want to return as binary)
        return "data:image/png;base64," + buffer.getvalue().hex()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating QR code: {str(e)}")