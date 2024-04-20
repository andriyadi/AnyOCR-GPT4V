"""
AnyOCR Console App
Copyright (c) 2024 Andri Yadi (an.dri@me.com)
DycodeX, eFishery
"""

import os
import argparse
import time
import base64
import urllib.parse
import mimetypes
import logging

from rich.console import Console
from rich.markdown import Markdown
from rich.progress import (
    BarColumn,
    SpinnerColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TimeElapsedColumn
)
from rich.logging import RichHandler
from dotenv import load_dotenv
from enum import Enum

from _constants import *
from AnyOCREngine import AnyOCREngine, AnyOCREngineResponseHandler, AnyOCREngineImageDetailLevel, AnyOCREngineOpMode

class AnyOCRConsoleApp:
    def __init__(self, args):
        self.console = Console()
        self.args = args

        # self.api_key = os.environ.get("OPENAI_API_KEY")
        # self.api_base = os.environ.get("AZURE_OPENAI_BASE_URL")
        self.deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.azure_vision_endpoint = os.environ.get("AZURE_AI_VISION_ENDPOINT")
        self.azure_vision_key = os.environ.get("AZURE_AI_VISION_API_KEY")

        self.img_src = args.url if args.url else OCR_DEFAULT_IMG_SRC
        self.use_azure_vision = args.vision if args.vision else OCR_USE_AZURE_VISION
        self.streaming_response = args.stream if args.stream else OCR_USE_STREAMING_RESPONSE
        self.user_message = OCR_USER_MESSAGE

        self.last_response_content: str = ""

        self.resp_handler = AnyOCREngineResponseHandler(name="Default Handler")

        self.app_mode: AnyOCREngineOpMode = AnyOCREngineOpMode.CreateTemplate if args.create else AnyOCREngineOpMode.Recognition

    def run(self):
        # Load user_message from file if provided in prompt argument
        # self.load_prompt()
        self.user_message = AnyOCREngine.load_prompt_from_file(self.app_mode, self.args.prompt, OCR_PROMPT_GENERATOR_FILEPATH)

        # print()
        # print("Prompt: \n", self.user_message)
        logging.getLogger("rich").debug(f"Prompt: \n{self.user_message}", extra={"markup": True})
        # print()

        try:
            # self.load_image()
            self.img_src = AnyOCREngine.load_image(self.img_src)
        except Exception as e:
            logging.getLogger("rich").error(f"[bold red]Image URL Error:[/] {e}", extra={"markup": True})
            return

        # Check if the instance is created successfully
        assert isinstance(self.resp_handler, AnyOCREngineResponseHandler)

        # Connect handler to the response event
        self.resp_handler.on_chunked_content_available.connect(
            self.on_ocrengine_chunked_content_available, self.resp_handler
        )
        self.resp_handler.on_all_content_available.connect(
            self.on_ocrengine_all_content_available, self.resp_handler
        )

        # Create an instance of AnyOCREngine
        try:
            client = AnyOCREngine(
                # api_key=self.api_key,
                # azure_base_url=self.api_base,
                azure_deployment_name=self.deployment_name,
                api_version=OCR_API_VERSION_DEFAULT,
                azure_vision_key=self.azure_vision_key,
                azure_vision_api_version=OCR_API_VERSION_AI_VISION,
                azure_vision_endpoint=self.azure_vision_endpoint,
                azure_vision_active=self.use_azure_vision,
                response_handler=self.resp_handler,
            )
        except Exception as e:
            logging.getLogger("rich").error(f"[bold red]OCR Client Error:[/] {e}", extra={"markup": True})
            return


        start_time = time.time()

        # Perform OCR recognition
        # self.console.print(Markdown(f"**Recognizing...**"))
        # with self.console.status("Recognizing...", spinner='bouncingBall'):
        #     self.do_recognition(client)
        # print("\n")

        with Progress(
            SpinnerColumn('bouncingBall'),
            *Progress.get_default_columns(),
            TimeElapsedColumn(),
            console=self.console,
            transient=False,
        ) as progress:
            recog_task = progress.add_task("[green]Processing...", total=None)
            self.do_recognition(client)

        end_time = time.time()
        elapsed_time = end_time - start_time
        self.console.print(Markdown(f"Elapsed time: **{elapsed_time:.2f} seconds**"))
        print("\n")

    def on_ocrengine_all_content_available(self, sender, **kwargs):
        self.last_response_content = kwargs.get("content", "")
        if self.last_response_content != "":
            print("\n\n")
            self.console.print(Markdown("**All Content:** "))
            # render self.last_response_content as markdown on terminal
            self.console.print(Markdown(self.last_response_content))

        print("\n")

    def on_ocrengine_chunked_content_available(self, sender, **kwargs):
        # print(f"Caught signal from {sender!r}, data {kw!r}")
        chunked_content = kwargs.get("content", "")
        print(chunked_content, end="")

    def do_recognition(self, client: AnyOCREngine):
        # Send request to the OCR service
        try:
            response = client.recognize(
                img_src=self.img_src,
                user_message=self.user_message,
                temperature=0.2,
                streaming_response=self.streaming_response,
                img_detail_level=AnyOCREngineImageDetailLevel.DetailLow,
            )
        except Exception as e:
            logging.getLogger("rich").error(f"[bold red]OCR Client Error:[/] {e}", extra={"markup": True})
            return

        # Display Token Usage and Cost, only if not streaming_response
        if not self.streaming_response:
            token_info = response.usage
            self.display_token_usage(token_info)

        # If app_mode == CreateTemplate, then save the template if the output file is provided
        if self.app_mode == AnyOCREngineOpMode.CreateTemplate:
            #self.save_prompt_template()
            AnyOCREngine.save_prompt_template_to_file(self.args.output, self.last_response_content)

    def display_token_usage(self, token_info):

        ret_tok_info = AnyOCREngine.process_token_usage(token_info, True)

        md_token_info = f"**Token Usage & Cost:**\n\n\
* Prompt tokens: **{ret_tok_info['prompt_tokens']}**\n\
* Completion tokens: **{ret_tok_info['completion_tokens']}**\n\
* Total tokens: **{ret_tok_info['total_tokens']}**\n\
"

        #print("1 USD = Rp", ret_tok_info['usd_to_idr'])
        md_token_info += f"* 1 USD = **Rp {ret_tok_info['usd_to_idr']:.2f}**\n"

        #print(f"Estimated cost: $ {ret_tok_info['est_cost']} = Rp {ret_tok_info['est_cost_idr']}")
        md_token_info += f"* Estimated cost: **$ {ret_tok_info['est_cost']:.4f}** = **Rp {ret_tok_info['est_cost_idr']:.2f}**\n"

        self.console.print(Markdown(md_token_info))
        print("\n")


# Got it from: https://stackoverflow.com/questions/52403065/argparse-optional-boolean
def str_to_bool(value):
    if value.lower() in {'false', 'f', '0', 'no', 'n'}:
        return False
    elif value.lower() in {'true', 't', '1', 'yes', 'y'}:
        return True
    else:
        raise argparse.ArgumentTypeError(f'Invalid boolean value: {value}')

def parse_arguments():
    parser = argparse.ArgumentParser(description="AnyOCR Console App - Recognize text from any images", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-u', '--url', help='URL or file path of the image', default=OCR_DEFAULT_IMG_SRC)
    parser.add_argument('-p', '--prompt', help='Path to the prompt file to read')
    parser.add_argument('-n', '--create', help='Create a new prompt template', type=str_to_bool, nargs='?', const=True, default=False)
    parser.add_argument('-o', '--output', help='Output file path of created prompt template')
    parser.add_argument('-s', '--stream', help='Streaming the response or not', type=str_to_bool, nargs='?', const=True, default=OCR_USE_STREAMING_RESPONSE)
    parser.add_argument('-v', '--vision', help='Use Azure AI vision or not', type=str_to_bool, nargs='?', const=True, default=OCR_USE_AZURE_VISION)
    parser.add_argument('-d', '--debug', help='Show debugging messages', type=str_to_bool, nargs='?', const=True, default=False)
    _args = parser.parse_args()
    # print(vars(_args))
    return _args


if __name__ == "__main__":

    load_dotenv()

    args = parse_arguments()

    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    FORMAT = "%(message)s"
    # FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=log_level, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])

    logging.getLogger("rich").info("[bold green]AnyOCR Console App[/] is starting...", extra={"markup": True})
    app = AnyOCRConsoleApp(args)
    app.run()
