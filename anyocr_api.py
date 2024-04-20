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

from AnyOCREngine import AnyOCREngine, AnyOCREngineResponseHandler, AnyOCREngineImageDetailLevel, AnyOCREngineOpMode
from _constants import *
load_dotenv()

console = Console()
app = FastAPI()

class OCRRequest(BaseModel):
    img_url: str = ""
    img_file: UploadFile = None
    prompt: str = ""
    prompt_file: str = ""
    temperature: float = 0.1 #0.2
    use_ai_vision: bool = True
    img_detail_level: AnyOCREngineImageDetailLevel = AnyOCREngineImageDetailLevel.DetailAuto

# Create an instance of AnyOCREngine
engine = AnyOCREngine(
    azure_deployment_name=os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME"),
    api_version=OCR_API_VERSION_DEFAULT,
    azure_vision_key=os.environ.get("AZURE_AI_VISION_API_KEY"),
    azure_vision_api_version=OCR_API_VERSION_AI_VISION,
    azure_vision_endpoint=os.environ.get("AZURE_AI_VISION_ENDPOINT"),
    azure_vision_active=True
)

async def do_recognize(req_mode: AnyOCREngineOpMode, request: OCRRequest):
    # Check if either img_url or img_file is provided
    if not request.img_url and not request.img_file:
        raise HTTPException(status_code=400, detail="Either img_url or img_file must be provided.")

    if not request.prompt and request.prompt_file:
        request.prompt = AnyOCREngine.load_prompt_from_file(req_mode, request.prompt_file, OCR_PROMPT_GENERATOR_FILEPATH)

    # Override the default AnyOCREngine settings
    engine.azure_vision_active = request.use_ai_vision

    # Send request to the OCR service
    try:
        if request.img_url:
            img_src = AnyOCREngine.load_image(request.img_url)
        else: # Using file upload is not yet working
            img_bytes = await request.img_file.read()
            encoded_image = base64.b64encode(img_bytes).decode("ascii")
            mime_type = "image/jpg"
            img_src = f"data:{mime_type};base64,{encoded_image}"

        response = engine.recognize(
            img_src=img_src,
            user_message=request.prompt,
            temperature=request.temperature,
            streaming_response=False,
            img_detail_level=request.img_detail_level,
        )
    except Exception as e:
        logging.getLogger("rich").error(f"Exception: [bold red]{str(e)}[/]", extra={"markup": True})
        raise HTTPException(status_code=500, detail=str(e))

    # Handle the response
    all_content = response.choices[0].message.content

    # Process Token Usage and Estimate Cost, only if not streaming_response
    if True:
        token_info = AnyOCREngine.process_token_usage(response.usage, True)

    # If req_mode == CreateTemplate, then save the template if the output file is provided
    if req_mode == AnyOCREngineOpMode.CreateTemplate and request.prompt_file:
        #await save_prompt_template(request.prompt_file, all_content)
        AnyOCREngine.save_prompt_template_to_file(request.prompt_file, all_content)

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

"""
Use this endpoint to recognize text from an image
Example of request body:
{
  "img_url": "https://drive.usercontent.google.com/download?id=1wRVvTDjK79oJIakKlxeLs6IfG_xWULAK&export=download&authuser=0&confirm=t&uuid=57910263-5544-4ad4-8c25-09b2f7a43330&at=APZUnTVxm2e0pkXFIfNtvZ9oaJi7:1711563801165",
  "prompt_file": "prompt_json_notapanen.md",
  "use_ai_vision": false,
  "img_detail_level": "low"
}
"""

@app.post("/recognize")
async def recognize_endpoint(request: OCRRequest):
    return await do_recognize(AnyOCREngineOpMode.Recognition, request)

@app.post("/create-template")
async def create_template_endpoint(request: OCRRequest):
    return await do_recognize(AnyOCREngineOpMode.CreateTemplate, request)

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
