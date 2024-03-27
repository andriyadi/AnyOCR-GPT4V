"""
OCRClient.py
Copyright (c) 2024 Andri Yadi (an.dri@me.com)
DycodeX, eFishery
"""

import json
import os

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
class OCRClientResponseHandler:
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
        return f"<OCRClientResponseHandler {self.name}>"


class OCRClientImageDetailLevel(Enum):
    DetailAuto = "auto"
    DetailLow = "low"
    DetailHigh = "high"


# class OCRClient(BaseModel):
class OCRClient:

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

    response_handler: OCRClientResponseHandler = None

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
        img_detail_level: OCRClientImageDetailLevel = OCRClientImageDetailLevel.DetailAuto,
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
