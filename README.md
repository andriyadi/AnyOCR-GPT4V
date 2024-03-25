# AnyOCR-GPT4V
This repo contains the wrapper library and sample app to show the possibility of using GPT-4 with Vision model to recognize and understand text data from any images. You can imagine to use it to develop an OCR app for extracting textual data from any images.

Mentioned wrapper library is `OCRClient.py`. And you can see how to use it in the sample app or `exp_ocr_client.py`

## AnyOCR Console App

AnyOCR Console App is a provided Python application that shows the possibility to use the `OCRClient.py` wrapper library in order to recognize text from any image using OpenAI's GPT-4 with Vision model (hosted on Azure OpenAI Service) and Azure AI Vision. It provides a convenient way to extract text from images and perform various OCR-related tasks.

Features:

- Recognize text from images using OpenAI's GPT-4 with Vision model and Azure AI Vision
- Generate prompt templates to customize text recognition and understanding of specific image category  
- Support for streaming responses
- Estimate token usage and cost, only possible for non-streaming response

## Prerequisites

Before running the AnyOCR Console App, make sure you have the following:

- Latest Python 3.x installed
- Required Python packages installed (see `requirements.txt`)  
- Azure OpenAI Services credentials
- Azure AI Vision API credentials

## Setup  

1. Clone the repository:

   ```
   git clone https://github.com/andriyadi/AnyOCR-GPT4V.git
   ```

2. Install the required Python packages:

   ```
   pip install -r requirements.txt
   ```

3. You MUST create a `.env` file in the project root directory and provide the following values:

   ```
   OPENAI_API_KEY="your-openai-api-key"
   AZURE_OPENAI_BASE_URL="your-azure-openai-base-url" 
   AZURE_OPENAI_DEPLOYMENT_NAME="your-azure-openai-deployment-name"
   AZURE_AI_VISION_ENDPOINT="your-azure-ai-vision-endpoint"
   AZURE_AI_VISION_API_KEY="your-azure-ai-vision-api-key"
   ```

   Replace the placeholders with your actual API credentials.

4. (Optional) Modify the constants in `_constants.py` to customize the behavior of the application.

## Usage

To run the AnyOCR Console App, use the following command:
`python anyocr_app.py [options]`

Available options:

- `-u`, `--url`: URL or file path of the image (default: IMG_SRC from `_constants.py`)
- `-p`, `--prompt`: Path to the prompt file to read  
- `-n`, `--create`: Create a new prompt template (default: False)
- `-o`, `--output`: Output file path of created prompt template
- `-s`, `--stream`: Streaming the response or not (default: USE_STREAMING_RESPONSE from `_constants.py`)
- `-v`, `--vision`: Use Azure AI Vision or not (default: USE_AZURE_VISION from `_constants.py`)
- `-d`, `--debug`: Show debugging messages (default: False)

Example usage:
`python anyocr_app.py -u https://example.com/image.jpg -p prompts/custom_prompt.txt -s True -v True`

## Customization

You can customize the behavior of the AnyOCR Console App by modifying the constants in `_constants.py`. Some notable constants include:

- `USE_AZURE_VISION`: Set to `True` to use Azure AI Vision for OCR (default: `True`)
- `USE_STREAMING_RESPONSE`: Set to `True` to enable streaming responses (default: `False`)
- `PROMPT_GENERATOR_FILEPATH`: Path to the prompt generator file (default: `"prompts/prompt_generator.md"`)
- `USER_MESSAGE`: Default user message for prompting

Feel free to explore and modify other constants to suit your needs.

## License

This project is licensed under the [MIT License](LICENSE).
