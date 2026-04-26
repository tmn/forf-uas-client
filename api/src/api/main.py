from fastapi import HTTPException
from pydantic import ConfigDict
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import DeclarativeBase
from .db import SessionLocal
from fastapi import FastAPI

app = FastAPI()


class Base(DeclarativeBase):
    pass


class Uav(Base):
    __tablename__ = "uav"
    serial_number: Mapped[str] = mapped_column(primary_key=True)
    callsign: Mapped[str]
    regid: Mapped[str]
    notes: Mapped[str]
    active: Mapped[bool]
    external: Mapped[bool]
    updated_at: Mapped[datetime]


class UavResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    serial_number: str
    callsign: str
    regid: str
    notes: str
    active: bool
    external: bool


@app.get("/uav", response_model=list[UavResponse])
def get_all_uavs():
    with SessionLocal() as session:
        uavs = session.query(Uav).all()
        return uavs


@app.get("/uav/{id}", response_model=UavResponse)
def get_uav(id: str):
    with SessionLocal() as session:
        uav = session.query(Uav).where(Uav.serial_number == id).first()

        if uav is None:
            raise HTTPException(status_code=404, detail=f"UAV {id} not found")

        return uav
