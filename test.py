import requests

# --- Replace with your actual FastAPI endpoint URL ---
url = "http://localhost:8000/products/"

# --- Path to your image file ---
image_path = "sample5.jpg"  # make sure this image exists in the same directory

# --- Form data to send ---
form_data = {
    "name": "Test Product",
    "brand": "Test Brand",
    "category": "Test Category",
    "price": "199.99"
}

# --- Open the image in binary mode ---
with open(image_path, "rb") as image_file:
    files = {
        "image": ("sample.jpg", image_file, "image/jpeg")
    }

    # Send POST request
    response = requests.post(url, data=form_data, files=files)

# --- Print the response ---
print("Status Code:", response.status_code)
print("Response JSON:", response.json())
