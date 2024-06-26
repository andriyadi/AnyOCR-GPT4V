import os
import argparse
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv
from anyocr_app import AnyOCRConsoleApp, AnyOCRConsoleAppMode, parse_arguments


@patch("anyocr_app.OCRClient")
def test_run_recognition_mode(mock_ocr_client):
    load_dotenv()
    args = argparse.Namespace(
        url="https://urgent.id/sistem/foto/newminimallgmailcom-2021-12-29-19-31-30.png",
        prompt=None,
        create=False,
        output=None,
        stream=False,
        vision=False,
        debug=False,
    )
    app = AnyOCRConsoleApp(args)
    app.run()
    mock_ocr_client.assert_called_once()
    mock_ocr_client.return_value.recognize.assert_called_once_with(
        img_src="test_url",
        user_message=app.user_message,
        temperature=0.2,
        streaming_response=False,
        img_detail_level=2,
    )


@patch("anyocr_app.OCRClient")
def test_run_create_template_mode(mock_ocr_client):
    load_dotenv()
    args = argparse.Namespace(
        url="https://urgent.id/sistem/foto/newminimallgmailcom-2021-12-29-19-31-30.png",
        prompt=None,
        create=True,
        output="prompts/prompt_json_tester.md",
        stream=False,
        vision=False,
        debug=False,
    )
    app = AnyOCRConsoleApp(args)
    app.run()
    mock_ocr_client.assert_called_once()
    mock_ocr_client.return_value.recognize.assert_called_once_with(
        img_src="test_url",
        user_message=app.user_message,
        temperature=0.2,
        streaming_response=False,
        img_detail_level=2,
    )
    assert app.appMode == AnyOCRConsoleAppMode.CreateTemplate


def test_parse_arguments():
    with patch(
        "sys.argv",
        [
            "anyocr_app.py",
            "-u",
            "https://urgent.id/sistem/foto/newminimallgmailcom-2021-12-29-19-31-30.png",
            "-p",
            "prompts/prompt_json_ktp.md",
            "-n",
            "True",
            "-o",
            "prompts/prompt_json_tester.md",
            "-s",
            "False",
            "-v",
            "True",
            "-d",
            "True",
        ],
    ):
        args = parse_arguments()
        assert args.url == "https://urgent.id/sistem/foto/newminimallgmailcom-2021-12-29-19-31-30.png"
        assert args.prompt == "prompts/prompt_json_ktp.md"
        assert args.create == True
        assert args.output == "prompts/prompt_json_tester.md"
        assert args.stream == False
        assert args.vision == True
        assert args.debug == True


@patch("anyocr_app.requests.Session")
def test_get_currency_conversion_rate(mock_session):
    mock_response = MagicMock()
    mock_response.json.return_value = {"rates": {"IDR": 15000}}
    mock_session.return_value.__enter__.return_value.get.return_value = mock_response
    app = AnyOCRConsoleApp(argparse.Namespace())
    conversion_rate = app.get_currency_conversion_rate()
    assert conversion_rate == 15000


def test_str_to_bool():
    assert parse_arguments().str_to_bool("true") == True
    assert parse_arguments().str_to_bool("false") == False
    assert parse_arguments().str_to_bool("1") == True
    assert parse_arguments().str_to_bool("0") == False
