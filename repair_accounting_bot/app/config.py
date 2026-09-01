from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    BOT_TOKEN: str
    ALLOWED_USER_IDS: str = ''
    ADMIN_USER_IDS: str = ''
    DATABASE_PATH: str = './data/repair_accounting.db'
    EXPORT_DIR: str = './data/exports'
    TELEGRAM_PROXY: str | None = None

    def allowed_user_ids(self) -> set[int]:
        return self._parse_ids(self.ALLOWED_USER_IDS)

    def admin_user_ids(self) -> set[int]:
        admins = self._parse_ids(self.ADMIN_USER_IDS)
        if admins:
            return admins
        allowed = self.allowed_user_ids()
        return {next(iter(allowed))} if allowed else set()

    @staticmethod
    def _parse_ids(raw: str) -> set[int]:
        ids: set[int] = set()
        for part in raw.split(','):
            part = part.strip()
            if part.isdigit():
                ids.add(int(part))
        return ids


settings = Settings()
