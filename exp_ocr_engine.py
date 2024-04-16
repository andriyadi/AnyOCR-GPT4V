from pydantic import HttpUrl
from AnyOCREngine import AnyOCREngine, AnyOCREngineResponseHandler
from rich.console import Console
from rich.markdown import Markdown
from rich.spinner import Spinner
from dotenv import load_dotenv
import os
import sys
import argparse
from _constants import *

load_dotenv()

console = Console()

# Got it from: https://stackoverflow.com/questions/52403065/argparse-optional-boolean
def str_to_bool(value):
    if value.lower() in {'false', 'f', '0', 'no', 'n'}:
        return False
    elif value.lower() in {'true', 't', '1', 'yes', 'y'}:
        return True
    raise ValueError(f'{value} is not a valid boolean value')

parser = argparse.ArgumentParser(description='Recognize text from image', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-u', '--url', help='URL of the image')
parser.add_argument('-p', '--prompt', help='Path to the prompt file')
parser.add_argument('-s', '--stream', help='Streaming the response or not', type=str_to_bool, nargs='?', const=True, default=USE_STREAMING_RESPONSE)
parser.add_argument('-v', '--vision', help='Use Azure AI vision or not', type=str_to_bool, nargs='?', const=True, default=USE_AZURE_VISION)
args = parser.parse_args()
print(vars(args))

# Get img_src_url from terminal parameter, if provided
img_src_url = args.url if args.url else IMG_SRC

user_message = USER_MESSAGE

if args.prompt:
    with open(args.prompt, 'r') as f:
        user_message = f.read()

# print()        
# print("Prompt: \n", user_message)
# print()

# Configuration
use_azure_vision = args.vision if args.vision else USE_AZURE_VISION
# use_azure_vision: bool = False
# api_base = os.environ.get("AZURE_OPENAI_BASE_URL")
# api_key = os.environ.get("OPENAI_API_KEY")
deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME")
api_version_default = API_VERSION_DEFAULT  
api_version_ai_vision = API_VERSION_AI_VISION
azure_vision_endpoint = os.environ.get("AZURE_AI_VISION_ENDPOINT")
azure_vision_key = os.environ.get("AZURE_AI_VISION_API_KEY")

streaming_response = args.stream if args.stream else USE_STREAMING_RESPONSE

# Create an instance of AnyOCREngineResponseHandler
resp_handler = AnyOCREngineResponseHandler(name="Default Handler")
# Check if the instance is created successfully
assert isinstance(resp_handler, AnyOCREngineResponseHandler)

def on_ocrengine_chunked_content_available(sender, **kwargs):
    # print(f"Caught signal from {sender!r}, data {kw!r}")
    content = kwargs.get("content", "")
    print(content, end="")
# Connect handler to the response event
resp_handler.on_chunked_content_available.connect(
    on_ocrengine_chunked_content_available, resp_handler
)

# Or use attribute to connect handler to the response event
@resp_handler.on_all_content_available.connect
def on_ocrengine_all_content_available(sender, **kwargs):
    all_content = kwargs.get("content", "")
    if all_content != "":
        print("\n\n")
        console.print(Markdown("**All Content:** "))
        # render all_content as markdown on terminal
        console.print(Markdown(all_content))

    print("\n")


# Create an instance of AnyOCREngine
#print(deployment_name, api_version_default, azure_vision_key, azure_vision_endpoint, api_version_ai_vision, use_azure_vision)
client = AnyOCREngine(
    # api_key=api_key,
    # azure_base_url=HttpUrl(api_base),
    # azure_base_url=api_base,
    azure_deployment_name=deployment_name,
    api_version=api_version_default,
    azure_vision_key=azure_vision_key,
    azure_vision_endpoint=azure_vision_endpoint,
    azure_vision_api_version=api_version_ai_vision,
    azure_vision_active=use_azure_vision,
    response_handler=resp_handler,
)
# Check if the instance is created successfully
assert isinstance(client, AnyOCREngine)


def display_token_usage(token_info):

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

    if convert_idr:
        import requests
        # Make API call to get USD to IDR conversion rate
        conversion_url = "https://api.exchangerate-api.com/v4/latest/USD"
        response = requests.get(conversion_url)
        currency_data = response.json()
        # Get the conversion rate
        conversion_rate = currency_data["rates"]["IDR"]
    else:
        conversion_rate = 15600
    #print("1 USD = Rp", conversion_rate)
    md_token_info += f"* 1 USD = **Rp {conversion_rate:.2f}**\n"

    # Calculate estimated cost in Rupiah
    estimated_cost_rupiah = estimated_cost * conversion_rate

    #print(f"Estimated cost: $ {estimated_cost} = Rp {estimated_cost_rupiah}")
    md_token_info += f"* Estimated cost: **$ {estimated_cost:.4f}** = **Rp {estimated_cost_rupiah:.2f}**\n"

    console.print(Markdown(md_token_info))
    print("\n")


def do_recognition():
    
    # Send request to the OCR service
    response = client.recognize(
        img_src=img_src_url,
        user_message=user_message,
        temperature=0.2,
        streaming_response=streaming_response,
    )

    # Display Token Usage and Cost, only if not streaming_response
    if not streaming_response:
        token_info = response.usage
        #print("Token usage:", token_info)
        display_token_usage(token_info)


# console.print(Markdown(f"**Recognizing...**"))
with console.status("Recognizing...", spinner='bouncingBall'):
    do_recognition()

    
