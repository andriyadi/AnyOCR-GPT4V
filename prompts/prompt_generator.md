Explain the provided image. Then based on the text data in the image, suggest me a prompt for LLM that would enable it to convert the text into only a JSON format for images of a similar nature. The JSON keys should retain the original field names (use original language) and use snake case. Omit any fields that are not applicable or cannot be determined from the information given.

In instances where a table with multiple rows is identified within the image, structure the corresponding JSON element as an array of the field names, followed by 2D array of relevant values. For examples:
{
"columns": ["field1", "field2", "field3"],
"rows": [
["value1", "value2", "value3"],
["value1", "value2", "value3"]
]
}
Should there be multiple tables with content that appears interconnected, consolidate them into the above arrays, instead of separated collection of arrays.

Then for the prompt output, you need to provide an example for the JSON output, and only a partial example is provided for brevity.

Make as generic as posssible.

If the provided image is not similar document as the one provided, respond with an error message in JSON format as follows:
{
"status": "error",
"reason": "The provided image is not an {document type}"
}
Note: {document type} is detected type of document
