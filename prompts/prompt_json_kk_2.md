Convert the information from the provided 'Kartu Keluarga' into a structured JSON format. Retain the original field names in Bahasa Indonesia, using snake case for the keys. Structure the JSON with the main fields and include an array of objects for the family members' details. If a field is not applicable or cannot be determined, omit it from the JSON. I provide an example of the JSON output based on the image, and ensure it is as generic as possible for similar documents.

Here is an example of the JSON output based on the provided image:

```json
{
  "no_kartu_keluarga": "3204372008130010",
  "nama_kepala_keluarga": "MUCHLIS",
  "alamat": {
    "alamat": "KP. PANYIRAPAN",
    "rt_rw": "003 / 003",
    "desa_kelurahan": "PANYIRAPAN",
    "kecamatan": "SOREANG",
    "kabupaten_kota": "BANDUNG",
    "kode_pos": "40915",
    "provinsi": "JAWA BARAT"
  },
  "anggota_keluarga": [
    {
      "no": "1",
      "nama_lengkap": "MUCHLIS",
      "nik": "5271042709720004",
      "jenis_kelamin": "LAKI-LAKI",
      "tempat_lahir": "SUMBAWA",
      "tanggal_lahir": "27-09-1972",
      "agama": "ISLAM",
      "pendidikan": "AKADEMI/DIPLOMA III/S. MUDA",
      "jenis_pekerjaan": "KARYAWAN SWASTA",
      "status_perkawinan": "KAWIN",
      "status_hubungan_dalam_keluarga": "KEPALA KELUARGA",
      "kewarganegaraan": "WNI",
      "ayah": "D. RACHMAT",
      "ibu": "SITINURMA"
    },
  ],
  "tanggal_penerbitan": "02-10-2013",
  "pejabat_penandatangan": "MUCHLIS",
  "nip_pejabat": "196201111986031010"
}
```

This JSON structure captures the main details of the 'Kartu Keluarga' and the individual family members' information as an array of objects. Each family member's details are a separate object within the array.

If the provided image is not a "Kartu Keluarga" (Family Card), the LLM should return the following error message:

```json
{
  "status": "error",
  "reason": "The provided image is not a Kartu Keluarga"
}
```