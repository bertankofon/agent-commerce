def build_tools(sdk):
    def check_inventory(arguments):
        # TODO: Fetch merchant inventory from DB or config
        sku = arguments["sku"]
        return {
            "stock": 10,
            "unit_price": 120
        }

    def process_payment(arguments):
        amount = arguments["amount"]
        method = arguments.get("method", "google_pay")

        payment = sdk.payments.request_payment(
            method=method,
            amount=amount
        )
        return { "payment_status": payment.status }

    return {
        "check_inventory": check_inventory,
        "process_payment": process_payment
    }
