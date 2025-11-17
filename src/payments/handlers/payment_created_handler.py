"""
Handler: Payment Created
SPDX-License-Identifier: LGPL-3.0-or-later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""
from typing import Dict, Any
import config
from event_management.base_handler import EventHandler
from orders.commands.order_event_producer import OrderEventProducer

class PaymentCreatedHandler(EventHandler):
    """Handles PaymentCreated events"""
    
    def __init__(self):
        self.order_producer = OrderEventProducer()
        super().__init__()
    
    def get_event_type(self) -> str:
        """Get event type name"""
        return "PaymentCreated"
    
    def handle(self, event_data: Dict[str, Any]) -> None:
        """Execute every time the event is published"""
        # event_data["payment_link"] = "todo-add-payment-link-here" # par necessesaire, car déjà présent dans event_data

        try:
            event_data['event'] = "SagaCompleted" # Si l'operation a réussi, déclenchez SagaCompleted.
            self.logger.debug(f"payment_link={event_data['payment_link']}")
            OrderEventProducer().get_instance().send(config.KAFKA_TOPIC, value=event_data)

        except Exception as e:
            # ne peux pas echouer ici
            event_data['error'] = str(e)
            self.logger.error(f"Error in PaymentCreatedHandler: {str(e)}")