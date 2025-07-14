import asyncio
import random
import json
import base64
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pathlib import Path

router = APIRouter(prefix="/ws", tags=["websocket"])

# Dummy product data
DUMMY_PRODUCTS = [
    {"id": "1", "name": "Samsung Galaxy S24", "brand": "Samsung", "category": "Electronics", "price": 899.99, "image_url": "https://example.com/samsung-s24.jpg", "description": "Latest Samsung smartphone with advanced features"},
    {"id": "2", "name": "Nike Air Max 270", "brand": "Nike", "category": "Footwear", "price": 150.00, "image_url": "https://example.com/nike-airmax.jpg", "description": "Comfortable running shoes with Air Max technology"},
    {"id": "3", "name": "MacBook Pro M3", "brand": "Apple", "category": "Electronics", "price": 1999.99, "image_url": "https://example.com/macbook-pro.jpg", "description": "Professional laptop with M3 chip"},
    {"id": "4", "name": "Levi's 501 Jeans", "brand": "Levi's", "category": "Clothing", "price": 69.99, "image_url": "https://example.com/levis-jeans.jpg", "description": "Classic straight-fit jeans"},
    {"id": "5", "name": "Sony WH-1000XM5", "brand": "Sony", "category": "Electronics", "price": 399.99, "image_url": "https://example.com/sony-headphones.jpg", "description": "Noise-canceling wireless headphones"}
]

# Similar products for comparison flags
SIMILAR_PRODUCTS = [
    [
        {"id": "6", "name": "iPhone 15 Pro", "brand": "Apple", "price": 999.99, "image_url": "https://example.com/iphone-15-pro.jpg", "description": "Latest iPhone with titanium design"},
        {"id": "7", "name": "Google Pixel 8", "brand": "Google", "price": 699.99, "image_url": "https://example.com/pixel-8.jpg", "description": "AI-powered smartphone with exceptional photography"},
        {"id": "8", "name": "OnePlus 12", "brand": "OnePlus", "price": 799.99, "image_url": "https://example.com/oneplus-12.jpg", "description": "Flagship smartphone with fast charging"}
    ],
    [
        {"id": "9", "name": "Adidas Ultraboost", "brand": "Adidas", "price": 180.00, "image_url": "https://example.com/adidas-ultraboost.jpg", "description": "High-performance running shoes"},
        {"id": "10", "name": "New Balance 990v5", "brand": "New Balance", "price": 185.00, "image_url": "https://example.com/nb-990v5.jpg", "description": "Premium lifestyle sneakers"},
        {"id": "11", "name": "ASICS Gel-Kayano", "brand": "ASICS", "price": 160.00, "image_url": "https://example.com/asics-gel-kayano.jpg", "description": "Stability running shoes"}
    ]
]

# Ensure user audio dir exists (optional logging)
USER_AUDIO_DIR = Path(os.getenv("USER_AUDIO_DIR", "/tmp/user_audio"))
USER_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def get_random_flag_data() -> dict:
    """Generate random flag data (single, comparison, or similar)"""
    flag_types = ["single", "comparison", "similar"]
    choice = random.choice(flag_types)
    if choice == "single":
        return {"type": "product", "flag": "single", "data": random.choice(DUMMY_PRODUCTS)}
    if choice == "comparison":
        p1, p2 = random.sample(DUMMY_PRODUCTS, 2)
        return {"type": "product", "flag": "comparison", "data": {"product1": p1, "product2": p2, "comparison_reason": "Price difference detected"}}
    # similar
    group = random.choice(SIMILAR_PRODUCTS)
    return {"type": "product", "flag": "similar", "data": {"main_product": random.choice(DUMMY_PRODUCTS), "similar_products": group, "similarity_reason": "Same category products"}}

@router.websocket("/products")
async def websocket_products(websocket: WebSocket):
    """Support multiple audio+image roundtrips per WebSocket connection."""
    await websocket.accept()
    try:
        while True:
            # 1. Wait for audio input
            msg = await websocket.receive()
            if msg.get("type") == "websocket.disconnect":
                break
            if not msg.get("bytes"):
                continue
            audio_bytes = msg["bytes"]

            # 2. Try receiving optional image immediately after audio
            try:
                msg2 = await asyncio.wait_for(websocket.receive(), timeout=1.0)
                if msg2.get("type") == "websocket.disconnect":
                    break
                # Ignore the image bytes, or handle if needed
            except asyncio.TimeoutError:
                pass

            # 3. Respond with audio (and optional JSON)
            response = {
                "type": "audio",
                "data": base64.b64encode(audio_bytes).decode("utf-8"),
                "format": "wav"
            }
            if random.choice([True, False]):
                response["payload"] = get_random_flag_data()

            await websocket.send_text(json.dumps(response))

    except WebSocketDisconnect:
        pass
