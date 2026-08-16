from pydantic import BaseModel, EmailStr, SecretStr


class ResetAdminPasswordEntrada(BaseModel):
    email: EmailStr
    new_password: SecretStr


class MensajeInternoRespuesta(BaseModel):
    mensaje: str
