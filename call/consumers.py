import json
from channels.generic.websocket import AsyncWebsocketConsumer

class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data["type"] == "offer":
            await self.send(text_data=json.dumps({
                "type": "offer",
                "offer": data["offer"]
            }))
        elif data["type"] == "answer":
            await self.send(text_data=json.dumps({
                "type": "answer",
                "answer": data["answer"]
            }))
        elif data["type"] == "ice-candidate":
            await self.send(text_data=json.dumps({
                "type": "ice-candidate",
                "candidate": data["candidate"]
            }))
