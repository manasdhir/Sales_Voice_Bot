import asyncio
import random
import json
import base64
import os
from typing import List, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pathlib import Path

router = APIRouter(prefix="/ws", tags=["websocket"])

# Dummy product data
DUMMY_PRODUCTS = [
    {
        "id": "1",
        "name": "Samsung Galaxy S24",
        "brand": "Samsung",
        "category": "Electronics",
        "price": 899.99,
        "image_url": "https://example.com/samsung-s24.jpg",
        "description": "Latest Samsung smartphone with advanced features"
    },
    {
        "id": "2",
        "name": "Nike Air Max 270",
        "brand": "Nike",
        "category": "Footwear",
        "price": 150.00,
        "image_url": "https://example.com/nike-airmax.jpg",
        "description": "Comfortable running shoes with Air Max technology"
    },
    {
        "id": "3",
        "name": "MacBook Pro M3",
        "brand": "Apple",
        "category": "Electronics",
        "price": 1999.99,
        "image_url": "https://example.com/macbook-pro.jpg",
        "description": "Professional laptop with M3 chip"
    },
    {
        "id": "4",
        "name": "Levi's 501 Jeans",
        "brand": "Levi's",
        "category": "Clothing",
        "price": 69.99,
        "image_url": "https://example.com/levis-jeans.jpg",
        "description": "Classic straight-fit jeans"
    },
    {
        "id": "5",
        "name": "Sony WH-1000XM5",
        "brand": "Sony",
        "category": "Electronics",
        "price": 399.99,
        "image_url": "https://example.com/sony-headphones.jpg",
        "description": "Noise-canceling wireless headphones"
    }
]

# Similar products for comparison flags
SIMILAR_PRODUCTS = [
    [
        {"id": "6", "name": "iPhone 15 Pro", "brand": "Apple", "price": 999.99, "image_url": "https://example.com/iphone-15-pro.jpg", "description": "Latest iPhone with titanium design and advanced camera system"},
        {"id": "7", "name": "Google Pixel 8", "brand": "Google", "price": 699.99, "image_url": "https://example.com/pixel-8.jpg", "description": "AI-powered smartphone with exceptional photography capabilities"},
        {"id": "8", "name": "OnePlus 12", "brand": "OnePlus", "price": 799.99, "image_url": "https://example.com/oneplus-12.jpg", "description": "Flagship smartphone with fast charging and smooth performance"}
    ],
    [
        {"id": "9", "name": "Adidas Ultraboost", "brand": "Adidas", "price": 180.00, "image_url": "https://example.com/adidas-ultraboost.jpg", "description": "High-performance running shoes with responsive cushioning"},
        {"id": "10", "name": "New Balance 990v5", "brand": "New Balance", "price": 185.00, "image_url": "https://example.com/nb-990v5.jpg", "description": "Premium lifestyle sneakers with classic design and comfort"},
        {"id": "11", "name": "ASICS Gel-Kayano", "brand": "ASICS", "price": 160.00, "image_url": "https://example.com/asics-gel-kayano.jpg", "description": "Stability running shoes with gel cushioning technology"}
    ]
]

def get_random_flag_data() -> Dict[str, Any]:
    """Generate random flag data (single, comparison, or similar)"""
    flag_types = ["single", "comparison", "similar"]
    flag_type = random.choice(flag_types)
    
    if flag_type == "single":
        product = random.choice(DUMMY_PRODUCTS)
        return {
            "type": "product",
            "flag": "single",
            "data": product
        }
    
    elif flag_type == "comparison":
        # Two products for comparison
        products = random.sample(DUMMY_PRODUCTS, 2)
        return {
            "type": "product",
            "flag": "comparison",
            "data": {
                "product1": products[0],
                "product2": products[1],
                "comparison_reason": "Price difference detected"
            }
        }
    
    else:  # similar
        similar_group = random.choice(SIMILAR_PRODUCTS)
        return {
            "type": "product",
            "flag": "similar",
            "data": {
                "main_product": random.choice(DUMMY_PRODUCTS),
                "similar_products": similar_group,
                "similarity_reason": "Same category products"
            }
        }

def get_audio_file_data(filename: str) -> Dict[str, Any]:
    """Read and encode audio file to base64"""
    audio_path = Path(f"/home/manas/walmart_backend/{filename}")
    
    if not audio_path.exists():
        return {
            "type": "audio",
            "error": f"Audio file {filename} not found"
        }
    
    try:
        with open(audio_path, "rb") as audio_file:
            audio_data = audio_file.read()
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
        return {
            "type": "audio",
            "filename": filename,
            "data": audio_base64,
            "format": "wav"
        }
    except Exception as e:
        return {
            "type": "audio",
            "error": f"Failed to read {filename}: {str(e)}"
        }

@router.websocket("/products")
async def websocket_products(websocket: WebSocket):
    """WebSocket endpoint for streaming products with flags/audio and receiving user audio input."""
    await websocket.accept()

    # For debug or temporary storage
    user_audio_dir = Path("/tmp/user_audio")
    user_audio_dir.mkdir(parents=True, exist_ok=True)

    async def sender():
        while True:
            await asyncio.sleep(random.uniform(2, 8))
            try:
                if random.random() < 0.7:
                    message = get_random_flag_data()
                else:
                    audio_files = ["test audio_hindi.wav", "test audio_english.wav"]
                    selected_audio = random.choice(audio_files)
                    message = get_audio_file_data(selected_audio)
                message["timestamp"] = asyncio.get_event_loop().time()
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                print(f"[Sender] Error: {e}")
                break

    async def receiver():
        while True:
            try:
                data = await websocket.receive()
                if "bytes" in data:
                    # Save received audio blob to disk
                    filename = f"user_audio_{int(asyncio.get_event_loop().time() * 1000)}.wav"
                    file_path = user_audio_dir / filename
                    with open(file_path, "wb") as f:
                        f.write(data["bytes"])
                    print(f"[Receiver] Received and saved audio: {file_path}")
                elif "text" in data:
                    print(f"[Receiver] Ignoring received text: {data['text']}")
            except Exception as e:
                print(f"[Receiver] Error: {e}")
                break

    try:
        await asyncio.gather(sender(), receiver())
    except WebSocketDisconnect:
        print("WebSocket client disconnected.")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()

@router.websocket("/products/test")
async def websocket_test(websocket: WebSocket):
    """Test WebSocket endpoint for debugging"""
    await websocket.accept()
    
    try:
        counter = 0
        while True:
            counter += 1
            message = {
                "type": "test",
                "message": f"Test message {counter}",
                "timestamp": asyncio.get_event_loop().time()
            }
            
            await websocket.send_text(json.dumps(message))
            await asyncio.sleep(3)  # Send every 3 seconds
            
    except WebSocketDisconnect:
        print("Test WebSocket client disconnected")
    except Exception as e:
        print(f"Test WebSocket error: {str(e)}")
        await websocket.close()