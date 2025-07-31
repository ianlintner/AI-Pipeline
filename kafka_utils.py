import json
import logging
from typing import Any, Callable, Dict, Optional

from confluent_kafka import Consumer, Producer
from confluent_kafka.error import KafkaError

from config import Config

logger = logging.getLogger(__name__)


class KafkaProducerManager:
    def __init__(self):
        self.producer = Producer(
            {
                "bootstrap.servers": Config.KAFKA_BOOTSTRAP_SERVERS,
                "retries": 3,
                "acks": "all",
            }
        )

    def send_message(
        self, topic: str, message: Dict[str, Any], key: Optional[str] = None
    ) -> bool:
        """Send a message to a Kafka topic"""
        try:
            # Serialize the message
            value = json.dumps(message, default=str).encode("utf-8")
            key_bytes = key.encode("utf-8") if key else None

            # Send the message
            self.producer.produce(
                topic=topic,
                value=value,
                key=key_bytes,
                callback=self._delivery_callback,
            )

            # Wait for message to be delivered
            self.producer.flush(timeout=10)
            logger.info(f"Message sent to topic '{topic}'")
            return True
        except Exception as e:
            logger.error(f"Failed to send message to topic '{topic}': {e}")
            return False

    def _delivery_callback(self, err, msg):
        """Callback for message delivery confirmation"""
        if err:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(
                f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}"
            )

    def close(self):
        """Close the producer"""
        self.producer.flush()


class KafkaConsumerManager:
    def __init__(
        self,
        topics: list,
        group_id: str,
        message_handler: Callable[[str, Dict[str, Any]], None],
    ):
        self.topics = topics
        self.group_id = group_id
        self.message_handler = message_handler
        self.consumer = None
        self.running = False

    def start_consuming(self):
        """Start consuming messages from Kafka topics"""
        try:
            self.consumer = Consumer(
                {
                    "bootstrap.servers": Config.KAFKA_BOOTSTRAP_SERVERS,
                    "group.id": self.group_id,
                    "auto.offset.reset": "latest",
                    "enable.auto.commit": True,
                }
            )

            self.consumer.subscribe(self.topics)
            self.running = True
            logger.info(
                f"Started consuming from topics: {self.topics} with group_id: {self.group_id}"
            )

            while self.running:
                try:
                    # Poll for messages
                    msg = self.consumer.poll(timeout=1.0)

                    if msg is None:
                        continue

                    if msg.error():
                        if msg.error().code() == KafkaError._PARTITION_EOF:
                            # End of partition event
                            logger.debug(
                                f"Reached end of partition for topic {msg.topic()}"
                            )
                        else:
                            logger.error(f"Consumer error: {msg.error()}")
                        continue

                    # Process the message
                    try:
                        value = json.loads(msg.value().decode("utf-8"))
                        logger.info(
                            f"Received message from topic '{msg.topic()}' at offset {msg.offset()}"
                        )
                        self.message_handler(msg.topic(), value)
                    except Exception as e:
                        logger.error(
                            f"Error processing message from topic '{msg.topic()}': {e}"
                        )

                except KeyboardInterrupt:
                    logger.info("Consumer interrupted by user")
                    break

        except Exception as e:
            logger.error(f"Error in Kafka consumer: {e}")
        finally:
            if self.consumer:
                self.consumer.close()

    def stop_consuming(self):
        """Stop consuming messages"""
        self.running = False
        if self.consumer:
            self.consumer.close()
        logger.info("Stopped consuming messages")
