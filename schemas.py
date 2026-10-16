from pydantic import BaseModel, Field, field_validator
from typing import List


class LineItem(BaseModel):
    description: str = Field(..., min_length=1)
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)


class Invoice(BaseModel):
    vendor_name: str = Field(..., min_length=1)
    invoice_number: str = Field(..., min_length=1)
    line_items: List[LineItem] = Field(..., min_length=1)
    total_amount: float = Field(..., ge=0)

    @field_validator("total_amount")
    @classmethod
    def total_matches_line_items(cls, v, info):
        line_items = info.data.get("line_items")
        if line_items:
            computed = sum(li.quantity * li.unit_price for li in line_items)
            if abs(computed - v) > max(1.0, computed * 0.02):
                raise ValueError(
                    f"total_amount ({v}) doesn't match line items (computed {computed:.2f})"
                )
        return v