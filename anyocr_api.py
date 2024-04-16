"""
AnyOCR API
Copyright (c) 2024 Andri Yadi (an.dri@me.com)
DycodeX, eFishery
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import re
import logging
import json
from rich.console import Console
from rich.logging import RichHandler
from enum import Enum

from AnyOCREngine import AnyOCREngine, AnyOCREngineResponseHandler, AnyOCREngineImageDetailLevel
from _constants import *
load_dotenv()

console = Console()
app = FastAPI()

class AnyOCRApiRequestMode(Enum):
    Recognition = 0
    CreateTemplate = 1

class OCRRequest(BaseModel):
    img_url: str = None
    img_file: UploadFile = None
    prompt: str = None
    prompt_file: str = None
    temperature: float = 0.1 #0.2
    use_ai_vision: bool = True
    img_detail_level: AnyOCREngineImageDetailLevel = AnyOCREngineImageDetailLevel.DetailAuto

# Create an instance of AnyOCREngine
client = AnyOCREngine(
    azure_deployment_name=os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME"),
    api_version=API_VERSION_DEFAULT,
    azure_vision_key=os.environ.get("AZURE_AI_VISION_API_KEY"),
    azure_vision_api_version=API_VERSION_AI_VISION,
    azure_vision_endpoint=os.environ.get("AZURE_AI_VISION_ENDPOINT"),
    azure_vision_active=True
)

async def load_prompt(mode: AnyOCRApiRequestMode, prompt_file: str):
    if mode == AnyOCRApiRequestMode.CreateTemplate:
        # print(f"Creating template. Use prompt file: {PROMPT_GENERATOR_FILEPATH}")
        logging.getLogger("rich").debug(f"Creating template. Use prompt file: [bold green]{PROMPT_GENERATOR_FILEPATH}[/]", extra={"markup": True})
        prompt_file = PROMPT_GENERATOR_FILEPATH

    ret_prompt = USER_MESSAGE
    if prompt_file:
        # Ensure the path of prompt_file is correct
        if prompt_file.startswith("prompts") or prompt_file.startswith("prompts_efi"):
            prompt_file = os.path.join(os.path.dirname(__file__), prompt_file)
        else:
            prompt_file2 = os.path.join(os.path.dirname(__file__), "prompts", prompt_file)

            if not os.path.exists(prompt_file2):
                prompt_file = os.path.join(os.path.dirname(__file__), "prompts_efi", prompt_file)
            else:
                prompt_file = prompt_file2


        if os.path.exists(prompt_file):
            logging.getLogger("rich").info(f"Load prompt from file [bold green]{prompt_file}[/].", extra={"markup": True})
            with open(prompt_file, 'r') as f:
                ret_prompt = f.read()
        else:
            logging.getLogger("rich").error(f"Prompt generator file [bold red]{prompt_file}[/] does not exist.", extra={"markup": True})
            
    return ret_prompt
            
async def save_prompt_template(prompt_out: str, all_content: str):
    if prompt_out and all_content:
        # Ensure file path
        if prompt_out.startswith("prompts") or prompt_out.startswith("prompts_efi"):
            prompt_out = os.path.join(os.path.dirname(__file__), prompt_out)
        else:
            prompt_out = os.path.join(os.path.dirname(__file__), "prompts", prompt_out)

        with open(prompt_out, 'w') as f:
            f.write(all_content)
            logging.getLogger("rich").info(f"Prompt Template is saved to [bold green]{prompt_out}[/bold green]", extra={"markup": True})
    #else:
        # Omit, just display the template

async def get_currency_conversion_rate() -> float:
    import requests
    conversion_url = "https://api.exchangerate-api.com/v4/latest/USD"

    try:
        # Using a context manager to ensure the session is closed
        with requests.Session() as session:
            response = session.get(conversion_url)
            response.raise_for_status()  # This will raise an HTTPError if the HTTP request returned an unsuccessful status code
            currency_data = response.json()
    except requests.HTTPError as e:
        print(f"HTTPError occurred: {e}")
        return None
    except requests.RequestException as e:
        print(f"RequestException occurred: {e}")
        return None

    # Make API call to get USD to IDR conversion rate
    # response = requests.get(conversion_url)
    # currency_data = response.json()

    # Get the conversion rate
    conversion_rate = currency_data["rates"]["IDR"]
    return conversion_rate

async def process_token_usage(token_info):

    # If token_info is None, 
    if token_info is None:
        return None

    # Convert token_info to dict
    out_token_info = {
        "completion_tokens": token_info.completion_tokens, 
        "prompt_tokens": token_info.prompt_tokens,
        "total_tokens": token_info.total_tokens,
    }

    # Estimate cost based on open ai token usage
    # https://openai.com/pricing
    input_cost_per_token = 10.00 / 1000000  # $10.00 / 1M tokens
    input_token_used = token_info.prompt_tokens
    output_cost_per_token = 30.00 / 1000000  # $30.00 / 1M tokens
    output_token_used = token_info.completion_tokens
    estimated_cost = (input_cost_per_token * input_token_used) + (output_cost_per_token * output_token_used)

    # Convert cost to rupiah
    # convert_idr = False
    convert_idr = True
    conversion_rate = None

    if convert_idr:
        conversion_rate = await get_currency_conversion_rate()
    # If still None, use default conversion rate
    if conversion_rate is None:
        conversion_rate = 15600

    #print("1 USD = Rp", conversion_rate)
    out_token_info["est_cost"] = estimated_cost
    out_token_info["usd_to_idr"] = conversion_rate

    # Calculate estimated cost in Rupiah
    estimated_cost_rupiah = estimated_cost * conversion_rate
    out_token_info["est_cost_idr"] = estimated_cost_rupiah

    #print(f"Estimated cost: $ {estimated_cost} = Rp {estimated_cost_rupiah}")
    #console.print(out_token_info)

    return out_token_info
    
async def do_recognize(req_mode: AnyOCRApiRequestMode, request: OCRRequest):
    # Check if either img_url or img_file is provided
    if not request.img_url and not request.img_file:
        raise HTTPException(status_code=400, detail="Either img_url or image_file must be provided.")

    if not request.prompt and request.prompt_file:
        request.prompt = await load_prompt(req_mode, request.prompt_file)

    # Override the default AnyOCREngine settings
    client.azure_vision_active = request.use_ai_vision

    # Send request to the OCR service
    try:
        if request.img_url:
            img_src = request.img_url
        else:
            img_src = await request.img_file.read()

        response = client.recognize(
            img_src=img_src,
            user_message=request.prompt,
            temperature=request.temperature,
            streaming_response=False,
            img_detail_level=request.img_detail_level,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Handle the response
    all_content = response.choices[0].message.content

    # Process Token Usage and Estimate Cost, only if not streaming_response
    if True:
        token_info = await process_token_usage(response.usage)

    # If req_mode == CreateTemplate, then save the template if the output file is provided
    if req_mode == AnyOCRApiRequestMode.CreateTemplate and request.prompt_file:
        await save_prompt_template(request.prompt_file, all_content)

    # Remove "```", "json"
    cleaned_content = re.sub(r"```|json", "", all_content)

    # return response as json or plain-text
    try:
        parsed_json = json.loads(cleaned_content)

        response_json = {
            "status": "OK",
            "data": parsed_json,
            "usage": token_info
        }

        console.print(response_json)
        return response_json

    except json.JSONDecodeError as e:
        logging.getLogger("rich").warning(f"Not a JSON. Response:\n[bold green]{all_content}[/]", extra={"markup": True})
        return all_content    

# Use this endpoint to recognize text from an image
# Example of request body:
# {
#   "img_url": "https://drive.usercontent.google.com/download?id=1wRVvTDjK79oJIakKlxeLs6IfG_xWULAK&export=download&authuser=0&confirm=t&uuid=57910263-5544-4ad4-8c25-09b2f7a43330&at=APZUnTVxm2e0pkXFIfNtvZ9oaJi7:1711563801165",
#   "prompt_file": "prompt_json_notapanen.md",
#   "use_ai_vision": false,
#   "img_detail_level": "low"
# }

@app.post("/recognize")
async def recognize_endpoint(request: OCRRequest):
    return await do_recognize(AnyOCRApiRequestMode.Recognition, request)

@app.post("/create-template")
async def create_template_endpoint(request: OCRRequest):
    return await do_recognize(AnyOCRApiRequestMode.CreateTemplate, request)

if __name__ == "__main__":

    # Configure logging
    log_level = logging.INFO
    FORMAT = "%(message)s"
    # FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=log_level, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])
    logging.getLogger("rich").info("[bold green]AnyOCR API Service[/] is starting...", extra={"markup": True})

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

    logging.getLogger("rich").info("[bold green]AnyOCR API Service[/] is STOPPED", extra={"markup": True})
