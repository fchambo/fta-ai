"""Agent-facing text produced by the tools, in English and Spanish.

The language comes from the workbook being processed (its sheet names), so a
Spanish Trip Sheet gets Spanish labels, checks and report headers. JSON keys and
status codes stay in English: only Claude reads those.
"""

MESSAGES = {
    # timeline
    "departure": ("Departure", "Salida"),
    "return": ("Return", "Regreso"),
    "booking_starts": ("{name} starts", "Comienza: {name}"),
    "free_cancel_ends": ("Free cancellation ends: {name}", "Fin de cancelación sin cargo: {name}"),
    "payment": ("Payment", "Pago"),
    "deadline": ("Deadline", "Vencimiento"),
    # data checks
    "no_confirmation": ("Booking {id} has no confirmation number", "La reserva {id} no tiene número de confirmación"),
    "payment_no_due": ("Payment '{desc}' has no due date", "El pago '{desc}' no tiene fecha de vencimiento"),
    "payment_after_departure": ("Client payment '{desc}' is due after departure",
                                "El pago del cliente '{desc}' vence después de la salida"),
    "passport_expiry": ("{name}: passport expires {date}, less than 6 months after return",
                        "{name}: el pasaporte vence el {date}, menos de 6 meses después del regreso"),
    "payments_mismatch": ("Client payments ({billed}) don't match booking prices ({gross})",
                          "Los pagos del cliente ({billed}) no coinciden con los precios de las reservas ({gross})"),
    # commission warnings
    "no_taxes": ("{ref}: no taxes amount, used the full price as base (commission may be overstated)",
                 "{ref}: falta el monto de impuestos, se usó el precio completo como base (la comisión puede estar sobreestimada)"),
    "net_needs_amounts": ("{ref}: net-rate rule needs both client price and net amount",
                          "{ref}: la regla de tarifa neta necesita el precio al cliente y el neto"),
    "markup_below": ("{ref}: markup {actual}% is below the suggested {target}%",
                     "{ref}: el markup de {actual}% está por debajo del {target}% sugerido"),
    "fixed_no_units_pax": ("{ref}: fixed amount per passenger but the booking has no passengers",
                           "{ref}: monto fijo por pasajero, pero la reserva no indica pasajeros"),
    "fixed_no_units_night": ("{ref}: fixed amount per night but the booking has no nights",
                             "{ref}: monto fijo por noche, pero la reserva no indica noches"),
    "no_rule": ("{ref}: provider has no commission rule set", "{ref}: el proveedor no tiene regla de comisión"),
    "no_taxes_settings": ("VAT and withholding % are not set in Settings: amounts are before taxes",
                          "IVA y retenciones % no están cargados en Configuración: los montos son antes de impuestos"),
    "contract_expired": ("{id}: contract expired on {date}", "{id}: el contrato venció el {date}"),
    "unknown_provider": ("{ref}: provider '{provider}' is not in the Providers sheet",
                         "{ref}: el proveedor '{provider}' no está en la hoja Proveedores"),
    "currency_mismatch": ("{ref}: booking in {booking} but provider pays in {provider}",
                          "{ref}: reserva en {booking} pero el proveedor paga en {provider}"),
}

# Commission report: sheet names, column headers and values shown to the agent.
REPORT = {
    "sheet_commissions": ("Commissions", "Comisiones"),
    "sheet_by_provider": ("By provider", "Por proveedor"),
    "sheet_by_currency": ("By currency", "Por moneda"),
    "sheet_incentives": ("Incentives", "Incentivos"),
    "sheet_warnings": ("Warnings", "Avisos"),
    "client": ("Client", "Cliente"),
    "booking": ("Booking", "Reserva"),
    "bookings": ("Bookings", "Reservas"),
    "provider": ("Provider", "Proveedor"),
    "product": ("Product", "Producto"),
    "rule": ("Rule", "Regla"),
    "gross": ("Client price", "Precio al cliente"),
    "commission": ("Commission", "Comisión"),
    "withholding": ("Withholding", "Retención"),
    "vat_to_invoice": ("VAT to invoice", "IVA a facturar"),
    "currency": ("Currency", "Moneda"),
    "expected_date": ("Expected on", "Fecha esperada"),
    "status": ("Status", "Estado"),
    "received": ("Received", "Cobrada"),
    "retained": ("Retained", "Retenida al pagar"),
    "pending": ("Pending", "Pendiente"),
    "overdue": ("Overdue", "Vencida"),
    "year": ("Year", "Año"),
    "volume": ("Sales volume", "Volumen de ventas"),
    "current_extra_pct": ("Current extra %", "% extra actual"),
    "bonus_estimate": ("Bonus estimate", "Bono estimado"),
    "next_tier": ("Next tier", "Próximo nivel"),
    "warning": ("Warning", "Aviso"),
    "percentage": ("Percentage", "Porcentaje"),
    "net_markup": ("Net rate + markup", "Neto + markup"),
    "fixed": ("Fixed amount", "Monto fijo"),
    "product_rule": ("product", "producto"),
    "provider_default": ("provider default", "regla del proveedor"),
    "next_tier_text": ("{missing} more to reach {extra}% (from {start})", "faltan {missing} para llegar al {extra}% (desde {start})"),
}


def _pick(table, key, lang):
    en, es = table[key]
    return es if lang == "es" else en


def t(lang, key, **values):
    return _pick(MESSAGES, key, lang).format(**values)


def r(lang, key, **values):
    return _pick(REPORT, key, lang).format(**values)


def money(amount, lang):
    """1,234.50 in English, 1.234,50 in Spanish."""
    text = f"{amount:,.2f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".") if lang == "es" else text


def number(value, lang):
    text = f"{value:g}"
    return text.replace(".", ",") if lang == "es" else text


def date_text(value, lang):
    """2026-10-14 in English, 14/10/2026 in Spanish."""
    return value.strftime("%d/%m/%Y") if lang == "es" else value.isoformat()
