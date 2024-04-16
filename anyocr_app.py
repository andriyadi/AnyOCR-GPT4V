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
from AnyOCREngine import AnyOCREngine, AnyOCREngineResponseHandler, AnyOCREngineImageDetailLevel

class AnyOCRConsoleAppMode(Enum):
    Recognition = 0
    CreateTemplate = 1

class AnyOCRConsoleApp:
    def __init__(self, args):
        self.console = Console()
        self.args = args

        # self.api_key = os.environ.get("OPENAI_API_KEY")
        # self.api_base = os.environ.get("AZURE_OPENAI_BASE_URL")
        self.deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.azure_vision_endpoint = os.environ.get("AZURE_AI_VISION_ENDPOINT")
        self.azure_vision_key = os.environ.get("AZURE_AI_VISION_API_KEY")

        self.img_src = args.url if args.url else IMG_SRC
        self.use_azure_vision = args.vision if args.vision else USE_AZURE_VISION
        self.streaming_response = args.stream if args.stream else USE_STREAMING_RESPONSE
        self.user_message = USER_MESSAGE

        self.last_response_content: str = ""

        self.resp_handler = AnyOCREngineResponseHandler(name="Default Handler")

        self.appMode: AnyOCRConsoleAppMode = AnyOCRConsoleAppMode.CreateTemplate if args.create else AnyOCRConsoleAppMode.Recognition

    def load_prompt(self):
        if self.appMode == AnyOCRConsoleAppMode.CreateTemplate:
            # print(f"Creating template. Use prompt file: {PROMPT_GENERATOR_FILEPATH}")
            logging.getLogger("rich").debug(f"Creating template. Use prompt file: [bold green]{PROMPT_GENERATOR_FILEPATH}[/]", extra={"markup": True})
            self.args.prompt = PROMPT_GENERATOR_FILEPATH

        if self.args.prompt:
            # Ensure the path of self.args.prompt is correct
            if not (self.args.prompt.startswith("prompts") or self.args.prompt.startswith("prompts_efi")):
                prompt_file = os.path.join(os.path.dirname(__file__), "prompts", self.args.prompt)

                if not os.path.exists(prompt_file):
                    self.args.prompt = os.path.join(os.path.dirname(__file__), "prompts_efi", self.args.prompt)
                else:
                    self.args.prompt = prompt_file

            if os.path.exists(self.args.prompt):
                logging.getLogger("rich").info(f"Load prompt from file [bold green]{self.args.prompt}[/].", extra={"markup": True})
                with open(self.args.prompt, 'r') as f:
                    self.user_message = f.read()
            else:
                logging.getLogger("rich").error(f"Prompt generator file [bold red]{self.args.prompt}[/] does not exist.", extra={"markup": True})

    def run(self):
        # Load user_message from file if provided in prompt argument
        self.load_prompt()

        # print()
        # print("Prompt: \n", self.user_message)
        logging.getLogger("rich").debug(f"Prompt: \n{self.user_message}", extra={"markup": True})
        # print()

        try:
            self.ensure_image()
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
                api_version=API_VERSION_DEFAULT,
                azure_vision_key=self.azure_vision_key,
                azure_vision_api_version=API_VERSION_AI_VISION,
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

        # If appMode == CreateTemplate, then save the template if the output file is provided
        if self.appMode == AnyOCRConsoleAppMode.CreateTemplate:
            self.save_prompt_template()

    def ensure_image(self):
        try:
            result = urllib.parse.urlparse(self.img_src)
            if all([result.scheme, result.netloc]):
                logging.getLogger("rich").debug(f"Valid image URL: {self.img_src}", extra={"markup": True})
                # It's a URL. All's good, return
                return
        except ValueError:
            logging.getLogger("rich").error(f"Invalid image URL: {self.img_src}", extra={"markup": True})

        # If not return, assumed it's a file path
        if os.path.exists(self.img_src):
            # Load file
            with open(self.img_src, 'rb') as f:
                # Check if the file is actually an image file
                try:
                    # Get image file type
                    mime_type, _ = mimetypes.guess_type(self.img_src)
                    logging.getLogger("rich").debug(f"MIME type: [bold green]{mime_type}[/bold green]", extra={"markup": True})
                    if mime_type and mime_type.startswith('image/'):
                        encoded_image = base64.b64encode(f.read()).decode("ascii")
                        self.img_src = f"data:{mime_type};base64,{encoded_image}"
                        # print(self.img_src)
                except IOError:
                    raise ValueError(f"File {self.img_src} is not a valid image file.")
        else:
            raise FileNotFoundError(f"Image file {self.img_src} does not exist.")

    def save_prompt_template(self):
        if self.args.output and self.last_response_content != "":
            with open(self.args.output, 'w') as f:
                f.write(self.last_response_content)
                logging.getLogger("rich").info(f"Prompt Template is saved to [bold green]{self.args.output}[/bold green]", extra={"markup": True})
        #else:
            # Omit, just display the template

    def get_currency_conversion_rate(self):
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

    def display_token_usage(self, token_info):
        md_token_info = f"**Token Usage & Cost:**\n\n\
* Prompt tokens: **{token_info.prompt_tokens}**\n\
* Completion tokens: **{token_info.completion_tokens}**\n\
* Total tokens: **{token_info.total_tokens}**\n\
"

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
            conversion_rate = self.get_currency_conversion_rate()
        # If still None, use default conversion rate
        if conversion_rate is None:
            conversion_rate = 15600

        #print("1 USD = Rp", conversion_rate)
        md_token_info += f"* 1 USD = **Rp {conversion_rate:.2f}**\n"

        # Calculate estimated cost in Rupiah
        estimated_cost_rupiah = estimated_cost * conversion_rate

        #print(f"Estimated cost: $ {estimated_cost} = Rp {estimated_cost_rupiah}")
        md_token_info += f"* Estimated cost: **$ {estimated_cost:.4f}** = **Rp {estimated_cost_rupiah:.2f}**\n"

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
    parser.add_argument('-u', '--url', help='URL or file path of the image', default=IMG_SRC)
    parser.add_argument('-p', '--prompt', help='Path to the prompt file to read')
    parser.add_argument('-n', '--create', help='Create a new prompt template', type=str_to_bool, nargs='?', const=True, default=False)
    parser.add_argument('-o', '--output', help='Output file path of created prompt template')
    parser.add_argument('-s', '--stream', help='Streaming the response or not', type=str_to_bool, nargs='?', const=True, default=USE_STREAMING_RESPONSE)
    parser.add_argument('-v', '--vision', help='Use Azure AI vision or not', type=str_to_bool, nargs='?', const=True, default=USE_AZURE_VISION)
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
