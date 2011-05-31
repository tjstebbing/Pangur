$(function() {
    $(".button, input:submit, input:button").button();
    $(".newList").click(listful.ListView);
});

listful = module('listful');

String.prototype.format = function() {
    var formatted = this;
    for (var i = 0; i < arguments.length; i++) {
        var regexp = new RegExp('\\{'+i+'\\}', 'gi');
        formatted = formatted.replace(regexp, arguments[i]);
    }
    return formatted;
};

listful.load = function(path, sel) {
    var tmp = $('<div>');
    $('body').append(tmp);
    var d = pomke.Deferred();
    tmp.load(path + " " + sel,
            pomke.partial(listful._fragmentLoaded, tmp, sel, d));
    return d;
};

listful._fragmentLoaded = function(tmp, sel, d) {
    var e = $(tmp.find(sel)[0]);
    e.detach();
    tmp.remove();
    $('body').append(e);
    d.callback(e);
};

listful.ListView = klass({

    __init__ : function(listData) {
        this.list = listData || {};
        listful.load('/js/templates.html', '.listBox').addCallback(
            this.loaded);
    },

    loaded : function(el) {
        this.box = el;
        if(this.list.x != undefined && this.list.y != undefined) {
            var position = [this.list.x, this.list.y];
        } else { 
            var position = 'center'; 
        }
        var opts = {
            width: this.list.w || 200, 
            height: this.list.h || 400,
            minWidth:200, 
            minHeight:200,
            position: position,
            hide: 'fade',
            closeOnEscape: false,
            beforeClose: this.save,
            dialogClass : 'list',
            title:"<div class='noteTitle'>{0}</div>".format(
                    this.list.name || 'Untitled')};
        this.box.dialog(opts);
    },

    save : function() {
        var dialog = this.box.parent();
        var coords = dialog.offset();
        var data = {
            id : this.list.id,
            name : this.list.title,
            h : dialog.height(),
            w : dialog.width(),
            y : coords.top,
            x : coords.left};
        var d = pomke.Deferred();
        $.post("/api/list/update", {data:$.toJSON(data)}, d.callback);
        return d;
    }

});
