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

from OCRClient import OCRClient, OCRClientResponseHandler, OCRClientImageDetailLevel
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
    user_message: str = None
    prompt_file: str = None
    temperature: float = 0.1 #0.2
    streaming_response: bool = False
    img_detail_level: OCRClientImageDetailLevel = OCRClientImageDetailLevel.DetailAuto

# Create an instance of OCRClient
client = OCRClient(
    azure_deployment_name=os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME"),
    api_version=API_VERSION_DEFAULT,
    azure_vision_key=os.environ.get("AZURE_AI_VISION_API_KEY"),
    azure_vision_api_version=API_VERSION_AI_VISION,
    azure_vision_endpoint=os.environ.get("AZURE_AI_VISION_ENDPOINT"),
    azure_vision_active=True
)

def load_prompt(mode: AnyOCRApiRequestMode, prompt_file: str):
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
            
@app.post("/recognize")
async def recognize_endpoint(request: OCRRequest):
    # Check if either img_url or img_file is provided
    if not request.img_url and not request.img_file:
        raise HTTPException(status_code=400, detail="Either img_url or image_file must be provided.")

    if not request.user_message:
        request.user_message = load_prompt(AnyOCRApiRequestMode.Recognition, request.prompt_file)

    # Send request to the OCR service
    try:
        if request.img_url:
            img_src = request.img_url
        else:
            img_src = await request.img_file.read()

        response = client.recognize(
            img_src=img_src,
            user_message=request.user_message,
            temperature=request.temperature,
            streaming_response=request.streaming_response,
            img_detail_level=request.img_detail_level,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # return response

    all_content = response.choices[0].message.content

    # Remove "```", "json"
    all_content = re.sub(r"```|json", "", all_content)
    # all_content = all_content.replace('\n', '')
    # all_content = re.sub(r'\s', '', all_content)

    try:
        json_output = json.loads(all_content)
        console.print(json_output)
        return json_output
    except json.JSONDecodeError as e:
        return all_content    

@app.post("/create-template")
async def create_template_endpoint(request: OCRRequest):
    # Similar to the ocr_endpoint, but with the additional logic for creating a template
    # ...
    pass

if __name__ == "__main__":

    # Configure logging
    log_level = logging.INFO
    FORMAT = "%(message)s"
    # FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=log_level, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])
    logging.getLogger("rich").info("[bold green]AnyOCR Console App[/] is starting...", extra={"markup": True})



    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
