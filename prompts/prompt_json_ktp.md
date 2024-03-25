First, check if the provided image is actually an Indonesian citizen card (Kartu Tanda Penduduk - KTP). If not, please do not continue, and provide an error message in JSON format as follows:
{
"status": "error",
"reason": "The provided image is not an Indonesian citizen card (KTP)"
}
If the image is a valid Indonesian KTP, please extract all the text from the card and organize it into a JSON object with appropriate key-value pairs for each field. The JSON keys should retain the original field names in Bahasa Indonesia. Omit any fields that are not applicable or cannot be clearly determined from the information given in the image.
The JSON object should follow this structure:
{
"provinsi": "",
"kota": "",
"nik": "",
"nama": "",
"tempat_lahir": "",
"tgl_lahir": "",
"jenis_kelamin": "",
"gol_darah": "",
"alamat": "",
"alamat_rt_rw": "",
"alamat_kel_desa": "",
"alamat_kecamatan": "",
"agama": "",
"status_perkawinan": "",
"pekerjaan": "",
"kewarganegaraan": "",
"berlaku_hingga": "",
"tgl_terbit": ""
}

Notes:

- "tgl_terbit" refers to the date of issuance, which is located above the signature on the card.
- The keys reflect the field labels visible on the KTP image. Only include keys for fields that are clearly legible.
- If a field is present on the card but the value is not clearly legible, include the key but leave the value as an "-" string.
