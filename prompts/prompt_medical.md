Convert the medical laboratory report into only a JSON format, retaining the original field names in snake case and structuring tables as arrays of values. Omit any fields that are not applicable or cannot be determined from the information given. Translate all text data to English, don't show the original language anymore. If you find jargon or term, use English translation, e.g 'Leukozyten' (in Germany) to 'Leukocytes' (in English).

Example JSON output for the provided image (partial for brevity):

```json
{
  "labor_gemeinschaft": "HAMBURG",
  "address": "Haferweg 36, 22769 Hamburg",
  "fax": "040/334411/9949",
  "report_information": "Befundauskunft: - 9944",
  "responsible_physician": "Dr. med. Niklas Thilo",
  "recipient": {
    "name": "Dr. med. Norbert Sajons",
    "specialization": "Orthopedics",
    "address": "Rathausallee 70, 22846 Norderstedt"
  },
  "id_number": "683-1486",
  "lanr": "0",
  "sample_collection_date": "20.05.2015",
  "receipt_date": "20.05.2015",
  "report_issue_date": "20.05.2015",
  "patient": {
    "name": "Aurorae, Princess",
    "date_of_birth": "28.11.1896"
  },
  "hematology": {
    "small_blood_count": {
      "columns": ["test", "result", "unit", "reference_range"],
      "rows": [
        ["leukozyten", "5.0", "c/nl", "4.2 - 9.1"],
        ["erythrozyten", "4.22", "c/pl", "4.63 - 6.08"],
        ...
      ]
    },
    "differential_blood_count": {
     "columns": ["test", "result", "unit", "reference_range"],
      "rows": [
        ["neutrophile", "65.2", "%", "34.0 - 67.9"],
        ["neutrophile_abs", "3270", "c/ul", "1780 - 5380"],
        ...
      ]
    },
    "clinical_chemistry": {
      "columns": ["test", "result", "unit", "reference_range"],
      "rows": [
        ["got", "55", "u/l", "10 - 50"],
        ["gpt", "84", "u/l", "10 - 50"],
        ...
      ]
    }
  },
  "esr": "34/70"
}
```

If the provided image is not a medical laboratory report, the error message would be:

```json
{
  "status": "error",
  "reason": "The provided image is not a medical laboratory report"
}
```