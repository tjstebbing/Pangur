comments = module('comments', 0.1);

/* CommentMenu */
comments.CommentMenu = klass({

    __init__ : function() {
        $(".commentActions").click(this.clicked);
        this.hoverBox = $("#commentMenu");
        this.emoticon = $(".emoticon");
        this.emoticonIcon = $(".emoticon .icon");
        this.emoticons = $(".emoticons");
        this.emoticon.click(this.showEmoticons);
        $('#emoticons ul li ul li').click(this.selectEmoticon);
    },

    json = function(url, callback) {
        $.ajax({url:url, dataType:'json', type :'POST', 'success':callback});
    },

    clicked : function(e) {
        var id = $(e.currentTarget).attr('id');
        this.json('/api/comment/'+id+'/info', this.showCommentMenu);
    },

    showEmoticons : function() {
        var off = this.emoticon.offset();
        this.emoticons.css({
            'left' : off.left-15+'px',
            'top' : off.top-32+'px'
            });
        this.emoticons.show();
    },

    selectEmoticon : function(e) {
        this.emoticonIcon.addClass($(e.currentTarget).attr('class'));
        this.emoticons.hide();
    },

    showCommentMenu : function(info) {
        this.info = info
        var t = $('#'+info.id);
        var p = t.offset();
        var s = t.children('.slug').attr('id');
        this.hoverBox.css({'left' : p.left-0+'px', 'top' : p.top+t.height()+'px'});
        var list = $("<ul></ul>");
        pomke.map(pomke.partial(this.addAction, list),
            ['reply', 'edit', 'delete']);
        this.hoverBox.html(list);
        this.hoverBox.show();
    },

    addAction : function(list, action) {
        if(this.info.actions.indexOf(action) >= 0) {
            var btn = $('<div>'+action+'</div>');
            btn.button();
            btn.click(this[action+"Comment"]);
            list.append(btn);
        }
    },

    deleteComment : function() {
        if(confirm("Are you sure you would like to delete this comment?")) {
            this.json('/api/comment/'+this.info.id+'/delete', this.reloadToComment);
        }
    },

    reloadToComment : function() {
        window.location = "{0}?d={1}#c{1}".format(
                window.location.pathname, this.info.id);
    },

    editComment : function() {
        var comment = $("#c"+this.info.id);

    }

});
