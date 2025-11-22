async def negotiate(buyer_agent, seller_agent):
    offer = await seller_agent.run("Make your initial offer.")

    while True:
        counter = await buyer_agent.run(f"Seller offers: {offer}")

        reply = await seller_agent.run(f"Buyer responds: {counter}")

        if "accept" in reply.lower():
            return {
                "status": "AGREED",
                "final_offer": offer
            }

        offer = reply
