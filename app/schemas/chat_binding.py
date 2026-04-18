from pydantic import BaseModel


class AthleteChatBinding(BaseModel):
    athlete_id: int
    chat_id: int
