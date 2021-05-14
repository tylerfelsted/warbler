"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql://postgres:postgres@localhost:5433/warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.testuser1 = User(
            email="test1@test.com",
            username="testuser1",
            password="HASHED_PASSWORD"
        )
        self.testuser2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD"
        )
        db.session.add_all([self.testuser1, self.testuser2])
        db.session.commit()

        new_follow = Follows(user_being_followed_id=self.testuser2.id, user_following_id=self.testuser1.id)
        db.session.add(new_follow)
        db.session.commit()

        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_repr(self):
        """Does the __repr__ method work"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        self.assertEqual(f'<User #{u.id}: testuser, test@test.com>', str(u))

    def test_is_followed_by(self):
        """The is_followed_by method successfully detects if user2 is followed by user1"""
        self.assertTrue(self.testuser2.is_followed_by(self.testuser1))
        self.assertFalse(self.testuser1.is_followed_by(self.testuser2))

    def test_is_following(self):
        """The is_following method successfully detects if user 1 is following user2"""
        self.assertTrue(self.testuser1.is_following(self.testuser2))
        self.assertFalse(self.testuser2.is_following(self.testuser1))

    def test_signup(self):
        """The signup method successfully creates a new user"""

        u = User.signup(
            username='testuser', 
            email='test@user.com', 
            password='password',
            image_url=None
        )
        db.session.commit()

        self.assertTrue(u.id)
        self.assertEquals(u.username, 'testuser')
        self.assertEquals(u.email, 'test@user.com')
        self.assertTrue(u.password)
        self.assertEquals(u.image_url, '/static/images/default-pic.png')

    def test_authenticate(self):
        """The authenicate method correctly authenticates a user given the correct username and password"""
        u = User.signup(
            username='testuser', 
            email='test@user.com', 
            password='password',
            image_url=None
        )
        User.signup(
            username='wronguser', 
            email='wronguser@user.com', 
            password='differentpassword',
            image_url=None
        )
        db.session.commit()
        self.assertEquals(User.authenticate('testuser', 'password'), u)
        self.assertFalse(User.authenticate('testuser', 'wrongpassword'))
        self.assertFalse(User.authenticate('wronguser', 'password'))      
