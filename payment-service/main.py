import json
import os

from dapr.clients import DaprClient
from fastapi import FastAPI, HTTPException
import grpc

from stripe import StripeClient, StripeError

import logging
from model.payment_model import Status, PaymentModel
import dapr.ext.workflow as wf

app = FastAPI()
base_url = os.getenv("DAPR_HTTP_ENDPOINT", "http://localhost")

payments_db = os.getenv("DAPR_PAYMENTS_DB", "")
stripe_secret = os.getenv("STRIPE_SECRET_KEY", "")

logging.basicConfig(level=logging.INFO)

client = StripeClient(stripe_secret)
wfr = wf.WorkflowRuntime()
wf_client = wf.DaprWorkflowClient()
wfr.start()


@app.get("/")
def health_check():
    return {"Health is Ok"}


@app.post("/v1.0/payments/{payment_intent}/confirm")
def confirm_payment_intent(payment_intent: str):
    with DaprClient() as d:
        print(f"payment intent: Received input: {payment_intent}.")

        try:
            kv = d.get_state(payments_db, payment_intent)
            print(f"value of kv is {kv.data}")
            if kv.data:
                payment_model = PaymentModel(**json.loads(kv.data))
                try:
                    payment_confirmation = client.payment_intents.confirm(
                        payment_intent,
                        params={
                            "payment_method": "pm_card_visa",
                            "return_url": "https://www.example.com",
                        },
                    )

                    payment_model.status = payment_confirmation["status"]
                    return {"status_code": 200, "body": payment_model.model_dump_json()}

                except StripeError as err:
                    raise HTTPException(status_code=500, detail=err.user_message)

        except grpc.RpcError as err:
            raise HTTPException(status_code=500, detail=err.details())


@app.post("/v1.0/payments/{payment_intent}/cancel")
def cancel_payment_intent(payment_intent: str):
    with DaprClient() as d:
        try:
            print(f"cancel payment intent: Received input: {payment_intent}.")
            kv = d.get_state(payments_db, payment_intent)
            print(f"value of kv is {kv.data}")
            if kv.data:
                payment_model = PaymentModel(**json.loads(kv.data))
                try:
                    client.payment_intents.cancel(payment_intent)

                    payment_model.status = Status.CANCELLED

                    d.save_state(
                        store_name=payments_db,
                        key=payment_model.id,
                        value=payment_model.model_dump_json(),
                        state_metadata={"contentType": "application/json"},
                    )

                    return {"status_code": 200, "body": payment_model.model_dump_json()}

                except StripeError as err:
                    raise HTTPException(status_code=500, detail=err.user_message)
        except grpc.RpcError as err:
            print(f"Error={err.details()}")
            raise HTTPException(status_code=500, detail=err.details())


@app.post("/v1.0/payments/create")
def create_payment_intent(payment: PaymentModel):
    with (DaprClient() as d):
        try:
            print(f"create payment intent: Received input: {payment.model_dump()}.")
            payment_intent = client.payment_intents.create(
                params={"amount": payment.amount, "currency": "usd"}
            )
            payment.id = payment_intent.id
            payment.status = Status.IN_PROGRESS
            payment.instance_id = payment_intent.id
            d.save_state(
                store_name=payments_db,
                key=payment.id,
                value=payment.model_dump_json(),
                state_metadata={"contentType": "application/json"},
            )

            print(f"created payment intent: {payment.model_dump()}")

            return {"status_code": 200, "body": payment.model_dump_json()}

        except grpc.RpcError as err:
            print(f"Error={err.details()}")
            raise HTTPException(status_code=500, detail=err.details())
