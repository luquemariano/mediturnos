from pydantic import BaseModel, EmailStr


class LoginDatos(BaseModel):
    email: EmailStr
    password: str


class TokenRespuesta(BaseModel):
    access_token: str
    token_type: str = "bearer"