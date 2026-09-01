from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

# ISO 4217 minor-unit exponents that differ from the two-decimal default. Payments
# talks to Stripe in minor units, so converting with a blanket x100 silently
# overcharges a zero-decimal currency by a hundred and undercharges a three-decimal
# one by ten.
_MINOR_UNIT_EXPONENTS: dict[str, int] = {
    **dict.fromkeys(
        (
            "BIF", "CLP", "DJF", "GNF", "ISK", "JPY", "KMF", "KRW", "PYG",
            "RWF", "UGX", "VND", "VUV", "XAF", "XOF", "XPF",
        ),
        0,
    ),
    **dict.fromkeys(("BHD", "IQD", "JOD", "KWD", "LYD", "OMR", "TND"), 3),
}
DEFAULT_MINOR_UNIT_EXPONENT = 2


def minor_unit_exponent(currency: str) -> int:
    return _MINOR_UNIT_EXPONENTS.get(currency.strip().upper(), DEFAULT_MINOR_UNIT_EXPONENT)


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        currency = self.currency.strip().upper()
        if len(currency) != 3 or not currency.isascii() or not currency.isalpha():
            raise ValueError("currency must be a three-letter ISO code")
        object.__setattr__(self, "currency", currency)

        # A float amount is rejected rather than coerced: binary rounding error is
        # exactly what a money type exists to keep out. Integers and Decimal-like
        # values arriving from SQLAlchemy Numeric columns are accepted.
        if isinstance(self.amount, float):
            raise TypeError("amount must not be a float; use Decimal or int")
        if not isinstance(self.amount, Decimal):
            try:
                object.__setattr__(self, "amount", Decimal(self.amount))
            except (ArithmeticError, TypeError, ValueError) as exc:
                raise ValueError("amount must be convertible to Decimal") from exc
        if not self.amount.is_finite():
            raise ValueError("amount must be finite")

    @classmethod
    def from_minor(cls, amount_minor: int, currency: str) -> "Money":
        """Build from the minor-unit integer a payment provider works in."""
        exponent = minor_unit_exponent(currency)
        return cls(Decimal(amount_minor).scaleb(-exponent), currency)

    @property
    def minor_units(self) -> int:
        """Round to the currency's smallest unit, half-up, as invoices do."""
        scaled = self.amount.scaleb(minor_unit_exponent(self.currency))
        return int(scaled.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
