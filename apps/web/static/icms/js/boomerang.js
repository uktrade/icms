/*
 * Copyright (c) 2011, Yahoo! Inc.  All rights reserved.
 * Copyright (c) 2012, Log-Normal, Inc.  All rights reserved.
 * Copyright (c) 2014, SOASTA, Inc. All rights reserved.
 * Copyrights licensed under the BSD License. See the accompanying LICENSE.txt file for terms.
 */

/**
\file boomerang.js
boomerang measures various performance characteristics of your user's browsing
experience and beacons it back to your server.

\details
To use this you'll need a web site, lots of users and the ability to do
something with the data you collect.  How you collect the data is up to
you, but we have a few ideas.
*/

// Measure the time the script started
// This has to be global so that we don't wait for the entire
// BOOMR function to download and execute before measuring the
// time.  We also declare it without `var` so that we can later
// `delete` it.  This is the only way that works on Internet Explorer
BOOMR_start = new Date().getTime();

/**
 Check the value of document.domain and fix it if incorrect.
 This function is run at the top of boomerang, and then whenever
 init() is called.  If boomerang is running within an iframe, this
 function checks to see if it can access elements in the parent
 iframe.  If not, it will fudge around with document.domain until
 it finds a value that works.

 This allows customers to change the value of document.domain at
 any point within their page's load process, and we will adapt to
 it.
 */
function BOOMR_check_doc_domain(domain) {
	var test;

	// If domain is not passed in, then this is a global call
	// domain is only passed in if we call ourselves, so we
	// skip the frame check at that point
	if(!domain) {
		// If we're running in the main window, then we don't need this
		if(window.parent === window || !document.getElementById('boomr-if-as')) {
			return true;	// nothing to do
		}

		domain = document.domain;
	}

	if(domain.indexOf(".") === -1) {
		return false;	// not okay, but we did our best
	}

	// 1. Test without setting document.domain
	try {
		test = window.parent.document;
		return test !== undefined;	// all okay
	}
	// 2. Test with document.domain
	catch(err) {
		document.domain = domain;
	}
	try {
		test = window.parent.document;
		return test !== undefined;	// all okay
	}
	// 3. Strip off leading part and try again
	catch(err) {
		domain = domain.replace(/^[\w\-]+\./, '');
	}

	return BOOMR_check_doc_domain(domain);
}

BOOMR_check_doc_domain();


// beaconing section
// the parameter is the window
(function(w) {

var impl, boomr, d, myurl, createCustomEvent;

// This is the only block where we use document without the w. qualifier
if(w.parent !== w
		&& document.getElementById('boomr-if-as')
		&& document.getElementById('boomr-if-as').nodeName.toLowerCase() === 'script') {
	w = w.parent;
	myurl = document.getElementById('boomr-if-as').src;
}

d = w.document;

// Short namespace because I don't want to keep typing BOOMERANG
if(w.BOOMR === undefined) {
	w.BOOMR = {};
}
BOOMR = w.BOOMR;
// don't allow this code to be included twice
if(BOOMR.version) {
	return;
}

BOOMR.version = "0.9";
BOOMR.window = w;

// CustomEvent proxy for IE9 & 10 from https://developer.mozilla.org/en-US/docs/Web/API/CustomEvent
(function() {
	try {
		if (new w.CustomEvent("CustomEvent") !== undefined) {
			createCustomEvent = function (e_name, params) {
				return new w.CustomEvent(e_name, params);
			};
		}
	}
	catch(e) {
		if (d.createEvent) {
			createCustomEvent = function (e_name, params) {
				var evt = d.createEvent( 'CustomEvent' );
				params = params || { cancelable: false, bubbles: false };
				evt.initCustomEvent( e_name, params.bubbles, params.cancelable, params.detail );

				return evt;
			};
		}
		else if (d.createEventObject) {
			createCustomEvent = function (e_name, params) {
				var evt = d.createEventObject();
				evt.type = evt.propertyName = e_name;
				evt.detail = params.detail;

				return evt;
			};
		}
	}
	if(!createCustomEvent) {
		createCustomEvent = function() { return undefined; };
	}
}());

function dispatchEvent(e_name, e_data) {
	var ev = createCustomEvent(e_name, {"detail": e_data});
	if (!ev) {
		return;
	}

	BOOMR.setImmediate(function() {
		if (d.dispatchEvent) {
			d.dispatchEvent(ev);
		}
		else if(d.fireEvent) {
			d.fireEvent("onpropertychange", ev);
		}
	});
}

// impl is a private object not reachable from outside the BOOMR object
// users can set properties by passing in to the init() method
impl = {
	// properties
	beacon_url: "",
	// beacon request method, either GET, POST or AUTO. AUTO will check the
	// request size then use GET if the request URL is less than 2000 chars
	// otherwise it will fall back to a POST request.
	beacon_type: "AUTO",
	// strip out everything except last two parts of hostname.
	// This doesn't work well for domains that end with a country tld,
	// but we allow the developer to override site_domain for that.
	// You can disable all cookies by setting site_domain to a falsy value
	site_domain: w.location.hostname.
				replace(/.*?([^.]+\.[^.]+)\.?$/, '$1').
				toLowerCase(),
	//! User's ip address determined on the server.  Used for the BA cookie
	user_ip: '',

	strip_query_string: false,

	onloadfired: false,

	handlers_attached: false,
	events: {
		"page_ready": [],
		"page_unload": [],
		"dom_loaded": [],
		"visibility_changed": [],
		"before_beacon": [],
		"onbeacon": [],
		"xhr_load": [],
		"click": [],
		"form_submit": []
	},

	public_events: {
		"before_beacon": "onBeforeBoomerangBeacon",
		"onbeacon": "onBoomerangBeacon",
		"onboomerangloaded": "onBoomerangLoaded"
	},

	vars: {},

	errors: {},

	disabled_plugins: {},

	onclick_handler: function(ev) {
		var target;
		if (!ev) { ev = w.event; }
		if (ev.target) { target = ev.target; }
		else if (ev.srcElement) { target = ev.srcElement; }
		if (target.nodeType === 3) {// defeat Safari bug
			target = target.parentNode;
		}

		// don't capture clicks on flash objects
		// because of context slowdowns in PepperFlash
		if(target && target.nodeName.toUpperCase() === "OBJECT" && target.type === "application/x-shockwave-flash") {
			return;
		}
		impl.fireEvent("click", target);
	},

	onsubmit_handler: function(ev) {
		var target;
		if (!ev) { ev = w.event; }
		if (ev.target) { target = ev.target; }
		else if (ev.srcElement) { target = ev.srcElement; }
		if (target.nodeType === 3) {// defeat Safari bug
			target = target.parentNode;
		}

		impl.fireEvent("form_submit", target);
	},

	fireEvent: function(e_name, data) {
		var i, handler, ev;

		e_name = e_name.toLowerCase();

		if(!this.events.hasOwnProperty(e_name)) {
			return false;
		}

		ev = this.events[e_name];

		for(i=0; i<ev.length; i++) {
			try {
				handler = ev[i];
				handler.fn.call(handler.scope, data, handler.cb_data);
			}
			catch(err) {
				BOOMR.addError(err, 'fireEvent');
			}
		}

		if (this.public_events.hasOwnProperty(e_name)) {
			dispatchEvent(this.public_events[e_name], data);
		}

		return true;
	}
};


// We create a boomr object and then copy all its properties to BOOMR so that
// we don't overwrite anything additional that was added to BOOMR before this
// was called... for example, a plugin.
boomr = {
	t_lstart: null,
	t_start: BOOMR_start,
	t_end: null,

	url: myurl,

	// Utility functions
	utils: {
		objectToString: function(o, separator, nest_level) {
			var value = [], k;

			if(!o || typeof o !== "object") {
				return o;
			}
			if(separator === undefined) {
				separator="\n\t";
			}
			if(!nest_level) {
				nest_level=0;
			}

			if (Object.prototype.toString.call(o) === "[object Array]") {
				for(k=0; k<o.length; k++) {
					if (nest_level > 0 && o[k] !== null && typeof o[k] === "object") {
						value.push(
							this.objectToString(
								o[k],
								separator + (separator === "\n\t" ? "\t" : ""),
								nest_level-1
							)
						);
					}
					else {
						value.push(encodeURIComponent(o[k]));
					}
				}
				separator = ",";
			}
			else {
				for(k in o) {
					if(Object.prototype.hasOwnProperty.call(o, k)) {
						if (nest_level > 0 && o[k] !== null && typeof o[k] === "object") {
							value.push(encodeURIComponent(k) + '=' +
								this.objectToString(
									o[k],
									separator + (separator === "\n\t" ? "\t" : ""),
									nest_level-1
								)
							);
						}
						else {
							value.push(encodeURIComponent(k) + '=' + encodeURIComponent(o[k]));
						}
					}
				}
			}

			return value.join(separator);
		},

		getCookie: function(name) {
			if(!name) {
				return null;
			}

			name = ' ' + name + '=';

			var i, cookies;
			cookies = ' ' + d.cookie + ';';
			if ( (i=cookies.indexOf(name)) >= 0 ) {
				i += name.length;
				cookies = cookies.substring(i, cookies.indexOf(';', i));
				return cookies;
			}

			return null;
		},

		setCookie: function(name, subcookies, max_age) {
			var value, nameval, savedval, c, exp;

			if(!name || !impl.site_domain) {
				BOOMR.debug("No cookie name or site domain: " + name + "/" + impl.site_domain);
				return false;
			}

			value = this.objectToString(subcookies, "&");
			nameval = name + '=' + value;

			c = [nameval, "path=/", "domain=" + impl.site_domain];
			if(max_age) {
				exp = new Date();
				exp.setTime(exp.getTime() + max_age*1000);
				exp = exp.toGMTString();
				c.push("expires=" + exp);
			}

			if ( nameval.length < 500 ) {
				d.cookie = c.join('; ');
				// confirm cookie was set (could be blocked by user's settings, etc.)
				savedval = this.getCookie(name);
				if(value === savedval) {
					return true;
				}
				BOOMR.warn("Saved cookie value doesn't match what we tried to set:\n" + value + "\n" + savedval);
			}
			else {
				BOOMR.warn("Cookie too long: " + nameval.length + " " + nameval);
			}

			return false;
		},

		getSubCookies: function(cookie) {
			var cookies_a,
			    i, l, kv,
			    gotcookies=false,
			    cookies={};

			if(!cookie) {
				return null;
			}

			if(typeof cookie !== "string") {
				BOOMR.debug("TypeError: cookie is not a string: " + typeof cookie);
				return null;
			}

			cookies_a = cookie.split('&');

			for(i=0, l=cookies_a.length; i<l; i++) {
				kv = cookies_a[i].split('=');
				if(kv[0]) {
					kv.push("");	// just in case there's no value
					cookies[decodeURIComponent(kv[0])] = decodeURIComponent(kv[1]);
					gotcookies=true;
				}
			}

			return gotcookies ? cookies : null;
		},

		removeCookie: function(name) {
			return this.setCookie(name, {}, -86400);
		},

		cleanupURL: function(url) {
			if (!url) {
				return "";
			}
			if(impl.strip_query_string) {
				return url.replace(/\?.*/, '?qs-redacted');
			}
			return url;
		},

		hashQueryString: function(url, stripHash) {
			if(!url) {
				return url;
			}
			if(url.match(/^\/\//)) {
				url = location.protocol + url;
			}
			if(!url.match(/^(https?|file):/)) {
				BOOMR.error("Passed in URL is invalid: " + url);
				return "";
			}
			if(stripHash) {
				url = url.replace(/#.*/, '');
			}
			if(!BOOMR.utils.MD5) {
				return url;
			}
			return url.replace(/\?([^#]*)/, function(m0, m1) { return '?' + (m1.length > 10 ? BOOMR.utils.MD5(m1) : m1); });
		},

		pluginConfig: function(o, config, plugin_name, properties) {
			var i, props=0;

			if(!config || !config[plugin_name]) {
				return false;
			}

			for(i=0; i<properties.length; i++) {
				if(config[plugin_name][properties[i]] !== undefined) {
					o[properties[i]] = config[plugin_name][properties[i]];
					props++;
				}
			}

			return (props>0);
		},

		addListener: function(el, type, fn) {
			if (el.addEventListener) {
				el.addEventListener(type, fn, false);
			} else {
				el.attachEvent( 'on' + type, fn );
			}
		},

		removeListener: function (el, type, fn) {
			if (el.removeEventListener) {
				el.removeEventListener(type, fn, false);
			} else {
				el.detachEvent('on' + type, fn);
			}
		},

		pushVars: function (arr, vars, prefix) {
			var k, i, n=0;

			for(k in vars) {
				if(vars.hasOwnProperty(k)) {
					if(Object.prototype.toString.call(vars[k]) === "[object Array]") {
						for(i = 0; i < vars[k].length; ++i) {
							n += BOOMR.utils.pushVars(arr, vars[k][i], k + "[" + i + "]");
						}
					} else {
						++n;
						arr.push(
							encodeURIComponent(prefix ? (prefix + "[" + k + "]") : k)
							+ "="
							+ (vars[k]===undefined || vars[k]===null ? '' : encodeURIComponent(vars[k]))
						);
					}
				}
			}

			return n;
		},

		postData: function (urlenc) {
			var iframe = document.createElement("iframe"),
				form = document.createElement("form"),
				input = document.createElement("input");

			iframe.name = "boomerang_post";
			iframe.style.display = form.style.display = "none";

			form.method = "POST";
			form.action = impl.beacon_url;
			form.target = iframe.name;

			input.name = "data";

			if (window.JSON) {
				form.enctype = "text/plain";
				input.value = JSON.stringify(impl.vars);
			} else {
				form.enctype = "application/x-www-form-urlencoded";
				input.value = urlenc;
			}

			document.body.appendChild(iframe);
			form.appendChild(input);
			document.body.appendChild(form);

			BOOMR.utils.addListener(iframe, "load", function() {
				document.body.removeChild(form);
				document.body.removeChild(iframe);
			});

			form.submit();
		}
	},

	init: function(config) {
		var i, k,
		    properties = ["beacon_url", "beacon_type", "site_domain", "user_ip", "strip_query_string"];

		BOOMR_check_doc_domain();

		if(!config) {
			config = {};
		}

		for(i=0; i<properties.length; i++) {
			if(config[properties[i]] !== undefined) {
				impl[properties[i]] = config[properties[i]];
			}
		}

		if(config.log !== undefined) {
			this.log = config.log;
		}
		if(!this.log) {
			this.log = function(/* m,l,s */) { return; };
		}

		for(k in this.plugins) {
			if(this.plugins.hasOwnProperty(k)) {
				// config[plugin].enabled has been set to false
				if( config[k]
					&& config[k].hasOwnProperty("enabled")
					&& config[k].enabled === false
				) {
					impl.disabled_plugins[k] = 1;
					continue;
				}

				// plugin was previously disabled but is now enabled
				if(impl.disabled_plugins[k]) {
					delete impl.disabled_plugins[k];
				}

				// plugin exists and has an init method
				if(typeof this.plugins[k].init === "function") {
					try {
						this.plugins[k].init(config);
					}
					catch(err) {
						BOOMR.addError(err, this.plugins[k] + '.init');
					}
				}
			}
		}

		if(impl.handlers_attached) {
			return this;
		}

		// The developer can override onload by setting autorun to false
		if(!impl.onloadfired && (config.autorun === undefined || config.autorun !== false)) {
			if(d.readyState && d.readyState === "complete") {
				this.setImmediate(BOOMR.page_ready, null, null, BOOMR);
			}
			else {
				if(w.onpagehide || w.onpagehide === null) {
					boomr.utils.addListener(w, "pageshow", BOOMR.page_ready);
				}
				else {
					boomr.utils.addListener(w, "load", BOOMR.page_ready);
				}
			}
		}

		boomr.utils.addListener(w, "DOMContentLoaded", function() { impl.fireEvent("dom_loaded"); });

		(function() {
			var fire_visible, forms, iterator;
			// visibilitychange is useful to detect if the page loaded through prerender
			// or if the page never became visible
			// http://www.w3.org/TR/2011/WD-page-visibility-20110602/
			// http://www.nczonline.net/blog/2011/08/09/introduction-to-the-page-visibility-api/
			fire_visible = function() { impl.fireEvent("visibility_changed"); };
			if(d.webkitVisibilityState) {
				boomr.utils.addListener(d, "webkitvisibilitychange", fire_visible);
			}
			else if(d.msVisibilityState) {
				boomr.utils.addListener(d, "msvisibilitychange", fire_visible);
			}
			else if(d.visibilityState) {
				boomr.utils.addListener(d, "visibilitychange", fire_visible);
			}

			boomr.utils.addListener(d, "mouseup", impl.onclick_handler);

			forms = d.getElementsByTagName("form");
			for(iterator = 0; iterator < forms.length; iterator++) {
				boomr.utils.addListener(forms[iterator], "submit", impl.onsubmit_handler);
			}

			if(!w.onpagehide && w.onpagehide !== null) {
				// This must be the last one to fire
				// We only clear w on browsers that don't support onpagehide because
				// those that do are new enough to not have memory leak problems of
				// some older browsers
				boomr.utils.addListener(w, "unload", function() { BOOMR.window=w=null; });
			}
		}());

		impl.handlers_attached = true;
		return this;
	},

	// The page dev calls this method when they determine the page is usable.
	// Only call this if autorun is explicitly set to false
	page_ready: function(ev) {
		if (!ev) { ev = w.event; }
		if (!ev) { ev = { name: "load" }; }
		if(impl.onloadfired) {
			return this;
		}
		impl.fireEvent("page_ready", ev);
		impl.onloadfired = true;
		return this;
	},

	setImmediate: function(fn, data, cb_data, cb_scope) {
		var cb = function() {
			fn.call(cb_scope || null, data, cb_data || {});
			cb=null;
		};

		if(w.setImmediate) {
			w.setImmediate(cb);
		}
		else if(w.msSetImmediate) {
			w.msSetImmediate(cb);
		}
		else if(w.webkitSetImmediate) {
			w.webkitSetImmediate(cb);
		}
		else if(w.mozSetImmediate) {
			w.mozSetImmediate(cb);
		}
		else {
			setTimeout(cb, 10);
		}
	},

	subscribe: function(e_name, fn, cb_data, cb_scope) {
		var i, handler, ev, unload_handler;

		e_name = e_name.toLowerCase();

		if(!impl.events.hasOwnProperty(e_name)) {
			return this;
		}

		ev = impl.events[e_name];

		// don't allow a handler to be attached more than once to the same event
		for(i=0; i<ev.length; i++) {
			handler = ev[i];
			if(handler.fn === fn && handler.cb_data === cb_data && handler.scope === cb_scope) {
				return this;
			}
		}
		ev.push({ "fn": fn, "cb_data": cb_data || {}, "scope": cb_scope || null });

		// attaching to page_ready after onload fires, so call soon
		if(e_name === 'page_ready' && impl.onloadfired) {
			this.setImmediate(fn, null, cb_data, cb_scope);
		}

		// Attach unload handlers directly to the window.onunload and
		// window.onbeforeunload events. The first of the two to fire will clear
		// fn so that the second doesn't fire. We do this because technically
		// onbeforeunload is the right event to fire, but all browsers don't
		// support it.  This allows us to fall back to onunload when onbeforeunload
		// isn't implemented
		if(e_name === 'page_unload') {
			unload_handler = function(ev) {
							if(fn) {
								fn.call(cb_scope, ev || w.event, cb_data);
							}
						};
			// pagehide is for iOS devices
			// see http://www.webkit.org/blog/516/webkit-page-cache-ii-the-unload-event/
			if(w.onpagehide || w.onpagehide === null) {
				boomr.utils.addListener(w, "pagehide", unload_handler);
			}
			else {
				boomr.utils.addListener(w, "unload", unload_handler);
			}
			boomr.utils.addListener(w, "beforeunload", unload_handler);
		}

		return this;
	},

	addError: function(err, src) {
		if (typeof err !== "string") {
			err = String(err);
		}
		if (src !== undefined) {
			err = "[" + src + "] " + err;
		}

		if (impl.errors[err]) {
			impl.errors[err]++;
		}
		else {
			impl.errors[err] = 1;
		}
	},

	addVar: function(name, value) {
		if(typeof name === "string") {
			impl.vars[name] = value;
		}
		else if(typeof name === "object") {
			var o = name, k;
			for(k in o) {
				if(o.hasOwnProperty(k)) {
					impl.vars[k] = o[k];
				}
			}
		}
		return this;
	},

	removeVar: function(arg0) {
		var i, params;
		if(!arguments.length) {
			return this;
		}

		if(arguments.length === 1
				&& Object.prototype.toString.apply(arg0) === "[object Array]") {
			params = arg0;
		}
		else {
			params = arguments;
		}

		for(i=0; i<params.length; i++) {
			if(impl.vars.hasOwnProperty(params[i])) {
				delete impl.vars[params[i]];
			}
		}

		return this;
	},

	requestStart: function(name) {
		var t_start = new Date().getTime();
		BOOMR.plugins.RT.startTimer("xhr_" + name, t_start);

		return {
			loaded: function(data) {
				BOOMR.responseEnd(name, t_start, data);
			}
		};
	},

	responseEnd: function(name, t_start, data) {
		BOOMR.plugins.RT.startTimer("xhr_" + name, t_start);
		impl.fireEvent("xhr_load", {
			"name": "xhr_" + name,
			"data": data
		});
	},

	sendBeacon: function() {
		var k, data, url, img, nparams, errors=[];

		BOOMR.debug("Checking if we can send beacon");

		// At this point someone is ready to send the beacon.  We send
		// the beacon only if all plugins have finished doing what they
		// wanted to do
		for(k in this.plugins) {
			if(this.plugins.hasOwnProperty(k)) {
				if(impl.disabled_plugins[k]) {
					continue;
				}
				if(!this.plugins[k].is_complete()) {
					BOOMR.debug("Plugin " + k + " is not complete, deferring beacon send");
					return false;
				}
			}
		}

		impl.vars.v = BOOMR.version;
		// use d.URL instead of location.href because of a safari bug
		impl.vars.u = BOOMR.utils.cleanupURL(d.URL.replace(/#.*/, ''));
		if(w !== window) {
			impl.vars["if"] = "";
		}

		for (k in impl.errors) {
			if (impl.errors.hasOwnProperty(k)) {
				errors.push(k + (impl.errors[k] > 1 ? " (*" + impl.errors[k] + ")" : ""));
			}
		}

		if(errors.length > 0) {
			impl.vars.errors = errors.join("\n");
		}

		impl.errors = {};

		// If we reach here, all plugins have completed
		impl.fireEvent("before_beacon", impl.vars);

		// Don't send a beacon if no beacon_url has been set
		// you would do this if you want to do some fancy beacon handling
		// in the `before_beacon` event instead of a simple GET request
		if(!impl.beacon_url) {
			BOOMR.debug("No beacon_url, but would have sent: " + BOOMR.utils.objectToString(impl.vars));
			return true;
		}

		data = [];
		nparams = BOOMR.utils.pushVars(data, impl.vars);

		// If we reach here, we've transferred all vars to the beacon URL.
		this.setImmediate(impl.fireEvent, "onbeacon", impl.vars, impl);

		if(!nparams) {
			// do not make the request if there is no data
			return this;
		}

		data = data.join('&');

		if(impl.beacon_type === 'POST') {
			BOOMR.utils.postData(data);
		} else {
			// if there are already url parameters in the beacon url,
			// change the first parameter prefix for the boomerang url parameters to &
			url = impl.beacon_url + ((impl.beacon_url.indexOf('?') > -1)?'&':'?') + data;

			// using 2000 here as a de facto maximum URL length based on:
			// http://stackoverflow.com/questions/417142/what-is-the-maximum-length-of-a-url-in-different-browsers
			if(url.length > 2000 && impl.beacon_type === "AUTO") {
				BOOMR.utils.postData(data);
			} else {
				BOOMR.debug("Sending url: " + url.replace(/&/g, "\n\t"));
				img = new Image();
				img.src=url;
			}
		}

		return true;
	}

};

delete BOOMR_start;

if(typeof BOOMR_lstart === 'number') {
	boomr.t_lstart = BOOMR_lstart;
	delete BOOMR_lstart;
}
else if(typeof BOOMR.window.BOOMR_lstart === 'number') {
	boomr.t_lstart = BOOMR.window.BOOMR_lstart;
}

(function() {
	var make_logger;

	if(w.YAHOO && w.YAHOO.widget && w.YAHOO.widget.Logger) {
		boomr.log = w.YAHOO.log;
	}
	else if(w.Y && w.Y.log) {
		boomr.log = w.Y.log;
	}
	else if(typeof console === "object" && console.log !== undefined) {
		boomr.log = function(m,l,s) { console.log(s + ": [" + l + "] " + m); };
	}

	make_logger = function(l) {
		return function(m, s) {
			this.log(m, l, "boomerang" + (s?"."+s:""));
			return this;
		};
	};

	boomr.debug = make_logger("debug");
	boomr.info = make_logger("info");
	boomr.warn = make_logger("warn");
	boomr.error = make_logger("error");
}());


(function() {
var ident;
for(ident in boomr) {
	if(boomr.hasOwnProperty(ident)) {
		BOOMR[ident] = boomr[ident];
	}
}
}());

BOOMR.plugins = BOOMR.plugins || {};

dispatchEvent("onBoomerangLoaded", { "BOOMR": BOOMR } );

}(window));

// end of boomerang beaconing section



/*
 * Copyright (c) 2011, Yahoo! Inc.  All rights reserved.
 * Copyright (c) 2012, Log-Normal, Inc.  All rights reserved.
 * Copyrights licensed under the BSD License. See the accompanying LICENSE.txt file for terms.
 */

// This is the Round Trip Time plugin.  Abbreviated to RT
// the parameter is the window
(function(w) {

var d=w.document, impl;

BOOMR = BOOMR || {};
BOOMR.plugins = BOOMR.plugins || {};

// private object
impl = {
	onloadfired: false,	//! Set when the page_ready event fires
				//  Use this to determine if unload fires before onload
	unloadfired: false,	//! Set when the first unload event fires
				//  Use this to make sure we don't beacon twice for beforeunload and unload
	visiblefired: false,	//! Set when page becomes visible (Chrome/IE)
				//  Use this to determine if user bailed without opening the tab
	initialized: false,	//! Set when init has completed to prevent double initialization
	complete: false,	//! Set when this plugin has completed

	timers: {},		//! Custom timers that the developer can use
				// Format for each timer is { start: XXX, end: YYY, delta: YYY-XXX }
	cookie: 'RT',		//! Name of the cookie that stores the start time and referrer
	cookie_exp:600,		//! Cookie expiry in seconds
	strict_referrer: true,	//! By default, don't beacon if referrers don't match.
				// If set to false, beacon both referrer values and let
				// the back end decide

	navigationType: 0,	// Navigation Type from the NavTiming API.  We mainly care if this was BACK_FORWARD
				// since cookie time will be incorrect in that case
	navigationStart: undefined,
	responseStart: undefined,
	t_start: undefined,	// t_start that came off the cookie
	cached_t_start: undefined,	// cached value of t_start once we know its real value
	t_fb_approx: undefined,	// approximate first byte time for browsers that don't support navtiming
	r: undefined,		// referrer from the cookie
	r2: undefined,		// referrer from document.referer

	// These timers are added directly as beacon variables
	basic_timers: { t_done: 1, t_resp: 1, t_page: 1},

	/**
	 * Merge new cookie `params` onto current cookie, and set `timer` param on cookie to current timestamp
	 * @param params object containing keys & values to merge onto current cookie.  A value of `undefined`
	 *		 will remove the key from the cookie
	 * @param timer  string key name that will be set to the current timestamp on the cookie
	 *
	 * @returns true if the cookie was updated, false if the cookie could not be set for any reason
	 */
	updateCookie: function(params, timer) {
		var t_end, t_start, subcookies, k;

		// Disable use of RT cookie by setting its name to a falsy value
		if(!this.cookie) {
			return false;
		}

		subcookies = BOOMR.utils.getSubCookies(BOOMR.utils.getCookie(this.cookie)) || {};

		if (typeof params === "object") {
			for(k in params) {
				if(params.hasOwnProperty(k)) {
					if (params[k] === undefined ) {
						if (subcookies.hasOwnProperty(k)) {
							delete subcookies[k];
						}
					}
					else {
						if (k==="nu" || k==="r") {
							params[k] = BOOMR.utils.hashQueryString(params[k], true);
						}

						subcookies[k] = params[k];
					}
				}
			}
		}

		t_start = new Date().getTime();

		if(timer) {
			subcookies[timer] = t_start;
		}

		BOOMR.debug("Setting cookie (timer=" + timer + ")\n" + BOOMR.utils.objectToString(subcookies), "rt");
		if(!BOOMR.utils.setCookie(this.cookie, subcookies, this.cookie_exp)) {
			BOOMR.error("cannot set start cookie", "rt");
			return false;
		}

		t_end = new Date().getTime();
		if(t_end - t_start > 50) {
			// It took > 50ms to set the cookie
			// The user Most likely has cookie prompting turned on so
			// t_start won't be the actual unload time
			// We bail at this point since we can't reliably tell t_done
			BOOMR.utils.removeCookie(this.cookie);

			// at some point we may want to log this info on the server side
			BOOMR.error("took more than 50ms to set cookie... aborting: "
					+ t_start + " -> " + t_end, "rt");
		}

		return true;
	},

	/**
	 * Read initial values from cookie and clear out cookie values it cares about after reading.
	 * This makes sure that other pages (eg: loaded in new tabs) do not get an invalid cookie time.
	 * This method should only be called from init, and may be called more than once.
	 *
	 * Request start time is the greater of last page beforeunload or last click time
	 * If start time came from a click, we check that the clicked URL matches the current URL
	 * If it came from a beforeunload, we check that cookie referrer matches document.referrer
	 *
	 * If we had a pageHide time or unload time, we use that as a proxy for first byte on non-navtiming
	 * browsers.
	 */
	initFromCookie: function() {
		var url, subcookies;
		subcookies = BOOMR.utils.getSubCookies(BOOMR.utils.getCookie(this.cookie));

		if(!subcookies) {
			return;
		}

		subcookies.s = Math.max(+subcookies.ul||0, +subcookies.cl||0);

		BOOMR.debug("Read from cookie " + BOOMR.utils.objectToString(subcookies), "rt");

		// If we have a start time, and either a referrer, or a clicked on URL,
		// we check if the start time is usable
		if(subcookies.s && (subcookies.r || subcookies.nu)) {
			this.r = subcookies.r;
			url = BOOMR.utils.hashQueryString(d.URL, true);

			// Either the URL of the page setting the cookie needs to match document.referrer
			BOOMR.debug(this.r + " =?= " + this.r2, "rt");

			// Or the start timer was no more than 15ms after a click or form submit
			// and the URL clicked or submitted to matches the current page's URL
			// (note the start timer may be later than click if both click and beforeunload fired
			// on the previous page)
			BOOMR.debug(subcookies.s + " <? " + (+subcookies.cl+15), "rt");
			BOOMR.debug(subcookies.nu + " =?= " + url, "rt");

			if (!this.strict_referrer ||
				(subcookies.nu && subcookies.nu === url && subcookies.s < +subcookies.cl + 15) ||
				(subcookies.s === +subcookies.ul && this.r === this.r2)
			) {
				this.t_start = subcookies.s;

				// additionally, if we have a pagehide, or unload event, that's a proxy
				// for the first byte of the current page, so use that wisely
				if(+subcookies.hd > subcookies.s) {
					this.t_fb_approx = parseInt(subcookies.hd, 10);
				}
			}
			else {
				this.t_start = this.t_fb_approx = undefined;
			}
		}

		// Now that we've pulled out the timers, we'll clear them so they don't pollute future calls
		this.updateCookie({
			s: undefined,	// start timer
			r: undefined,	// referrer
			nu: undefined,	// clicked url
			ul: undefined,	// onbeforeunload time
			cl: undefined,	// onclick time
			hd: undefined	// onunload or onpagehide time
		});
	},

	/**
	 * Figure out how long boomerang and config.js took to load using resource timing if available, or built in timestamps
	 */
	getBoomerangTimings: function() {
		var res, k, urls, url;
		if(BOOMR.t_start) {
			// How long does it take Boomerang to load up and execute (fb to lb)?
			BOOMR.plugins.RT.startTimer('boomerang', BOOMR.t_start);
			BOOMR.plugins.RT.endTimer('boomerang', BOOMR.t_end);	// t_end === null defaults to current time

			// How long did it take from page request to boomerang fb?
			BOOMR.plugins.RT.endTimer('boomr_fb', BOOMR.t_start);

			if(BOOMR.t_lstart) {
				// when did the boomerang loader start loading boomerang on the page?
				BOOMR.plugins.RT.endTimer('boomr_ld', BOOMR.t_lstart);
				// What was the network latency for boomerang (request to first byte)?
				BOOMR.plugins.RT.setTimer('boomr_lat', BOOMR.t_start - BOOMR.t_lstart);
			}
		}

		// use window and not w because we want the inner iframe
		try
		{
			if (window.performance && window.performance.getEntriesByName) {
				urls = { "rt.bmr." : BOOMR.url };

				for(url in urls) {
					if(urls.hasOwnProperty(url) && urls[url]) {
						res = window.performance.getEntriesByName(urls[url]);
						if(!res || res.length === 0) {
							continue;
						}
						res = res[0];

						for(k in res) {
							if(res.hasOwnProperty(k) && k.match(/(Start|End)$/) && res[k] > 0) {
								BOOMR.addVar(url + k.replace(/^(...).*(St|En).*$/, '$1$2'), res[k]);
							}
						}
					}
				}
			}
		}
		catch(e)
		{
			BOOMR.addError(e, 'rt.getBoomerangTimings');
		}
	},

	/**
	 * Check if we're in a prerender state, and if we are, set additional timers.
	 * In Chrome/IE, a prerender state is when a page is completely rendered in an in-memory buffer, before
	 * a user requests that page.  We do not beacon at this point because the user has not shown intent
	 * to view the page.  If the user opens the page, the visibility state changes to visible, and we
	 * fire the beacon at that point, including any timing details for prerendering.
	 *
	 * Sets the `t_load` timer to the actual value of page load time (request initiated by browser to onload)
	 *
	 * @returns true if this is a prerender state, false if not (or not supported)
	 */
	checkPreRender: function() {
		if(
			!(d.visibilityState && d.visibilityState === "prerender")
			&&
			!(d.msVisibilityState && d.msVisibilityState === 3)
		) {
			return false;
		}

		// This means that onload fired through a pre-render.  We'll capture this
		// time, but wait for t_done until after the page has become either visible
		// or hidden (ie, it moved out of the pre-render state)
		// http://code.google.com/chrome/whitepapers/pagevisibility.html
		// http://www.w3.org/TR/2011/WD-page-visibility-20110602/
		// http://code.google.com/chrome/whitepapers/prerender.html

		BOOMR.plugins.RT.startTimer("t_load", this.navigationStart);
		BOOMR.plugins.RT.endTimer("t_load");					// this will measure actual onload time for a prerendered page
		BOOMR.plugins.RT.startTimer("t_prerender", this.navigationStart);
		BOOMR.plugins.RT.startTimer("t_postrender");				// time from prerender to visible or hidden

		BOOMR.subscribe("visibility_changed", BOOMR.plugins.RT.done, "visible", BOOMR.plugins.RT);

		return true;
	},

	/**
	 * Initialise timers from the NavigationTiming API.  This method looks at various sources for
	 * Navigation Timing, and also patches around bugs in various browser implementations.
	 * It sets the beacon parameter `rt.start` to the source of the timer
	 */
	initFromNavTiming: function() {
		var ti, p, source;

		if(this.navigationStart) {
			return;
		}

		// Get start time from WebTiming API see:
		// https://dvcs.w3.org/hg/webperf/raw-file/tip/specs/NavigationTiming/Overview.html
		// http://blogs.msdn.com/b/ie/archive/2010/06/28/measuring-web-page-performance.aspx
		// http://blog.chromium.org/2010/07/do-you-know-how-slow-your-web-page-is.html
		p = w.performance || w.msPerformance || w.webkitPerformance || w.mozPerformance;

		if(p && p.navigation) {
			this.navigationType = p.navigation.type;
		}

		if(p && p.timing) {
			ti = p.timing;
		}
		else if(w.chrome && w.chrome.csi && w.chrome.csi().startE) {
			// Older versions of chrome also have a timing API that's sort of documented here:
			// http://ecmanaut.blogspot.com/2010/06/google-bom-feature-ms-since-pageload.html
			// source here:
			// http://src.chromium.org/viewvc/chrome/trunk/src/chrome/renderer/loadtimes_extension_bindings.cc?view=markup
			ti = {
				navigationStart: w.chrome.csi().startE
			};
			source = "csi";
		}
		else if(w.gtbExternal && w.gtbExternal.startE()) {
			// The Google Toolbar exposes navigation start time similar to old versions of chrome
			// This would work for any browser that has the google toolbar installed
			ti = {
				navigationStart: w.gtbExternal.startE()
			};
			source = 'gtb';
		}

		if(ti) {
			// Always use navigationStart since it falls back to fetchStart (not with redirects)
			// If not set, we leave t_start alone so that timers that depend
			// on it don't get sent back.  Never use requestStart since if
			// the first request fails and the browser retries, it will contain
			// the value for the new request.
			BOOMR.addVar("rt.start", source || "navigation");
			this.navigationStart = ti.navigationStart || ti.fetchStart || undefined;
			this.responseStart = ti.responseStart || undefined;

			// bug in Firefox 7 & 8 https://bugzilla.mozilla.org/show_bug.cgi?id=691547
			if(navigator.userAgent.match(/Firefox\/[78]\./)) {
				this.navigationStart = ti.unloadEventStart || ti.fetchStart || undefined;
			}
		}
		else {
			BOOMR.warn("This browser doesn't support the WebTiming API", "rt");
		}

		return;
	},

	/**
	 * Set timers appropriate at page load time.  This method should be called from done() only when
	 * the page_ready event fires.  It sets the following timer values:
	 *		- t_resp:	time from request start to first byte
	 *		- t_page:	time from first byte to load
	 *		- t_postrender	time from prerender state to visible state
	 *		- t_prerender	time from navigation start to visible state
	 *
	 * @param t_done The timestamp when the done() method was called
	 *
	 * @returns true if timers were set, false if we're in a prerender state, caller should abort on false.
	 */
	setPageLoadTimers: function(t_done) {
		impl.initFromCookie();
		impl.initFromNavTiming();

		if(impl.checkPreRender()) {
			return false;
		}

		if(impl.responseStart) {
			// Use NavTiming API to figure out resp latency and page time
			// t_resp will use the cookie if available or fallback to NavTiming
			BOOMR.plugins.RT.endTimer("t_resp", impl.responseStart);
			if(impl.timers.t_load) {	// t_load is the actual time load completed if using prerender
				BOOMR.plugins.RT.setTimer("t_page", impl.timers.t_load.end - impl.responseStart);
			}
			else {
				BOOMR.plugins.RT.setTimer("t_page", t_done - impl.responseStart);
			}
		}
		else if(impl.timers.hasOwnProperty("t_page")) {
			// If the dev has already started t_page timer, we can end it now as well
			BOOMR.plugins.RT.endTimer("t_page");
		}
		else if(impl.t_fb_approx) {
			BOOMR.plugins.RT.endTimer("t_resp", impl.t_fb_approx);
			BOOMR.plugins.RT.setTimer("t_page", t_done - impl.t_fb_approx);
		}

		// If a prerender timer was started, we can end it now as well
		if(impl.timers.hasOwnProperty("t_postrender")) {
			BOOMR.plugins.RT.endTimer("t_postrender");
			BOOMR.plugins.RT.endTimer("t_prerender");
		}

		return true;
	},

	/**
	 * Writes a bunch of timestamps onto the beacon that help in request tracing on the server
	 * 	- rt.tstart: The value of t_start that we determined was appropriate
	 *	- rt.cstart: The value of t_start from the cookie if different from rt.tstart
	 *	- rt.bstart: The timestamp when boomerang started
	 *	- rt.end:    The timestamp when the t_done timer ended
	 *
	 * @param t_start The value of t_start that we plan to use
	 */
	setSupportingTimestamps: function(t_start) {
		BOOMR.addVar('rt.tstart', t_start);
		if(typeof impl.t_start === 'number' && impl.t_start !== t_start) {
			BOOMR.addVar('rt.cstart', impl.t_start);
		}
		BOOMR.addVar('rt.bstart', BOOMR.t_start);
		if (BOOMR.t_lstart) {
			BOOMR.addVar('rt.blstart', BOOMR.t_lstart);
		}
		BOOMR.addVar('rt.end', impl.timers.t_done.end);	// don't just use t_done because dev may have called endTimer before we did
	},

	/**
	 * Determines the best value to use for t_start.
	 * If called from an xhr call, then use the start time for that call
	 * Else, If we have navigation timing, use that
	 * Else, If we have a cookie time, and this isn't the result of a BACK button, use the cookie time
	 * Else, if we have a cached timestamp from an earlier call, use that
	 * Else, give up
	 *
	 * @param ename	 The event name that resulted in this call. Special consideration for "xhr"
	 * @param pgname If the event name is "xhr", this should be the page group name for the xhr call
	 *
	 * @returns the determined value of t_start or undefined if unknown
	 */
	determineTStart: function(ename, pgname) {
		var t_start;
		if(ename==="xhr" && pgname && impl.timers[pgname]) {
			// For xhr timers, t_start is stored in impl.timers.xhr_{page group name}
			// and xhr.pg is set to {page group name}
			t_start = impl.timers[pgname].start;
			BOOMR.addVar("rt.start", "manual");
		}
		else if(impl.navigationStart) {
			t_start = impl.navigationStart;
		}
		else if(impl.t_start && impl.navigationType !== 2) {
			t_start = impl.t_start;			// 2 is TYPE_BACK_FORWARD but the constant may not be defined across browsers
			BOOMR.addVar("rt.start", "cookie");	// if the user hit the back button, referrer will match, and cookie will match
		}						// but will have time of previous page start, so t_done will be wrong
		else if(impl.cached_t_start) {
			t_start = impl.cached_t_start;
		}
		else {
			BOOMR.addVar("rt.start", "none");
			t_start = undefined;			// force all timers to NaN state
		}

		BOOMR.debug("Got start time: " + t_start, "rt");
		impl.cached_t_start = t_start;

		return t_start;
	},

	page_ready: function() {
		// we need onloadfired because it's possible to reset "impl.complete"
		// if you're measuring multiple xhr loads, but not possible to reset
		// impl.onloadfired
		this.onloadfired = true;
	},

	visibility_changed: function() {
		// we care if the page became visible at some point
		if(!(d.hidden || d.msHidden || d.webkitHidden)) {
			impl.visiblefired = true;
		}
	},

	page_unload: function(edata) {
		BOOMR.debug("Unload called with " + BOOMR.utils.objectToString(edata) + " when unloadfired = " + this.unloadfired, "rt");
		if(!this.unloadfired) {
			// run done on abort or on page_unload to measure session length
			BOOMR.plugins.RT.done(edata, "unload");
		}

		// set cookie for next page
		// We use document.URL instead of location.href because of a bug in safari 4
		// where location.href is URL decoded
		this.updateCookie({ 'r': d.URL }, edata.type === 'beforeunload'?'ul':'hd');

		this.unloadfired = true;
	},

	_iterable_click: function(name, element, etarget, value_cb) {
		var value;
		if(!etarget) {
			return;
		}
		BOOMR.debug(name + " called with " + etarget.nodeName, "rt");
		while(etarget && etarget.nodeName.toUpperCase() !== element) {
			etarget = etarget.parentNode;
		}
		if(etarget && etarget.nodeName.toUpperCase() === element) {
			BOOMR.debug("passing through", "rt");
			// user event, they may be going to another page
			// if this page is being opened in a different tab, then
			// our unload handler won't fire, so we need to set our
			// cookie on click or submit
			value = value_cb(etarget);
			this.updateCookie({ "nu": value }, 'cl' );
			BOOMR.addVar("nu", BOOMR.utils.cleanupURL(value));
		}
	},

	onclick: function(etarget) {
		impl._iterable_click("Click", "A", etarget, function(t) { return t.href; });
	},

	onsubmit: function(etarget) {
		impl._iterable_click("Submit", "FORM", etarget, function(t) { var v = t.action || d.URL; return v.match(/\?/) ? v : v + "?"; });
	},

	domloaded: function() {
		BOOMR.plugins.RT.endTimer("t_domloaded");
	}
};

BOOMR.plugins.RT = {
	// Methods

	init: function(config) {
		BOOMR.debug("init RT", "rt");
		if(w !== BOOMR.window) {
			w = BOOMR.window;
			d = w.document;
		}

		BOOMR.utils.pluginConfig(impl, config, "RT",
					["cookie", "cookie_exp", "strict_referrer"]);

		// A beacon may be fired automatically on page load or if the page dev fires
		// it manually with their own timers.  It may not always contain a referrer
		// (eg: XHR calls).  We set default values for these cases.
		// This is done before reading from the cookie because the cookie overwrites
		// impl.r
		impl.r = impl.r2 = BOOMR.utils.hashQueryString(d.referrer, true);

		// Now pull out start time information from the cookie
		// We'll do this every time init is called, and every time we call it, it will
		// overwrite values already set (provided there are values to read out)
		impl.initFromCookie();

		// We'll get BoomerangTimings every time init is called because it could also
		// include additional timers which might happen on a subsequent init call.
		impl.getBoomerangTimings();

		// only initialize once.  we still collect config and check/set cookies
		// every time init is called, but we attach event handlers only once
		if(impl.initialized) {
			return this;
		}

		impl.complete = false;
		impl.timers = {};

		BOOMR.subscribe("page_ready", impl.page_ready, null, impl);
		impl.visiblefired = !(d.hidden || d.msHidden || d.webkitHidden);
		if(!impl.visiblefired) {
			BOOMR.subscribe("visibility_changed", impl.visibility_changed, null, impl);
		}
		BOOMR.subscribe("page_ready", this.done, "load", this);
		BOOMR.subscribe("xhr_load", this.done, "xhr", this);
		BOOMR.subscribe("dom_loaded", impl.domloaded, null, impl);
		BOOMR.subscribe("page_unload", impl.page_unload, null, impl);
		BOOMR.subscribe("click", impl.onclick, null, impl);
		BOOMR.subscribe("form_submit", impl.onsubmit, null, impl);
		BOOMR.subscribe("before_beacon", this.addTimersToBeacon, "beacon", this);

		impl.initialized = true;
		return this;
	},

	startTimer: function(timer_name, time_value) {
		if(timer_name) {
			if (timer_name === 't_page') {
				this.endTimer('t_resp', time_value);
			}
			impl.timers[timer_name] = {start: (typeof time_value === "number" ? time_value : new Date().getTime())};
		}

		return this;
	},

	endTimer: function(timer_name, time_value) {
		if(timer_name) {
			impl.timers[timer_name] = impl.timers[timer_name] || {};
			if(impl.timers[timer_name].end === undefined) {
				impl.timers[timer_name].end =
						(typeof time_value === "number" ? time_value : new Date().getTime());
			}
		}

		return this;
	},

	setTimer: function(timer_name, time_delta) {
		if(timer_name) {
			impl.timers[timer_name] = { delta: time_delta };
		}

		return this;
	},

	addTimersToBeacon: function(vars, source) {
		var t_name, timer,
		    t_other=[];

		for(t_name in impl.timers) {
			if(impl.timers.hasOwnProperty(t_name)) {
				timer = impl.timers[t_name];

				// if delta is a number, then it was set using setTimer
				// if not, then we have to calculate it using start & end
				if(typeof timer.delta !== "number") {
					if(typeof timer.start !== "number") {
						timer.start = impl.cached_t_start;
					}
					timer.delta = timer.end - timer.start;
				}

				// If the caller did not set a start time, and if there was no start cookie
				// Or if there was no end time for this timer,
				// then timer.delta will be NaN, in which case we discard it.
				if(isNaN(timer.delta)) {
					continue;
				}

				if(impl.basic_timers.hasOwnProperty(t_name)) {
					BOOMR.addVar(t_name, timer.delta);
				}
				else {
					t_other.push(t_name + '|' + timer.delta);
				}
			}
		}

		if (t_other.length) {
			BOOMR.addVar("t_other", t_other.join(','));
		}

		if (source === "beacon") {
			impl.timers = {};
			impl.complete = false;	// reset this state for the next call
		}
	},

	// Called when the page has reached a "usable" state.  This may be when the
	// onload event fires, or it could be at some other moment during/after page
	// load when the page is usable by the user
	done: function(edata, ename) {
		BOOMR.debug("Called done with " + BOOMR.utils.objectToString(edata) + ", " + ename, "rt");
		var t_start, t_done=new Date().getTime(),
		    subresource = false;

		impl.complete = false;

		if(ename==="load" || ename==="visible") {
			if (!impl.setPageLoadTimers(t_done)) {
				return this;
			}
		}

		if(ename === "xhr" && edata && edata.data) {
			subresource = edata.data.subresource;
		}

		t_start = impl.determineTStart(ename, edata ? edata.name : null);

		// If the dev has already called endTimer, then this call will do nothing
		// else, it will stop the page load timer
		this.endTimer("t_done", t_done);

		// make sure old variables don't stick around
		BOOMR.removeVar(
			't_done', 't_page', 't_resp', 't_postrender', 't_prerender', 't_load', 't_other',
			'r', 'r2', 'rt.tstart', 'rt.cstart', 'rt.bstart', 'rt.end', 'rt.subres', 'rt.abld'
		);

		impl.setSupportingTimestamps(t_start);

		this.addTimersToBeacon();

		if(ename !== "xhr") {
			BOOMR.addVar("r", BOOMR.utils.cleanupURL(impl.r));

			if(impl.r2 !== impl.r) {
				BOOMR.addVar("r2", BOOMR.utils.cleanupURL(impl.r2));
			}
		}

		if(subresource) {
			BOOMR.addVar("rt.subres", 1);
		}
		impl.updateCookie();

		if(ename==='unload') {
			BOOMR.addVar('rt.quit', '');

			if(!impl.onloadfired) {
				BOOMR.addVar('rt.abld', '');
			}

			if(!impl.visiblefired) {
				BOOMR.addVar('rt.ntvu', '');
			}
		}

		impl.complete = true;

		BOOMR.sendBeacon();

		return this;
	},

	is_complete: function() { return impl.complete; }

};

}(window));
// End of RT plugin


/*
 * Copyright (c), Buddy Brewer.
 */

/**
\file navtiming.js
Plugin to collect metrics from the W3C Navigation Timing API. For more information about Navigation Timing,
see: http://www.w3.org/TR/navigation-timing/
*/

(function() {

// First make sure BOOMR is actually defined.  It's possible that your plugin is loaded before boomerang, in which case
// you'll need this.
BOOMR = BOOMR || {};
BOOMR.plugins = BOOMR.plugins || {};

// A private object to encapsulate all your implementation details
var impl = {
	complete: false,
	done: function() {
		var w = BOOMR.window, p, pn, pt, data;
		if(this.complete) {
			return this;
		}

		p = w.performance || w.msPerformance || w.webkitPerformance || w.mozPerformance;
		if(p && p.timing && p.navigation) {
			BOOMR.info("This user agent supports NavigationTiming.", "nt");
			pn = p.navigation;
			pt = p.timing;
			data = {
				nt_red_cnt: pn.redirectCount,
				nt_nav_type: pn.type,
				nt_nav_st: pt.navigationStart,
				nt_red_st: pt.redirectStart,
				nt_red_end: pt.redirectEnd,
				nt_fet_st: pt.fetchStart,
				nt_dns_st: pt.domainLookupStart,
				nt_dns_end: pt.domainLookupEnd,
				nt_con_st: pt.connectStart,
				nt_con_end: pt.connectEnd,
				nt_req_st: pt.requestStart,
				nt_res_st: pt.responseStart,
				nt_res_end: pt.responseEnd,
				nt_domloading: pt.domLoading,
				nt_domint: pt.domInteractive,
				nt_domcontloaded_st: pt.domContentLoadedEventStart,
				nt_domcontloaded_end: pt.domContentLoadedEventEnd,
				nt_domcomp: pt.domComplete,
				nt_load_st: pt.loadEventStart,
				nt_load_end: pt.loadEventEnd,
				nt_unload_st: pt.unloadEventStart,
				nt_unload_end: pt.unloadEventEnd
			};
			if (pt.secureConnectionStart) {
				// secureConnectionStart is OPTIONAL in the spec
				data.nt_ssl_st = pt.secureConnectionStart;
			}
			if (pt.msFirstPaint) {
				// msFirstPaint is IE9+ http://msdn.microsoft.com/en-us/library/ff974719
				data.nt_first_paint = pt.msFirstPaint;
			}

			BOOMR.addVar(data);
		}

		// XXX Inconsistency warning.  msFirstPaint above is in milliseconds while
		//     firstPaintTime below is in seconds.microseconds.  The server needs to deal with this.

		// This is Chrome only, so will not overwrite nt_first_paint above
		if(w.chrome && w.chrome.loadTimes) {
			pt = w.chrome.loadTimes();
			if(pt) {
				data = {
					nt_spdy: (pt.wasFetchedViaSpdy?1:0),
					nt_first_paint: pt.firstPaintTime
				};

				BOOMR.addVar(data);
			}
		}

		this.complete = true;
		BOOMR.sendBeacon();
	}
};

BOOMR.plugins.NavigationTiming = {
	init: function() {
		// we'll fire on whichever happens first
		BOOMR.subscribe("page_ready", impl.done, null, impl);
		BOOMR.subscribe("page_unload", impl.done, null, impl);
		return this;
	},

	is_complete: function() {
		return impl.complete;
	}
};

}());

