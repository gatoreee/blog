/**
* event handler for new comments
*/
$(document).ready(function(){$('.comment-form').submit(function(e){
    // intercept submit post
	e.preventDefault();
	e.stopImmediatePropagation();
    // read post-id, username and content of comment
    var instance = $(this);
    var post_id = instance.data('post-id');
    var username = instance.data('username');
    var values = $(this).serializeArray();
    var data = JSON.stringify(values);
    console.log("submitted:", post_id, values[0].value);
    // submit to backend function so it can be added to DB
    $.ajax({
    	type: "post",
        url: "/blog/newcomment", // route which will handle the request
        dataType: 'json',
        data: {"post_id": post_id, "comment": values[0].value},
        // if successful, display new comment on page
        success: function(data){
        	console.log("Got to success, %s", values[0].value);
        	$('#' + post_id + '-cmt-area > div').removeAttr('hidden');
        	$('#' + post_id + '-cmt-area > div').append("<p class='cmt-section-din'>" + username + ": <i>" + values[0].value + "</i></p>");
        },
        error: function(err){
            console.log(err);
    	}
 	});
 	clearInput();
 })});


/**
* event handler for profile pic upload
*/
$(document).ready(function(){$('.profile-pic-form').submit(function(e){
    console.log("got to profile-pic-form submit ajax");
    // intercept submit post
	e.preventDefault();
	e.stopImmediatePropagation();
    // read username and pic
    var file_data = $("#avatar").prop("files")[0];   // Getting the properties of file from file field
	var form_data = new FormData();                  // Creating object of FormData class

    console.log("Got to load pic %r", $("#avatar"));

	form_data.append("file", file_data);          // Appending parameter named file with properties of file_field to form_data
	form_data.append("username", $(this).data('username'));   // submit to backend function so it can be added to DB
    $.ajax({
    	type: "post",
        url: "/uploadprofilepic", // route which will handle the request  
        data: form_data,
        processData: false,
        contentType: false,        
        // if successful, display new comment on page
        success: function(data){
        	console.log("Got to success load pic %i", data);
        },
        error: function(err){
            console.log(err);
            console.log("Got to error load pic %i", data);
    	}
 	});
 })});

/**
* event handler for post likes/unlikes
*/
$(document).ready(function(){$('.like-button').on('click', function(e){
	e.preventDefault();
    // read post-id, the event (like/unlike)
    var instance = $(this);
    var post_id = instance.data('post-id');
    var liked = instance.hasClass('active');
    console.log("event like-button click:", liked, post_id);
    // submit to backend function so it can be added to DB
    $.ajax({
    	type: "post",
    	url: "/blog/like", // route which will handle the request
    	dataType: 'json',
    	data: {"post_id": post_id, "liked":liked},
        // if successful, update counter on page
    	success: function(data){
    		if (liked == false) {
    			console.log("Got to likes false selector");
    			instance.find("span").addClass("glyphicon-heart").removeClass("glyphicon-heart-empty");
    		}
    		else {
    			console.log("Got to likes true selector");
    			instance.find("span").addClass("glyphicon-heart-empty").removeClass("glyphicon-heart");
    		}
            console.log(data.likes_counter);
            console.log(instance.parent().parent().find(".post-likes").empty().append(data.likes_counter + " likes"));
    	},
    	error: function(err){
    		console.log(err);
    	}
   	});
})});

/**
* event handler for post delete
*/
$(document).ready(function(){$('.delete-button').on('click', function(e){
	e.preventDefault();
    // read post-id
    var instance = $(this);
    var post_id = instance.data('post-id');
    console.log("event delete-button click:", post_id);
    var confirm = deletePopup();
    if (!confirm)
    	return;
    console.log("delete confirmed:", post_id);
    // submit to backend function so it can be deleted from DB
    $.ajax({
    	type: "post",
    	url: "/blog/deletepost", // route which will handle the request
    	dataType: 'json',
    	data: {"post_id": post_id},
        // if successful, remove post from page
    	success: function(data){
    		instance.parent().parent().parent().parent().remove();
    	},
    	error: function(err){
    		console.log(err);
    	}
   	});
})});

/**
* This function clears form inputs
*/
function clearInput() {
    $(".comment-form :input").each( function() {
       $(this).val('');
       $(this).blur();
    });
}

/**
* This function pops a confimation alert when user tries to delete post
*/
function deletePopup() {
    var txt;
   	var r = confirm("Are you sure you want to delete your post?");
    return r;
}