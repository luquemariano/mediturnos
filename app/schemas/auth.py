from pydantic import BaseModel, EmailStr, Field, model_validator


class LoginDatos(BaseModel):
    email: EmailStr
    password: str


class TokenRespuesta(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordDatos(BaseModel):
    email: EmailStr


class ResetPasswordDatos(BaseModel):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)


class ChangePasswordDatos(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def validar_password_distinta(self) -> "ChangePasswordDatos":
        if self.current_password == self.new_password:
            raise ValueError("La nueva contraseña debe ser diferente de la actual.")
        return self


class MensajeRespuesta(BaseModel):
    mensaje: str
