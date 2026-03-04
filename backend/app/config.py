from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://secnews:secnews_dev_password@localhost:5432/secnews"
    JWT_SECRET: str = "change-me-to-a-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    LOG_LEVEL: str = "INFO"
    CRAWL_BROWSER_TYPE: str = "chromium"
    CRAWL_HEADLESS: bool = True
    CRAWL_PAGE_TIMEOUT_MS: int = 45000
    CRAWL_MAX_RETRIES: int = 2
    CRAWL_WAIT_FOR: str = "css:article, main, [role='main']"
    CRAWL_MIN_CONTENT_LEN: int = 200
    CRAWL_MAX_CONTENT_LEN: int = 5000
    CRAWL_SIMULATE_USER: bool = True
    CRAWL_MAGIC: bool = True
    CRAWL_CHECK_ROBOTS: bool = False
    CRAWL_USER_AGENT: str = "SecNewsBot/1.0 (+https://example.com)"
    CRAWL_DOMAIN_OVERRIDES_JSON: str = "{}"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
