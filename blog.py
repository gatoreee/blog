"""Main python module defining model, classes and functions."""
import re
import hmac
import json
from model import User, Comment, Post, render_str

import webapp2

from google.appengine.ext import ndb


secret = 'tart'


def make_secure_val(val):
    """Utility function required for cookies."""
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())


def check_secure_val(secure_val):
    """Utility function required for cookies."""
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val


class BlogHandler(webapp2.RequestHandler):
    """Main class to handle requests."""

    def write(self, *a, **kw):
        """Utility method to save long method call."""
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        """Utility method to add current user to params."""
        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        """Utility method to render template."""
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        """Utility method to set cookies."""
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        """Utility method to read cookies."""
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        """Utility method to set cookie when user logs in."""
        self.set_secure_cookie('user_id', str(user.key.integer_id()))

    def logout(self):
        """Utility method to update cookie when user logs out."""
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        """Utility method to initialize session."""
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))


def blog_key(name='default'):
    """Utility function returns posts parent key."""
    return ndb.Key('blogs', name)


class NewComment(BlogHandler):
    """Class handles requests for and from new comment form."""

    def post(self):
        """Handle post requests from comment form."""
        if not self.user:
            return self.redirect('/blog')

        comment = self.request.get('comment')
        post_id = self.request.get('post_id')
        parent_key = ndb.Key('Post', int(post_id), parent=blog_key())
        parent_post = parent_key.get()

        if comment:
            c = Comment(parent=blog_key(), comment=comment,
                        author=self.user.key)
            c.put()
            parent_post.comments.append(c)
            parent_post.put()
            self.write(json.dumps(({'comment': comment})))
        return


class BlogFront(BlogHandler):
    """Class handles requests for main blog page."""

    def get(self):
        """Handle get requests for main blog page."""
        posts = Post.query().order(-Post.created)
        self.render('front.html', posts=posts, current_user=self.user)


class PostPage(BlogHandler):
    """Class handles requests for individual post page."""

    def get(self, post_id):
        """Handle get requests for individual post page."""
        key = ndb.Key('Post', int(post_id), parent=blog_key())
        post = key.get()

        if not post:
            self.error(404)
            return

        self.render("permalink.html", post=post)


class NewPost(BlogHandler):
    """Class handles requests for and from new post form."""

    def get(self):
        """Handle get requests for new post form."""
        if self.user:
            self.render("newpost.html")
        else:
            self.redirect("/login")

    def post(self):
        """Handle post requests from new post form."""
        if not self.user:
            return self.redirect('/blog')

        subject = self.request.get('subject')
        content = self.request.get('content')
        if subject and content:
            p = Post(parent=blog_key(), subject=subject, content=content,
                     poster=self.user.key)
            p.put()
            self.redirect('/blog/%s' % str(p.key.integer_id()))
        else:
            error = "subject and content, please!"
            self.render("newpost.html", subject=subject, content=content,
                        error=error)


class EditPost(BlogHandler):
    """Class handles requests for and from edit post form."""

    def get(self, post_id):
        """Handle get requests for edit post form."""
        key = ndb.Key('Post', int(post_id), parent=blog_key())
        post = key.get()

        if not post:
            self.error(404)
            return

        poster_id = post.poster.integer_id()
        user_id = self.user.key.integer_id()

        if poster_id != user_id:
            self.redirect('/blog/notauth?username=' + self.user.name)
        else:
            self.render("editpost.html", post=post)

    def post(self, post_id):
        """Handle post requests from edit post form."""
        if not self.user:
            self.redirect('/blog')

        key = ndb.Key('Post', int(post_id), parent=blog_key())
        post = key.get()

        poster_id = post.poster.integer_id()
        user_id = self.user.key.integer_id()

        if poster_id != user_id:
            self.redirect('/blog/notauth?username=' + self.user.name)

        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            post.subject = subject
            post.content = content
            post.put()
            self.redirect('/blog/%s' % str(post.key.integer_id()))
        else:
            error = "subject and content, please!"
            self.render("newpost.html", subject=subject, content=content,
                        error=error)


class DeletePost(BlogHandler):
    """Class handles requests for deleting posts."""

    def post(self):
        """Handle post request to delete post."""
        if not self.user:
            self.redirect('/blog')

        post_id = self.request.get('post_id')
        key = ndb.Key('Post', int(post_id), parent=blog_key())
        post = key.get()

        poster_id = post.poster.integer_id()
        user_id = self.user.key.integer_id()

        if poster_id != user_id:
            self.redirect('/blog/notauth?username=' + self.user.name)

        if key:
            key.delete()
            self.write(json.dumps(({'deleted': post_id})))
        return


class LikesHandler(BlogHandler):
    """Class handles likes for posts."""

    def post(self):
        """Handle post requests to like/unlike post."""
        if not self.user:
            self.redirect('/blog')

        post_id = self.request.get('post_id')
        liked = self.request.get('liked')
        parent_key = ndb.Key('Post', int(post_id), parent=blog_key())
        parent_post = parent_key.get()
        likes_counter = parent_post.likes_counter
        author = self.user.name

        """Only add like if user hasn't liked already."""
        if liked == "false" and author not in parent_post.likes_authors:
            parent_post.likes_authors.append(author)
            parent_post.likes_counter = likes_counter + 1
            parent_post.put()
            self.write(json.dumps(({'likes_counter':
                                  parent_post.likes_counter})))
        else:
            parent_post.likes_authors.remove(author)
            parent_post.likes_counter = likes_counter - 1
            parent_post.put()
            self.write(json.dumps(({'likes_counter':
                                  parent_post.likes_counter})))
        return


class Signup(BlogHandler):
    """Class handles requests for and from sign-up form."""

    def get(self):
        """Handle get requests for sign-up form."""
        self.render("signup-form.html")

    def post(self):
        """Handle post requests from sign-up form."""
        have_error = False
        self.username = self.request.get('username')
        self.password = self.request.get('password')
        self.verify = self.request.get('verify')
        self.email = self.request.get('email')
        self.avatar = str(self.request.get('avatar'))

        params = dict(username=self.username,
                      email=self.email)

        if not valid_username(self.username):
            params['error_username'] = "That's not a valid username"
            have_error = True

        if not valid_password(self.password):
            params['error_password'] = "That wasn't a valid password"
            have_error = True
        elif self.password != self.verify:
            params['error_verify'] = "Your passwords didn't match"
            have_error = True

        if not valid_email(self.email):
            params['error_email'] = "That's not a valid email"
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)
        else:
            self.done()


def valid_username(username):
    """Utility function to verify sign-up from inputs."""
    return username and re.compile(r"^[a-zA-Z0-9_-]{3,20}$").match(username)


def valid_password(password):
    """Utility function to verify sign-up from inputs."""
    return password and re.compile(r"^.{3,20}$").match(password)


def valid_email(email):
    """Utility function to verify sign-up from inputs."""
    return not email or re.compile(r'^[\S]+@[\S]+\.[\S]+$').match(email)


class Register(Signup):
    """Class handles request for sign-up form."""

    def done(self):
        """Verify user doesn't already exist."""
        u = User.by_name(self.username)
        if u:
            msg = 'That user already exists.'
            self.render('signup-form.html', error_username=msg)
        else:
            u = User.register(self.username, self.password, self.email, self.avatar)
            u.put()

            self.login(u)
            self.redirect('/blog')

class UserProfile(BlogHandler):
    """Class handles requests for and from edit user form."""

    def get(self, user_id):
        """Handle get requests for edit user form."""
        key = ndb.Key('User', int(user_id), parent=blog_key())
        post = key.get()

        if not post:
            self.error(404)
            return

        poster_id = post.poster.integer_id()
        user_id = self.user.key.integer_id()

        if poster_id != user_id:
            self.redirect('/blog/notauth?username=' + self.user.name)
        else:
            self.render("editpost.html", post=post)

    def post(self, post_id):
        """Handle post requests from edit post form."""
        if not self.user:
            self.redirect('/blog')

        key = ndb.Key('Post', int(post_id), parent=blog_key())
        post = key.get()

        poster_id = post.poster.integer_id()
        user_id = self.user.key.integer_id()

        if poster_id != user_id:
            self.redirect('/blog/notauth?username=' + self.user.name)

        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            post.subject = subject
            post.content = content
            post.put()
            self.redirect('/blog/%s' % str(post.key.integer_id()))
        else:
            error = "subject and content, please!"
            self.render("newpost.html", subject=subject, content=content,
                        error=error)

class EditUser(BlogHandler):
    """Class handles requests for and from edit user form."""

    def get(self, user_id):
        """Handle get requests for edit user form."""
        key = ndb.Key('User', int(user_id), parent=blog_key())
        post = key.get()

        if not post:
            self.error(404)
            return

        poster_id = post.poster.integer_id()
        user_id = self.user.key.integer_id()

        if poster_id != user_id:
            self.redirect('/blog/notauth?username=' + self.user.name)
        else:
            self.render("editpost.html", post=post)

    def post(self, post_id):
        """Handle post requests from edit post form."""
        if not self.user:
            self.redirect('/blog')

        key = ndb.Key('Post', int(post_id), parent=blog_key())
        post = key.get()

        poster_id = post.poster.integer_id()
        user_id = self.user.key.integer_id()

        if poster_id != user_id:
            self.redirect('/blog/notauth?username=' + self.user.name)

        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            post.subject = subject
            post.content = content
            post.put()
            self.redirect('/blog/%s' % str(post.key.integer_id()))
        else:
            error = "subject and content, please!"
            self.render("newpost.html", subject=subject, content=content,
                        error=error)

class Login(BlogHandler):
    """Class handles request for signup form."""

    def get(self):
        """Handle get requests for login form."""
        self.render('login-form.html')

    def post(self):
        """Handle post requests from login form."""
        username = self.request.get('username')
        password = self.request.get('password')

        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect('/blog')
        else:
            name = User.by_name(username)
            if not name:
                msg = 'User not found, please '
            else:
                msg = 'Invalid login'
            self.render('login-form.html', error=msg)


class Logout(BlogHandler):
    """Class handles request for logout."""

    def get(self):
        """Handle request to logout."""
        self.logout()
        self.redirect('/blog')


class NotAuthorized(BlogHandler):
    """Class handles request for not authorized landing page."""

    def get(self):
        """Handle request for not authorized landing page."""
        username = self.request.get('username')
        if valid_username(username):
            self.render('notauth.html', username=username)
        else:
            self.redirect('/login')

app = webapp2.WSGIApplication([('/', BlogFront),
                               ('/blog/notauth', NotAuthorized),
                               ('/blog/?', BlogFront),
                               ('/blog/([0-9]+)', PostPage),
                               ('/blog/newpost', NewPost),
                               ('/blog/newcomment', NewComment),
                               ('/blog/editpost/([0-9]+)', EditPost),
                               ('/blog/deletepost', DeletePost),
                               ('/blog/like', LikesHandler),
                               ('/signup', Register),
                               ('/user', UserProfile),
                               ('/edituser', EditUser),
                               ('/login', Login),
                               ('/logout', Logout),
                               ],
                              debug=True)
