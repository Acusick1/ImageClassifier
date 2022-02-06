import unittest
import uuid
import time
from UnifiedAPI import adapter, settings
from unittest import mock


# Wrapping abstract test class in blank class so that is not called for testing
class AdapterTest:
    class SystemTests(unittest.TestCase):

        def setUp(self) -> None:
            self.broker = adapter.MessageBroker()
            raise NotImplementedError

        def test_create_topic(self):
            # TODO: TEST_TOPIC already created in setUp, not good practice. Test first or at least mock call
            pass

        # Kafka and pubsub return different types of futures so have to overwrite this test
        def test_send_message(self):
            raise NotImplementedError

        def test_subscriber(self):
            try:
                self.broker.create_subscriber(settings.TEST_SUB, settings.TEST_TOPIC)
            except Exception as e:
                self.fail(f"Subscription creator raised exception {e}")

            try:
                self.broker.delete_subscriber(settings.TEST_SUB)
            except Exception as e:
                self.fail(f"Subscription deleter raised exception {e}")

        @mock.patch('builtins.print')
        def test_consume(self, mock_print):
            sub_name = settings.TEST_SUB
            uid = str(uuid.uuid4())
            self.broker.create_subscriber(sub_name, settings.TEST_TOPIC)
            # Make sure subscriber has been created before sending message
            time.sleep(5)
            self.broker.send_message(settings.TEST_TOPIC, {"id": uid})
            self.broker.consume(sub_name, callback=print, timeout=10)
            self.assertEqual(mock_print.call_args.args[0]["id"], uid)
            self.broker.delete_subscriber(sub_name)

        def tearDown(self) -> None:
            self.broker.delete_topic(settings.TEST_TOPIC)


class PubsubTest(AdapterTest.SystemTests):

    def setUp(self) -> None:
        self.broker = adapter.PubsubBroker(settings.PROJECT)
        self.broker.create_topic(settings.TEST_TOPIC)

    def test_send_message(self):
        future = self.broker.send_message(settings.TEST_TOPIC, {"id": str(uuid.uuid4())})
        self.assertEqual(future._state, 'FINISHED')
        self.assertEqual(future._exception, None)


class KafkaTest(AdapterTest.SystemTests):

    def setUp(self) -> None:
        self.broker = adapter.KafkaBroker(settings.PROJECT)
        self.broker.create_topic(settings.TEST_TOPIC)

    def test_send_message(self):
        future = self.broker.send_message(settings.TEST_TOPIC, {"id": str(uuid.uuid4())})
        self.assertEqual(future.is_done, True)
        self.assertEqual(future.exception, None)


if __name__ == "__main__":
    unittest.main()
