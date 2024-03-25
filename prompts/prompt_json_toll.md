Please convert the following toll receipt information into a JSON format. Retain the original field names in Bahasa Indonesia and use snake case for the JSON keys. Structure the JSON output as follows:

- `nama_jalan_tol`: The name of the toll road.
- `info_tol`: The toll information contact number.
- `lokasi`: The location where the toll was charged.
- `tanggal_transaksi`: The date and time of the transaction.
- `no_seri`: The serial number of the receipt.
- `asal`: The origin point of the journey.
- `golongan_kendaraan`: The vehicle class.
- `metode_pembayaran`: The payment method used.
- `jumlah_tarif`: The amount charged for the toll.
- `sn`: The serial number associated with the transaction.
- `balance`: The total amount paid.

Exclude any fields that are not applicable or cannot be determined from the information given. If the image is not a toll receipt, return an error message in JSON format stating that the provided image is not a toll receipt.

Here is an example of the JSON output for the provided image:

```json
{
  "nama_jalan_tol": "Surabaya Mojukerto",
  "info_tol": {
    "telepon": "031-7876677",
    "handphone": "082211826677"
  },
  "lokasi": "WARU GUNUNG",
  "tanggal_transaksi": "20/01/2019 20:51:48",
  "no_seri": "322152 01034/02005",
  "asal": "COLOMADU [14 21]",
  "golongan_kendaraan": "GOL-1",
  "metode_pembayaran": "e-Toll BRI",
  "jumlah_tarif": 220000,
  "sn": "6013502102504195",
  "balance": 46046
}
```

If the provided image is not a toll receipt, the LLM should return the following error message:

```json
{
  "status": "error",
  "reason": "The provided image is not a toll receipt"
}
```