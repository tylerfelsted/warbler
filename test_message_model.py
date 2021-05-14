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
db.drop_all()
db.create_all()


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        
        self.user = User.signup(
            username='testuser', 
            email='test@user.com', 
            password='password',
            image_url=None
        )
        db.session.add(self.user)
        db.session.commit()

        self.client = app.test_client()

    def test_message_model(self):
        """Does basic model work?"""

        m = Message(
            text="This is a test message",
            timestamp=None,
            user_id=self.user.id
        )

        db.session.add(m)
        db.session.commit()

        self.assertEqual(m.user, self.user)

    
