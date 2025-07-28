import json
import logging
from typing import Dict, Any, Callable, Optional
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
from config import Config

logger = logging.getLogger(__name__)

class KafkaProducerManager:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS.split(','),
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            retries=3,
            acks='all'
        )
    
    def send_message(self, topic: str, message: Dict[str, Any], key: Optional[str] = None) -> bool:
        """Send a message to a Kafka topic"""
        try:
            future = self.producer.send(topic, value=message, key=key)
            record_metadata = future.get(timeout=10)
            logger.info(f"Message sent to topic '{topic}' at offset {record_metadata.offset}")
            return True
        except KafkaError as e:
            logger.error(f"Failed to send message to topic '{topic}': {e}")
            return False
    
    def close(self):
        """Close the producer"""
        self.producer.close()

class KafkaConsumerManager:
    def __init__(self, topics: list, group_id: str, message_handler: Callable[[str, Dict[str, Any]], None]):
        self.topics = topics
        self.group_id = group_id
        self.message_handler = message_handler
        self.consumer = None
        self.running = False
    
    def start_consuming(self):
        """Start consuming messages from Kafka topics"""
        try:
            self.consumer = KafkaConsumer(
                *self.topics,
                bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS.split(','),
                group_id=self.group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            
            self.running = True
            logger.info(f"Started consuming from topics: {self.topics} with group_id: {self.group_id}")
            
            for message in self.consumer:
                if not self.running:
                    break
                
                try:
                    logger.info(f"Received message from topic '{message.topic}' at offset {message.offset}")
                    self.message_handler(message.topic, message.value)
                except Exception as e:
                    logger.error(f"Error processing message from topic '{message.topic}': {e}")
                    
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
