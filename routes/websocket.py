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

# Configurable directory for storing user audio
USER_AUDIO_DIR = Path(os.getenv("USER_AUDIO_DIR", "/tmp/user_audio"))
USER_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def get_random_flag_data() -> dict:
    """Generate random flag data (single, comparison, or similar)"""
    flag_types = ["single", "comparison", "similar"]
    flag_type = random.choice(flag_types)

    if flag_type == "single":
        product = random.choice(DUMMY_PRODUCTS)
        return {"type": "product", "flag": "single", "data": product}

    if flag_type == "comparison":
        p1, p2 = random.sample(DUMMY_PRODUCTS, 2)
        return {
            "type": "product",
            "flag": "comparison",
            "data": {"product1": p1, "product2": p2, "comparison_reason": "Price difference detected"}
        }

    # similar
    group = random.choice(SIMILAR_PRODUCTS)
    main = random.choice(DUMMY_PRODUCTS)
    return {
        "type": "product",
        "flag": "similar",
        "data": {"main_product": main, "similar_products": group, "similarity_reason": "Same category products"}
    }


@router.websocket("/products")
async def websocket_products(websocket: WebSocket):
    """WebSocket: on user audio, echo audio back or send audio + JSON flag data."""
    await websocket.accept()
    try:
        # 1. Receive initial audio from client
        msg = await websocket.receive()
        if msg.get("type") == "websocket.receive" and msg.get("bytes"):
            audio_bytes = msg["bytes"]
        else:
            # Invalid initial message, close with unsupported data
            await websocket.close(code=1003)
            return

        # 2. Decide whether to include product JSON
        include_text = random.choice([True, False])

        # 3. Build response
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        response = {"type": "audio", "data": audio_b64, "format": "wav"}

        if include_text:
            response["payload"] = get_random_flag_data()

        # 4. Send back the audio (and optional JSON)
        await websocket.send_text(json.dumps(response))

        # 5. Keep the connection alive until the client disconnects
        while True:
            msg2 = await websocket.receive()
            if msg2.get("type") == "websocket.disconnect":
                break

    except WebSocketDisconnect:
        # Client disconnected normally
        pass
    finally:
        await websocket.close()
