import os
from unittest import TestCase

from models import db, connect_db, Message, User, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql://postgres:postgres@localhost:5433/warbler-test"



# Now we can import app

from app import app, CURR_USER_KEY
app.config['SQLALCHEMY_ECHO'] = False

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
db.drop_all()
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False



class UserViewTestCase(TestCase):
    """Test views for Users"""

    def setUp(self):
        """Create test client, add sample data"""
        User.query.delete()
        Follows.query.delete()
        Likes.query.delete()

        self.client = app.test_client()

        self.testuser1 = User.signup(username="testuser1",
                                    email="test1@test.com",
                                    password="testuser1",
                                    image_url=None)
        self.testuser2 = User.signup(username="testuser2",
                                    email="test2@test.com",
                                    password="testuser2",
                                    image_url=None)
        self.testuser3 = User.signup(username="testuser3",
                                    email="test3@test.com",
                                    password="testuser3",
                                    image_url=None)
        self.testuser4 = User.signup(username="testuser4",
                                    email="test4@test.com",
                                    password="testuser4",
                                    image_url=None)
        db.session.commit()

        #User 1 is following user 3 and user 4
        #User 2 is follwing user 3
        followed_user3 = User.query.get_or_404(self.testuser3.id)
        followed_user4 = User.query.get_or_404(self.testuser4.id)
        self.testuser1.following.append(followed_user3)
        self.testuser1.following.append(followed_user4)
        self.testuser2.following.append(followed_user3)
        db.session.commit()

    def tearDown(self):
        
        db.session.rollback()

    def test_show_sign_up_form(self):
        """Sign up form is displayed"""

        with self.client as c:
            resp = c.get('/signup')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h2 class="join-message">Join Warbler today.</h2>', html)

    def test_sign_up(self):
        """A new user can register for the site"""

        with self.client as c:
            form_data = {'username': 'testuser5', 'email': 'test5@test.com', 'password': 'testuser5'}
            resp = c.post('/signup', data=form_data)

            self.assertEqual(resp.status_code, 302)
            with c.session_transaction() as sess:
                self.assertTrue(sess.get(CURR_USER_KEY))

    def test_sign_up_existing_username(self):
        """A new user cannot use an existing username"""

        with self.client as c:
            form_data = {'username': 'testuser1', 'email': 'test3@test.com', 'password': 'testuser3'}
            resp = c.post('/signup', data=form_data)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h2 class="join-message">Join Warbler today.</h2>', html)
            self.assertIn('<div class="alert alert-danger">Username already taken</div>', html)

    def test_show_login_form(self):
        """Login form is displayed"""

        with self.client as c:
            resp = c.get('/login')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<button class="btn btn-primary btn-block btn-lg">Log in</button>', html)

    def test_login(self):
        """A user can log in"""

        with self.client as c:
            form_data = {'username': 'testuser1', 'password': 'testuser1'}
            resp = c.post('/login', data=form_data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p>@testuser1</p>', html)
            self.assertIn('<div class="alert alert-success">Hello, testuser1!</div>', html)
            with c.session_transaction() as sess:
                self.assertEqual(sess.get(CURR_USER_KEY), self.testuser1.id)

    def test_login_wrong_password(self):
        """A user cannot login with invalid credentials, and a warning message is displayed."""

        with self.client as c:
            form_data = {'username': 'testuser1', 'password': 'testuser'}
            resp = c.post('/login', data=form_data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="alert alert-danger">Invalid credentials.</div>', html)
            with c.session_transaction() as sess:
                self.assertFalse(sess.get(CURR_USER_KEY))

    def test_logout(self):
        """A user can log out"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id
            
            resp = c.get('/logout')
            self.assertEqual(resp.status_code, 302)

            with c.session_transaction() as sess:

                self.assertEqual(sess.get(CURR_USER_KEY), None)

    def test_list_users(self):
        """List of users displays properly"""

        with self.client as c:
            resp = c.get('/users')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("<p>@testuser1</p>", html)
            self.assertIn("<p>@testuser2</p>", html)

    def test_search_users(self):
        """List of users that match the search term displays properly"""

        with self.client as c:
            resp = c.get('/users?q=testuser2')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("<p>@testuser1</p>", html)
            self.assertIn("<p>@testuser2</p>", html)

    def test_search_users_no_results(self):
        """The correct message displays when there are no search results"""

        with self.client as c:
            resp = c.get('/users?q=notauser')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("<p>@testuser1</p>", html)
            self.assertIn("<h3>Sorry, no users found</h3>", html)

    def test_show_following_unathorized(self):
        """A user must be logged-in in order to see the list of users they are following"""

        with self.client as c:
            resp = c.get(f'/users/{self.testuser1.id}/following',  follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="alert alert-danger">Access unauthorized.</div>', html)

    def test_show_following(self):
        """The list of users that the user is following displays correctly"""
        
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

            resp = c.get(f'/users/{self.testuser1.id}/following')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)

            self.assertNotIn('<p>@testuser2</p>', html)
            self.assertIn('<p>@testuser3</p>', html)
            self.assertIn('<p>@testuser4</p>', html)

    def test_show_followers(self):
        """The list of a user's followers displays correctly"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser3.id

            resp = c.get(f'/users/{self.testuser3.id}/followers')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)

            self.assertNotIn('<p>@testuser4</p>', html)
            self.assertIn('<p>@testuser1</p>', html)
            self.assertIn('<p>@testuser2</p>', html)

    def test_add_follow(self):
        """A user can successfully follow another user"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

            resp = c.post(f'/users/follow/{self.testuser2.id}')

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(len(User.query.get(self.testuser1.id).following), 3)

    def test_remove_follow(self):
        """A user can successfully unfollow another user"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id
            
            resp = c.post(f'/users/stop-following/{self.testuser3.id}')

            self.assertEqual(resp.status_code, 302)
            self.assertEqual(len(User.query.get(self.testuser1.id).following), 1)

    def test_update_user(self):
        """A user can successfully update their information"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id
            
            form_data = {
                'username': 'newusername',
                'email': 'test1@test.com',
                'image_url': '/static/images/default-pic.png',
                'header_image_url': '/static/images/warbler-hero.jpg',
                'bio': 'Test Bio that I just added',
                'location': 'Test Location',
                'password': 'testuser1'
            }
            resp = c.post('/users/profile', data=form_data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h4 id="sidebar-username">@newusername</h4>', html)
            self.assertIn('Test Bio that I just added', html)
            self.assertIn('Test Location', html)

    def test_update_user_wrong_password(self):
        """A user cannot update their information with the worng password"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id
            
            form_data = {
                'username': 'newusername',
                'email': 'test1@test.com',
                'image_url': '/static/images/default-pic.png',
                'header_image_url': '/static/images/warbler-hero.jpg',
                'bio': 'Test Bio that I just added',
                'location': 'Test Location',
                'password': 'testuser'
            }
            resp = c.post('/users/profile', data=form_data, follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="alert alert-danger">Not Authorized: Incorrect Password</div>', html)

    def test_delete_user(self):
        """A user can delete their profile"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser1.id

            resp = c.post('/users/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<button class="btn btn-primary btn-lg btn-block">Sign me up!</button>', html)
            self.assertEqual(len(User.query.all()), 3)