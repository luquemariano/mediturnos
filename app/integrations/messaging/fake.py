from dataclasses import dataclass, field

from .base import (
    MessageDeliveryResult,
    MessagingProviderError,
    OutboundMessage,
)


@dataclass
class FakeMessagingProvider:
    sent_messages: list[OutboundMessage] = field(default_factory=list)
    fail_next: bool = False
    _next_id: int = 1

    def send(self, message: OutboundMessage) -> MessageDeliveryResult:
        if self.fail_next:
            self.fail_next = False
            raise MessagingProviderError("El proveedor de mensajería no está disponible.")
        self.sent_messages.append(message)
        provider_message_id = f"fake-message-{self._next_id:06d}"
        self._next_id += 1
        return MessageDeliveryResult(
            accepted=True,
            provider="fake",
            provider_message_id=provider_message_id,
        )
