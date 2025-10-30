from strands import tool
import base64
from PIL import Image
import numpy as np
from skimage.metrics import structural_similarity as ssim
import cv2
from io import BytesIO
from pyautogui import screenshot


IMAGE_SIMILARITY_THRESHOLD = 0.95  # Threshold for image similarity (0 to 1)


@tool(description="Convert an image file to a base64-encoded string.")
def image_to_base64(image_path: str) -> list:
    """
    Convert an image file to a base64-encoded string.

    Args:
        image_path (str): Path to the image file to convert to base64

    Returns:
        Dictionary containing status and tool response:
        {
            "toolUseId": "unique_id",
            "status": "success|error",
            "content": [{"text": "base64 string or error message"}]
        }

        Success: Returns the base64-encoded JPEG image as text.
        Error: Returns information about what went wrong.
    """
    if not image_path:
        return [{"text": "image_path is required"}]

    try:
        with open(image_path, "rb") as image_file:
            # convert to jpeg format
            pil_image = Image.open(image_file)
            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")

            # Save the image to a bytes buffer
            buffer = BytesIO()
            pil_image.save(buffer, format="JPEG")

            encoded_string = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return [{"text": encoded_string}]
    except Exception as e:
        return [{"text": f"Error reading/converting image: {str(e)}"}]


@tool(
    description="Take a screenshot and return it as a base64-encoded string.",
)
def take_screenshot() -> list:
    """
    Take a screenshot and return it as a base64-encoded string.

    Args:
        (no inputs required) - tool input can be empty

    Returns:
        Dictionary containing status and tool response:
        {
            "toolUseId": "unique_id",
            "status": "success|error",
            "content": [{"image": {"format":"JPEG","source":{"bytes": b"..."}}}]
        }

        Success: Returns the screenshot bytes in the content as an image object.
        Error: Returns information about what went wrong.
    """
    try:
        return [{"image": {"format": "JPEG", "source": {"bytes": screenshot_bytes()}}}]
    except Exception as e:
        return [{"text": f"Error taking screenshot: {str(e)}"}]


def compare_images(before_image: bytes, expected_change: bool) -> bool:
    """
    Compare two images and determine if they are identical.

    Args:
        before_image (bytes): The image bytes taken before the robot action. This one should be present in the chat history.
        expected_change (bool): Whether a change is expected between the two images.

    Returns:
        bool: True if the comparison matches the expectation, False otherwise.
    """
    try:
        after_image_cv2 = cv2.imdecode(
            np.frombuffer(screenshot_bytes(), np.uint8), cv2.IMREAD_GRAYSCALE
        )
        before_image_cv2 = cv2.imdecode(
            np.frombuffer(before_image, np.uint8), cv2.IMREAD_GRAYSCALE
        )
        # assert before_image.shape == after_image_cv2.shape, (
        #     "Images must be the same size."
        # )

        # Compute SSIM between two images
        ssim_index, _ = ssim(
            before_image_cv2,
            after_image_cv2,
            full=True,
            multichannel=True,
        )

        return (ssim_index < IMAGE_SIMILARITY_THRESHOLD) == expected_change

    except Exception as _:
        raise ValueError(
            "Error comparing images. Use the take_screenshot() tool and judge the outcome yourself"
        )


def screenshot_bytes() -> bytes:
    """
    Take a screenshot and return it as bytes.

    Returns:
        bytes: Screenshot image data in bytes.
    """
    buffer = BytesIO()
    screenshot().save(buffer, format="JPEG")
    return buffer.getvalue()
