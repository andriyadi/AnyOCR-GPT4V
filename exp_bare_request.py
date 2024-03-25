import os
import requests
import base64
import json
import re
import os

from dotenv import load_dotenv

load_dotenv()

# Configuration
use_azure_vision = False
api_base = os.environ.get("AZURE_OPENAI_BASE_URL")
api_key = os.environ.get("OPENAI_API_KEY")
deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")
api_version_default = "2024-02-15-preview"  # this might change in the future
api_version_ai_vision = "2023-12-01-preview"  # this might change in the future
azure_vision_endpoint = os.environ.get("AZURE_AI_VISION_ENDPOINT")
azure_vision_key = os.environ.get("AZURE_AI_VISION_API_KEY")

# IMAGE_PATH = "/Users/andri/Projects/LLM/Projects/AzureOpenAI/images/20230907_213533.jpg"
IMAGE_PATH = "/Users/andri/Projects/LLM/Projects/AzureOpenAI/images/20230907_213612.jpg"

encoded_image = base64.b64encode(open(IMAGE_PATH, "rb").read()).decode("ascii")
headers = {
    "Content-Type": "application/json",
    "api-key": api_key,
}

# Payload for the request
payload = {
    "messages": [
        {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": 'You are an AI assistant that helps extracting data (text or numbers) from provided photo. The photo is a document entitled "FORM LAPORAN BUDIDAYA HARIAN TAMBAK (DATA KUALITAS AIR)"\n\nThere are 3 parts to be extracted from the document:\n1. On top left of the photo, there\'s data contains:\n- Date (Tanggal)\n- A table contains farm information (Informasi Tambak/Site) which are: BLOK/PETAK, NAMA TAMBAK/SITE, and NAMA TEKNISI\n\n2. On top mid part of document photo is "Informasi Tebar", contains JUMLAH TEBAR, TANGGAL TEBAR. \n\n3. The mid part is the biggest table contains actual cultivation data: Data Kualitas Air. First row is the table columns. Second and following rows are the actual data.\n\nThe decimal number data in the photo may be formatted using "." or ",". \n\nPlease extract the data from all those 3 parts, and display to JSON format. \nThe JSON output format will be like this:\n```\n{\n    "Tanggal": "17 Januari 2023",\n    "Informasi Tambak": {\n        "BLOK/PETAK": "B6",\n        "NAMA TAMBAK/SITE": "Coconut",\n        "NAMA TEKNISI": "KOKO"\n    },\n    "Informasi Tebar": {\n        "JUMLAH TEBAR": "30.000",\n        "TANGGAL TEBAR": "15 Januari 2023"\n    },\n    "Data Kualitas Air": {\n        "Columns": [\n            "ID Kolam", "DOC", "pH Pagi", "pH Sore", "DO Pagi", "DO Sore", "Suhu Pagi", "Suhu Sore", "Anco Skor Pakan", "Anco Jumlah Udang", "Cuaca", "Tinggal Air (cm)", "Kecerahan", "Warna Air", "Salinitas", "Jumlah Kematian (ekor)", "Siphon (jam)", "Sirkulasi Air (cm)", "Jumlah Kincir Aktif"\n        ],\n        "Rows": [\n            ["B1", 3, 7, 7.8, 6.9, 7.1, 20.1, 26.1, 0.02, 4, "H", 110, 20, "C", 28, 2, "", 2, 1],\n            ["B4", 3, 7.2, 7.3, 6.9, 7.1, 20.1, 26.1, 0.02, 4, "C", 110, 20, "H", 28, 2,"9:00", 2, 1 ]\n        ]\n    }\n}\n```\n',
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{encoded_image}",
                    },
                },
                {"type": "text", "text": "proceed"},
            ],
        },
    ],
    "temperature": 0.4,
    "top_p": 0.95,
    "max_tokens": 4096,
}

if use_azure_vision:
    payload["enhancements"] = {"ocr": {"enabled": True}, "grounding": {"enabled": True}}

    payload["dataSources"] = [
        {
            "type": "AzureComputerVision",
            "parameters": {"endpoint": azure_vision_endpoint, "key": azure_vision_key},
        }
    ]

    GPT4V_ENDPOINT = f"{api_base}/openai/deployments/{deployment_name}/extensions/chat/completions?api-version=2023-12-01-preview"
else:
    GPT4V_ENDPOINT = f"{api_base}/openai/deployments/{deployment_name}/chat/completions?api-version=2024-02-15-preview"

# print("Payload: ", payload)s
print("Sending request...")
# Send request
try:
    response = requests.post(GPT4V_ENDPOINT, headers=headers, json=payload)
    response.raise_for_status()  # Will raise an HTTPError if the HTTP request returned an unsuccessful status code
except requests.RequestException as e:
    raise SystemExit(f"Failed to make the request. Error: {e}")

# Print the response as it is
# print(response.json())

# Parse the JSON
json_resp = response.json()
if use_azure_vision:
    json_payload = json_resp["choices"][0]["enhancements"]["grounding"]["lines"][0]["text"]
else:
    json_payload = json_resp["choices"][0]["message"]["content"]
print("JSON: ", json_payload)

# Remove "```", "json"
json_payload = re.sub(r"```|json", "", json_payload)
# print("JSON payload: ", json_payload)

# Colorify JSON
from pygments import highlight, lexers, formatters

colorful_json = highlight(
    json_payload, lexers.JsonLexer(), formatters.TerminalFormatter()
)
print(colorful_json)

# Display Token Usage
# print("\n\nToken usage:", json_resp["usage"]["prompt_tokens"])
token_info = json_resp["usage"]
print("Token usage:", token_info)

# Estimate cost based on open ai token usage
# https://openai.com/pricing
input_cost_per_token = 10.00 / 1000000  # $10.00 / 1M tokens
input_token_used = token_info["prompt_tokens"]
output_cost_per_token = 30.00 / 1000000  # $30.00 / 1M tokens
output_token_used = token_info["completion_tokens"]
estimated_cost = (input_cost_per_token * input_token_used) + (
    output_cost_per_token * output_token_used
)

# Convert cost to rupiah
convert_idr = False
if convert_idr:
    # Make API call to get USD to IDR conversion rate
    conversion_url = "https://api.exchangerate-api.com/v4/latest/USD"
    response = requests.get(conversion_url)
    currency_data = response.json()
    # Get the conversion rate
    conversion_rate = currency_data["rates"]["IDR"]
else:
    conversion_rate = 15600
print("1 USD = Rp", conversion_rate)
# Calculate estimated cost in Rupiah
estimated_cost_rupiah = estimated_cost * conversion_rate

print(f"Estimated cost: $ {estimated_cost} = Rp {estimated_cost_rupiah}")
