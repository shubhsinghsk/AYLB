"""FastAPI application setup for AYLB Logistics."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent
load_dotenv(PROJECT_DIR / ".env")
INSTANCE_DIR = PROJECT_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite:///{(INSTANCE_DIR / 'site.db').as_posix()}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


@asynccontextmanager
async def lifespan(_: FastAPI):
    from AYLB_LOGIS import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="AYLB Logistics", lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key="5791628bb0b13ce0c676dfde280ba245",
    same_site="lax",
    https_only=False,
)
app.mount("/static", StaticFiles(directory=PACKAGE_DIR / "static"), name="static")

from AYLB_LOGIS import routes  # noqa: E402,F401
