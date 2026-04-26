from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Config(BaseSettings):
    app_name: str = "Data-Collection-Backend"
    debug: bool = False
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "slep"
    db_host: str = "localhost"
    db_port: int = 5432
    redis_url: str = "redis://redis:6379/0"
    s3_url: str = "http://s3:9000"
    s3_user: str = "minioadmin"
    s3_password: str = "minioadmin"
    s3_bucket: str = "slep-bucket"
    tmp_dir: str = "/tmp-dir"

    @property
    def db_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def db_url_sync(self) -> str:
        return f"postgresql+psycopg2://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

config = Config()