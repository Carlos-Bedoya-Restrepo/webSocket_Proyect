from fastapi import FastAPI,WebSocket,WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Websocket Demo</title>
        <!-- Bootstrap CSS -->
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" 
              rel="stylesheet"  
              crossorigin="anonymous">
    </head>
    <body>
        <div class="container mt-3">
            <h1>FastAPI WebSocket Chat</h1>
            <h2>Your ID: <span id="ws-id"></span></h2>
            <form action="" onsubmit="sendMessage(event)">
                <input type="text" class="form-control" id="messageText" autocomplete="off" />
                <button class="btn btn-outline-primary mt-2">Send</button>
            </form>
            <ul id="messages" class="mt-5">
            </ul>
        </div>

        <script>
            // Generate a unique client ID based on the timestamp
            var client_id = Date.now();
            document.querySelector("#ws-id").textContent = client_id;

            // Create a WebSocket connection with the server
            var ws = new WebSocket(`ws://localhost:8000/ws/${client_id}`);
            
            // Handle incoming messages from the WebSocket server
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages');
                var message = document.createElement('li');
                var content = document.createTextNode(event.data);
                message.appendChild(content);
                messages.appendChild(message);
            };

            // Send a message through the WebSocket when the form is submitted
            function sendMessage(event) {
                var input = document.getElementById("messageText");
                ws.send(input.value);
                input.value = ''; // Clear the input field
                event.preventDefault(); // Prevent form submission
            }
        </script>
    </body>
</html>
"""


class ConnectionManager:
    def __init__(self):
        self.active_connections:list[WebSocket]=[]

    async def connect(self,websocket:WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self,websocket:WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket:WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self,message:str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager=ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def get():
    return HTMLResponse(html)

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket:WebSocket,client_id:int):
    await manager.connect(websocket)
    try:
        while True:
            data=await websocket.receive_text()
            await manager.send_personal_message(f"you wrote: {data}",websocket)
            await manager.broadcast(f'Client #{client_id} says: {data}')
        
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} has left the chat")



