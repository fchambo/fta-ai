"""Single definition of every spreadsheet the agent sees.

Fields are (key, English label, Spanish label, type). Types: text, number, date,
or choice:<name>. Choice values are stored as translated labels in the workbook
and read back as codes, so the logic never depends on the workbook language.
"""

LANGS = ("en", "es")

CHOICES = {
    "status": [("inquiry", "Inquiry", "Consulta"), ("quoting", "Quoting", "Cotizando"),
               ("booked", "Booked", "Reservado"), ("paid", "Paid", "Pagado"),
               ("traveling", "Traveling", "Viajando"), ("closed", "Closed", "Cerrado"),
               ("cancelled", "Cancelled", "Cancelado")],
    "contact": [("whatsapp", "WhatsApp", "WhatsApp"), ("email", "Email", "Email"),
                ("phone", "Phone", "Teléfono")],
    "budget_per": [("total", "Total", "Total"), ("person", "Per person", "Por persona")],
    "booking_type": [("flight", "Flight", "Vuelo"), ("hotel", "Hotel", "Hotel"),
                     ("tour", "Tour / package", "Tour / paquete"), ("cruise", "Cruise", "Crucero"),
                     ("transfer", "Transfer", "Traslado"), ("insurance", "Insurance", "Asistencia / seguro"),
                     ("car", "Car rental", "Alquiler de auto"), ("activity", "Activity", "Actividad"),
                     ("other", "Other", "Otro")],
    "payer": [("client", "Client", "Cliente"), ("agent", "Me (agent)", "Yo (agente)")],
    "yesno": [("yes", "Yes", "Sí"), ("no", "No", "No")],
    "category": [("tour_operator", "Tour operator", "Operador"), ("dmc", "DMC / receptive", "Receptivo / DMC"),
                 ("hotel", "Hotel", "Hotel"), ("airline", "Airline", "Aerolínea"),
                 ("consolidator", "Consolidator", "Consolidador"), ("cruise", "Cruise line", "Naviera"),
                 ("insurance", "Insurance", "Asistencia / seguro"), ("car_rental", "Car rental", "Alquiler de autos"),
                 ("activity", "Activities", "Actividades"), ("other", "Other", "Otro")],
    "payout_method": [("deduct", "I collect gross and pay net", "Cobro bruto y pago neto"),
                      ("invoice", "I invoice the provider", "Le facturo al proveedor"),
                      ("provider_pays", "Provider pays me", "El proveedor me paga")],
    "payout_timing": [("on_booking", "On booking", "Al reservar"),
                      ("on_final_payment", "On final payment", "Al pago final"),
                      ("after_travel", "After travel", "Después del viaje")],
    "rule_type": [("percentage", "Percentage", "Porcentaje"),
                  ("net_markup", "Net rate + my markup", "Tarifa neta + mi markup"),
                  ("fixed", "Fixed amount", "Monto fijo")],
    "base": [("gross", "Gross", "Bruto"), ("gross_ex_taxes", "Gross without taxes", "Bruto sin impuestos")],
    "fixed_per": [("booking", "Per booking", "Por reserva"), ("pax", "Per passenger", "Por pasajero"),
                  ("night", "Per night", "Por noche")],
    "period": [("year", "Year", "Año"), ("quarter", "Quarter", "Trimestre")],
    "lang": [("en", "English", "Inglés"), ("es", "Spanish", "Español")],
}

# --- Trip Sheet workbook -----------------------------------------------------

TRIP_FIELDS = [
    ("trip_id", "Trip ID", "ID del viaje", "text"),
    ("status", "Status", "Estado", "choice:status"),
    ("created", "Created", "Creado", "date"),
    ("client_name", "Client", "Cliente", "text"),
    ("client_email", "Email", "Email", "text"),
    ("client_phone", "Phone / WhatsApp", "Teléfono / WhatsApp", "text"),
    ("preferred_contact", "Preferred contact", "Contacto preferido", "choice:contact"),
    ("client_language", "Client language", "Idioma del cliente", "text"),
    ("destinations", "Destinations", "Destinos", "text"),
    ("start_date", "Start date", "Fecha de salida", "date"),
    ("end_date", "End date", "Fecha de regreso", "date"),
    ("purpose", "Occasion / trip type", "Motivo / tipo de viaje", "text"),
    ("budget_amount", "Budget", "Presupuesto", "number"),
    ("budget_currency", "Budget currency", "Moneda del presupuesto", "text"),
    ("budget_per", "Budget is", "El presupuesto es", "choice:budget_per"),
    ("notes", "Notes", "Notas", "text"),
]

TRAVELERS = [
    ("name", "Name (as in passport)", "Nombre (como en pasaporte)", "text"),
    ("birth_date", "Birth date", "Fecha de nacimiento", "date"),
    ("nationality", "Nationality", "Nacionalidad", "text"),
    ("passport_last4", "Passport (last 4)", "Pasaporte (últimos 4)", "text"),
    ("passport_expiry", "Passport expiry", "Vencimiento pasaporte", "date"),
    ("notes", "Notes (diet, mobility, loyalty #)", "Notas (dieta, movilidad, millas)", "text"),
]

BOOKINGS = [
    ("id", "ID", "ID", "text"),
    ("type", "Type", "Tipo", "choice:booking_type"),
    ("provider", "Provider ID", "ID proveedor", "text"),
    ("product", "Product", "Producto", "text"),
    ("confirmation", "Confirmation #", "Nº de confirmación", "text"),
    ("start", "Start", "Inicio", "date"),
    ("end", "End", "Fin", "date"),
    ("details", "Details", "Detalles", "text"),
    ("booked_date", "Booked on", "Reservado el", "date"),
    ("pax", "Passengers", "Pasajeros", "number"),
    ("nights", "Nights", "Noches", "number"),
    ("gross_amount", "Client price (gross)", "Precio al cliente (bruto)", "number"),
    ("taxes_amount", "Taxes included", "Impuestos incluidos", "number"),
    ("net_amount", "Net (what I pay)", "Neto (lo que pago)", "number"),
    ("currency", "Currency", "Moneda", "text"),
    ("cancellation_deadline", "Free cancellation until", "Cancelación sin cargo hasta", "date"),
    ("commission_received_date", "Commission received on", "Comisión cobrada el", "date"),
]

PAYMENTS = [
    ("booking", "Booking ID (or ALL)", "ID reserva (o ALL)", "text"),
    ("payer", "Who pays", "Quién paga", "choice:payer"),
    ("payee", "Paid to", "Se paga a", "text"),
    ("description", "Description", "Descripción", "text"),
    ("amount", "Amount", "Monto", "number"),
    ("currency", "Currency", "Moneda", "text"),
    ("due_date", "Due date", "Vence", "date"),
    ("paid_date", "Paid on", "Pagado el", "date"),
]

DEADLINES = [
    ("date", "Date", "Fecha", "date"),
    ("what", "What", "Qué", "text"),
    ("done", "Done", "Hecho", "choice:yesno"),
]

TRIP_WORKBOOK = {
    "trip": ("Trip", "Viaje", TRIP_FIELDS, "kv"),
    "travelers": ("Travelers", "Pasajeros", TRAVELERS, "table"),
    "bookings": ("Bookings", "Reservas", BOOKINGS, "table"),
    "payments": ("Payments", "Pagos", PAYMENTS, "table"),
    "deadlines": ("Deadlines", "Vencimientos", DEADLINES, "table"),
}

# --- Providers & Commissions workbook -----------------------------------------

SETTINGS = [
    ("agency_name", "Agency / brand name", "Nombre de agencia / marca", "text"),
    ("language", "Language", "Idioma", "choice:lang"),
    ("home_currency", "Home currency", "Moneda principal", "text"),
    ("tax_on_commission_pct", "VAT on commissions %", "IVA sobre comisiones %", "number"),
    ("withholding_pct", "Withholding %", "Retenciones %", "number"),
]

RULE_FIELDS = [
    ("rule_type", "Rule", "Regla", "choice:rule_type"),
    ("rate_pct", "Rate %", "Tasa %", "number"),
    ("base", "Calculated on", "Se calcula sobre", "choice:base"),
    ("fixed_amount", "Fixed amount", "Monto fijo", "number"),
    ("fixed_per", "Fixed per", "Monto fijo por", "choice:fixed_per"),
    ("markup_pct", "Suggested markup %", "Markup sugerido %", "number"),
]

PROVIDERS = [
    ("id", "Provider ID", "ID proveedor", "text"),
    ("name", "Name", "Nombre", "text"),
    ("category", "Category", "Categoría", "choice:category"),
    ("currency", "Currency", "Moneda", "text"),
    ("payout_method", "How I get paid", "Cómo cobro", "choice:payout_method"),
    ("payout_timing", "When", "Cuándo", "choice:payout_timing"),
    ("days_after", "Days after", "Días después", "number"),
    *RULE_FIELDS,
    ("contact", "Contact", "Contacto", "text"),
    ("contract_expires", "Contract expires", "Vence contrato", "date"),
    ("notes", "Notes / contract clause", "Notas / cláusula", "text"),
]

PRODUCTS = [
    ("provider_id", "Provider ID", "ID proveedor", "text"),
    ("product_id", "Product", "Producto", "text"),
    ("product_name", "Description", "Descripción", "text"),
    *RULE_FIELDS,
    ("notes", "Notes / contract clause", "Notas / cláusula", "text"),
]

INCENTIVES = [
    ("provider_id", "Provider ID", "ID proveedor", "text"),
    ("period", "Period", "Período", "choice:period"),
    ("from_volume", "From sales volume", "Desde volumen de ventas", "number"),
    ("rate_pct", "Extra %", "% extra", "number"),
    ("notes", "Notes", "Notas", "text"),
]

PROVIDERS_WORKBOOK = {
    "settings": ("Settings", "Configuración", SETTINGS, "kv"),
    "providers": ("Providers", "Proveedores", PROVIDERS, "table"),
    "products": ("Products", "Productos", PRODUCTS, "table"),
    "incentives": ("Incentives", "Incentivos", INCENTIVES, "table"),
}

# --- Folder names -------------------------------------------------------------

ROOT_FOLDERS = {
    "clients": ("Clients", "Clientes"),
    "commissions": ("Commissions", "Comisiones"),
    "marketing": ("Marketing", "Marketing"),
    "destinations": ("Destinations", "Destinos"),
}

TRIP_FOLDERS = [
    ("1 - Intake", "1 - Consulta"),
    ("2 - Research", "2 - Investigación"),
    ("3 - Quotes", "3 - Cotizaciones"),
    ("4 - Bookings & Vouchers", "4 - Reservas y Vouchers"),
    ("5 - Documents (private)", "5 - Documentos (privado)"),
    ("6 - Payments & Receipts", "6 - Pagos y Recibos"),
    ("7 - Itinerary & Summaries", "7 - Itinerario y Resúmenes"),
    ("8 - Photos & Reviews", "8 - Fotos y Reseñas"),
]

FILE_NAMES = {
    "trip_sheet": ("Trip Sheet", "Ficha del Viaje"),
    "providers": ("Providers & Commissions.xlsx", "Proveedores y Comisiones.xlsx"),
}


def label(entry, lang):
    """entry is (key, en, es, ...) or (en, es); return the label for lang."""
    offset = 1 if len(entry) > 2 else 0
    return entry[offset + LANGS.index(lang)]


def choice_labels(name, lang):
    return [label(c, lang) for c in CHOICES[name]]


def choice_code(name, value):
    """Map a label in any language (or a code) back to its code."""
    if value in (None, ""):
        return None
    text = str(value).strip().lower()
    for code, *labels in CHOICES[name]:
        if text == code or text in (lbl.lower() for lbl in labels):
            return code
    return str(value).strip()


def choice_label(name, code, lang):
    for c in CHOICES[name]:
        if c[0] == code:
            return label(c, lang)
    return code
