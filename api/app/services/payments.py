from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class PaymentConfirmation:
    confirmed: bool
    note: str
    external_reference: str


class PaymentProvider(ABC):
    @abstractmethod
    def confirm(self, confirmation: PaymentConfirmation) -> None:
        """Validate a payment confirmation without performing a payment."""


class ManualPaymentProvider(PaymentProvider):
    def confirm(self, confirmation: PaymentConfirmation) -> None:
        if not confirmation.confirmed:
            raise ValueError("线下付款尚未确认")
        if not confirmation.note.strip() and not confirmation.external_reference.strip():
            raise ValueError("请填写付款备注或外部付款参考号")


payment_provider: PaymentProvider = ManualPaymentProvider()
