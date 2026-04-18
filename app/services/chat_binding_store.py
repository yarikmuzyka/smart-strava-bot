import json
from pathlib import Path

from app.core.config import get_settings
from app.schemas.chat_binding import AthleteChatBinding


class ChatBindingStore:
    def __init__(self, file_path: str | None = None) -> None:
        settings = get_settings()
        resolved_path = file_path or str(
            Path(settings.app_data_dir) / "chat_bindings.json"
        )
        self.path = Path(resolved_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save_binding(self, binding: AthleteChatBinding) -> None:
        payload = self._read_all()
        payload[str(binding.athlete_id)] = binding.model_dump()
        self.path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=True),
            encoding="utf-8",
        )

    def get_chat_id(self, athlete_id: int) -> int | None:
        payload = self._read_all()
        raw = payload.get(str(athlete_id))
        if raw is None:
            return None
        binding = AthleteChatBinding.model_validate(raw)
        return binding.chat_id

    def _read_all(self) -> dict:
        if not self.path.exists():
            return {}

        raw_text = self.path.read_text(encoding="utf-8").strip()
        if not raw_text:
            return {}

        return json.loads(raw_text)
