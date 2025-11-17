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
from payments.outbox_processor import Outbox    # important
from payments.outbox_processor import OutboxProcessor
from db import get_sqlalchemy_session

class StockDecreasedHandler(EventHandler):
    """Handles StockDecreased events"""
    
    def __init__(self):
        self.order_producer = OrderEventProducer()
        super().__init__()
    
    def get_event_type(self) -> str:
        """Get event type name"""
        return "StockDecreased" # Notez le suffixe _Monolithic pour éviter les conflits avec l'implémentation event-driven.
    
    def handle(self, event_data: Dict[str, Any]) -> None:
        """Execute every time the event is published"""
        session = get_sqlalchemy_session()
        try:
            # 1. On enregistre la demande de paiement dans la table Outbox
            new_outbox_item = Outbox(
                order_id=event_data['order_id'],
                user_id=event_data['user_id'],
                total_amount=event_data['total_amount'],
                order_items=event_data['order_items']
            )

            session.add(new_outbox_item)
            session.flush()
            session.commit()

            # 2. On exécute le processeur Outbox (synchrone)
            OutboxProcessor().run(new_outbox_item)

        except Exception as e:
            session.rollback()
            self.logger.debug("La création d'une transaction de paiement a échoué : " + str(e))

            event_data['event'] = "PaymentCreationFailed"
            event_data['error'] = str(e)
            OrderEventProducer().get_instance().send(config.KAFKA_TOPIC, value=event_data)

        finally:
            session.close()
