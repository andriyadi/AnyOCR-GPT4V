"""
This script uses the Azure OpenAI API to extract text from an image and perform OCR (Optical Character Recognition).
It sends a request to the API with the image URL and user message, and receives a response containing the extracted text.
The extracted text is then displayed on the terminal.

Note: This script requires the `openai` and `rich` libraries to be installed.
"""

from openai import AzureOpenAI
import json
from rich.console import Console
from rich.markdown import Markdown
from dotenv import load_dotenv
import os

load_dotenv()

console = Console()

# KTP
# img_src_url = "https://urgent.id/sistem/foto/newminimallgmailcom-2021-12-29-19-31-30.png"

# Kartu Keluarga
# img_src_url = "https://i.pinimg.com/originals/72/29/fd/7229fde0cbf5869e961946b0b7e75969.jpg"

# Toll receipt
# img_src_url = "https://img.cintamobil.com/resize/600x-/2020/08/11/f8286LtF/struk-jalan-tol-6ecd.jpg"
img_src_url = "https://cf.shopee.co.id/file/sg-11134201-22120-zc9wai89n9kvf0"

# Receipt image
# Not too challenging
# img_src_url = "https://akcdn.detik.net.id/community/media/visual/2023/07/13/bikin-kantong-kering-harga-makanan-di-5-tempat-ini-terlalu-mahal-1.jpeg?w=1024"
# img_src_url = "https://media-cdn.tripadvisor.com/media/photo-s/11/7d/b7/58/bon-makan-di-paul.jpg"
# Handwritten text
# img_src_url = "https://akcdn.detik.net.id/community/media/visual/2023/07/13/bikin-kantong-kering-harga-makanan-di-5-tempat-ini-terlalu-mahal-4.jpeg?w=700&q=90"
# img_src_url = "https://cdn1-production-images-kly.akamaized.net/4hFAOzyOoPf86cye6hjTx6E-62s=/500x667/smart/filters:quality(75):strip_icc():format(webp)/kly-media-production/medias/3470509/original/051746300_1622604393-WhatsApp_Image_2021-06-02_at_10.03.32__1_.jpeg"
# img_src_url = "https://boombastis.sgp1.digitaloceanspaces.com/wp-content/uploads/2014/09/Heboh-Makan-di-Warung-Biasa-Harus-Bayar-Sampai-Rp-1-Juta-1.jpg"
# Miring
# img_src_url = "https://media-cdn.tripadvisor.com/media/photo-s/1a/c5/40/6d/the-receipt.jpg"

# Configuration for Azure OpenAI Vision API
use_azure_vision: bool = True
api_base = os.environ.get("AZURE_OPENAI_BASE_URL")
api_key = os.environ.get("OPENAI_API_KEY")
deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")
api_version_default = '2024-02-15-preview' # this might change in the future
api_version_ai_vision = '2023-12-01-preview' # this might change in the future
azure_vision_endpoint = os.environ.get("AZURE_AI_VISION_ENDPOINT")
azure_vision_key = os.environ.get("AZURE_AI_VISION_API_KEY")

# GPT4V_ENDPOINT = "https://andri-explore-oai.openai.azure.com/openai/deployments/andri-oai-vision/chat/completions?api-version=2024-02-15-preview"
# GPT4V_ENDPOINT = "https://andri-explore-oai.openai.azure.com/openai/deployments/andri-oai-vision/extensions/chat/completions?api-version=2024-02-15-preview"

# System message and user message
# system_message = "You are a helpful assistant."
system_message = "You are a helpful AI assistant for OCR. You will explain the provided image. Extract all text within all parts from this image."

#user_message = "Explain the image. Extract all text from this image and turn into table format if possible. If you find person face photo, give me coordinate of bounding box."
user_message = " \
    Extract title, number, and date from the image. Turn all information into table format, \
    if possible. And if the table is too wide, split into more than one table. \
    If no value recognized, put '-' string. \
    If there are price number in the list, add all to the total price by yourself and show, only if the total number is not present. \
    Don't translate the text to English. Keep it in Indonesian. Give your judgement about image and text clarity. Explain all in Bahasa Indonesia." \

# the most bottom number is saldo akhir. the biggest one is the transaction cost. This is receipt for highway toll road."\
# Also estimate the coordinate of recognized text within the image in (x, y, w, h) format, right after you display the text information. \
# Calculate the total amount of listed currency number. \

# Create the client
if use_azure_vision:
    api_version = api_version_ai_vision
    base_url = f"{api_base}/openai/deployments/{deployment_name}/extensions"

    extra_body = {
        "dataSources": [
            {
                "type": "AzureComputerVision",
                "parameters": {
                    "endpoint": azure_vision_endpoint,
                    "key": azure_vision_key
                }
            }],
        "enhancements": {
            "ocr": {
                "enabled": True
            },
            "grounding": {
                "enabled": True
            }
        }
    }
else:
    api_version = api_version_default
    base_url = f"{api_base}/openai/deployments/{deployment_name}"
    extra_body = {}

# Create the client
client = AzureOpenAI(
    api_key=api_key,  
    api_version=api_version,
    base_url=base_url,
)

# Send the request
response = client.chat.completions.create(
    model=deployment_name,
    messages=[
        { "role": "system", "content": system_message },
        { "role": "user", "content": [  
            { 
                "type": "text", 
                "text": user_message 
            },
            { 
                "type": "image_url",
                "image_url": {
                    "url": img_src_url,
                }
            }
        ] } 
    ],
    extra_body=extra_body,
    max_tokens=4096,
    temperature=0.2,
    stream=True
)

# Print the response
for chunk in response:
    # print(chunk.model_dump_json())

    if use_azure_vision:
        if chunk.choices[0].messages[0]["delta"]["content"] is not None:
            if 'grounding' in chunk.choices[0].messages[0]["delta"]["content"]:
                print("\n\nAll response: ")
                try:
                    parsed_content = json.loads(chunk.choices[0].messages[0]["delta"]["content"])
                    all_content = parsed_content["grounding"]["lines"][0]["text"]
                    #print(all_content)

                    # render all_content as markdown on terminal
                    console.print(Markdown(all_content))

                except json.JSONDecodeError:
                    print("Not a JSON\n")
                    print(chunk.choices[0].messages[0]["delta"]["content"])

                print("\n")                
            else:
                for item in chunk.choices[0].messages[0]["delta"]["content"]:
                    print(item, end="")
    else:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="")
            #console.print(Markdown(chunk.choices[0].delta.content))
