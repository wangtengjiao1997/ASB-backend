from app.entities.base import BaseDocument

class Subscribe(BaseDocument):
    user_id: str
    target_id: str
    target_type: str

    class Settings:
        name = "subscribes"
        indexes = [
            [("user_id", 1)],
            [("target_id", 1)],
            [("target_type", 1)]
        ]