from strands import tool
import base64
from PIL import Image
from io import BytesIO
from pyautogui import screenshot


@tool(description="Convert an image file to a base64-encoded string.")
def image_to_base64(image_path: str) -> str:
    """
    Convert an image file to a base64-encoded string.

    Args:
        image_path (str): The path to the image file.

    Returns:
        str: Base64-encoded string of the image, converted to jpeg.
    """
    with open(image_path, "rb") as image_file:
        # convert to jpeg format
        pil_image = Image.open(image_file)
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        # Save the image to a bytes buffer
        buffer = BytesIO()
        pil_image.save(buffer, format="JPEG")

        encoded_string = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return encoded_string


@tool(
    description="Take a screenshot and return it as a base64-encoded string.",
)
def take_screenshot() -> bytes:
    """
    Take a screenshot and return it as a base64-encoded string.

    Returns:
        str: Base64-encoded string of the screenshot.
    """
    buffer = BytesIO()
    screenshot().save(buffer, format="JPEG")

    return buffer.getvalue()
