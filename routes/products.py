import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from transformers import AutoImageProcessor, AutoModel
from PIL import Image
import torch
from io import BytesIO
from fastapi.concurrency import run_in_threadpool
from supabase import create_client
import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # or anon key for public upload

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

processor = AutoImageProcessor.from_pretrained("facebook/dinov2-base",use_fast=True)
model = AutoModel.from_pretrained("facebook/dinov2-base").to(device)

model=torch.compile(model, mode='reduce-overhead')
model.eval()

def get_embedding(inputs):
    with torch.no_grad():
        outputs = model(**inputs)
        cls = outputs.last_hidden_state[:, 0, :]
        return torch.nn.functional.normalize(cls, dim=-1)

router = APIRouter(prefix="/products", tags=["products"])

def upload_to_supabase(bucket, filename, image_bytes, content_type):
    return supabase.storage.from_(bucket).upload(
        path=filename,
        file=image_bytes,
        file_options={"content-type": content_type}
    )

def insert_product_with_supabase(name, brand, category, price, image_url, embedding_tensor):
        embedding_list = embedding_tensor.squeeze().tolist()
        
        data = {
            "name": name,
            "brand": brand,
            "category": category,
            "price": price,
            "image_url": image_url,
            "embedding": embedding_list
        }
        result = supabase.table("products").insert(data).execute()
        return result

class ProductResponse(BaseModel):
    id: str
    name: str
    brand: str
    category: str
    price: float
    image_url: str

@router.post("/",response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    name: str = Form(...),
    brand: str = Form(...),
    category: str = Form(...),
    price: float = Form(...),
    image: UploadFile = File(...)
):
    try:
        image_bytes = await image.read()
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        inputs = processor(images=img, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        embedding = await run_in_threadpool(get_embedding, inputs)
        unique_id = str(uuid.uuid4())
        filename = f"{unique_id}.jpg"
        bucket = "product-images"

        response = await run_in_threadpool(
        upload_to_supabase,
        bucket,
        filename,
        image_bytes,
        f"image/jpg"
    )   
        public_url = supabase.storage.from_(bucket).get_public_url(response.path)\
        
        insert_result=await run_in_threadpool(
        insert_product_with_supabase,
        name,
        brand,
        category,
        price,
        public_url,
        embedding
    )
        product_data = insert_result.data[0]
        return ProductResponse(**product_data)
    except Exception as e:
         raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
         

    

    