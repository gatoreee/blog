# Project: Multiuser Blog - [Enrique B]

Required Libraries and Dependencies

The project uses Twitter's Bootstrap and jQuery. The stylesheets and js are linked to in the base.html file so there's no need for local copies. The project was developed using Google App Engine so in order to easily configure and run the project with the instructions below, the user should have GAE installed and configured in their system.

How to Run Project

The project repository can be found at https://github.com/gatoreee/blog. Save all files to a local folder. In order to run the application, open a command prompt and follow the instructions below: 
1) From the command prompt, use cd command to take you to the folder where the files are saved
2) From the command prompt, run the 'dev_appserver.py app.yaml' to launch the application locally 
3) Open Chrome and enter 'localhost/8080' in the address bar to use the application

Alternatively, the project is hosted at http://bees-blog.appspot.com/blog

Extra Credit Description

I used jQuery to make some of the blog features dynamic. When a user likes a post, it dynamically updates the counter without needing a reload; when a user adds a comment, it dynamically adds the comment to the post without having to reload; when a user deletes a post, it dynamically removes the post without having to reload.
