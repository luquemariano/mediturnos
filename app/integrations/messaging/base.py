from dataclasses import dataclass, field
from typing import Literal, Mapping, Protocol, runtime_checkable


MessagingChannel = Literal["whatsapp"]
MessageStatus = Literal["accepted"]


@dataclass(frozen=True)
class OutboundMessage:
    channel: MessagingChannel
    recipient: str
    message_type: str
    payload: Mapping[str, str] = field(default_factory=dict)
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class MessageDeliveryResult:
    accepted: bool
    provider: str
    provider_message_id: str | None = None
    status: MessageStatus = "accepted"


class MessagingProviderError(RuntimeError):
    """Error sanitizado de entrega de mensajería."""


class MessagingConfigurationError(MessagingProviderError):
    """El provider solicitado no está disponible o configurado."""


@runtime_checkable
class MessagingProvider(Protocol):
    def send(self, message: OutboundMessage) -> MessageDeliveryResult: ...
