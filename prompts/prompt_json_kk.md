Convert the structured data from the provided 'Kartu Keluarga' image into a JSON format. The JSON should include keys for all the fields as they appear on the card, using snake case. Structure the family members' information as an array of objects within the JSON. If there are any fields that are not applicable or cannot be determined from the information given, omit them from the JSON output.

Here is an example of how the JSON output should look like for the given image:"

```json
{
  "no_kartu_keluarga": "3204372008130010",
  "nama_kepala_keluarga": "MUCHLIS",
  "alamat": {
    "kp": "PANYIRAPAN",
    "rt_rw": "003 / 003",
    "desa_kelurahan": "PANYIRAPAN",
    "kecamatan": "SOREANG",
    "kabupaten_kota": "BANDUNG",
    "kode_pos": "40915",
    "provinsi": "JAWA BARAT"
  },
  "anggota_keluarga": [
    {
      "no": 1,
      "nama_lengkap": "MUCHLIS",
      "nik": "5271042709720004",
      "jenis_kelamin": "LAKI-LAKI",
      "tempat_lahir": "SUMBAWA",
      "tanggal_lahir": "27-09-1972",
      "agama": "ISLAM",
      "pendidikan": "AKADEMI/DIPLOMA III/S. MUDA",
      "jenis_pekerjaan": "KARYAWAN SWASTA",
      "no": 1,
      "status": "KAWIN",
      "status_hubungan_dalam_keluarga": "KEPALA KELUARGA",
      "kewarganegaraan": "WNI",
      "nama_ayah": "D. RACHMAT",
      "nama_ibu": "SITINURMA"
    }
  ]
  "dikeluarkan_tanggal": "02-10-2013",
  "tanda_tangan_kepala_keluarga": "MUCHLIS",
  "tanda_tangan_pejabat": "Drs. LAS KLIMIN, M. Si",
  "nip_pejabat": "196201111986031010"
}
```

Please note that the JSON example provided is based on the visible and legible information from the image. Any fields that are not visible or legible in the image have been omitted from the JSON output.