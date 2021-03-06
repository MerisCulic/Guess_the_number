import os
import pytest
from main import app, db
from models import User


@pytest.fixture
def client():
    app.config['TESTING'] = True
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    client = app.test_client()

    cleanup()

    db.create_all()

    yield client


def login(client):
    return client.post('/login', data={
        "user-name": "Test User", "user-email": "test@user.com",
        "user-password": "password123"},
        follow_redirects=True
    )


def test_login(client):
    login(client)
    response = client.get("/")
    assert b'Enter your guess' in response.data


def test_index_not_logged_in(client):
    response = client.get('/')
    assert b'Enter your name' in response.data


def test_profile(client):
    login(client)
    response = client.get('/profile')
    assert b'Your name:' in response.data


def test_profile_delete(client):
    login(client)
    response = client.get('/profile/delete')
    assert b'Delete your profile' in response.data

    response = client.post('/profile/delete', follow_redirects=True)
    assert b'Enter your name' in response.data

    # test za link -> cancel?


def test_profile_edit(client):
    login(client)
    response = client.get('/profile/edit')
    assert response.status_code == 200
    assert b'Edit your profile' in response.data

    response = client.post('/profile/edit', data=
                      {"profile-name": "Test User 2",
                       "profile-email": "test2@user.com"},
                       follow_redirects=True)

    assert b'Test User 2' in response.data
    assert b'test2@user.com' in response.data


def test_all_users(client):
    response = client.get('/users')
    assert b'Test User' not in response.data

    login(client)
    response = client.get('/users')
    assert b'Test User' in response.data


def test_result_correct(client):
    login(client)
    user = db.query(User).first()
    user.secret_number = 10

    db.add(user)
    db.commit()

    response = client.post('/result', data={"guess": 10})

    assert b'Correct! The secret number is 10' in response.data


def test_result_incorrect_smaller(client):
    login(client)
    user = db.query(User).first()
    user.secret_number = 10

    db.add(user)
    db.commit()

    response = client.post('/result', data={"guess": 20})
    assert b'Your guess is not correct... try something smaller' in response.data


def test_result_incorrect_bigger(client):
    login(client)
    user = db.query(User).first()
    user.secret = 10

    db.add(user)
    db.commit()

    response = client.post('/result', data={"guess": 5})
    assert b'Your guess is not correct... try something bigger' in response.data


def cleanup():
    db.drop_all()