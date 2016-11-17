"""Main python module defining data model and utility functions."""
import os
import random
import hashlib
import jinja2
from string import letters
from google.appengine.ext import ndb


"""jinja required setup"""
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)


def render_str(template, **params):
    """Utility function required for jinja."""
    t = jinja_env.get_template(template)
    return t.render(params)


def make_salt(length=5):
    """Utility function to make salt value."""
    return ''.join(random.choice(letters) for x in xrange(length))


def make_pw_hash(name, pw, salt=None):
    """Utility function to make hash value."""
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)


def valid_pw(name, password, h):
    """Utility function to verify user password."""
    salt = h.split(',')[0]
    return h == make_pw_hash(name, password, salt)


def users_key(group='default'):
    """Utility function that returns users parent key."""
    return ndb.Key('users', group)


class User(ndb.Model):
    """Class defines user model for DB and utility methods."""

    name = ndb.StringProperty(required=True)
    pw_hash = ndb.StringProperty(required=True)
    email = ndb.StringProperty()

    @classmethod
    def by_id(cls, uid):
        """Utility method finds existing user by id."""
        return User.get_by_id(uid, parent=users_key())

    @classmethod
    def by_name(cls, name):
        """Utility method finds existing user by name."""
        u = User.query(User.name == name).get()
        return u

    @classmethod
    def register(cls, name, pw, email=None):
        """Utility method registers new user."""
        pw_hash = make_pw_hash(name, pw)
        return User(parent=users_key(),
                    name=name,
                    pw_hash=pw_hash,
                    email=email)

    @classmethod
    def login(cls, name, pw):
        """Utility method returns user logged in."""
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u


class Comment(ndb.Model):
    """Class defines comment model for DB."""

    comment = ndb.TextProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    author = ndb.KeyProperty(User, required=True)
    last_modified = ndb.DateTimeProperty(auto_now=True)


class Post(ndb.Model):
    """Class defines post model for DB and utility methods."""

    subject = ndb.StringProperty(required=True)
    content = ndb.TextProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    poster = ndb.KeyProperty(User, required=True)
    likes_counter = ndb.IntegerProperty(default=0)
    comments = ndb.StructuredProperty(Comment, repeated=True)
    likes_authors = ndb.StringProperty(repeated=True)
    last_modified = ndb.DateTimeProperty(auto_now=True)

    def render(self, user):
        """Utility method adds html line breaks and calls render function."""
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p=self, user=user)
