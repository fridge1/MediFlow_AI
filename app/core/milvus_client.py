from typing import Optional

class MilvusClient:
    def __init__(self, host: str, port: int, user: Optional[str] = None, password: Optional[str] = None):
        self.host = host
        self.port = port
        self.user = user
        self.password = password

    async def connect(self):
        return True

    async def close(self):
        return True
