"""
Handler: Stock Decreased
SPDX-License-Identifier: LGPL-3.0-or-later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""
from typing import Dict, Any
import config
from event_management.base_handler import EventHandler
from orders.commands.order_event_producer import OrderEventProducer
from orders.commands.write_order import delete_order
class StockIncreasedHandler(EventHandler):
    """Handles StockIncrease events"""
    
    def __init__(self):
        self.order_producer = OrderEventProducer()
        super().__init__()
    
    def get_event_type(self) -> str:
        """Get event type name"""
        return "StockIncreased"
    
    def handle(self, event_data: Dict[str, Any]) -> None:
        """Execute every time the event is published"""
        self.logger.debug(f"stock increased for order_id={event_data.get('order_id')}, items={event_data.get('items')}")
        try:
            delete_order(event_data.get('order_id')) # suprimmer le order
            event_data['event'] = "OrderCancelled" # Si l'operation a réussi, déclenchez OrderCancelled.
        except Exception as e:
            event_data['error'] = str(e)
            self.logger.error(f"failled to cancel order for order_id={event_data.get('order_id')}, error={str(e)}")
            event_data['event'] = "OrderCancelled" # Si l'operation a echoué, continuez quand meme vers OrderCancelled.
        finally:
            self.order_producer.get_instance().send(config.KAFKA_TOPIC, value=event_data)
