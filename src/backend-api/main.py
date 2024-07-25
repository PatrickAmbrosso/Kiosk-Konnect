from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json
import os
from typing import List, Tuple
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
from fastapi.middleware.cors import CORSMiddleware

# Global Declarations
app = FastAPI()
content = None
content_file_path: str = os.path.join("data", "content.json")
active_clients: List[WebSocket] = []

# Add this to your FastAPI app setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Utility functions ===================================
async def reload_clients():
    for client in active_clients:
        try:
            await client.send_text("reload")
        except:
            # Handle potential errors here
            active_clients.remove(client)


async def update_content() -> Tuple[bool, str]:
    global content
    try:
        with open(content_file_path, "r") as file:
            content = json.load(file)
        print("Loaded content ")
        return (True, f"Content updated successfully")
    except FileNotFoundError:
        return (False, f"File not found: {content_file_path}")
    except json.JSONDecodeError:
        return (False, f"Invalid JSON in file: {content_file_path}")


# API Endpoints =======================================

# Functionalities of the application
# - Has a way to manage the content
# - Has an interface to set the content to each node
# - Each node takes in an adoption route
# -

# Required Endpoints
# - To fetch the content to be used as json


@app.post("/actions/update-content")
async def trigger_content_update() -> JSONResponse:
    status, msg = await update_content()
    if status:
        return JSONResponse(content={"SUCCESS": msg}, status_code=200)
    else:
        return JSONResponse(content={"ERROR": msg}, status_code=500)


@app.post("/actions/trigger-reload")
async def trigger_ws_reload() -> JSONResponse:
    try:
        await reload_clients()
        return JSONResponse(
            content={"message": "Reload signal sent to all clients"}, status_code=200
        )
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/")
async def home():
    return JSONResponse(content={"Status": "API is operational"}, status_code=200)


@app.get("/content/{node_id}")
async def get_content(node_id: str):
    global content
    if content is None:
        return JSONResponse(
            content={"error": "Content not initialized"}, status_code=500
        )
    if node_id not in content:
        return JSONResponse(
            content={"error": "Requested node does not have content set"},
            status_code=404,
        )
    return content[node_id]


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_clients.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            if data == "reload":
                await reload_clients()
    except WebSocketDisconnect:
        active_clients.remove(websocket)


# Run the application using uvicorn if this script is executed directly
if __name__ == "__main__":
    asyncio.run(update_content())
    uvicorn.run(app, host="127.0.0.1", port=3500)
