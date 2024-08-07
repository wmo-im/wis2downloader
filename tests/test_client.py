import json


def test_expose_metrics(client):
    response = client.get('/metrics')
    assert response.status_code == 200
    assert response.mimetype == 'text/plain'
    assert b'# HELP' in response.data
    assert b'# TYPE' in response.data
    assert b'queue_size' in response.data
    assert b'downloaded_bytes_total' in response.data
    assert b'downloaded_files_total' in response.data
    assert b'failed_downloads_total' in response.data
    assert b'topic_subscription_status' in response.data


def test_list_subscriptions(client):
    response = client.get('/subscriptions')
    assert response.status_code == 200
    assert response.mimetype == 'application/json'
    data = json.loads(response.data)
    assert isinstance(data, dict)


def test_add_valid_subscription(client):
    data = {
        "topic": "cache/a/wis2/ai-metservice/data/core/weather/surface-based-observations/synop",  # noqa
        "target": "test/target"
    }
    output = {
        "pattern": "cache/a/wis2/ai-metservice/data/core/weather/surface-based-observations/synop",  # noqa
        "target": "test/target"
    }
    subscriptions = {
        "cache/a/wis2/ai-metservice/data/core/weather/surface-based-observations/synop": {  # noqa
            "pattern": "cache/a/wis2/ai-metservice/data/core/weather/surface-based-observations/synop",  # noqa
            "target": "test/target"
        }
    }

    response = client.post('/subscriptions', json=data)
    confirmation = client.get('/subscriptions')
    response_data = json.loads(response.data)
    confirmation_data = json.loads(confirmation.data)

    assert response.status_code == 201
    assert response.mimetype == 'application/json'
    assert response_data == output
    assert confirmation_data == subscriptions


def test_add_invalid_topic(client):
    bad_topic = "invalid/topic/example"
    data = {
        "topic": bad_topic,  # noqa
        "target": "test/target"
    }

    expected_error = b"Invalid topic (" + bad_topic.encode() + \
        b"), topic must validate against the WIS2 topic hierarchy."

    response = client.post('/subscriptions', json=data)

    assert response.status_code == 400
    assert response.mimetype == 'text/html'
    assert expected_error in response.data


def test_add_invalid_target(client):
    bad_target = "MI$TAK€"
    data = {
        "topic": "cache/a/wis2/ai-metservice/data/core/weather/surface-based-observations/synop",  # noqa
        "target": bad_target
    }
    expected_error = b"Invalid target"

    response = client.post('/subscriptions', json=data)

    assert response.status_code == 400
    assert response.mimetype == 'text/html'
    assert expected_error in response.data


def test_delete_topic(client):
    topic = "cache/a/wis2/ai-metservice/data/core/weather/surface-based-observations/synop"  # noqa

    response = client.delete(f'/subscriptions/{topic}')

    assert response.status_code == 200
    assert response.mimetype == 'application/json'
    assert response.data == b'{}'


def test_delete_wrong_topic(client):
    topic = "cache/a/wis2/ai-metservice/data/core/weather/surface-based-observations/synop"  # noqa
    expected_error = b"Subscription not found"

    response = client.delete(f'/subscriptions/{topic}')

    assert response.status_code == 404
    assert response.mimetype == 'text/html'
    assert expected_error in response.data


def test_delete_invalid_topic(client):
    bad_topic = "invalid/topic/example"
    expected_error = b"Invalid topic (" + bad_topic.encode() + \
        b"), topic must validate against the WIS2 topic hierarchy."

    response = client.delete(f'/subscriptions/{bad_topic}')

    assert response.status_code == 400
    assert response.mimetype == 'text/html'
    assert expected_error in response.data
