/* Copyright (c) 2005 Pomke Nohkan 
 * 
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 * 
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */

/* Pomke creates 3 global variables: 'pomke', 'module' & 'klass'. */

pomke = {};
pomke.NAME = 'pomke';
pomke.VERSION = 0.7;
pomke.DEPS = [];
pomke.loadedStyles = [];
pomke.NOINIT = {};
pomke.MOD_PATHS = {};
pomke.debug = false;

/* klass constructs a user defined javascript class constructor with the
 * given super classes and methods. You can instantiate the returned class
 * with or without the 'new' operator. If your class has an __init__ method
 * this will be called when the class is instantiated with the arguments
 * passed to the constructor. All methods will be bound to the instance 
 * with pomke.bindAll.
 *
 * //In this example we subclass Bar and alert Hello World 
 * Foo = klass(Bar, {
 *     '__init__' : function(a) { this.output(a); },
 *     'output' : function(value) { alert(value); }
 * });
 * f = Foo("Hello World"); //Hello World will be alerted
 * f.output("Goodbye Cruel World"); //another alert 
 */
klass = function() {
    var methods = arguments[arguments.length-1];
    var cls = function() {
        if (arguments[0] == pomke.NOINIT) return;
        if(this instanceof cls) {
            var self = this;
        } else {
            var self = new cls(pomke.NOINIT);
        }
        pomke.update(self, pomke.flattenedMethods(cls));
        self._super = pomke._super; // super is a reserved word
        pomke.bindAll(self);
        self.__class__ = cls;
        if(typeof(self.__init__) == 'function') {
            self.__init__.apply(self, arguments);
        }
        return self;
    }
    var bases = [];
    for(var i=arguments.length-2; i>=0; i--) {
        bases.push(arguments[i]);
    }
    cls.__bases__ = bases;
    cls.__methods__ = methods;
    return cls;
}

/* module is a module constructor, it takes a module path name and version, 
 * and returns a module struct. 
 * You should add an __init__ function to your module, this will be called
 * when all dependancies have been included and the page is loaded. 
 *
 * The 'dependsOn' function in the module allows dependancies to be specified, 
 * these will be included using the ImportManager before your modules __init__
 * is run.
 * yourCode.flibble = module('yourCode.flibble', 1.0);
 * yourCode.flibbe.__init__ = function() { 
 *     pomke.log("yay! welcome to", yourCode.flibble.NAME);
 * }
 */
module = function(name, version) {
    var mod = {
        'NAME' : name, 
        'VERSION' : version, 
        'DEPS' : [], 
        'ready' : new pomke.Deferred(),
        'dependsOn' : pomke.partial(pomke.mods.dependsOn, name) };
    pomke.mods.register(mod);
    return mod;
}

pomke.forEach = function(func, list /* extra args */) {
    for (var i = 0; i < list.length; i++) {
        func.apply(this, [list[i]].concat(
                    pomke.arrayFromArgs(arguments).slice(2)));
    }
}

pomke.map = function(func, list /* extra args */) {
    var l = [];
    for (var i = 0; i < list.length; i++) {
        l.push(func.apply(this, [list[i]].concat(
                        pomke.arrayFromArgs(arguments).slice(2))));
    }
    return l;
}

pomke.bind = function(obj, func) {
    //TODO some funcs like alert do not have apply, see mochi bind
    /* we assign this function a name so its obvious in a debugger */
    function boundMethod() { return func.apply(obj, arguments); }
    boundMethod.__wrapped__ = func;
    return boundMethod;
}

pomke.arrayFromArgs = function(args, skip) {
    if(!skip) { skip = 0; }
    var a = [];
    for (var i = skip; i < args.length; i++) { 
        a.push(args[i]); 
    }
    return a;
}

pomke.partial = function(func) {
    var args = pomke.arrayFromArgs(arguments, 1);
    function partial() { 
        return func.apply(this, args.concat(pomke.arrayFromArgs(arguments)));
    };
    partial.__wrapped__ = func;
    return partial;
}

pomke.bindAll = function(obj) {
    for (var k in obj) {
        var func = obj[k];
        if(typeof(func) == 'function') {
            obj[k] = pomke.bind(obj, func);
        }
    }
}

pomke.update = function (self, obj/*, ... */) {
    /* Clone of Mochikit.Base.update */
    if (self === null || self === undefined) {
        self = {};
    }
    for (var i = 1; i < arguments.length; i++) {
        var o = arguments[i];
        if (typeof(o) != 'undefined' && o !== null) {
            for (var k in o) {
                self[k] = o[k];
            }
        }
    }
    return self;
};

pomke.log = function () {
    msg = pomke.arrayFromArgs(arguments).join(' ');
    /* Clone of MochiKit.Logging.Logger.prototype.logToConsole */
    if (typeof(window) != "undefined" && window.console && window.console.log) {
        // Safari and FireBug 0.4
        // Percent replacement is a workaround for cute Safari crashing bug
        window.console.log(msg);
    } else if (typeof(opera) != "undefined" && opera.postError) {
        // Opera
        opera.postError(msg);
    } else if (typeof(printfire) == "function") {
        // FireBug 0.3 and earlier
        printfire(msg);
    } else if (typeof(Debug) != "undefined" && Debug.writeln) {
        // IE Web Development Helper (?)
        // http://www.nikhilk.net/Entry.aspx?id=93
        Debug.writeln(msg);
    } else if (typeof(debug) != "undefined" && debug.trace) {
        // Atlas framework (?)
        // http://www.nikhilk.net/Entry.aspx?id=93
        debug.trace(msg);
    }
}

pomke.trace = function() {
    if(pomke.debug) {
        pomke.partial(pomke.log, '>> TRACE: ').apply(this, arguments)
    }
}

pomke.createInHead = function(name, attrs) {
    //Create a new element in the HEAD tag of the page.
    var elem = document.createElement(name); //TODO what about XHTML NS?
    for (var k in attrs) {
        elem.setAttribute(k,attrs[k]);
    }
    document.getElementsByTagName('head')[0].appendChild(elem);
    return elem;
}

//pomke.loadStyle = function(url) {
//    var l = [];
//    var checkLoaded = function(l, url, s) { if(url == s) { l.push(url); } }
//    forEach(mItr.iter(pomke.loadedStyles), pomke.partial(checkLoaded, l, url));
//    if(l.length == 0) {
//        pomke.createInHead('LINK',
//                {'rel':'stylesheet','href':url,'type':'text/css'});
//        pomke.loadedStyles.push(url);
//        pomke.log(":: loaded style",url);
//    } else {
//        pomke.log(':: Attempting to load style ' + url + ' twice, ignoring.');
//    }
//}

pomke.flattenedMethods = function(cls) {
    if (cls.__flattened__) {
        return cls.__flattened__; // cached
    }
    var proto = {};
    for(var i=0; i < cls.__bases__.length; i++) {
        var base = cls.__bases__[i];
        if(typeof(base) == "string") {
            var baseObj = eval(base);
            if(typeof(baseObj) == "undefined") {
                pomke.log("base class not found: "+base);
            }
            base = baseObj;
            cls.__bases__[i] = base;
        } if(typeof(base) == "undefined") {
            pomke.log("base class not found (undefined)");
        } else if(typeof(base.__methods__) == "undefined") {
            pomke.log("broken base class (no methods attribute)");
        }
        pomke.update(proto, pomke.flattenedMethods(base));
    }
    var methods = cls.__methods__;
    for (var k in methods) {
        if (typeof(methods[k]) == 'function')
            methods[k].__name__ = k;
        proto[k] = methods[k];
    }
    cls.__flattened__ = proto;
    return cls.__flattened__;
}

/* implements this.super('funcname', ...) for instances */
pomke._super = function(caller /*args*/) {
    while (caller.__wrapped__) caller = caller.__wrapped__; // un-bind/partial
    //pomke.trace("supercall: " + caller.__name__);
    var f = pomke._findSuper(this.__class__, caller, 0);
    if (typeof(f) != "undefined") {
        //pomke.trace("super: found method in superclass.");
        var args = pomke.arrayFromArgs(arguments, 1);
        f.apply(this, args);
    }
    else {
        //pomke.trace("super: no method found.");
    }
}
pomke._super.__name__ = "super"; // for debugging

pomke._findSuper = function(cls, caller, found) {
    //pomke.trace("super: checking a class for "+caller.__name__);
    var f = cls.__methods__[caller.__name__];
    if (f) {
        //pomke.trace("super: found a candidate, " + (f==caller));
        if (found) return f;
        while (f.__wrapped__) f = f.__wrapped__; // un-bind/partial
        if (f == caller) {
            found = 1;
            //pomke.trace("super: found caller");
        }
    }
    var bases = cls.__bases__;
    for(var i=0; i<bases.length; i++) {
        f = pomke._findSuper(bases[i], caller, found);
        if (f) return f;
    }
}


/* a minimalistic mochikit deferred, ALL SAFTEY REMOVED! */ 

pomke.Deferred = klass({
        
    __init__ : function() {
        this.chain = [];
        this.fired = -1;
        this.paused = 0;
        this.results = [null, null];
        this.chained = false;
    },

    _resback: function (res) {
        this.fired = ((res instanceof Error) ? 1 : 0);
        this.results[this.fired] = res;
        this._fire();
    },

    callback: function (res) {
        this._resback(res);
    },

    errback: function (res) {
        this._resback(res);
    },

    addBoth: function (fn) {
        if (arguments.length > 1) {
            fn = pomke.partial.apply(null, arguments);
        }
        return this.addCallbacks(fn, fn);
    },

    addCallback: function (fn) {
        if (arguments.length > 1) {
            fn = pomke.partial.apply(null, arguments);
        }
        return this.addCallbacks(fn, null);
    },

    addErrback: function (fn) {
        if (arguments.length > 1) {
            fn = pomke.partial.apply(null, arguments);
        }
        return this.addCallbacks(null, fn);
    },

    addCallbacks: function (cb, eb) {
        this.chain.push([cb, eb]);
        if (this.fired >= 0) {
            this._fire();
        }
        return this;
    },

    _fire: function () {
        var chain = this.chain;
        var fired = this.fired;
        var res = this.results[fired];
        var self = this;
        var cb = null;
        while (chain.length > 0 && this.paused === 0) {
            // Array
            var pair = chain.shift();
            var f = pair[fired];
            if (f === null) {
                continue;
            }
            try {
                res = f(res);
                fired = ((res instanceof Error) ? 1 : 0);
                if (res instanceof pomke.Deferred) {
                    cb = function (res) {
                        self._resback(res);
                        self.paused--;
                        if ((self.paused === 0) && (self.fired >= 0)) {
                            self._fire();
                        }
                    };
                    this.paused++;
                }
            } catch (err) {
                fired = 1;
                if (!(err instanceof Error)) {
                    err = new Error(err);
                }
                res = err;
            }
        }
        this.fired = fired;
        this.results[fired] = res;
        if (cb && this.paused) {
            res.addBoth(cb);
            res.chained = true;
        }
    }
});

/* DeferredList, subclasses Deferred */

pomke.DeferredList = klass('pomke.Deferred', { 
        
    __init__ : function (list, fireOnOneCallback, 
                   fireOnOneErrback, consumeErrors) {

        // call parent constructor
        pomke.Deferred.__methods__.__init__.apply(this)
        this.list = list;
        var resultList = [];
        this.resultList = resultList;

        this.finishedCount = 0;
        this.fireOnOneCallback = fireOnOneCallback;
        this.fireOnOneErrback = fireOnOneErrback;
        this.consumeErrors = consumeErrors;

        var cb = this._cbDeferred; 
        for (var i = 0; i < list.length; i++) {
            var d = list[i];
            resultList.push(undefined);
            d.addCallback(cb, i, true);
            d.addErrback(cb, i, false);
        }

        if (list.length === 0 && !fireOnOneCallback) {
            this.callback(this.resultList);
        }
    },

    _cbDeferred : function (index, succeeded, result) {
        this.resultList[index] = [succeeded, result];
        this.finishedCount += 1;
        if (this.fired == -1) {
            if (succeeded && this.fireOnOneCallback) {
                this.callback([index, result]);
            } else if (!succeeded && this.fireOnOneErrback) {
                this.errback(result);
            } else if (this.finishedCount == this.list.length) {
                this.callback(this.resultList);
            }
        }
        if (!succeeded && this.consumeErrors) {
            result = null;
        }
        return result;
    }
});


/* pomke.ImportManager manages importing modules from dot-string paths. Module paths are 
 * relative to the base directory the pomke/pomke.js library is loaded from in the 
 * current page. You can manually override basepaths for particular modules using the 
 * pomke.MOD_PATHS array:
 *
 * pomke.MOD_PATHS['somelib'] = 'http://somelib.com/static/';
 *
 * to allow dependsOn('somelib.somemodule') to load from that location.
 */ 
pomke._ImportManager = klass({

    __init__ : function() {
        this.modMap = {};
        this.importedModules = {};
        this.pendingInit = [];
        this.pageLoaded = false;
        var re = /^(.*\/)pomke\/pomke\.js$/;
        var scripts = document.getElementsByTagName('script');
        for(var i=0; i< scripts.length; i++) {
            var res = re.exec(scripts[i].src);
            if(res) {
                break;
            }
        }
        if(res) {
            pomke.MOD_PATHS['_B'] = res[1];
        } else {
            throw Error('pomke.js incorrectly installed');
        }
    },

    mkPath : function(path) {
    /* assume that a path is dotted ie: pomke.i18n, MochiKit.DOM */
        var bits = path.split('.');
        var first = bits.shift();

        if(first in pomke.MOD_PATHS) { 
            var base = pomke.MOD_PATHS[first]; 
        } else { 
            var base = pomke.MOD_PATHS['_B']; 
            bits.unshift(first);
        }
        return base + bits.join('/') + ".js";
    },

    importModule : function(modulePath) {
        if(this.importedModules[modulePath]) {
            //if someone requests this module as a dep, and it's already 
            //been requested, we need to hand them a new deferred which will
            //fire when the original deferred is fired.
            pomke.trace("Module " + modulePath + " is already imported");
            var d = pomke.Deferred();
            this.importedModules[modulePath].addCallback(function(){d.callback(1)});
            return d;
        } else {
            //Add a deferred to our queue and append the script tag to the dom
            var d = pomke.Deferred();
            this.importedModules[modulePath] = d;
            var s = pomke.createInHead('SCRIPT', {'type':'text/javascript', 
                    'src':this.mkPath(modulePath)});
            //XXX Does this work in all browsers? 
            if(s.addEventListener) {
                s.addEventListener("load", 
                        function(){pomke.mods.moduleImported(modulePath);},
                        false);
            } else {
                s.onreadystatechange = function() {
                    if (this.readyState == "complete" || 
                        this.readyState == "loaded") {
                        pomke.mods.moduleImported(modulePath);
                    }
                }
            }
            return d;
        }
    },

    moduleImported : function(modulePath) {
        pomke.trace('moduleImported:', modulePath);
        //this gets called from the loaded script when the server appends
        //to it, see importModule.
        var def = this.importedModules[modulePath];
        if(def.fired == 1) {
            pomke.log("Already loaded "+modulePath+
                    " once! this shouldn't happen!");
        } else {
            //check if this module has any dependancies and load them 
            //then fire our callback.
            var d = this.loadDepends(modulePath);
            d.addCallback(function(){def.callback(1)});
        }
    }, 

    loadDepends : function(modulePath) {
        pomke.trace('loadDepends', modulePath);
        var def = pomke.Deferred();
        var module = this.modMap[modulePath];
        if(module && module.DEPS.length > 0) {
            //oh we have some deps, lets import those and wait on them:
            pomke.trace('need some deps:', module.DEPS);
            var d = pomke.DeferredList(pomke.map(this.importModule, module.DEPS));
            d.addCallback(function(){def.callback(1)}); //back up the import tree
            d.addCallback(this._callInit, module);
            return def;
        } else if(module) {
            pomke.trace('no deps for this module');
            def.callback(1); //back up the import tree
            this._callInit(module);
            return def;
        } else {
            //either no deps or not even a module! no more to do here.
            pomke.trace('not a module at all');
            def.callback(1);
            return def;
        }
    },
    
    register : function(module) {
        //called from inside the module constructor
        pomke.trace(":: registering module: "+module.NAME+" ::");
        this.modMap[module.NAME] = module;
        if(!this.importedModules[module.NAME]) {
            //This looks like an inline module which is not being 'imported'
            var d = pomke.Deferred();
            this.importedModules[module.NAME] = d;
            window.setTimeout("pomke.mods.moduleImported('"+module.NAME+"')",0);
        }
    },


    dependsOn :  function(/* modName, dep1, dep2, ... */) {
        var mod = this.modMap[arguments[0]];
        var deps = "";
        for(var i=1; i<arguments.length; i++) {
            deps = deps + "," + arguments[i];
            mod.DEPS.push(arguments[i]);
        }
    },

    _callInit : function(module) {
        var callInit = function() {
            pomke.trace(':: init module: '+module.NAME+' ::');
            module.__init__();
        }
        if(typeof(module.__init__) == 'function') {
            if(this.pageLoaded) {
                callInit();
            } else {
                pomke.trace("pending init:", module.NAME);
                this.pendingInit.push(callInit);
            }
        }
    },


    run : function() {
        //called on page load
        this.pageLoaded = true;
        pomke.forEach(function(f){f();}, this.pendingInit);
    }
});

pomke.mods = pomke._ImportManager();

/*  OLD load method
pomke._addEventListener = function(obj, evt, func) {
    if(obj.addEventListener) {
        obj.addEventListener(evt, func, false);
    } else if(obj.attachEvent) {
        obj.attachEvent('on' + evt, func);
    } else {
        var old = obj['on'+evt];
        if(typeof(old) == 'function') {
            func = function(e) { func(e); return old(e); }
        }
        obj['on' + evt] = func;
    }
}

pomke.mods.register(pomke);
pomke._addEventListener(window, 'load', function() {
    // do not capture any DOM nodes in this closure
    pomke.mods.run();
}); 
*/

if ( document.addEventListener ) {
    var e = "DOMContentLoaded";
    document.addEventListener(e, function() {
        document.removeEventListener(e, arguments.callee, false);
        pomke.mods.run();
    }, false);
} else if ( document.attachEvent ) {
    var e = "onreadystatechange";
    document.attachEvent(e, function() {
        if ( document.readyState === "complete" ) {
            document.detachEvent(e, arguments.callee );
            pomke.mods.run();
        }
    });
} 
