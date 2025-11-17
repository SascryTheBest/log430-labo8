"""
Handler: Stock Decreased
SPDX-License-Identifier: LGPL-3.0-or-later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""
from typing import Dict, Any
import config
from event_management.base_handler import EventHandler
from orders.commands.order_event_producer import OrderEventProducer
import requests

class StockDecreasedHandler(EventHandler):
    """Handles StockDecreased events"""
    
    def __init__(self):
        self.order_producer = OrderEventProducer()
        super().__init__()
    
    def get_event_type(self) -> str:
        """Get event type name"""
        return "StockDecreased"
    
    def handle(self, event_data: Dict[str, Any]) -> None:
        """Execute every time the event is published"""
        '''
        TODO: Consultez le diagramme de machine à états pour savoir quelle opération 
        effectuer dans cette méthode. 
        
        **Conseil** : si vous préférez, avant de travailler sur l'implémentation event-driven, 
        effectuez un appel synchrone (requête HTTP) à l'API Payments, attendez le résultat, puis 
        continuez la saga. L'approche synchrone peut être plus facile à comprendre dans un premier temps.
          
        En revanche, dans une implémentation 100% event-driven, ce StockDecreasedHandler se trouvera 
        dans l'API Payments et non dans Store Manager, car c'est l'API Payments qui doit 
        être notifiée de la mise à jour du stock afin de générer une transaction de paiement.
        '''
        try:
            self.logger.debug(f"Creating payment for order_id={event_data.get('order_id')}, total_amount={event_data.get('total_amount')}")
            payment_created = self._create_payment(event_data)
            if not payment_created:
                raise Exception("Payment creation failed")
            event_data['payment_link'] = self._payments_base() + "/" + str(payment_created)
            self.logger.debug(f"payment_link={event_data['payment_link']}")
            event_data['event'] = "PaymentCreated" # Si la transaction de paiement a été crée, déclenchez PaymentCreated.
        except Exception as e:
            event_data['event'] = "PaymentCreationFailed"
            event_data['error'] = str(e)
            self.logger.error(f"Failed to create payment for order_id={event_data.get('order_id')}, error={str(e)}")
        finally:
            self.order_producer.get_instance().send(config.KAFKA_TOPIC, value=event_data)

    def _payments_base(self) -> str:
        return f"http://api-gateway:8080/payments-api/payments"

    def _create_payment(self, event_data) -> bool:
        """Crée une transaction de paiement côté Payments API"""
        url = self._payments_base()
        payload = {
            "order_id": event_data["order_id"],
            "total_amount": event_data["total_amount"],
            "user_id": event_data["user_id"]
        }
        self.logger.debug("POST %s payload=%s", url, payload)
        resp = requests.post(url, json=payload, timeout=15)
        if 200 <= resp.status_code < 300:
            self.logger.debug("Paiement accepté: %s", resp.text)
            data = resp.json()
            return data.get("payment_id")
        self.logger.error("POST %s -> status=%s response_text=%s", url, resp.status_code, resp.text)
        return None
