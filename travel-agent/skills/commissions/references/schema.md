# Providers & Commissions workbook: fields

JSON keys (used with `read-providers` / `update-providers`) are in `code` font. The workbook shows English or Spanish labels, and dropdown values accept codes or labels.

## Settings (`settings`)
| Key | Meaning |
|---|---|
| `agency_name` | Shown in document footers |
| `language` | `en` or `es` |
| `home_currency` | Currency for reporting |
| `tax_on_commission_pct` | VAT/IVA added when invoicing a commission (only for `invoice` payouts) |
| `withholding_pct` | Income tax providers withhold from what they pay |

## Providers (`providers`)
| Key | Meaning |
|---|---|
| `id` | Short code, e.g. `andes-dmc`. Trip Sheet bookings must use it in **Provider ID** |
| `name`, `category`, `currency`, `contact`, `contract_expires`, `notes` | Descriptive. Expired contracts are flagged |
| `payout_method` | `deduct` (collect gross, pay net, keep the difference) · `invoice` (agent bills the provider) · `provider_pays` (provider transfers automatically) |
| `payout_timing` | `on_booking` · `on_final_payment` (latest client payment due date for that booking or ALL) · `after_travel` (booking end, or trip end) |
| `days_after` | Days added to the timing event |
| rule fields | The default rule, see below |

## Products (`products`)
`provider_id` + `product_id` (must match the booking's **Product** column), `product_name`, the rule fields and `notes`. These override the provider default when `rule_type` is set.

## Rule fields
| `rule_type` | Uses | Commission |
|---|---|---|
| `percentage` | `rate_pct`, `base` = `gross` or `gross_ex_taxes` | base × rate % (`gross_ex_taxes` subtracts the booking's **Taxes included**) |
| `net_markup` | `markup_pct` (optional target) | client price − net. Warns when the markup is below the target |
| `fixed` | `fixed_amount`, `fixed_per` = `booking`, `pax` or `night` | amount × units (uses the booking's Passengers or Nights) |

## Incentives (`incentives`)
`provider_id`, `period` (`year` or `quarter`), `from_volume`, `rate_pct` (extra %), `notes`. One row per tier. The estimate applies the highest tier reached to the full volume of the period, counting only the trips included in the calculation.

## Trip Sheet booking fields used
`provider`, `product`, `gross_amount`, `taxes_amount`, `net_amount`, `pax`, `nights`, `currency`, `start`, `end`, `booked_date`, `commission_received_date`.
