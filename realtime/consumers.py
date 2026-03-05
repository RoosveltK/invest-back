"""
Django Channels WebSocket consumer for real-time project updates.

Each project has a dedicated group channel: `project_{id}`.
Clients subscribe by connecting to ws/projects/<project_id>/.

The class method `broadcast_update` can be called from sync views/tasks
to push updates to all connected clients of a project.
"""
import json

from channels.generic.websocket import AsyncWebsocketConsumer


class ProjectConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time project event broadcasting."""

    async def connect(self):
        self.project_id = self.scope["url_route"]["kwargs"]["project_id"]
        self.group_name = f"project_{self.project_id}"

        # Authenticate: only authenticated users may connect
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        # Join project group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        """Handle incoming messages from the client (e.g., ping)."""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return
        # Echo back for now; extend for collaborative features
        await self.send(text_data=json.dumps({"echo": data}))

    # ------------------------------------------------------------------
    # Group message handler — called when channel_layer.group_send fires
    # ------------------------------------------------------------------
    async def project_update(self, event):
        """Relay a project_update group message to the WebSocket client."""
        await self.send(text_data=json.dumps(event.get("data", {})))

    # ------------------------------------------------------------------
    # Class-level helper for broadcasting from sync code (views / tasks)
    # ------------------------------------------------------------------
    @classmethod
    async def broadcast_update(cls, project_id: int, data: dict):
        """
        Send a message to all WebSocket clients subscribed to the project group.
        Use from sync code via: asyncio.run(ProjectConsumer.broadcast_update(...))
        """
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            f"project_{project_id}",
            {
                "type": "project.update",
                "data": data,
            },
        )
