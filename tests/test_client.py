import json
from flask import Flask


def test_expose_metrics(client):
    response = client.get('/metrics')
    assert response.status_code == 200
    assert response.mimetype == 'text/plain'


def test_list_subscriptions(client):
    response = client.get('/subscriptions')
    assert response.status_code == 200
    assert response.mimetype == 'application/json'
    data = json.loads(response.data)
    assert isinstance(data, list)


def test_add_subscription(client):
    data = {
        "topic": "test/topic",
        "target": "test/target"
    }
    response = client.post('/subscriptions', json=data)
    assert response.status_code == 201
    assert response.mimetype == 'application/json'
    assert 'Location' in response.headers


def test_get_subscription(client):
    topic = "test/topic"
    response = client.get(f'/subscriptions/{topic}')
    assert response.status_code == 200
    assert response.mimetype == 'application/json'
    data = json.loads(response.data)
    assert isinstance(data, dict)


def test_delete_subscription(client):
    topic = "test/topic"
    response = client.delete(f'/subscriptions/{topic}')
    assert response.status_code == 200
    assert response.mimetype == 'application/json'
    data = json.loads(response.data)
    assert isinstance(data, dict)
