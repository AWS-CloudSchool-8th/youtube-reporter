from app.utils.s3 import upload_bytes
# Placeholder for actual image gen call

def generate_image(prompt: str) -> str:
    content = b""  # real image bytes from API
    key = f"images/{hash(prompt)}.png"
    return upload_bytes(content, key)