# import base64
# import mimetypes
# import requests
# from django.conf import settings

# BASE_URL = "https://router.huggingface.co/v1"
# CHAT_URL = f"{BASE_URL}/chat/completions"


# def _file_to_data_url(path: str) -> str:
#     mime, _ = mimetypes.guess_type(path)
#     if mime is None:
#         mime = "image/jpeg"

#     with open(path, "rb") as f:
#         encoded = base64.b64encode(f.read()).decode("utf-8")

#     return f"data:{mime};base64,{encoded}"


# def analyze_image(image_path: str):
#     headers = {
#         "Authorization": f"Bearer {settings.HF_TOKEN}",
#         "Content-Type": "application/json",
#     }

#     data_url = _file_to_data_url(image_path)

#     prompt = """
#     Describe clearly what is visible in this image.
#     If it is a receipt, extract merchant name, date, and total amount in plain English.
#     If it is damage, describe visible damage clearly.
#     Do not invent missing information.
#     """

#     payload = {
#         "model": "Qwen/Qwen2.5-VL-7B-Instruct",
#         "messages": [
#             {
#                 "role": "user",
#                 "content": [
#                     {"type": "text", "text": prompt.strip()},
#                     {"type": "image_url", "image_url": {"url": data_url}},
#                 ],
#             }
#         ],
#         "temperature": 0.0,
#         "max_tokens": 400,
#     }

#     try:
#         r = requests.post(CHAT_URL, headers=headers, json=payload, timeout=120)

#         if r.status_code != 200:
#             return "Vision service temporarily unavailable. Image requires manual review."

#         data = r.json()
#         return data["choices"][0]["message"]["content"]

#     except requests.exceptions.RequestException:
#         return "Vision service failed due to network error. Manual review required."

# myapp/vision.py
import base64
import mimetypes
import os
import requests
from django.conf import settings

BASE_URL = "https://router.huggingface.co/v1"
CHAT_URL = f"{BASE_URL}/chat/completions"


def _is_image_file(path: str) -> bool:
    mime, _ = mimetypes.guess_type(path)
    return bool(mime and mime.startswith("image/"))


def _file_to_data_url(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    if mime is None:
        mime = "image/jpeg"

    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime};base64,{encoded}"


def analyze_image(image_path: str) -> str:
    # file existence guard
    if not os.path.exists(image_path):
        return "No evidence file found for vision analysis."

    # type guard
    if not _is_image_file(image_path):
        return "Evidence is not an image; vision analysis skipped."

    headers = {
        "Authorization": f"Bearer {settings.HF_TOKEN}",
        "Content-Type": "application/json",
    }

    data_url = _file_to_data_url(image_path)

    prompt = """
    Describe clearly what is visible in this image.
    If it is a receipt, extract merchant name, date, and total amount in plain English.
    If it is damage, describe visible damage clearly.
    Do not invent missing information.
    """

    payload = {
        "model": "Qwen/Qwen2.5-VL-7B-Instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt.strip()},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        "temperature": 0.0,
        "max_tokens": 400,
    }

    try:
        r = requests.post(CHAT_URL, headers=headers, json=payload, timeout=120)
        if r.status_code != 200:
            return "Vision service temporarily unavailable. Manual review required."

        data = r.json()
        return data["choices"][0]["message"]["content"] or "Vision returned no description."

    except requests.exceptions.RequestException:
        return "Vision service failed due to network error. Manual review required."