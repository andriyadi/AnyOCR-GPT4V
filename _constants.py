# Constants
# OpenAI default parameters
OCR_OAI_DEFAULT_TEMPERATURE: float = 0.0
OCR_OAI_DEFAULT_MAX_TOKEN: int = 4096

OCR_USE_AZURE_VISION: bool = True
OCR_USE_STREAMING_RESPONSE: bool = False
OCR_API_VERSION_DEFAULT: str = "2024-02-15-preview"     # this might change in the future
OCR_API_VERSION_AI_VISION: str = "2023-12-01-preview"   # this might change in the future

OCR_PROMPT_GENERATOR_FILEPATH = "prompts/prompt_generator.md"

# OCR_USER_MESSAGE = "Explain the image. Extract all text from this image and turn into table format if possible. If you find person face photo, give me coordinate of bounding box."
OCR_USER_MESSAGE: str = " \
    Extract title, number, and date from the image. Turn all information into table format, if possible. \
    And if the table is too wide, split into more than one table. \
    If no value recognized, put '-' string. \
    If there are price number in the list, add all to the total price by yourself and show, only if the total number is not present. \
    Don't translate the text to English. Keep it in Indonesian. Give your judgement about image and text clarity. Explain all in Bahasa Indonesia. "  
    # The most bottom number is saldo akhir. The biggest one is the transaction cost. This is receipt for highway toll road. "
# Also estimate the coordinate of recognized text within the image in (x, y, w, h) format, right after you display the text information. \
# Calculate the total amount of listed currency number. \



# === SAMPLE IMAGES ===
# KTP
OCR_DEFAULT_IMG_SRC = "https://urgent.id/sistem/foto/newminimallgmailcom-2021-12-29-19-31-30.png"

# Kartu Keluarga
# OCR_DEFAULT_IMG_SRC = "https://i.pinimg.com/originals/72/29/fd/7229fde0cbf5869e961946b0b7e75969.jpg"
OCR_DEFAULT_IMG_SRC = "https://i.pinimg.com/originals/e0/2d/7b/e02d7b14363fa33abcd775366c877890.jpg"

# Toll receipt
# OCR_DEFAULT_IMG_SRC = "https://img.cintamobil.com/resize/600x-/2020/08/11/f8286LtF/struk-jalan-tol-6ecd.jpg"
# OCR_DEFAULT_IMG_SRC = "https://cf.shopee.co.id/file/sg-11134201-22120-zc9wai89n9kvf0"

# Struk SPBU
# OCR_DEFAULT_IMG_SRC = "https://edorusyanto.files.wordpress.com/2013/12/struk-spbu-isi-gan.jpg"

# Receipt image
# Not too challenging
# OCR_DEFAULT_IMG_SRC = "https://akcdn.detik.net.id/community/media/visual/2023/07/13/bikin-kantong-kering-harga-makanan-di-5-tempat-ini-terlalu-mahal-1.jpeg?w=1024"
# OCR_DEFAULT_IMG_SRC = "https://media-cdn.tripadvisor.com/media/photo-s/11/7d/b7/58/bon-makan-di-paul.jpg"
# Handwritten text
# OCR_DEFAULT_IMG_SRC = "https://akcdn.detik.net.id/community/media/visual/2023/07/13/bikin-kantong-kering-harga-makanan-di-5-tempat-ini-terlalu-mahal-4.jpeg?w=700&q=90"
# OCR_DEFAULT_IMG_SRC = "https://cdn1-production-images-kly.akamaized.net/4hFAOzyOoPf86cye6hjTx6E-62s=/500x667/smart/filters:quality(75):strip_icc():format(webp)/kly-media-production/medias/3470509/original/051746300_1622604393-WhatsApp_Image_2021-06-02_at_10.03.32__1_.jpeg"
# OCR_DEFAULT_IMG_SRC = "https://boombastis.sgp1.digitaloceanspaces.com/wp-content/uploads/2014/09/Heboh-Makan-di-Warung-Biasa-Harus-Bayar-Sampai-Rp-1-Juta-1.jpg"
# Miring
# OCR_DEFAULT_IMG_SRC = "https://media-cdn.tripadvisor.com/media/photo-s/1a/c5/40/6d/the-receipt.jpg"