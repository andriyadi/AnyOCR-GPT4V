"""
AnyOCREngine.py
Copyright (c) 2024 Andri Yadi (an.dri@me.com)
DycodeX, eFishery
"""

import json
import os
import logging
import urllib.parse
import mimetypes
import base64

# from pydantic import BaseModel, HttpUrl
# from pydantic.dataclasses import dataclass
from openai import AzureOpenAI
from enum import Enum
from blinker import Signal


OCR_CLIENT_SYSTEM_MESSAGE = "\
    You are a helpful AI assistant for OCR. \
    You will explain the provided image. Extract all text within all parts from this image. \
    "


# @dataclass
class AnyOCREngineResponseHandler:
    # Define handler's name
    name: str

    # Define signals
    on_all_content_available = Signal()
    on_chunked_content_available = Signal()
    on_non_json_content = Signal()
    on_error = Signal()

    def __init__(self, name: str):
        self.name = name

    def handle_all_content_available(self, content):
        self.on_all_content_available.send(self, content=content)

    def handle_chunked_content_available(self, content):
        self.on_chunked_content_available.send(self, content=content)

    def handle_non_json_content(self, content):
        print("Not a JSON\n")
        self.print_content(content)
        self.on_non_json_content.send(self, content=content)

    def handle_default_response(self, content):
        self.print_content(content)

    def handle_error(self, content):
        self.on_error.send(self, content=content)

    def print_content(self, content):
        print(content, end="")

    def __repr__(self):
        return f"<AnyOCREngineResponseHandler {self.name}>"


class AnyOCREngineImageDetailLevel(Enum):
    DetailAuto = "auto"
    DetailLow = "low"
    DetailHigh = "high"

class AnyOCREngineOpMode(Enum):
    Recognition = 0
    CreateTemplate = 1

# class AnyOCREngine(BaseModel):
class AnyOCREngine:

    api_key: str
    # azure_base_url: HttpUrl
    azure_base_url: str
    azure_deployment_name: str
    api_version: str
    azure_vision_active: bool = True
    azure_vision_key: str | None = None
    azure_vision_endpoint: str | None = None
    azure_vision_api_version: str | None = None
    system_message: str = OCR_CLIENT_SYSTEM_MESSAGE

    response_handler: AnyOCREngineResponseHandler = None

    openai_base_url: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        azure_base_url: str | None = None,
        azure_deployment_name: str | None = None,
        api_version: str | None = None,
        azure_vision_active: bool = True,
        azure_vision_key: str | None = None,
        azure_vision_endpoint: str | None = None,
        azure_vision_api_version: str | None = None,
        system_message: str | None = OCR_CLIENT_SYSTEM_MESSAGE,
        response_handler=None,
    ):

        # super().__init__(api_key = api_key,
        #         azure_base_url = azure_base_url,
        #         azure_deployment_name = azure_deployment_name,
        #         api_version = api_version,
        #         azure_vision_active = azure_vision_active,
        #         azure_vision_key = azure_vision_key,
        #         azure_vision_endpoint = azure_vision_endpoint,
        #         azure_vision_api_version = azure_vision_api_version,
        #         system_message = system_message,
        #         response_handler = response_handler)

        # super().__init__(...)

        if api_key is None:
            api_key = os.environ.get("OPENAI_API_KEY")
        if api_key is None:
            raise OpenAIError(
                "The api_key client option must be set either by passing api_key to the client or by setting the OPENAI_API_KEY environment variable"
            )
        self.api_key = api_key

        if azure_base_url is None:
            azure_base_url = os.environ.get("AZURE_OPENAI_BASE_URL")
        if azure_base_url is None:
            raise OpenAIError(
                "The azure_base_url client option must be set either by passing azure_base_url to the client or by setting the AZURE_OPENAI_BASE_URL environment variable"
            )
        self.azure_base_url = azure_base_url

        self.azure_deployment_name = azure_deployment_name
        self.api_version = api_version
        self.azure_vision_active = azure_vision_active
        self.azure_vision_key = azure_vision_key
        self.azure_vision_endpoint = azure_vision_endpoint
        self.azure_vision_api_version = azure_vision_api_version
        self.system_message = system_message
        self.response_handler = response_handler


    def recognize(
        self,
        *,
        img_src: str,
        user_message: str | None = None,
        streaming_response: bool = True,
        img_detail_level: AnyOCREngineImageDetailLevel = AnyOCREngineImageDetailLevel.DetailAuto,
        max_tokens: int = 4096,
        temperature: float = 0.2,
    ):

        # Check if Azure Vision is used
        if self.azure_vision_active:
            self.api_version = self.azure_vision_api_version
            self.openai_base_url = f"{self.azure_base_url}/openai/deployments/{self.azure_deployment_name}/extensions"

            # Set additional body parameters for Azure Computer Vision
            extra_body = {
                "dataSources": [
                    {
                        "type": "AzureComputerVision",
                        "parameters": {
                            "endpoint": self.azure_vision_endpoint,
                            "key": self.azure_vision_key,
                        },
                    }
                ],
                "enhancements": {
                    "ocr": {"enabled": True},
                    "grounding": {"enabled": True},
                },
            }
        else:
            # api_version = self.api_version
            self.openai_base_url = (
                f"{self.azure_base_url}/openai/deployments/{self.azure_deployment_name}"
            )
            extra_body = {}

        # Create AzureOpenAI client
        client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            base_url=self.openai_base_url,
        )

        # Send request to the OCR service
        response = client.chat.completions.create(
            model=self.azure_deployment_name,
            messages=[
                {"role": "system", "content": self.system_message},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_message},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": img_src,
                                "detail": img_detail_level.value,
                            },
                        },
                    ],
                },
            ],
            extra_body=extra_body,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=streaming_response,
        )

        # Prepare a variable to store the all content
        all_content: str = ""

        # Process the response
        if not streaming_response:
            # print(response.model_dump_json())
            all_content = response.choices[0].message.content
            if self.response_handler is not None and all_content != "":
                self.response_handler.handle_all_content_available(all_content)

        else:
            # If streaming response is enabled
            for response_chunk in response:

                if not response_chunk.choices:
                    continue

                # print(response_chunk.model_dump_json())
                if self.azure_vision_active:
                    if response_chunk.choices[0].messages[0]["delta"]["content"] is not None:
                        if "grounding" in response_chunk.choices[0].messages[0]["delta"]["content"]:
                            # Handle all content response
                            try:
                                if self.response_handler is not None:
                                    parsed_content = json.loads(
                                        response_chunk.choices[0].messages[0]["delta"]["content"]
                                    )
                                    all_content = parsed_content["grounding"]["lines"][0]["text"]
                                    self.response_handler.handle_all_content_available(
                                        all_content
                                    )

                            except json.JSONDecodeError:
                                print("Not a JSON\n")
                                if self.response_handler is not None:
                                    self.response_handler.handle_non_json_content(
                                        response_chunk.choices[0].messages[0]["delta"]["content"]
                                    )

                        else:
                            # Handle chunked response
                            for item in response_chunk.choices[0].messages[0]["delta"]["content"]:
                                if self.response_handler is not None:
                                    self.response_handler.handle_chunked_content_available(
                                        item
                                    )
                else:
                    if response_chunk.choices[0].delta.content is not None:
                        # Handle chunked response
                        chunk_content = response_chunk.choices[0].delta.content
                        all_content += chunk_content

                        if self.response_handler is not None:
                            self.response_handler.handle_chunked_content_available(
                                chunk_content
                            )

            # Handle the all content response only if azure_vision_active is False
            if not self.azure_vision_active:
                if self.response_handler is not None and all_content != "":
                    self.response_handler.handle_all_content_available(all_content)

        return response

    ########################## 
    # Helper static methods
    ########################## 
    def load_prompt_from_file(mode: AnyOCREngineOpMode, prompt_file: str, prompt_file_generator: str):
        if mode == AnyOCREngineOpMode.CreateTemplate:
            # print(f"Creating template. Use prompt file: {prompt_file_generator}")
            logging.getLogger("rich").debug(f"Creating template. Use prompt file: [bold green]{prompt_file_generator}[/]", extra={"markup": True})
            prompt_file = prompt_file_generator

        ret_prompt = ""
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
            
            # Read prompt file
            if os.path.exists(prompt_file):
                logging.getLogger("rich").info(f"Load prompt from file [bold green]{prompt_file}[/].", extra={"markup": True})
                with open(prompt_file, 'r') as f:
                    ret_prompt = f.read()
            else:
                logging.getLogger("rich").error(f"Prompt generator file [bold red]{prompt_file}[/] does not exist.", extra={"markup": True})
                
        return ret_prompt
    
    def save_prompt_template_to_file(prompt_out_file: str, all_content: str):
        if prompt_out_file and all_content:
            # Ensure file path
            if prompt_out_file.startswith("prompts") or prompt_out_file.startswith("prompts_efi"):
                prompt_out_file = os.path.join(os.path.dirname(__file__), prompt_out_file)
            else:
                prompt_out_file = os.path.join(os.path.dirname(__file__), "prompts", prompt_out_file)

            with open(prompt_out_file, 'w') as f:
                f.write(all_content)
                logging.getLogger("rich").info(f"Prompt Template is saved to [bold green]{prompt_out_file}[/bold green]", extra={"markup": True})
        #else:
            # Omit, just display the template

    def load_image(img_url: str) -> str:
        try:
            result = urllib.parse.urlparse(img_url)
            if all([result.scheme, result.netloc]):
                logging.getLogger("rich").debug(f"Valid image URL: {img_url}", extra={"markup": True})
                # It's a URL. All's good, return
                return img_url
        except ValueError:
            logging.getLogger("rich").error(f"Invalid image URL: {img_url}", extra={"markup": True})
            raise ValueError(f"Invalid image URL: {img_url}")

        # If not return, assumed it's a file path
        if os.path.exists(img_url):
            # Load file
            with open(img_url, 'rb') as f:
                # Check if the file is actually an image file
                try:
                    # Get image file type
                    mime_type, _ = mimetypes.guess_type(img_url)
                    logging.getLogger("rich").debug(f"MIME type: [bold green]{mime_type}[/bold green]", extra={"markup": True})
                    if mime_type and mime_type.startswith('image/'):
                        encoded_image = base64.b64encode(f.read()).decode("ascii")
                        img_base64 = f"data:{mime_type};base64,{encoded_image}"
                        # print(img_base64)
                        return img_base64                        
                except IOError:
                    raise ValueError(f"File {img_url} is not a valid image file.")
        else:
            raise FileNotFoundError(f"Image file {img_url} does not exist.")

    def process_token_usage(token_info, convert_idr: bool = False):
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
        conversion_rate = None

        if convert_idr:
            conversion_rate = AnyOCREngine.get_currency_conversion_rate()
        # If still None, use default conversion rate
        if conversion_rate is None:
            conversion_rate = 16000

        #print("1 USD = Rp", conversion_rate)
        out_token_info["est_cost"] = estimated_cost
        out_token_info["usd_to_idr"] = conversion_rate

        # Calculate estimated cost in Rupiah
        estimated_cost_rupiah = estimated_cost * conversion_rate
        out_token_info["est_cost_idr"] = estimated_cost_rupiah

        #print(f"Estimated cost: $ {estimated_cost} = Rp {estimated_cost_rupiah}")
        #print(out_token_info)

        return out_token_info

    def get_currency_conversion_rate() -> float:
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

    
