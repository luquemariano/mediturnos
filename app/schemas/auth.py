from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator
from app.schemas.profesional import OnboardingStep


class LoginDatos(BaseModel):
    email: EmailStr
    password: str


class TokenRespuesta(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegistroProfesionalDatos(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: str = Field(min_length=2, max_length=100)
    apellido: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    telefono: str | None = Field(default=None, max_length=30)
    matricula: str = Field(min_length=3, max_length=50)
    especialidad_id: int = Field(gt=0)

    @field_validator("email", mode="before")
    @classmethod
    def normalizar_email(cls, valor: str) -> str:
        return valor.strip().lower()


class RegistroProfesionalRespuesta(TokenRespuesta):
    usuario_id: int
    usuario: str
    rol: str
    profesional_id: int
    onboarding_step: OnboardingStep


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
