import jwt
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import relationship

from saraki.model import BaseModel, Model


class DummyBaseModel(BaseModel):
    __tablename__ = "dummy_base_model"

    id = Column(Integer, primary_key=True)


class DummyModel(Model):
    __tablename__ = "dummy_model"

    id = Column(Integer, primary_key=True)


class Person(Model):

    __tablename__ = "person"

    id = Column(Integer, primary_key=True)

    firstname = Column(String, nullable=False)

    lastname = Column(String, nullable=False)

    age = Column(Integer, nullable=False)

    def export_data(self, include=("id", "firstname"), exclude=()):
        return super(Person, self).export_data(include, exclude)


class Product(BaseModel):

    __tablename__ = "product"

    id = Column(Integer, primary_key=True)

    name = Column(String(120), nullable=False)

    color = Column(String, default="white")

    price = Column(Integer, default=0)

    created_at = Column(DateTime, nullable=False, default=func.now())

    updated_at = Column(DateTime, nullable=False, server_default=func.now())

    enabled = Column(Boolean, default=False)


class Order(BaseModel):

    __tablename__ = "order"

    id = Column(Integer, primary_key=True)

    customer_id = Column(Integer, ForeignKey("person.id"), nullable=False)

    lines = relationship("OrderLine")

    customer = relationship("Person", uselist=False)


class OrderLine(Model):

    __tablename__ = "order_line"

    order_id = Column(Integer, ForeignKey("order.id"), nullable=False, primary_key=True)

    product_id = Column(
        Integer, ForeignKey("product.id"), nullable=False, primary_key=True
    )

    unit_price = Column(Integer, nullable=False)

    quantity = Column(Integer, default=1, nullable=False)

    product = relationship("Product", uselist=False)

    def export_data(self, include=("product_id", "unit_price", "quantity"), exclude=()):
        return super(OrderLine, self).export_data(include, exclude)


class Cartoon(Model):

    __tablename__ = "cartoon"

    id = Column(Integer, primary_key=True)

    name = Column(String(80), unique=True, nullable=False)

    nickname = Column(String(80), unique=True)


class Todo(Model):

    __tablename__ = "todo"

    id = Column(Integer, primary_key=True)

    org_id = Column(Integer, ForeignKey("org.id"), nullable=False)

    task = Column(String(200), nullable=False)


def login(username, orgname=None, scope=None):
    iat = datetime.utcnow()
    exp = iat + timedelta(seconds=6000)
    payload = {"iss": "acme.local", "sub": username, "iat": iat, "exp": exp}

    if orgname:
        payload.update({"aud": orgname, "scp": {"org": ["manage"]}})

    if scope:
        payload.update({"scp": scope})

    token = jwt.encode(payload, "secret").decode()

    return f"JWT {token}"
