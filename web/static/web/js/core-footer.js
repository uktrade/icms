/*
 * FOX JS
 *
 * Copyright 2017, Fivium Ltd.
 * Released under the BSD 3-Clause license.
 *
 * Dependencies:
 *   jQuery v1.11
 *   jQuery-FontSpy v3
 *   Tooltipster v4.2.5
 */

// Can be run through JSDoc (https://github.com/jsdoc3/jsdoc) and JSHint (http://www.jshint.com/)

/*jshint laxcomma: true, laxbreak: true, strict: false */

var FOXjs = {
  gPageDisabled: false,
  gPageExpired: false,

  // Store a reason for why the page cannot be submitted
  gBlockSubmitReason: null,

  // Hold timers to clear later
  gTimers: {},

  // Array of client actions
  gClientActionQueue: [],

  /**
   * Get a cookie for a given name
   * @param {string} name The name of the cookie to get
   * @returns {string} The value stored in the cookie
   * @static
   */
  getCookie: function(name) {
    if (document.cookie.length > 0) {
      var begin = document.cookie.indexOf(name + "=");
      if (begin != -1) {
        begin += name.length + 1;
        var end = document.cookie.indexOf(";", begin);
        if (end == -1) {
          end = document.cookie.length;
        }
        return decodeURIComponent(document.cookie.substring(begin, end));
      }
    }
    return null;
  },

  /**
   * Set the value of a cookie, optionally specifying when to expire and a path the cookie should be available on
   * @param {string} name The name of the cookie to set
   * @param {string} value The value of the cookie
   * @param {int} expireDays How many days should the cookie last for
   * @param {string} path The path to scope access to this cookie to
   * @static
   */
  setCookie: function(name, value, expireDays, path) {
    var newCookie = name + "=" + encodeURI(value);
    if (expireDays !== null) {
      var expiresDateTime = new Date();
      expiresDateTime.setTime(expiresDateTime.getTime() + (expireDays * 24 * 3600 * 1000));
      newCookie += "; expires=" + expiresDateTime.toUTCString();
    }
    if (path !== null) {
      newCookie += "; path=" + path;
    }
    document.cookie = newCookie;
  },

  /**
   * Remove a cookie on the current domain which has a given name
   * @param {string} name The name of the cookie to remove
   * @static
   */
  removeCookie: function(name) {
    this.setCookie(name, "", -1, null);
  },

  /**
   * Initialise everything needed for a FOX page e.g. Scroll position, hint icons, calendars...
   * @param {function} successFunction Function to run when a page is successfully initialised
   */
  init: function(successFunction) {
    // Check icon font has loaded
    // Glyphs have to be ones that are more than 1em wide otherwise this doesn't work in IE
    fontSpy("icomoon", {glyphs: "\ue9be\ue90e\ue91b\ue920"});

    // Init sticky panels
    $( document ).ready(function(){$(".sticky").stick_in_parent({parent: '.container'});});

    //https://github.com/leafo/sticky-kit/issues/31
    $('.sticky')
    .on('sticky_kit:bottom', function(e) {
        $(this).parent().css('position', 'static');
    })
    .on('sticky_kit:unbottom', function(e) {
        $(this).parent().css('position', 'relative');
    });

    // Preserve scroll position
    // var scrollPosition = parseInt(document.mainForm.scroll_position.value);
    // if (scrollPosition > 0) {
      // window.scrollTo(0, scrollPosition);
    // }


    // Scroll to first error on the page after submit.
    var error = $("form .error-message");
    if(error.length > 0) {
      var row = error.first().closest('div.row');
      $('html, body').animate({
        scrollTop: (row.offset().top)
      },0);
    }

    // Prevent page presentation caching in browsers that support it
    $(window).on("unload", function () {
      // no body needed
    });

    // Set default properties for hint icons
    $.tooltipster.setDefaults({
      theme: "tooltipster-foxopen",
      contentAsHTML: true,
      delay: 0,
      animationDuration: 100,
      side: "bottom",
      maxWidth: 250
    });

    // Enable hints on focus of elements with hint icons, rather than requiring hovering the icon
    $("[data-hint-id]").on({
      focus: function() {
        $("#" + $(this).data("hint-id")).tooltipster("open");
      },
      blur: function() {
        $("#" + $(this).data("hint-id")).tooltipster("close");
      }
    });

    // Add tooltipster hooks to elements with hints/tooltips
    $(".hint, .tooltip").each(
        function() {
          FOXjs.addHintToTarget(this);
        }
    );

    // Enable autosize on textareas with the autosize data attribute
    $("textarea[data-auto-resize = 'true']").autosize();

    // Limit textarea length in <= IE9
    if (!("maxLength" in document.createElement("textarea"))) {
      $("textarea[maxlength]").on('keyup blur paste drop', function () {
        var that = $(this);
        //setTimeout required so the browser has time to see the pasted value in a paste event
        setTimeout(function() {
          var maxLength = that.attr('maxlength');
          var val = that.val();

          if (val.length > maxLength) {
            that.val(val.slice(0, maxLength));
          }
        }, 0);
      });
    }

    // Initialise the date pickers for fields that need them
    $( ".date-input").not(".date-time-input").not("[readonly='readonly']").datepicker({
      changeMonth: true,
      changeYear: true,
      dateFormat: "dd'-'M'-'yy",
      showButtonPanel: true,
      yearRange: "c-100:c+100"
    });
    $( ".date-time-input" ).not('[readonly="readonly"]').datetimepicker({
      controlType: $.timepicker.textTimeControl,
      changeMonth: true,
      changeYear: true,
      dateFormat: "dd'-'M'-'yy",
      showButtonPanel: true,
      yearRange: "c-100:c+100"
    });
    $( ".date-icon").click(function(){
      var inputId = '#' + $(this).attr("id").replace("icon","");
      if($(inputId).datepicker( "widget" ).is(":visible")) {
        $(inputId).datepicker("hide");
      }
      else {
        $(inputId).datepicker("show");
      }
    });

    // Enable onchange attribute on selectors in a keyboard-accessible way
    this._overrideSelectorOnChange();

    // Enable focussing on tickboxes/radio buttons that have been styled like buttons
    this._enableTickboxButtonFocus();

    // Enable dropdown buttons
    FOXdropdowns.init();

    // Run page scripts or catch erroneous navigation
    // if (!this.isExpired()) {
    //   successFunction();

    //   // Trigger any blocks of code inside a $(document).on('foxReady', function(){ });
    //   $(document).trigger('foxReady');

    //   // Okay to give 'back' nav warning again
    //   this.removeCookie("backWarningGiven_" + document.mainForm.thread_id.value);

    //   this.allowSubmit();
    // }
    // else {
    //   this.erroneousNavigation();
    // }

  },

  /**
   * Add tooltip hint to a target element
   *
   * @param {object} targetElement Element to trigger the tooltip off
   * @param {string} hintContentID Optionally set the ID of the hint content element to make sure it's set on the target
   * @static
   */
  addHintToTarget: function(targetElement, hintContentID) {
    targetElement = $(targetElement);
    if (hintContentID) {
      // make sure the target element has an aria tag pointing to the content
      targetElement.attr('aria-describedby', hintContentID);
    }

    var hintContentElement = $('#' + targetElement.attr("aria-describedby"));
    targetElement.tooltipster({
      functionInit: function(instance, helper){
        instance.content(hintContentElement.html());
      },
      functionReady: function(instance, helper){
        hintContentElement.attr('aria-hidden', false);
      },
      functionAfter: function(instance, helper){
        hintContentElement.attr('aria-hidden', true);
      },
      interactive: (hintContentElement.find('a').length > 0)
    });
  },

  /**
   * Set up selector elements to deal with OnChange events in a more accessible way
   */
  _overrideSelectorOnChange: function() {
    /**
     * Handle onchange event for the selector
     *
     * @param theElement
     * @returns {boolean}
     */
    function selectChanged(theElement) {
      var theSelect;

      if (theElement && theElement.value) {
        theSelect = theElement;
      }
      else {
        theSelect = this;
      }

      // Return false if nothing was noted as being changed and the element wasn't turned into a tagger
      if (theSelect.suppressOnChange || (theSelect.value === theSelect.initValue && !$(theSelect).data('isTagger'))) {
        theSelect.suppressOnChange = false;
        return false;
      }

      // In IE, we get a warning that the form has been submitted twice if we fire the original onchange twice
      // (because selectChange gets triggered by onchange and by selectBlurred) so we set supressOnChange so
      // it doesn't get fired again
      theSelect.suppressOnChange = true;

      theSelect.originalonchange();

      return true;
    }

    /**
     * Handle the focus event by storing the original value so we can test later to see if it actually changed before
     * firing the onchange event
     * @returns {boolean}
     */
    function selectFocused() {
      if(!this.hasOwnProperty('initValue')) {
        this.initValue = this.value;
      }
      return true;
    }

    /**
     * Handle the blur event
     * @returns {boolean}
     */
    function selectBlurred() {
      selectChanged(this);
      return true;
    }

    /**
     * Handle keydown events
     * @param e
     * @returns {boolean}
     */
    function selectKeyed(e) {
      var theEvent;
      var keyCodeTab = 9; // Tab
      var keyCodeEnter = 13; // Enter
      var keyCodeEsc = 27; // Esc


      if (e) {
        theEvent = e;
      }
      else {
        theEvent = event;
      }

      if ((theEvent.keyCode === keyCodeEnter || theEvent.keyCode === keyCodeTab) && this.value !== this.initValue) {
        this.suppressOnChange = false;
        selectChanged(this);
      }
      else if (theEvent.keyCode === keyCodeEsc) {
        this.value = this.initValue;
      }

      this.suppressOnChange = true;

      return true;
    }

    $('select[onchange]').map(function(pIndex, pElement) {
      pElement.originalonchange = pElement.onchange;
      pElement.onfocus = selectFocused;
      pElement.onchange = selectChanged;
      pElement.onkeydown = selectKeyed;
      pElement.onblur = selectBlurred;
    });
  },

  /**
   * For tickboxes and radio buttons that have been styled like buttons, allow focusing on the label and pass the
   * click through to the input
   */
  _enableTickboxButtonFocus: function() {
    $('.button-option-label input').on('focus',function(){
      $(this).attr('tabindex','-1');
      $('label[for='+$(this).attr('id').replace('/','\\/')+']').attr('tabindex','0').focus();
    });

    $('.button-option-label label').on('blur',function(){
      $(this).removeAttr('tabindex');
      $('input[id='+$(this).attr('for').replace('/','\\/')+']').removeAttr('tabindex');
    });

    $('.button-option-label label').on('keydown', function(e){
      //Enter or Space
      if(e.keyCode==13 || e.keyCode==32) {
        $('input[id='+$(this).attr('for').replace('/','\\/')+']').click();
      }
    });
  },

  /**
   * Show an alert with information telling the user that because of their backwards navigation links will not work until
   * they navigate forwards again.
   */
  erroneousNavigation: function() {
    var cookieId = "backWarningGiven_" + document.mainForm.thread_id.value;
    this.setPageExpired(true);
    if (!FOXjs.getCookie(cookieId)) {
      FOXalert.textAlert("<p>To avoid losing data, please don't use your browser's Back button.</p><p>You can read or copy information from this page, but you'll need to go forward again to continue.</p>", {"alertStyle": "warning", "title":"Page expired"});
      // warn only on first back
      FOXjs.setCookie(cookieId, "true", 1, null);
    }
  },

  /**
   * Check to see if the page has "expired"
   * @private
   */
  isExpired: function() {
    // Get the cookie's raw value (decoded from URI encoding)
    var fieldSetCookie = this.getCookie("field_set");
    // Parse into an object
    var fieldSetArray = $.parseJSON(fieldSetCookie);
    // Loop through each item in the array and find the object with a matching thread id
    for(var i = 0; i < fieldSetArray.length; i++){
      // t = thread id, f = field set id
      if(document.mainForm.thread_id.value == fieldSetArray[i].t){
        return (fieldSetArray[i].f != document.mainForm.field_set.value);
      }
    }
    // This thread ID not found in cookie
    return false;
  },

  /**
   * Greys out page and marks it as expired if passed true
   * @param {boolean} isExpired Is the page expired
   * @private
   */
  setPageExpired: function(isExpired) {

    if (isExpired) {
      this.gPageExpired = true;
      $(document.body).addClass("disabled");
    }
    else {
      this.gPageExpired = false;
      $(document.body).removeClass("disabled");
    }
  },

  /**
   * Block out the page and "disable" it if passed true
   * @param {boolean} isDisabled Is the page disabled
   * @protected
   */
  setPageDisabled: function(isDisabled) {
    if (isDisabled == this.gPageDisabled) {
      return;
    }

    if (this.gPageExpired) {
      // Page shouldn't be expired and disabled
      this.setPageExpired(false);
    }

    if (isDisabled) {
      var blockingDiv = document.createElement("div");
      blockingDiv.setAttribute("id", "blocking-div");
      blockingDiv.style.height = document.body.scrollHeight;
      blockingDiv.style.width = document.body.scrollWidth;

      // Dynamically resize blocking div
      $(window).resize(function() {
        blockingDiv.style.height = document.body.scrollHeight;
        blockingDiv.style.width = document.body.scrollWidth;
      });

      document.body.appendChild(blockingDiv);
    }
    else {
      document.body.removeChild(document.getElementById("blocking-div"));
    }

    this.gPageDisabled = isDisabled;
  },

  /**
   * Display optional loading blocker when sending data to update
   * @private
   */
  showUpdating: function() {
    var updatingDiv = $("#updating");

    if (!updatingDiv) {
      // If no loading div on the page ignore this fucntion
      return;
    }

    updatingDiv.show();

    var blankingFrame = $("#iframe-wrapper");
    blankingFrame.show();

    $("img", updatingDiv).each(function() {
          // Update src URLs of images in the updating div so IE continues to run their animation
          this.src = this.src;
        }
    );

    document.body.style.cursor = "wait";

    this.setPageDisabled(true);

    window.setTimeout(function(){
      var closeButton = document.getElementById("updating-close-button");
      closeButton.style.visibility = "visible";
      closeButton.style.display = "block";
    }, 1000*60*5); // 5 minutes
    // Stop resubmission in IE
    if ("activeElement" in document && document.activeElement !== document.body) {
      document.activeElement.blur();
    }
    this.blockSubmit("The page is already loading. Please wait for the page to finish loading before performing further actions.");
  },

  /**
   * Run a server side action. Make sure the main form is up to date and post it.
   * @param {object} options Information about the action to run
   * @param {HTMLElement} [triggerElement] Element used to trigger the action
   */
  action: function(options, triggerElement) {
    var settings = $.extend({
      ref: null,
      ctxt: null,
      confirm: null,
      params: null
    }, options);

    if (settings.ref === null) {
      return; // Can't run an action without reference
    }

    var that = this;
    if (this.isExpired()) {
      // If the page has expired notify them
      var goForwardConfirm = "<p>It looks like you have navigated back to this page using the browser back button.</p> " +
        "<p>You will need to go forward to the most recent page before you can click any links or buttons.</p>" +
        "<p>Click <strong>OK</strong> to be taken to your most recent page.</p>" +
        "<p>Click <strong>Cancel</strong> to remain on this expired page.</p>";

      FOXalert.textConfirm(goForwardConfirm, {title: 'Page expired', alertStyle: 'warning'}, function() { that._expiredPageGoForward(settings); }, null);
    }
    else if (settings.confirm) {
      // Can't run an action if a confirm is defined and not okay'd by the user
      // Note if confirm fails, option widgets (selectors/tickboxes/radios) must be reset to their initial value
      FOXalert.textConfirm(settings.confirm, {}, function() { that._runAction(settings); },  function() { FOXoptions.resetToInitialValue(triggerElement); } );
    }
    else {
      this._runAction(settings);
    }
  },

  _runAction : function(settings) {

    if (this.gBlockSubmitReason !== null) {
      alert(this.gBlockSubmitReason);
    }
    else if (!this.gPageDisabled) {

      //Notify listeners that the form is about to be submitted, giving them a chance to set field values etc
      $(document).trigger('foxBeforeSubmit');

      // If the page is not disabled, set up some values and submit the form
      document.mainForm.scroll_position.value = Math.round($(document).scrollTop());
      document.mainForm.action_name.value = settings.ref;
      document.mainForm.context_ref.value = settings.ctxt;

      // Action params - write to JSON
      document.mainForm.action_params.value = JSON.stringify(settings.params);

      if(this.gClientActionQueue.length > 0) {
        $(document.mainForm).append($("<input type=\"hidden\" name=\"client_actions\"/>"));
        document.mainForm.client_actions.value = JSON.stringify(this.gClientActionQueue);
      }

      // Process HTMLArea code, or anything else pre-submit
      document.mainForm.onsubmit();

      // POST form
      document.mainForm.submit();

      // Show "loading/updating"
      this.showUpdating();
    }
  },

  _expiredPageGoForward : function() {
    // A bit ugly, but worst case scenario is that we go nowhere and user has to use browser forward button
    // If problematic, could add a form POST timeout to make sure users go somewhere

    // IE, Opera will go to top of history stack with this
    // assuming < 999 pages navigated
    for (var b = 999; b > 0; b--) {
      window.history.go(b);
    }

    // Firefox prefers this instead
    for (var f = 1; f <= 999; f++) {
      window.history.go(f);
    }
  },

  /**
   * Open popup windows
   * @param {object} options Information about the window to pop up
   */
  openwin: function(options) {
    var settings = $.extend({
      url: null
      , windowName: ""
      , windowOptions: "default"
      , windowProperties: ""
    }, options);

    if (settings.url) {
      settings.url = settings.url.replace(/&amp;/g,"&");

      switch (settings.windowOptions) {
        case "default":
          window.open(settings.url, settings.windowName, "");
          break;
        case "custom":
          window.open(settings.url, settings.windowName, settings.windowProperties);
          break;
        case "appwin":
          window.open(settings.url, settings.windowName, "toolbar=0,location=0,directories=0,status=1,menubar=0,scrollbars=1,resizable=1,left=0,top=0,width=" + (screen.availWidth-10) + ",height=" + (screen.availHeight-25));
          break;
        case "searchwin":
          window.open(settings.url, "searchwin", "toolbar=0,location=0,directories=0,status=0,menubar=0,scrollbars=1,resizable=0,bgcolor=#003399,width=600,height=700,left=100,top=10");
          break;
        case "filewin":
          window.open(settings.url, "filewin", "toolbar=0,location=0,directories=0,status=0,menubar=0,scrollbars=1,resizable=1,bgcolor=#003399,width=1013,height=680,left=100,top=10");
          break;
        case "refwin":
          window.open(settings.url, "refwin", "toolbar=0,location=0,directories=0,status=0,menubar=0,scrollbars=1,resizable=1,bgcolor=#000066,width=800,height=600,left=100,top=75");
          break;
        case "helpwin":
          window.open(settings.url, "", "toolbar=0,location=0,directories=0,status=0,menubar=0,scrollbars=1,resizable=1,bgcolor=#003399,width=600,height=500,left=100,top=10");
          break;
        case "fullwin":
          window.open(settings.url, settings.windowName, "toolbar=1,location=1,directories=1,status=1,menubar=1,scrollbars=1,resizable=1,width=900,height=700,left=50,top=10");
          break;
        case "flushwin":
          window.open(settings.url, "flushwin", "toolbar=1,location=0,directories=0,status=0,menubar=1,scrollbars=1,resizable=1,width=638,height=105,left=100,top=100");
          break;
        default:
          window.open(settings.url, settings.windowName, "");
      }
    }
  },

  /**
   * Left pad string with paddingCharacter until string is resultLength long
   * @param {string} string String to add padding to
   * @param {string} resultLength Length of the string after padding
   * @param {string} paddingCharacter Character to pad with
   * @return {string} string padded with paddingCharacter until resultLength characters long
   */
  leftPad: function(string, resultLength, paddingCharacter) {
    string = string.toString();
    return string.length < resultLength ? this.leftPad(paddingCharacter + string, resultLength) : string;
  },

  /**
   * Run timer code for elements with a value of MM:SS with a callback at the deadline
   * @param {element} element Input field with a timeout defined in it with the format MM:SS
   * @param {function} callback Function to run after the timeout defined in element
   */
  startTimer: function(element, callback) {
    var that = this;
    this.gTimers[element.attr("id")] = setInterval(function() {
          var lTimeParts = element.val().split(':');
          var lMinutes = parseInt(lTimeParts[0]);
          var lSeconds = parseInt(lTimeParts[1]);
          if (lMinutes === 0 && lSeconds === 0) {
            // Bail out if there's no time on the clock to start with
            clearInterval(that.gTimers[element.attr('id')]);
            return;
          }
          else if (lSeconds === 0) {
            // If no seconds left, decrement the minutes and reset the seconds
            lMinutes--;
            lSeconds = "60";
          }

          lSeconds--;

          element.val(that.leftPad(lMinutes, 2, "0") + ":" + that.leftPad(lSeconds, 2, "0"));

          // If we just got to the deadline, clear this interval and run the action
          if (lMinutes === 0 && lSeconds === 0) {
            clearInterval(that.gTimers[element.attr("id")]);
            callback();
          }
        }
        , 1000);
  },

  /**
   * Mark the page as non-submittable, i.e. no actions should be run, with a reason
   * @param {string} reason Reason why the page cannot be submitted currently
   * @private
   */
  blockSubmit: function(reason) {
    this.gBlockSubmitReason = reason;
  },

  /**
   * Mark the page as submittable, clearing any previous blockage reason
   * @private
   */
  allowSubmit: function() {
    this.gBlockSubmitReason = null;
  },

  /**
   * Move focus to an element with an optional Y offset
   * @param {string} externalFoxId Value of a data-xfid on one or more elements
   * @param {int} yOffset Vertical offset, should you want the page to show information above/below the targeted elements
   */
  focus: function(externalFoxId, yOffset) {
    var lFocusTargets = $("*[data-xfid=" + externalFoxId + "]");
    // Scroll document to focus position
    if(lFocusTargets.offset()) {
      $(document).scrollTop(lFocusTargets.offset().top + yOffset);
    }
    // Attempt to focus a focusable element
    // TODO PN this needs to be aware of element visibility (otherwise IE might have an error)
    var lFocusTargetElement = lFocusTargets.find("input, select, textarea").first();
    if (!lFocusTargetElement.is(":visible")) {
      lFocusTargetElement.triggerHandler('focus');
    }
    else {
      lFocusTargetElement.focus();
    }
  },

  /**
   * Record a client side action with a given actionType for processing by the thread as part of the post data
   * @param {string} actionType
   * @param {string} actionKey
   * @param {object} actionParams
   */
  enqueueClientAction: function(actionType, actionKey, actionParams) {
    this.gClientActionQueue.push({action_type: actionType, action_key: actionKey, action_params: actionParams});
  },

  /**
   * Get all stored client side actions for a given actionType
   * @param actionType
   * @returns {array}
   */
  dequeueClientActions: function(actionType) {
    var lPreservedQueue = [];
    var lDequeuedItems = [];

    while(this.gClientActionQueue.length > 0) {
      // Remove items from the front of the queue
      var lItem = this.gClientActionQueue.splice(0, 1)[0];
      if(lItem.action_type == actionType) {
        lDequeuedItems.push(lItem);
      }
      else {
        lPreservedQueue.push(lItem);
      }
    }

    // Replace the original queue with the preserved queue
    this.gClientActionQueue = lPreservedQueue;

    return lDequeuedItems;
  }
};
var FOXtabs = {
  switchTab: function(pTabGroupKey, pTabKey) {
    // Hide all tab content divs and just show the one with the selected key
    $("div[data-tab-group='" + pTabGroupKey + "']").hide();
    $("div[data-tab-group='" + pTabGroupKey + "'][data-tab-key='" + pTabKey + "']").show();

    // Remove the accessible hidden attribute from all tab content divs and re-apply it to the one with the selected key
    $("div[data-tab-group='" + pTabGroupKey + "']").attr("aria-hidden", "true");
    $("div[data-tab-group='" + pTabGroupKey + "'][data-tab-key='" + pTabKey + "']").attr("aria-hidden", "false");

    // Remove the current-tab class from all tab links and re-apply it to the one with the selected key
    $("ul[data-tab-group='" + pTabGroupKey + "'] > li").removeClass("current-tab");
    $("ul[data-tab-group='" + pTabGroupKey + "'] > li[data-tab-key='" + pTabKey + "']").addClass("current-tab");

    // Remove the accessible selected attribute from all tab links and re-apply it to the one with the selected key
    $("ul[data-tab-group='" + pTabGroupKey + "'] > li").attr("aria-selected", "false");
    $("ul[data-tab-group='" + pTabGroupKey + "'] > li[data-tab-key='" + pTabKey + "']").attr("aria-selected", "true");

    // Set the hidden input field to the selected key
    $("input[data-tab-group='" + pTabGroupKey + "']").val(pTabKey);
  }
};

/*
 Adapted from accessible-modal-dialog by gdkraus: https://github.com/gdkraus/accessible-modal-dialog

 ============================================
 License for Application
 ============================================

 This license is governed by United States copyright law, and with respect to matters
 of tort, contract, and other causes of action it is governed by North Carolina law,
 without regard to North Carolina choice of law provisions.  The forum for any dispute
 resolution shall be in Wake County, North Carolina.

 Redistribution and use in source and binary forms, with or without modification, are
 permitted provided that the following conditions are met:

 1. Redistributions of source code must retain the above copyright notice, this list
 of conditions and the following disclaimer.

 2. Redistributions in binary form must reproduce the above copyright notice, this
 list of conditions and the following disclaimer in the documentation and/or other
 materials provided with the distribution.

 3. The name of the author may not be used to endorse or promote products derived from
 this software without specific prior written permission.

 THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS" AND ANY EXPRESS OR IMPLIED
 WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY
 AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE
 LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
 NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
 ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

 */

AccessibleModal = {
  // jQuery formatted selector to search for focusable items
  focusableElementsString: "a[href], area[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), button:not([disabled]), iframe, object, embed, *[tabindex], *[contenteditable]",

  /**
   * Prevents tab key presses from focusing on elements outside the given object.
   * @param obj {jQuery} Object to prevent tabbing out of (i.e. the modal container)
   * @param evt {event} Keypress event which has fired.
   */
  trapTabKey: function (obj, evt) {
    // get list of all children elements in given object
    var o = obj.find('*');

    // get list of focusable items
    var focusableItems = o.filter(this.focusableElementsString).filter(':visible');

    // get currently focused item
    var focusedItem = jQuery(':focus');

    // get the number of focusable items
    var numberOfFocusableItems = focusableItems.length;

    // get the index of the currently focused item
    var focusedItemIndex = focusableItems.index(focusedItem);

    if (focusedItemIndex == -1 || (!evt.shiftKey && focusedItemIndex == numberOfFocusableItems - 1)) {
      //If focused outside the modal, bring focus to first item
      //Or if tab is pressed without shift, and we are on the last item, wrap around to the first item
      focusableItems.get(0).focus();
      evt.preventDefault();
    }
    else if (evt.shiftKey && focusedItemIndex == 0) {
      //back tab and we're focused on first item - go to the last focusable item
      focusableItems.get(numberOfFocusableItems - 1).focus();
      evt.preventDefault();
    }
  }
};
var FOXmodal = {

  /** Current DisplayedModals, in stack order. */
  modalStack: [],

  /**
   * Handles any initialisation actions which need to be performed if the page has been rendered with a visible modal popover
   * in the HTML.
   */
  _handleWindowLoad: function() {
    var $engineModal = $('#engine-modal-popover');
    if ($engineModal.is(':visible')) {
      this._createDisplayedModal($engineModal, 'engine-internal', false, null);
    }
  },

  /**
   * Gets the modal currently underneath the top modal on the stack, or undefined if the stack contains 1 or 0 modals.
   * @returns {DisplayedModal}
   * @private
   */
  _underTopModal: function () {
    return this.modalStack[this.modalStack.length - 2];
  },

  _keyEventHandler: function(event) {

    if (event.which == 27 && FOXmodal.topModal() && FOXmodal.topModal().escapeAllowed) {
      //Escape key - dismiss top modal if allowed
      FOXmodal.dismissTopModal();
    }
    else if (event.which == 9) {
      //Tab key - prevent tabbing out of modal
      AccessibleModal.trapTabKey(FOXmodal.topModal().$containerDiv, event);
    }
  },

  _registerKeyListeners: function() {
    $(document).on('keydown', this._keyEventHandler);
  },

  _deregisterKeyListeners: function() {
    $(document).off('keydown', this._keyEventHandler);
  },

  /**
   * Constructs a DisplayedModal and adds it onto the stack.
   * @param {jQuery} $modalContainer Div containing the rendered modal.
   * @param {string} modalKey Key for the new modal.
   * @param {boolean} escapeAllowed True if an 'escape' keypress can close the modal.
   * @param {HTMLElement} restoreFocusTo DOM element to restore focus to on modal close.
   * @param {function} closeCallback Callback function to run when the modal is closed.
   */
  _createDisplayedModal: function($modalContainer, modalKey, escapeAllowed, restoreFocusTo, closeCallback) {
    this.modalStack.push(new DisplayedModal($modalContainer, modalKey, escapeAllowed, restoreFocusTo, closeCallback));
    if (this.modalStack.length == 1) {
      $('body').addClass('contains-popover');
      this._registerKeyListeners();
    }

    if (this.modalStack.length > 1) {
      //Ensure the z-index of the top modal is higher than the modal it is over
      this.topModal().$containerDiv.css("z-index", parseInt(this._underTopModal().$containerDiv.css("z-index") + 1));

      //Disallow scrolling in the modal which is now beneath the top modal
      this._underTopModal().$containerDiv.addClass('contains-popover');
    }
  },

  /**
   * Displays a modal popover on the screen, which blocks clicks to underlying content.
   * @param {jQuery} $modalContent jQuery for the container of the popover content. The contents of this target will be copied into a new modal div.
   * @param {string} modalKey Key to identify the new modal, used to prevent the same modal being displayed repeatedly.
   * @param {object} modalOptions Additional options for the modal - title, size, etc.
   * @param {function} closeCallback Callback function to run when the modal is closed. The callback may take an object
   * parameter to be passed from dismissTopModal().
   */
  displayModal: function($modalContent, modalKey, modalOptions, closeCallback) {

    //Short circuit out if there is already a modal with the sanme key in the stack
    var matchingKeys = $.grep(this.modalStack, function(displayedModal) {
      return displayedModal.modalKey === modalKey;
    });
    if (matchingKeys.length > 0) {
      return;
    }

    modalOptions = $.extend({
      title: '',
      cssClass: '',
      size: 'regular',
      dismissAllowed: false,
      escapeAllowed: false,
      ariaRole: 'dialog',
      icon: ''
    }, modalOptions);

    //Note: until we add full Mustache support this must be kept in sync with ModalPopover.mustache
    var $modalContainer = $('<div class="modal-popover-container"><div class="modal-popover"><div class="modal-popover-content"></div></div></div>');

    if (modalOptions.title) {
      $modalContainer.find('.modal-popover-content').append('<h2 id="modal-title-' + modalKey + '">' + modalOptions.title + '</h2>');
      $modalContainer.find('.modal-popover-content').attr('aria-labelledby', 'modal-title-' + modalKey);
      //TODO: aria-describedby, needs to be sensible
    }

    $modalContainer.find('.modal-popover').addClass(modalOptions.size + '-popover').addClass(modalOptions.cssClass);

    //Copy CLONED contents so they are not removed from the DOM when we dimsiss the modal div
    $modalContainer.find('.modal-popover-content').append($modalContent.contents().clone());

    $modalContainer.find('.modal-popover-icon').addClass(modalOptions.icon);

    //Accessibility role
    $modalContainer.find('.modal-popover-content').attr('role', modalOptions.ariaRole);

    //Add new modal container to the start of the page body
    $('body').prepend($modalContainer);

    //Add dismiss icon if client side dismiss is allowed
    if (modalOptions.dismissAllowed) {
      $modalContainer.find('.modal-popover-content').prepend('<div class="icon-cancel-circle modal-dismiss" tabindex="1"></div>');
      var that = this;
      $modalContainer.find('.modal-dismiss').click(function(){
        that.dismissTopModal();
      });
    }

    //Construct tracker object and add to stack
    this._createDisplayedModal($modalContainer, modalKey, modalOptions.escapeAllowed, document.activeElement, closeCallback);
  },

  /**
   * Gets the top modal currently on the stack, or undefined if the stack is empty.
   * @returns {DisplayedModal}
   */
  topModal: function() {
    return this.modalStack[this.modalStack.length - 1];
  },

  /**
   * Dismisses (closes) the top modal.
   * @param {Object} [callbackArgs] Arguments to pass to the callback function.
   */
  dismissTopModal: function(callbackArgs) {

    var topModal =  this.modalStack.pop();

    if(topModal) {
      topModal.$containerDiv.remove(); //Note: this will remove the engine modal div, so will need to be recreated
    }

    if(this.modalStack.length == 0) {
      $('body').removeClass('contains-popover');
      this._deregisterKeyListeners();
    }
    else {
      //Still a modal on the stack, make sure scrolling is now allowed in it
      this.topModal().$containerDiv.removeClass('contains-popover');
    }

    //If we popped a DisplayedModal, run close actions
    if(topModal) {
      //Restore focus to whatever had it before
      if(topModal.restoreFocusTo) {
        var focusTargetElement = $(topModal.restoreFocusTo);
        if (!focusTargetElement.is(":visible")) {
          focusTargetElement.triggerHandler('focus');
        }
        else {
          focusTargetElement.focus();
        }
      }

      //Run close callback function
      if(topModal.closeCallback) {
        topModal.closeCallback(callbackArgs);
      }
    }
  },

  /**
   * Updates the hidden scroll position field to the current scroll position of the internal engine modal, if it is on the stack.
   */
  updateScrollPositionInput: function() {

    for (var i=0; i < this.modalStack.length; i++) {
      if (this.modalStack[i].isInternal) {
        $("input[name='modal_scroll_position']").val(Math.round(this.modalStack[i].$containerDiv.scrollTop()));
      }
    }
  },

  /**
   * Gets the jQuery object containing the currently displayed modal, or undefined if no modal is displayed.
   * @returns {jQuery}
   */
  getCurrentModalContainer: function() {
    return this.topModal().$containerDiv;
  }

};

/**
 * Creates a new DisplayedModal object which can be tracked by the FOXModal stack.
 * @param {jQuery} containerDiv element for the rendered modal
 * @param {string} modalKey key for the new modal.
 * @param {boolean} escapeAllowed True if an 'escape' keypress can close the modal.
 * @param {HTMLElement} restoreFocusTo DOM element to restore focus to on modal close.
 * @param {function} closeCallback Callback function to run when this modal is closed.
 * @constructor
 */
function DisplayedModal(containerDiv, modalKey, escapeAllowed, restoreFocusTo, closeCallback) {

  this.$containerDiv = containerDiv;
  this.modalKey = modalKey;
  this.isInternal = modalKey == 'engine-internal';
  this.escapeAllowed = escapeAllowed;
  this.restoreFocusTo = restoreFocusTo;
  this.closeCallback = closeCallback;

  if (this.isInternal && this.$containerDiv.data('initial-scroll-position')) {
    this.$containerDiv.scrollTop(this.$containerDiv.data('initial-scroll-position'));
    this.lastScrollTop = this.$containerDiv.scrollTop();
  }

  this.$containerDiv.on('scroll', function(e) {
    FOXmodal.topModal().updateDatePickerScrollPosition(e);
  })
}

DisplayedModal.prototype = {
  $containerDiv: null,
  modalKey: null,
  isInternal: false,
  escapeAllowed: false,
  restoreFocusTo: null,
  closeCallback: null,
  lastScrollTop: null,
  updateDatePickerScrollPosition: function(e) {
    var newTop = parseFloat($('#ui-datepicker-div').css('top')) - ( e.target.scrollTop - this.lastScrollTop);
    $('#ui-datepicker-div').css('top', newTop + 'px');
    this.lastScrollTop = e.target.scrollTop;
  }
};

//Modal event listeners

$(document).on('foxBeforeSubmit', function() {
  FOXmodal.updateScrollPositionInput();
});

$(document).ready(function() {
  FOXmodal._handleWindowLoad();
});FOXalert = {

  onLoadAlertQueue: [],

  alertCount: 0,

  /**
   * Gets a jQuery of HTML for an alert close button.
   * @param closePrompt
   * @returns {jQuery}
   * @private
   */
  _getAlertCloseControl: function(closePrompt) {
    return $('<ul class="modal-popover-actions"><li><button class="primary-button alert-dismiss" onclick="FOXmodal.dismissTopModal(); return false;">' + closePrompt + '</button></li></ul>');
  },

  /**
   * Gets a jQuery of HTML for an confirm "OK" and "Cancel" button.
   * @returns {jQuery}
   * @private
   */
  _getConfirmCloseControl: function() {
    return $('<ul class="modal-popover-actions">' +
      '<li><button class="primary-button alert-dismiss" onclick="FOXmodal.dismissTopModal({confirmResult: true}); return false;">OK</button></li>' +
      '<li><button class="link-button" onclick="FOXmodal.dismissTopModal({confirmResult: false}); return false;">Cancel</button></li></ul>');
  },

  /**
   * Gets an object containing styling properties to apply to an alert modal.
   * @param alertStyle Alert style enum.
   * @returns {{cssClass: string, icon: string}}
   * @private
   */
  _getAlertStyleData: function(alertStyle) {

    var result = {cssClass: 'modal-alert-' + alertStyle, icon: ''};

    switch (alertStyle) {
      case 'info':
        result.icon = 'icon-info'; break;
      case 'success':
        result.icon = 'icon-checkmark'; break;
      case 'warning':
        result.icon = 'icon-warning'; break;
      case 'danger':
        result.icon = 'icon-cross'; break;
      case 'confirm':
        result.icon = 'icon-question'; break;
    }

    return result;
  },

  /**
   * Displays an alert using FOXmodal.
   * @param $alertContent Alert content locator.
   * @param alertProperties Modal properties.
   * @param callback Callback to run on alert close.
   * @private
   */
  _displayAlert: function($alertContent, alertProperties, callback) {

    alertProperties = $.extend({
      size: 'small',
      alertStyle: 'normal',
      title: 'Alert',
      ariaRole: 'alertdialog',
      escapeAllowed: true,
      closePrompt: 'OK',
      isConfirm: false
    }, alertProperties);

    var alertKey = 'FOXalert' + (this.alertCount++);

    //Add close controls to the content container
    if (alertProperties.isConfirm) {
      $alertContent.append(this._getConfirmCloseControl());
    }
    else {
      $alertContent.append(this._getAlertCloseControl(alertProperties.closePrompt));
    }

    //Resolve alertStyle enum to icon/CSS classes
    var styleData = this._getAlertStyleData(alertProperties.alertStyle);

    alertProperties.cssClass = (alertProperties.cssClass ? alertProperties.cssClass + ' ' : '') + styleData.cssClass;
    alertProperties.icon = styleData.icon;

    //Show the modal
    FOXmodal.displayModal($alertContent, alertKey, alertProperties, callback);

    //Default focus on close action
    FOXmodal.getCurrentModalContainer().find('.alert-dismiss').focus();
  },

  /**
   * Displays a text-based alert.
   * @param alertText Alert text, which may contain HTML tags.
   * @param alertProperties Additional properties for the alert.
   * @param callback Callback to run on alert close.
   */
  textAlert: function(alertText, alertProperties, callback) {
    this._displayAlert($('<div><div class="modal-popover-icon"></div><div class="modal-popover-text">' + alertText +'</div></div>'), alertProperties, callback);
  },

  /**
   * Displays an alert with the contents of the given buffer.
   * @param $buffer Buffer locator.
   * @param alertProperties Additional properties for the alert.
   * @param callback Callback to run on alert close.
   */
  bufferAlert: function($buffer, alertProperties, callback) {
    this._displayAlert($buffer, alertProperties, callback);
  },

  /**
   * Displays a text-based confirm dialog.
   * @param confirmText Text of the confirm message.
   * @param confirmProperties Properties to pass to alert/modal functions.
   * @param successCallback Callback to run if the user clicks "OK".
   * @param cancelCallback Callback to run if the user clicks "Cancel".
   */
  textConfirm: function(confirmText, confirmProperties, successCallback, cancelCallback) {

    var callback = function(callbackResult) {
      if (callbackResult && callbackResult.confirmResult && successCallback) {
        successCallback();
      }
      else if (callbackResult && !callbackResult.confirmResult && cancelCallback) {
        cancelCallback();
      }
    };

    confirmProperties = $.extend({isConfirm: true, title: '', alertStyle: 'confirm'}, confirmProperties);

    this.textAlert(confirmText, confirmProperties, callback);
  },

  /**
   * Enqueues an alert for display when the page onLoad event fires.
   * @param alertProperties All alert properties, including message and alertType.
   */
  enqueueOnLoadAlert: function(alertProperties) {
    this.onLoadAlertQueue.push(alertProperties);
  },

  /**
   * Displays the next alert in the onLoad queue, if one exists.
   */
  processNextOnLoadAlert: function() {

    var alertProperties = this.onLoadAlertQueue.shift();
    if (alertProperties) {

      var that = this;
      var callback = function() { that.processNextOnLoadAlert(); };

      //Note callback chaining so only one alert is displayed at a time

      switch (alertProperties.alertType) {
        case 'native':
          //Convert newline strings to actual newlines (legacy behaviour migrated from HTML generator escaping logic)
          alert(alertProperties.message.replace(/\\n/g,'\n'));
          this.processNextOnLoadAlert();
          break;
        case 'text':
          this.textAlert(alertProperties.message, alertProperties, callback);
          break;
        case 'buffer':
          this.bufferAlert($('#' + alertProperties.bufferId), alertProperties, callback);
          break;
        default:
          throw 'Unknown alert type ' + alertProperties.alertType;
      }
    }
  }
};

/*
 * FOX Flash
 *
 * Copyright 2016, Fivium Ltd.
 * Released under the BSD 3-Clause license.
 *
 * Dependencies:
 *   jQuery v1.11
 */

// Can be run through JSDoc (https://github.com/jsdoc3/jsdoc) and JSHint (http://www.jshint.com/)

/*jshint laxcomma: true, laxbreak: true, strict: false */

var FOXflash = {

  /**
   * Gets a jQuery pointing to the container div for flash messages, creating it if it doesn't exist.
   * @returns {jQuery}
   * @private
   */
  _$getFlashContainer : function() {
    var container = $('.flash-message');
    if(container.length === 0) {
      container = $('<div class="flash-message"></div>').prependTo($(document.body));
      $('.flash-message').hide();
    }

    return container;
  },

  /**
   * Creates a flash div in the correct location.
   * @param message Message to display - may contain HTML for formatting.
   * @param infoBoxClass CSS classes to set on the div.
   * @private
   */
  _insertFlashHTML : function(message, infoBoxClass) {
    var flashContainer = this._$getFlashContainer();
    flashContainer.append('<div role="alert" class="info-box info-box-' + infoBoxClass + '" tabindex="0">' +
      '<button class="flash-message-close icon-cross" aria-label="Close this message">' +
    '</button>' + message +'</div>');
    flashContainer.find('.flash-message-close').click(function() { $(this).parent().fadeOut(100); });
    flashContainer.delay(200).fadeIn(300);
    // The focus has to happen once the element is visible, 500ms should be when it's fully visible
    setTimeout(function() {
      if ($(document.activeElement).parents('.flash-message').length === 0) {
        // Only focus the first child in the flash message container if the active element isn't already something in the flash message container
        flashContainer.children().first().focus();
      }
    }, 500);
  },

  /**
   * Displays a non-modal, text-based flash message at the top of the screen.
   * @param {string} message Message to display - may contain HTML for formatting.
   * @param {Object} flashProperties Additional properties such as style rules for the flash.
   */
  textFlash : function(message, flashProperties) {
    flashProperties = $.extend({
      displayType : 'info',
      cssClass: ''
    }, flashProperties);

    this._insertFlashHTML(message, flashProperties.displayType + ' ' + flashProperties.cssClass);
  }
};
/**
 * Controls for option widgets (selects, tickboxes, radios, etc)
 */
var FOXoptions = {

  /**
   * Records the initial values for option widgets in data attributes.
   */
  registerInitialValues: function() {
    //Record initial values of option widgets
    $('select, input[type="radio"], input[type="checkbox"]').each(function(i, e) {
      var value;
      var $element = $(e);
      if ($element.is('select')) {
        value = $element.val();
      }
      else {
        value = $element.prop('checked');
      }

      $element.data('fox-initial-value', value);
    });
  },

  /**
   * Resets the given element to its original value recorded in registerInitialValues.
   * @param resetTarget HTMLElement - a radio, tickbox or selector element.
   */
  resetToInitialValue: function(resetTarget) {
    var $target = $(resetTarget);
    if ($target.is('select')) {
      //If the element is a select, reset the value (this may be an array for multi selects)
      $target.val($target.data('fox-initial-value'));
    }
    else if ($target.is('input')) {
      if ($target.attr('type') === 'radio') {
        //Changing one radio will usually change another indirectly so we must reset them all
        $('input[name="' + $target.attr('name') + '"]').each(function (i, e) {
          $(e).prop('checked', $(e).data('fox-initial-value'));
        });
      }
      else if ($target.attr('type') === 'checkbox') {
        //For checkboxes, we only need to reset the current element
        $target.prop('checked', $target.data('fox-initial-value'));
      }
    }
  }
};

$(document).ready(function() { FOXoptions.registerInitialValues(); });
/*
 * FOX Dropdown Buttons
 *
 * Copyright 2017, Fivium Ltd.
 * Released under the BSD 3-Clause license.
 */

// Can be run through JSDoc (https://github.com/jsdoc3/jsdoc) and JSHint (http://www.jshint.com/)

/*jshint laxcomma: true, laxbreak: true, strict: false */
var FOXdropdowns = {

  /**
   * Toggles a dropdown's visiblity
   * @param {object} clickTarget The DOM element (button) that's been clicked
   * @private
   */
  _toggle: function(clickTarget) {
    // Record whether the one that was just clicked was already open, before we collapse them all
    var targetAlreadyExpanded = $(clickTarget).attr('aria-expanded') === 'true';

    // Collapse all dropdowns on page
    FOXdropdowns._hideAll();

    // Open the one that was clicked if it wasn't already open
    if(!targetAlreadyExpanded) {
      $(clickTarget).attr('aria-expanded',  'true');

      // Position the dropdown
      // Reset position first
      var $ul = $(clickTarget).siblings('ul');
      $ul.css('left', $(clickTarget).css('margin-left')).css('right','auto');

      $ul.show();

      var windowWidth = Math.max(document.documentElement.clientWidth, window.innerWidth || 0);
      var ulWidth = parseFloat($ul.css('width'));
      var ulLeft = $ul.offset().left;

      // If the dropdown would go off the right edge of the screen, align it to the right edge of the button
      // instead of the left edge
      if(ulWidth + ulLeft > windowWidth) {
        $ul.css('left','auto').css('right', $(clickTarget).css('margin-right'));
      }

      // Position the dropdown below the bottom of the button
      var newTop = $(clickTarget).height() + parseFloat( $(clickTarget).css('padding-top')) + parseFloat( $(clickTarget).css('padding-bottom')) + 5 + 'px';
      $ul.css('top', newTop);
    }
  },

  /**
   * Hides all dropdown menus on the page
   * @private
   */
  _hideAll: function() {
    $('.dropdown-button').attr('aria-expanded', 'false').siblings('ul').hide();
  },

  /**
   * Initialises event handlers for dropdown buttons
   */
  init: function() {
    $('body').on('click', '.dropdown-button', function(e) {
      FOXdropdowns._toggle(e.target);
    });

    // Hide dropdowns when clicking or focussing anything that's not the currently open dropdown
    $('body').on('click', function(e) {
      // If the click isn't on a dropdown or one of its children (one of the list items), hide all dropdowns
      if($(e.target).closest('.dropdown-menu-out').length === 0) {
        FOXdropdowns._hideAll();
        e.stopPropagation();
      }
    });

    $('body').on('focus', '*', function(e) {
      // If the element with focus isn't inside the currently expanded dropdown, hide all dropdowns
      if($(e.target).closest('.dropdown-menu-out').find('.dropdown-button[aria-expanded=true]').length === 0) {
        FOXdropdowns._hideAll();
        e.stopPropagation();
      }
    });
  }
};
/*jshint laxcomma: true, laxbreak: true, strict: false */

var FOXdownloadBar = {

  showDownloadBar: function (params) {

    this._closeDownloadBar(); // Close in case its already open.
    this._buildDiv(params);

  },

  _buildDiv: function (params) {

    var containerDiv = $('<div id="foxDownloadBar">' +
      '<span id="downloadBarPromptSpan" class="icon-download"> </span>' +
      '</div>');

    if(params.isLocalTargetEnabled === true) {
      var localDownloadButton = $('<button id="downloadBarDownloadButton" class="button small-button icon-download">Download</button>');
      localDownloadButton.click(function () {document.location=params.downloadUrl; FOXdownloadBar. _closeDownloadBar();});
      containerDiv.append(localDownloadButton);
    }
    if(params.isGoogleDriveTargetEnabled === true) {
      var googleDriveButton = $('<button id="downloadBarSaveToDrive" class="button small-button icon-google-drive">Save to Google Drive</button>');
      googleDriveButton.click(function () {FOXdownloadBar._saveToDrive(params);});
      containerDiv.append(googleDriveButton);
    }

    containerDiv.append($('<span id="downloadBarStatusSpan" class="icon-animated-spinner"> </span>'));
    containerDiv.append($('<a id="downloadBarClose" href="#" class="icon-cross" title="Close" aria-label="Close download bar"> </a>'));

    var prompt;
    // Fox defaults to the filename 'file' if no filename was specified in some cases.
    if (!params.fileName || params.fileName === 'file') {
      prompt = 'What do you want to do with this file?';
    }
    else {
      prompt = 'What do you want to do with: ' + params.fileName + '?';
    }

    containerDiv.children('#downloadBarPromptSpan').text(prompt);

    // Return false here to stop the browser scrolling to the top of the page when clicking the a tag.
    containerDiv.children('#downloadBarClose').click( function () {FOXdownloadBar._closeDownloadBar(); return false;});

    $(document.body).append(containerDiv);

  },

  _saveToDrive: function (params) {
    $('#foxDownloadBar').find('> button').attr('disabled', true);
    $('#downloadBarStatusSpan').show().text('Saving to Google Drive');
    GoogleOauthProvider.initGoogleAuthInstance('https://www.googleapis.com/auth/drive.file', function () {FOXdownloadBar._googleAuthCallback(params);});
  },

  _googleAuthCallback: function (params) {

    var targetDownloadUrl = params.downloadUrl;
    var postData = [
      {name: "streamTarget", value: "GOOGLE_DRIVE"},
      {name: "accessToken", value: GoogleOauthProvider.getOauthAccessToken()}
    ];

    $.post(targetDownloadUrl, postData)
      .done(FOXdownloadBar._saveToDriveSuccessCallback)
      .fail(FOXdownloadBar._saveToDriveFailCallback);
  },

  _saveToDriveSuccessCallback: function (data, textStatus, jqXHR) {
    window.open(data, '_blank');
    FOXdownloadBar._closeDownloadBar();
  },

  _saveToDriveFailCallback: function (jqXHR, textStatus, errorThrown) {
    $('#downloadBarPromptSpan').remove();
    $('#foxDownloadBar').find('> button').remove();
    $('#downloadBarStatusSpan').removeClass('icon-animated-spinner').addClass('icon-cross').text('An error occurred when saving the file to Google Drive.');
  },

  _closeDownloadBar: function () {
    $('#foxDownloadBar').remove();
  }

};/*jshint laxcomma: true, laxbreak: true, strict: false */

var GoogleOauthProvider = {

  // The single instance of the google authorisation object. The auth2 can only be initialised once, so we manage the object here.
  _googleAuth: null,
  _clientId: null,

  _setClientId: function (clientId) {
    this._clientId = clientId;
  },

  _initGoogleAPIs: function (scope, callback) {
    var _this = this;
    if(!this.isGoogleDriveApiLoadStarted) {
      this.isGoogleDriveApiLoadStarted = true;
      // Load the Google Oauth APIs
      gapi.load('auth2:picker', {'callback': function () {
        //_this.isGoogleDriveApiLoadComplete = true;
        _this._initGoogleDriveAuth(scope, callback);
      }});
    }
  },

  _initGoogleDriveAuth: function (scope, callback) {
    var _this = this;
    // Initialise the OAuth2 context.
    gapi.auth2.init(
      {
        'client_id': _this._clientId,
        'scope': scope,
        'fetch_basic_profile': false // We don't need their profile information.
      }
    ).then(function () {
      // Set the GoogleAuth object now its been initialised.
      _this._googleAuth = gapi.auth2.getAuthInstance();

      // Request the user to sign in if they are not already
      if(_this._googleAuth.currentUser.get().isSignedIn()) {
        callback();
      }
      else {
        _this._googleAuth.signIn().then(callback);
      }

    }, function (error) {
      // Initialisation can fail if local storage or 3rd party cookies are disabled. The main culprit of this seems to be IE InPrivate mode.
      alert('An error occurred while loading Google Drive. If you are using InPrivate browsing in Internet Explorer, please disable InPrivate mode and load the page again.');
    });

  },

  /**
   * Initialises the Google Auth object instance, running the provided callback function once initialisation is complete.
   * The provided Google scope is guaranteed to be set, although other scopes may also be set.
   *
   * Once this is called, consumers can get an OAuth access token valid for the provided scope for the current user by
   * calling getOauthAccessToken();
   *
   * If initialisation fails the callback is not run.
   *
   * @param scope The scope needing to be authorised.
   * @param callback A function which is run on successful initialisation.
   */
  initGoogleAuthInstance: function (scope, callback) {

    // Check if the auth object is already initialised
    if(this._googleAuth !== null) {

      // Check if the user is logged in
      if(this._googleAuth.currentUser.get().isSignedIn()) {

        // User is logged in. Do they have the requested scope?
        var scopes = this._googleAuth.currentUser.get().getGrantedScopes().split(" ");
        if (scopes.indexOf(scope) > -1) {
          // They have the scope. Nothing needs to be done.
          callback();
        }
        else {
          // User is signed in, but doesn't have that scope. Request the scope
          this._googleAuth.currentUser.get().grant({'scope': scope}).then(callback);
        }
      }
      else {
        // User is not logged in. Sign in and request that scope in case they don't have it
        this._googleAuth.signIn({'scope': scope}).then(callback);
      }

    }
    else {
      // Initialise the auth object
      this._initGoogleAPIs(scope, callback);
    }
  },

  /**
   * Returns an OAuth access token for the current initialised scope(s) authorised by the current user.
   * initGoogleAuthInstance() MUST be called first to specify the required scope before calling this function. It is the
   * consumers responsibility to do this.
   *
   * @returns {string} The OAuth access token.
   */
  getOauthAccessToken: function() {
    return this._googleAuth.currentUser.get().getAuthResponse().access_token;
  }

};
/*! jQuery Timepicker Addon - v1.5.0 - 2014-09-01
 * http://trentrichardson.com/examples/timepicker
 * Copyright (c) 2014 Trent Richardson; Licensed MIT */
(function ($) {

    /*
     * Lets not redefine timepicker, Prevent "Uncaught RangeError: Maximum call stack size exceeded"
     */
    $.ui.timepicker = $.ui.timepicker || {};
    if ($.ui.timepicker.version) {
        return;
    }

    /*
     * Extend jQueryUI, get it started with our version number
     */
    $.extend($.ui, {
        timepicker: {
            version: "1.5.0"
        }
    });

    /*
     * Timepicker manager.
     * Use the singleton instance of this class, $.timepicker, to interact with the time picker.
     * Settings for (groups of) time pickers are maintained in an instance object,
     * allowing multiple different settings on the same page.
     */
    var Timepicker = function () {
        this.regional = []; // Available regional settings, indexed by language code
        this.regional[''] = { // Default regional settings
            currentText: 'Now',
            closeText: 'Done',
            amNames: ['AM', 'A'],
            pmNames: ['PM', 'P'],
            timeFormat: 'HH:mm',
            timeSuffix: '',
            timeOnlyTitle: 'Choose Time',
            timeText: 'Time',
            hourText: 'Hour',
            minuteText: 'Minute',
            secondText: 'Second',
            millisecText: 'Millisecond',
            microsecText: 'Microsecond',
            timezoneText: 'Time Zone',
            isRTL: false
        };
        this._defaults = { // Global defaults for all the datetime picker instances
            showButtonPanel: true,
            timeOnly: false,
            timeOnlyShowDate: false,
            showHour: null,
            showMinute: null,
            showSecond: null,
            showMillisec: null,
            showMicrosec: null,
            showTimezone: null,
            showTime: true,
            stepHour: 1,
            stepMinute: 1,
            stepSecond: 1,
            stepMillisec: 1,
            stepMicrosec: 1,
            hour: 0,
            minute: 0,
            second: 0,
            millisec: 0,
            microsec: 0,
            timezone: null,
            hourMin: 0,
            minuteMin: 0,
            secondMin: 0,
            millisecMin: 0,
            microsecMin: 0,
            hourMax: 23,
            minuteMax: 59,
            secondMax: 59,
            millisecMax: 999,
            microsecMax: 999,
            minDateTime: null,
            maxDateTime: null,
            maxTime: null,
            minTime: null,
            onSelect: null,
            hourGrid: 0,
            minuteGrid: 0,
            secondGrid: 0,
            millisecGrid: 0,
            microsecGrid: 0,
            alwaysSetTime: true,
            separator: ' ',
            altFieldTimeOnly: true,
            altTimeFormat: null,
            altSeparator: null,
            altTimeSuffix: null,
            altRedirectFocus: true,
            pickerTimeFormat: null,
            pickerTimeSuffix: null,
            showTimepicker: true,
            timezoneList: null,
            addSliderAccess: false,
            sliderAccessArgs: null,
            controlType: 'slider',
            defaultValue: null,
            parse: 'strict'
        };
        $.extend(this._defaults, this.regional['']);
    };

    $.extend(Timepicker.prototype, {
        $input: null,
        $altInput: null,
        $timeObj: null,
        inst: null,
        hour_slider: null,
        minute_slider: null,
        second_slider: null,
        millisec_slider: null,
        microsec_slider: null,
        timezone_select: null,
        maxTime: null,
        minTime: null,
        hour: 0,
        minute: 0,
        second: 0,
        millisec: 0,
        microsec: 0,
        timezone: null,
        hourMinOriginal: null,
        minuteMinOriginal: null,
        secondMinOriginal: null,
        millisecMinOriginal: null,
        microsecMinOriginal: null,
        hourMaxOriginal: null,
        minuteMaxOriginal: null,
        secondMaxOriginal: null,
        millisecMaxOriginal: null,
        microsecMaxOriginal: null,
        ampm: '',
        formattedDate: '',
        formattedTime: '',
        formattedDateTime: '',
        timezoneList: null,
        units: ['hour', 'minute', 'second', 'millisec', 'microsec'],
        support: {},
        control: null,

        /*
         * Override the default settings for all instances of the time picker.
         * @param  {Object} settings  object - the new settings to use as defaults (anonymous object)
         * @return {Object} the manager object
         */
        setDefaults: function (settings) {
            extendRemove(this._defaults, settings || {});
            return this;
        },

        /*
         * Create a new Timepicker instance
         */
        _newInst: function ($input, opts) {
            var tp_inst = new Timepicker(),
                inlineSettings = {},
                fns = {},
                overrides, i;

            for (var attrName in this._defaults) {
                if (this._defaults.hasOwnProperty(attrName)) {
                    var attrValue = $input.attr('time:' + attrName);
                    if (attrValue) {
                        try {
                            inlineSettings[attrName] = eval(attrValue);
                        } catch (err) {
                            inlineSettings[attrName] = attrValue;
                        }
                    }
                }
            }

            overrides = {
                beforeShow: function (input, dp_inst) {
                    if ($.isFunction(tp_inst._defaults.evnts.beforeShow)) {
                        return tp_inst._defaults.evnts.beforeShow.call($input[0], input, dp_inst, tp_inst);
                    }
                },
                onChangeMonthYear: function (year, month, dp_inst) {
                    // Update the time as well : this prevents the time from disappearing from the $input field.
                    tp_inst._updateDateTime(dp_inst);
                    if ($.isFunction(tp_inst._defaults.evnts.onChangeMonthYear)) {
                        tp_inst._defaults.evnts.onChangeMonthYear.call($input[0], year, month, dp_inst, tp_inst);
                    }
                },
                onClose: function (dateText, dp_inst) {
                    if (tp_inst.timeDefined === true && $input.val() !== '') {
                        tp_inst._updateDateTime(dp_inst);
                    }
                    if ($.isFunction(tp_inst._defaults.evnts.onClose)) {
                        tp_inst._defaults.evnts.onClose.call($input[0], dateText, dp_inst, tp_inst);
                    }
                }
            };
            for (i in overrides) {
                if (overrides.hasOwnProperty(i)) {
                    fns[i] = opts[i] || null;
                }
            }

            tp_inst._defaults = $.extend({}, this._defaults, inlineSettings, opts, overrides, {
                evnts: fns,
                timepicker: tp_inst // add timepicker as a property of datepicker: $.datepicker._get(dp_inst, 'timepicker');
            });
            tp_inst.amNames = $.map(tp_inst._defaults.amNames, function (val) {
                return val.toUpperCase();
            });
            tp_inst.pmNames = $.map(tp_inst._defaults.pmNames, function (val) {
                return val.toUpperCase();
            });

            // detect which units are supported
            tp_inst.support = detectSupport(
                    tp_inst._defaults.timeFormat +
                    (tp_inst._defaults.pickerTimeFormat ? tp_inst._defaults.pickerTimeFormat : '') +
                    (tp_inst._defaults.altTimeFormat ? tp_inst._defaults.altTimeFormat : ''));

            // controlType is string - key to our this._controls
            if (typeof(tp_inst._defaults.controlType) === 'string') {
                if (tp_inst._defaults.controlType === 'slider' && typeof($.ui.slider) === 'undefined') {
                    tp_inst._defaults.controlType = 'select';
                }
                tp_inst.control = tp_inst._controls[tp_inst._defaults.controlType];
            }
            // controlType is an object and must implement create, options, value methods
            else {
                tp_inst.control = tp_inst._defaults.controlType;
            }

            // prep the timezone options
            var timezoneList = [-720, -660, -600, -570, -540, -480, -420, -360, -300, -270, -240, -210, -180, -120, -60,
                0, 60, 120, 180, 210, 240, 270, 300, 330, 345, 360, 390, 420, 480, 525, 540, 570, 600, 630, 660, 690, 720, 765, 780, 840];
            if (tp_inst._defaults.timezoneList !== null) {
                timezoneList = tp_inst._defaults.timezoneList;
            }
            var tzl = timezoneList.length, tzi = 0, tzv = null;
            if (tzl > 0 && typeof timezoneList[0] !== 'object') {
                for (; tzi < tzl; tzi++) {
                    tzv = timezoneList[tzi];
                    timezoneList[tzi] = { value: tzv, label: $.timepicker.timezoneOffsetString(tzv, tp_inst.support.iso8601) };
                }
            }
            tp_inst._defaults.timezoneList = timezoneList;

            // set the default units
            tp_inst.timezone = tp_inst._defaults.timezone !== null ? $.timepicker.timezoneOffsetNumber(tp_inst._defaults.timezone) :
                ((new Date()).getTimezoneOffset() * -1);
            tp_inst.hour = tp_inst._defaults.hour < tp_inst._defaults.hourMin ? tp_inst._defaults.hourMin :
                    tp_inst._defaults.hour > tp_inst._defaults.hourMax ? tp_inst._defaults.hourMax : tp_inst._defaults.hour;
            tp_inst.minute = tp_inst._defaults.minute < tp_inst._defaults.minuteMin ? tp_inst._defaults.minuteMin :
                    tp_inst._defaults.minute > tp_inst._defaults.minuteMax ? tp_inst._defaults.minuteMax : tp_inst._defaults.minute;
            tp_inst.second = tp_inst._defaults.second < tp_inst._defaults.secondMin ? tp_inst._defaults.secondMin :
                    tp_inst._defaults.second > tp_inst._defaults.secondMax ? tp_inst._defaults.secondMax : tp_inst._defaults.second;
            tp_inst.millisec = tp_inst._defaults.millisec < tp_inst._defaults.millisecMin ? tp_inst._defaults.millisecMin :
                    tp_inst._defaults.millisec > tp_inst._defaults.millisecMax ? tp_inst._defaults.millisecMax : tp_inst._defaults.millisec;
            tp_inst.microsec = tp_inst._defaults.microsec < tp_inst._defaults.microsecMin ? tp_inst._defaults.microsecMin :
                    tp_inst._defaults.microsec > tp_inst._defaults.microsecMax ? tp_inst._defaults.microsecMax : tp_inst._defaults.microsec;
            tp_inst.ampm = '';
            tp_inst.$input = $input;

            if (tp_inst._defaults.altField) {
                tp_inst.$altInput = $(tp_inst._defaults.altField);
                if (tp_inst._defaults.altRedirectFocus === true) {
                    tp_inst.$altInput.css({
                        cursor: 'pointer'
                    }).focus(function () {
                        $input.trigger("focus");
                    });
                }
            }

            if (tp_inst._defaults.minDate === 0 || tp_inst._defaults.minDateTime === 0) {
                tp_inst._defaults.minDate = new Date();
            }
            if (tp_inst._defaults.maxDate === 0 || tp_inst._defaults.maxDateTime === 0) {
                tp_inst._defaults.maxDate = new Date();
            }

            // datepicker needs minDate/maxDate, timepicker needs minDateTime/maxDateTime..
            if (tp_inst._defaults.minDate !== undefined && tp_inst._defaults.minDate instanceof Date) {
                tp_inst._defaults.minDateTime = new Date(tp_inst._defaults.minDate.getTime());
            }
            if (tp_inst._defaults.minDateTime !== undefined && tp_inst._defaults.minDateTime instanceof Date) {
                tp_inst._defaults.minDate = new Date(tp_inst._defaults.minDateTime.getTime());
            }
            if (tp_inst._defaults.maxDate !== undefined && tp_inst._defaults.maxDate instanceof Date) {
                tp_inst._defaults.maxDateTime = new Date(tp_inst._defaults.maxDate.getTime());
            }
            if (tp_inst._defaults.maxDateTime !== undefined && tp_inst._defaults.maxDateTime instanceof Date) {
                tp_inst._defaults.maxDate = new Date(tp_inst._defaults.maxDateTime.getTime());
            }
            tp_inst.$input.bind('focus', function () {
                tp_inst._onFocus();
            });

            return tp_inst;
        },

        /*
         * add our sliders to the calendar
         */
        _addTimePicker: function (dp_inst) {
            var currDT = (this.$altInput && this._defaults.altFieldTimeOnly) ? this.$input.val() + ' ' + this.$altInput.val() : this.$input.val();

            this.timeDefined = this._parseTime(currDT);
            this._limitMinMaxDateTime(dp_inst, false);
            this._injectTimePicker();
        },

        /*
         * parse the time string from input value or _setTime
         */
        _parseTime: function (timeString, withDate) {
            if (!this.inst) {
                this.inst = $.datepicker._getInst(this.$input[0]);
            }

            if (withDate || !this._defaults.timeOnly) {
                var dp_dateFormat = $.datepicker._get(this.inst, 'dateFormat');
                try {
                    var parseRes = parseDateTimeInternal(dp_dateFormat, this._defaults.timeFormat, timeString, $.datepicker._getFormatConfig(this.inst), this._defaults);
                    if (!parseRes.timeObj) {
                        return false;
                    }
                    $.extend(this, parseRes.timeObj);
                } catch (err) {
                    $.timepicker.log("Error parsing the date/time string: " + err +
                        "\ndate/time string = " + timeString +
                        "\ntimeFormat = " + this._defaults.timeFormat +
                        "\ndateFormat = " + dp_dateFormat);
                    return false;
                }
                return true;
            } else {
                var timeObj = $.datepicker.parseTime(this._defaults.timeFormat, timeString, this._defaults);
                if (!timeObj) {
                    return false;
                }
                $.extend(this, timeObj);
                return true;
            }
        },

        /*
         * generate and inject html for timepicker into ui datepicker
         */
        _injectTimePicker: function () {
            var $dp = this.inst.dpDiv,
                o = this.inst.settings,
                tp_inst = this,
                litem = '',
                uitem = '',
                show = null,
                max = {},
                gridSize = {},
                size = null,
                i = 0,
                l = 0;

            // Prevent displaying twice
            if ($dp.find("div.ui-timepicker-div").length === 0 && o.showTimepicker) {
                var noDisplay = ' style="display:none;"',
                    html = '<div class="ui-timepicker-div' + (o.isRTL ? ' ui-timepicker-rtl' : '') + '"><dl>' + '<dt class="ui_tpicker_time_label"' + ((o.showTime) ? '' : noDisplay) + '>' + o.timeText + '</dt>' +
                        '<dd class="ui_tpicker_time"' + ((o.showTime) ? '' : noDisplay) + '></dd>';

                // Create the markup
                for (i = 0, l = this.units.length; i < l; i++) {
                    litem = this.units[i];
                    uitem = litem.substr(0, 1).toUpperCase() + litem.substr(1);
                    show = o['show' + uitem] !== null ? o['show' + uitem] : this.support[litem];

                    // Added by Peter Medeiros:
                    // - Figure out what the hour/minute/second max should be based on the step values.
                    // - Example: if stepMinute is 15, then minMax is 45.
                    max[litem] = parseInt((o[litem + 'Max'] - ((o[litem + 'Max'] - o[litem + 'Min']) % o['step' + uitem])), 10);
                    gridSize[litem] = 0;

                    html += '<dt class="ui_tpicker_' + litem + '_label"' + (show ? '' : noDisplay) + '>' + o[litem + 'Text'] + '</dt>' +
                        '<dd class="ui_tpicker_' + litem + '"><div class="ui_tpicker_' + litem + '_slider"' + (show ? '' : noDisplay) + '></div>';

                    if (show && o[litem + 'Grid'] > 0) {
                        html += '<div style="padding-left: 1px"><table class="ui-tpicker-grid-label"><tr>';

                        if (litem === 'hour') {
                            for (var h = o[litem + 'Min']; h <= max[litem]; h += parseInt(o[litem + 'Grid'], 10)) {
                                gridSize[litem]++;
                                var tmph = $.datepicker.formatTime(this.support.ampm ? 'hht' : 'HH', {hour: h}, o);
                                html += '<td data-for="' + litem + '">' + tmph + '</td>';
                            }
                        }
                        else {
                            for (var m = o[litem + 'Min']; m <= max[litem]; m += parseInt(o[litem + 'Grid'], 10)) {
                                gridSize[litem]++;
                                html += '<td data-for="' + litem + '">' + ((m < 10) ? '0' : '') + m + '</td>';
                            }
                        }

                        html += '</tr></table></div>';
                    }
                    html += '</dd>';
                }

                // Timezone
                var showTz = o.showTimezone !== null ? o.showTimezone : this.support.timezone;
                html += '<dt class="ui_tpicker_timezone_label"' + (showTz ? '' : noDisplay) + '>' + o.timezoneText + '</dt>';
                html += '<dd class="ui_tpicker_timezone" ' + (showTz ? '' : noDisplay) + '></dd>';

                // Create the elements from string
                html += '</dl></div>';
                var $tp = $(html);

                // if we only want time picker...
                if (o.timeOnly === true) {
                    $tp.prepend('<div class="ui-widget-header ui-helper-clearfix ui-corner-all">' + '<div class="ui-datepicker-title">' + o.timeOnlyTitle + '</div>' + '</div>');
                    $dp.find('.ui-datepicker-header, .ui-datepicker-calendar').hide();
                }

                // add sliders, adjust grids, add events
                for (i = 0, l = tp_inst.units.length; i < l; i++) {
                    litem = tp_inst.units[i];
                    uitem = litem.substr(0, 1).toUpperCase() + litem.substr(1);
                    show = o['show' + uitem] !== null ? o['show' + uitem] : this.support[litem];

                    // add the slider
                    tp_inst[litem + '_slider'] = tp_inst.control.create(tp_inst, $tp.find('.ui_tpicker_' + litem + '_slider'), litem, tp_inst[litem], o[litem + 'Min'], max[litem], o['step' + uitem]);

                    // adjust the grid and add click event
                    if (show && o[litem + 'Grid'] > 0) {
                        size = 100 * gridSize[litem] * o[litem + 'Grid'] / (max[litem] - o[litem + 'Min']);
                        $tp.find('.ui_tpicker_' + litem + ' table').css({
                            width: size + "%",
                            marginLeft: o.isRTL ? '0' : ((size / (-2 * gridSize[litem])) + "%"),
                            marginRight: o.isRTL ? ((size / (-2 * gridSize[litem])) + "%") : '0',
                            borderCollapse: 'collapse'
                        }).find("td").click(function (e) {
                            var $t = $(this),
                                h = $t.html(),
                                n = parseInt(h.replace(/[^0-9]/g), 10),
                                ap = h.replace(/[^apm]/ig),
                                f = $t.data('for'); // loses scope, so we use data-for

                            if (f === 'hour') {
                                if (ap.indexOf('p') !== -1 && n < 12) {
                                    n += 12;
                                }
                                else {
                                    if (ap.indexOf('a') !== -1 && n === 12) {
                                        n = 0;
                                    }
                                }
                            }

                            tp_inst.control.value(tp_inst, tp_inst[f + '_slider'], litem, n);

                            tp_inst._onTimeChange();
                            tp_inst._onSelectHandler();
                        }).css({
                            cursor: 'pointer',
                            width: (100 / gridSize[litem]) + '%',
                            textAlign: 'center',
                            overflow: 'hidden'
                        });
                    } // end if grid > 0
                } // end for loop

                // Add timezone options
                this.timezone_select = $tp.find('.ui_tpicker_timezone').append('<select></select>').find("select");
                $.fn.append.apply(this.timezone_select,
                    $.map(o.timezoneList, function (val, idx) {
                        return $("<option />").val(typeof val === "object" ? val.value : val).text(typeof val === "object" ? val.label : val);
                    }));
                if (typeof(this.timezone) !== "undefined" && this.timezone !== null && this.timezone !== "") {
                    var local_timezone = (new Date(this.inst.selectedYear, this.inst.selectedMonth, this.inst.selectedDay, 12)).getTimezoneOffset() * -1;
                    if (local_timezone === this.timezone) {
                        selectLocalTimezone(tp_inst);
                    } else {
                        this.timezone_select.val(this.timezone);
                    }
                } else {
                    if (typeof(this.hour) !== "undefined" && this.hour !== null && this.hour !== "") {
                        this.timezone_select.val(o.timezone);
                    } else {
                        selectLocalTimezone(tp_inst);
                    }
                }
                this.timezone_select.change(function () {
                    tp_inst._onTimeChange();
                    tp_inst._onSelectHandler();
                });
                // End timezone options

                // inject timepicker into datepicker
                var $buttonPanel = $dp.find('.ui-datepicker-buttonpane');
                if ($buttonPanel.length) {
                    $buttonPanel.before($tp);
                } else {
                    $dp.append($tp);
                }

                this.$timeObj = $tp.find('.ui_tpicker_time');

                if (this.inst !== null) {
                    var timeDefined = this.timeDefined;
                    this._onTimeChange();
                    this.timeDefined = timeDefined;
                }

                // slideAccess integration: http://trentrichardson.com/2011/11/11/jquery-ui-sliders-and-touch-accessibility/
                if (this._defaults.addSliderAccess) {
                    var sliderAccessArgs = this._defaults.sliderAccessArgs,
                        rtl = this._defaults.isRTL;
                    sliderAccessArgs.isRTL = rtl;

                    setTimeout(function () { // fix for inline mode
                        if ($tp.find('.ui-slider-access').length === 0) {
                            $tp.find('.ui-slider:visible').sliderAccess(sliderAccessArgs);

                            // fix any grids since sliders are shorter
                            var sliderAccessWidth = $tp.find('.ui-slider-access:eq(0)').outerWidth(true);
                            if (sliderAccessWidth) {
                                $tp.find('table:visible').each(function () {
                                    var $g = $(this),
                                        oldWidth = $g.outerWidth(),
                                        oldMarginLeft = $g.css(rtl ? 'marginRight' : 'marginLeft').toString().replace('%', ''),
                                        newWidth = oldWidth - sliderAccessWidth,
                                        newMarginLeft = ((oldMarginLeft * newWidth) / oldWidth) + '%',
                                        css = { width: newWidth, marginRight: 0, marginLeft: 0 };
                                    css[rtl ? 'marginRight' : 'marginLeft'] = newMarginLeft;
                                    $g.css(css);
                                });
                            }
                        }
                    }, 10);
                }
                // end slideAccess integration

                tp_inst._limitMinMaxDateTime(this.inst, true);
            }
        },

        /*
         * This function tries to limit the ability to go outside the
         * min/max date range
         */
        _limitMinMaxDateTime: function (dp_inst, adjustSliders) {
            var o = this._defaults,
                dp_date = new Date(dp_inst.selectedYear, dp_inst.selectedMonth, dp_inst.selectedDay);

            if (!this._defaults.showTimepicker) {
                return;
            } // No time so nothing to check here

            if ($.datepicker._get(dp_inst, 'minDateTime') !== null && $.datepicker._get(dp_inst, 'minDateTime') !== undefined && dp_date) {
                var minDateTime = $.datepicker._get(dp_inst, 'minDateTime'),
                    minDateTimeDate = new Date(minDateTime.getFullYear(), minDateTime.getMonth(), minDateTime.getDate(), 0, 0, 0, 0);

                if (this.hourMinOriginal === null || this.minuteMinOriginal === null || this.secondMinOriginal === null || this.millisecMinOriginal === null || this.microsecMinOriginal === null) {
                    this.hourMinOriginal = o.hourMin;
                    this.minuteMinOriginal = o.minuteMin;
                    this.secondMinOriginal = o.secondMin;
                    this.millisecMinOriginal = o.millisecMin;
                    this.microsecMinOriginal = o.microsecMin;
                }

                if (dp_inst.settings.timeOnly || minDateTimeDate.getTime() === dp_date.getTime()) {
                    this._defaults.hourMin = minDateTime.getHours();
                    if (this.hour <= this._defaults.hourMin) {
                        this.hour = this._defaults.hourMin;
                        this._defaults.minuteMin = minDateTime.getMinutes();
                        if (this.minute <= this._defaults.minuteMin) {
                            this.minute = this._defaults.minuteMin;
                            this._defaults.secondMin = minDateTime.getSeconds();
                            if (this.second <= this._defaults.secondMin) {
                                this.second = this._defaults.secondMin;
                                this._defaults.millisecMin = minDateTime.getMilliseconds();
                                if (this.millisec <= this._defaults.millisecMin) {
                                    this.millisec = this._defaults.millisecMin;
                                    this._defaults.microsecMin = minDateTime.getMicroseconds();
                                } else {
                                    if (this.microsec < this._defaults.microsecMin) {
                                        this.microsec = this._defaults.microsecMin;
                                    }
                                    this._defaults.microsecMin = this.microsecMinOriginal;
                                }
                            } else {
                                this._defaults.millisecMin = this.millisecMinOriginal;
                                this._defaults.microsecMin = this.microsecMinOriginal;
                            }
                        } else {
                            this._defaults.secondMin = this.secondMinOriginal;
                            this._defaults.millisecMin = this.millisecMinOriginal;
                            this._defaults.microsecMin = this.microsecMinOriginal;
                        }
                    } else {
                        this._defaults.minuteMin = this.minuteMinOriginal;
                        this._defaults.secondMin = this.secondMinOriginal;
                        this._defaults.millisecMin = this.millisecMinOriginal;
                        this._defaults.microsecMin = this.microsecMinOriginal;
                    }
                } else {
                    this._defaults.hourMin = this.hourMinOriginal;
                    this._defaults.minuteMin = this.minuteMinOriginal;
                    this._defaults.secondMin = this.secondMinOriginal;
                    this._defaults.millisecMin = this.millisecMinOriginal;
                    this._defaults.microsecMin = this.microsecMinOriginal;
                }
            }

            if ($.datepicker._get(dp_inst, 'maxDateTime') !== null && $.datepicker._get(dp_inst, 'maxDateTime') !== undefined && dp_date) {
                var maxDateTime = $.datepicker._get(dp_inst, 'maxDateTime'),
                    maxDateTimeDate = new Date(maxDateTime.getFullYear(), maxDateTime.getMonth(), maxDateTime.getDate(), 0, 0, 0, 0);

                if (this.hourMaxOriginal === null || this.minuteMaxOriginal === null || this.secondMaxOriginal === null || this.millisecMaxOriginal === null) {
                    this.hourMaxOriginal = o.hourMax;
                    this.minuteMaxOriginal = o.minuteMax;
                    this.secondMaxOriginal = o.secondMax;
                    this.millisecMaxOriginal = o.millisecMax;
                    this.microsecMaxOriginal = o.microsecMax;
                }

                if (dp_inst.settings.timeOnly || maxDateTimeDate.getTime() === dp_date.getTime()) {
                    this._defaults.hourMax = maxDateTime.getHours();
                    if (this.hour >= this._defaults.hourMax) {
                        this.hour = this._defaults.hourMax;
                        this._defaults.minuteMax = maxDateTime.getMinutes();
                        if (this.minute >= this._defaults.minuteMax) {
                            this.minute = this._defaults.minuteMax;
                            this._defaults.secondMax = maxDateTime.getSeconds();
                            if (this.second >= this._defaults.secondMax) {
                                this.second = this._defaults.secondMax;
                                this._defaults.millisecMax = maxDateTime.getMilliseconds();
                                if (this.millisec >= this._defaults.millisecMax) {
                                    this.millisec = this._defaults.millisecMax;
                                    this._defaults.microsecMax = maxDateTime.getMicroseconds();
                                } else {
                                    if (this.microsec > this._defaults.microsecMax) {
                                        this.microsec = this._defaults.microsecMax;
                                    }
                                    this._defaults.microsecMax = this.microsecMaxOriginal;
                                }
                            } else {
                                this._defaults.millisecMax = this.millisecMaxOriginal;
                                this._defaults.microsecMax = this.microsecMaxOriginal;
                            }
                        } else {
                            this._defaults.secondMax = this.secondMaxOriginal;
                            this._defaults.millisecMax = this.millisecMaxOriginal;
                            this._defaults.microsecMax = this.microsecMaxOriginal;
                        }
                    } else {
                        this._defaults.minuteMax = this.minuteMaxOriginal;
                        this._defaults.secondMax = this.secondMaxOriginal;
                        this._defaults.millisecMax = this.millisecMaxOriginal;
                        this._defaults.microsecMax = this.microsecMaxOriginal;
                    }
                } else {
                    this._defaults.hourMax = this.hourMaxOriginal;
                    this._defaults.minuteMax = this.minuteMaxOriginal;
                    this._defaults.secondMax = this.secondMaxOriginal;
                    this._defaults.millisecMax = this.millisecMaxOriginal;
                    this._defaults.microsecMax = this.microsecMaxOriginal;
                }
            }

            if (dp_inst.settings.minTime!==null) {
                var tempMinTime=new Date("01/01/1970 " + dp_inst.settings.minTime);
                if (this.hour<tempMinTime.getHours()) {
                    this.hour=this._defaults.hourMin=tempMinTime.getHours();
                    this.minute=this._defaults.minuteMin=tempMinTime.getMinutes();
                } else if (this.hour===tempMinTime.getHours() && this.minute<tempMinTime.getMinutes()) {
                    this.minute=this._defaults.minuteMin=tempMinTime.getMinutes();
                } else {
                    if (this._defaults.hourMin<tempMinTime.getHours()) {
                        this._defaults.hourMin=tempMinTime.getHours();
                        this._defaults.minuteMin=tempMinTime.getMinutes();
                    } else if (this._defaults.hourMin===tempMinTime.getHours()===this.hour && this._defaults.minuteMin<tempMinTime.getMinutes()) {
                        this._defaults.minuteMin=tempMinTime.getMinutes();
                    } else {
                        this._defaults.minuteMin=0;
                    }
                }
            }

            if (dp_inst.settings.maxTime!==null) {
                var tempMaxTime=new Date("01/01/1970 " + dp_inst.settings.maxTime);
                if (this.hour>tempMaxTime.getHours()) {
                    this.hour=this._defaults.hourMax=tempMaxTime.getHours();
                    this.minute=this._defaults.minuteMax=tempMaxTime.getMinutes();
                } else if (this.hour===tempMaxTime.getHours() && this.minute>tempMaxTime.getMinutes()) {
                    this.minute=this._defaults.minuteMax=tempMaxTime.getMinutes();
                } else {
                    if (this._defaults.hourMax>tempMaxTime.getHours()) {
                        this._defaults.hourMax=tempMaxTime.getHours();
                        this._defaults.minuteMax=tempMaxTime.getMinutes();
                    } else if (this._defaults.hourMax===tempMaxTime.getHours()===this.hour && this._defaults.minuteMax>tempMaxTime.getMinutes()) {
                        this._defaults.minuteMax=tempMaxTime.getMinutes();
                    } else {
                        this._defaults.minuteMax=59;
                    }
                }
            }

            if (adjustSliders !== undefined && adjustSliders === true) {
                var hourMax = parseInt((this._defaults.hourMax - ((this._defaults.hourMax - this._defaults.hourMin) % this._defaults.stepHour)), 10),
                    minMax = parseInt((this._defaults.minuteMax - ((this._defaults.minuteMax - this._defaults.minuteMin) % this._defaults.stepMinute)), 10),
                    secMax = parseInt((this._defaults.secondMax - ((this._defaults.secondMax - this._defaults.secondMin) % this._defaults.stepSecond)), 10),
                    millisecMax = parseInt((this._defaults.millisecMax - ((this._defaults.millisecMax - this._defaults.millisecMin) % this._defaults.stepMillisec)), 10),
                    microsecMax = parseInt((this._defaults.microsecMax - ((this._defaults.microsecMax - this._defaults.microsecMin) % this._defaults.stepMicrosec)), 10);

                if (this.hour_slider) {
                    this.control.options(this, this.hour_slider, 'hour', { min: this._defaults.hourMin, max: hourMax, step: this._defaults.stepHour });
                    this.control.value(this, this.hour_slider, 'hour', this.hour - (this.hour % this._defaults.stepHour));
                }
                if (this.minute_slider) {
                    this.control.options(this, this.minute_slider, 'minute', { min: this._defaults.minuteMin, max: minMax, step: this._defaults.stepMinute });
                    this.control.value(this, this.minute_slider, 'minute', this.minute - (this.minute % this._defaults.stepMinute));
                }
                if (this.second_slider) {
                    this.control.options(this, this.second_slider, 'second', { min: this._defaults.secondMin, max: secMax, step: this._defaults.stepSecond });
                    this.control.value(this, this.second_slider, 'second', this.second - (this.second % this._defaults.stepSecond));
                }
                if (this.millisec_slider) {
                    this.control.options(this, this.millisec_slider, 'millisec', { min: this._defaults.millisecMin, max: millisecMax, step: this._defaults.stepMillisec });
                    this.control.value(this, this.millisec_slider, 'millisec', this.millisec - (this.millisec % this._defaults.stepMillisec));
                }
                if (this.microsec_slider) {
                    this.control.options(this, this.microsec_slider, 'microsec', { min: this._defaults.microsecMin, max: microsecMax, step: this._defaults.stepMicrosec });
                    this.control.value(this, this.microsec_slider, 'microsec', this.microsec - (this.microsec % this._defaults.stepMicrosec));
                }
            }

        },

        /*
         * when a slider moves, set the internal time...
         * on time change is also called when the time is updated in the text field
         */
        _onTimeChange: function () {
            if (!this._defaults.showTimepicker) {
                return;
            }
            var hour = (this.hour_slider) ? this.control.value(this, this.hour_slider, 'hour') : false,
                minute = (this.minute_slider) ? this.control.value(this, this.minute_slider, 'minute') : false,
                second = (this.second_slider) ? this.control.value(this, this.second_slider, 'second') : false,
                millisec = (this.millisec_slider) ? this.control.value(this, this.millisec_slider, 'millisec') : false,
                microsec = (this.microsec_slider) ? this.control.value(this, this.microsec_slider, 'microsec') : false,
                timezone = (this.timezone_select) ? this.timezone_select.val() : false,
                o = this._defaults,
                pickerTimeFormat = o.pickerTimeFormat || o.timeFormat,
                pickerTimeSuffix = o.pickerTimeSuffix || o.timeSuffix;

            if (typeof(hour) === 'object') {
                hour = false;
            }
            if (typeof(minute) === 'object') {
                minute = false;
            }
            if (typeof(second) === 'object') {
                second = false;
            }
            if (typeof(millisec) === 'object') {
                millisec = false;
            }
            if (typeof(microsec) === 'object') {
                microsec = false;
            }
            if (typeof(timezone) === 'object') {
                timezone = false;
            }

            if (hour !== false) {
                hour = parseInt(hour, 10);
            }
            if (minute !== false) {
                minute = parseInt(minute, 10);
            }
            if (second !== false) {
                second = parseInt(second, 10);
            }
            if (millisec !== false) {
                millisec = parseInt(millisec, 10);
            }
            if (microsec !== false) {
                microsec = parseInt(microsec, 10);
            }
            if (timezone !== false) {
                timezone = timezone.toString();
            }

            var ampm = o[hour < 12 ? 'amNames' : 'pmNames'][0];

            // If the update was done in the input field, the input field should not be updated.
            // If the update was done using the sliders, update the input field.
            var hasChanged = (
                hour !== parseInt(this.hour,10) || // sliders should all be numeric
                minute !== parseInt(this.minute,10) ||
                second !== parseInt(this.second,10) ||
                millisec !== parseInt(this.millisec,10) ||
                microsec !== parseInt(this.microsec,10) ||
                (this.ampm.length > 0 && (hour < 12) !== ($.inArray(this.ampm.toUpperCase(), this.amNames) !== -1)) ||
                (this.timezone !== null && timezone !== this.timezone.toString()) // could be numeric or "EST" format, so use toString()
                );

            if (hasChanged) {

                if (hour !== false) {
                    this.hour = hour;
                }
                if (minute !== false) {
                    this.minute = minute;
                }
                if (second !== false) {
                    this.second = second;
                }
                if (millisec !== false) {
                    this.millisec = millisec;
                }
                if (microsec !== false) {
                    this.microsec = microsec;
                }
                if (timezone !== false) {
                    this.timezone = timezone;
                }

                if (!this.inst) {
                    this.inst = $.datepicker._getInst(this.$input[0]);
                }

                this._limitMinMaxDateTime(this.inst, true);
            }
            if (this.support.ampm) {
                this.ampm = ampm;
            }

            // Updates the time within the timepicker
            this.formattedTime = $.datepicker.formatTime(o.timeFormat, this, o);
            if (this.$timeObj) {
                if (pickerTimeFormat === o.timeFormat) {
                    this.$timeObj.text(this.formattedTime + pickerTimeSuffix);
                }
                else {
                    this.$timeObj.text($.datepicker.formatTime(pickerTimeFormat, this, o) + pickerTimeSuffix);
                }
            }

            this.timeDefined = true;
            if (hasChanged) {
                this._updateDateTime();
                //this.$input.focus(); // may automatically open the picker on setDate
            }
        },

        /*
         * call custom onSelect.
         * bind to sliders slidestop, and grid click.
         */
        _onSelectHandler: function () {
            var onSelect = this._defaults.onSelect || this.inst.settings.onSelect;
            var inputEl = this.$input ? this.$input[0] : null;
            if (onSelect && inputEl) {
                onSelect.apply(inputEl, [this.formattedDateTime, this]);
            }
        },

        /*
         * update our input with the new date time..
         */
        _updateDateTime: function (dp_inst) {
            dp_inst = this.inst || dp_inst;
            var dtTmp = (dp_inst.currentYear > 0?
                    new Date(dp_inst.currentYear, dp_inst.currentMonth, dp_inst.currentDay) :
                    new Date(dp_inst.selectedYear, dp_inst.selectedMonth, dp_inst.selectedDay)),
                dt = $.datepicker._daylightSavingAdjust(dtTmp),
            //dt = $.datepicker._daylightSavingAdjust(new Date(dp_inst.selectedYear, dp_inst.selectedMonth, dp_inst.selectedDay)),
            //dt = $.datepicker._daylightSavingAdjust(new Date(dp_inst.currentYear, dp_inst.currentMonth, dp_inst.currentDay)),
                dateFmt = $.datepicker._get(dp_inst, 'dateFormat'),
                formatCfg = $.datepicker._getFormatConfig(dp_inst),
                timeAvailable = dt !== null && this.timeDefined;
            this.formattedDate = $.datepicker.formatDate(dateFmt, (dt === null ? new Date() : dt), formatCfg);
            var formattedDateTime = this.formattedDate;

            // if a slider was changed but datepicker doesn't have a value yet, set it
            if (dp_inst.lastVal === "") {
                dp_inst.currentYear = dp_inst.selectedYear;
                dp_inst.currentMonth = dp_inst.selectedMonth;
                dp_inst.currentDay = dp_inst.selectedDay;
            }

            /*
             * remove following lines to force every changes in date picker to change the input value
             * Bug descriptions: when an input field has a default value, and click on the field to pop up the date picker.
             * If the user manually empty the value in the input field, the date picker will never change selected value.
             */
            //if (dp_inst.lastVal !== undefined && (dp_inst.lastVal.length > 0 && this.$input.val().length === 0)) {
            //	return;
            //}

            if (this._defaults.timeOnly === true && this._defaults.timeOnlyShowDate === false) {
                formattedDateTime = this.formattedTime;
            } else if ((this._defaults.timeOnly !== true && (this._defaults.alwaysSetTime || timeAvailable)) || (this._defaults.timeOnly === true && this._defaults.timeOnlyShowDate === true)) {
                formattedDateTime += this._defaults.separator + this.formattedTime + this._defaults.timeSuffix;
            }

            this.formattedDateTime = formattedDateTime;

            if (!this._defaults.showTimepicker) {
                this.$input.val(this.formattedDate);
            } else if (this.$altInput && this._defaults.timeOnly === false && this._defaults.altFieldTimeOnly === true) {
                this.$altInput.val(this.formattedTime);
                this.$input.val(this.formattedDate);
            } else if (this.$altInput) {
                this.$input.val(formattedDateTime);
                var altFormattedDateTime = '',
                    altSeparator = this._defaults.altSeparator !== null ? this._defaults.altSeparator : this._defaults.separator,
                    altTimeSuffix = this._defaults.altTimeSuffix !== null ? this._defaults.altTimeSuffix : this._defaults.timeSuffix;

                if (!this._defaults.timeOnly) {
                    if (this._defaults.altFormat) {
                        altFormattedDateTime = $.datepicker.formatDate(this._defaults.altFormat, (dt === null ? new Date() : dt), formatCfg);
                    }
                    else {
                        altFormattedDateTime = this.formattedDate;
                    }

                    if (altFormattedDateTime) {
                        altFormattedDateTime += altSeparator;
                    }
                }

                if (this._defaults.altTimeFormat !== null) {
                    altFormattedDateTime += $.datepicker.formatTime(this._defaults.altTimeFormat, this, this._defaults) + altTimeSuffix;
                }
                else {
                    altFormattedDateTime += this.formattedTime + altTimeSuffix;
                }
                this.$altInput.val(altFormattedDateTime);
            } else {
                this.$input.val(formattedDateTime);
            }

            this.$input.trigger("change");
        },

        _onFocus: function () {
            if (!this.$input.val() && this._defaults.defaultValue) {
                this.$input.val(this._defaults.defaultValue);
                var inst = $.datepicker._getInst(this.$input.get(0)),
                    tp_inst = $.datepicker._get(inst, 'timepicker');
                if (tp_inst) {
                    if (tp_inst._defaults.timeOnly && (inst.input.val() !== inst.lastVal)) {
                        try {
                            $.datepicker._updateDatepicker(inst);
                        } catch (err) {
                            $.timepicker.log(err);
                        }
                    }
                }
            }
        },

        /*
         * Small abstraction to control types
         * We can add more, just be sure to follow the pattern: create, options, value
         */
        _controls: {
            // slider methods
            slider: {
                create: function (tp_inst, obj, unit, val, min, max, step) {
                    var rtl = tp_inst._defaults.isRTL; // if rtl go -60->0 instead of 0->60
                    return obj.prop('slide', null).slider({
                        orientation: "horizontal",
                        value: rtl ? val * -1 : val,
                        min: rtl ? max * -1 : min,
                        max: rtl ? min * -1 : max,
                        step: step,
                        slide: function (event, ui) {
                            tp_inst.control.value(tp_inst, $(this), unit, rtl ? ui.value * -1 : ui.value);
                            tp_inst._onTimeChange();
                        },
                        stop: function (event, ui) {
                            tp_inst._onSelectHandler();
                        }
                    });
                },
                options: function (tp_inst, obj, unit, opts, val) {
                    if (tp_inst._defaults.isRTL) {
                        if (typeof(opts) === 'string') {
                            if (opts === 'min' || opts === 'max') {
                                if (val !== undefined) {
                                    return obj.slider(opts, val * -1);
                                }
                                return Math.abs(obj.slider(opts));
                            }
                            return obj.slider(opts);
                        }
                        var min = opts.min,
                            max = opts.max;
                        opts.min = opts.max = null;
                        if (min !== undefined) {
                            opts.max = min * -1;
                        }
                        if (max !== undefined) {
                            opts.min = max * -1;
                        }
                        return obj.slider(opts);
                    }
                    if (typeof(opts) === 'string' && val !== undefined) {
                        return obj.slider(opts, val);
                    }
                    return obj.slider(opts);
                },
                value: function (tp_inst, obj, unit, val) {
                    if (tp_inst._defaults.isRTL) {
                        if (val !== undefined) {
                            return obj.slider('value', val * -1);
                        }
                        return Math.abs(obj.slider('value'));
                    }
                    if (val !== undefined) {
                        return obj.slider('value', val);
                    }
                    return obj.slider('value');
                }
            },
            // select methods
            select: {
                create: function (tp_inst, obj, unit, val, min, max, step) {
                    var sel = '<select class="ui-timepicker-select ui-state-default ui-corner-all" data-unit="' + unit + '" data-min="' + min + '" data-max="' + max + '" data-step="' + step + '">',
                        format = tp_inst._defaults.pickerTimeFormat || tp_inst._defaults.timeFormat;

                    for (var i = min; i <= max; i += step) {
                        sel += '<option value="' + i + '"' + (i === val ? ' selected' : '') + '>';
                        if (unit === 'hour') {
                            sel += $.datepicker.formatTime($.trim(format.replace(/[^ht ]/ig, '')), {hour: i}, tp_inst._defaults);
                        }
                        else if (unit === 'millisec' || unit === 'microsec' || i >= 10) { sel += i; }
                        else {sel += '0' + i.toString(); }
                        sel += '</option>';
                    }
                    sel += '</select>';

                    obj.children('select').remove();

                    $(sel).appendTo(obj).change(function (e) {
                        tp_inst._onTimeChange();
                        tp_inst._onSelectHandler();
                    });

                    return obj;
                },
                options: function (tp_inst, obj, unit, opts, val) {
                    var o = {},
                        $t = obj.children('select');
                    if (typeof(opts) === 'string') {
                        if (val === undefined) {
                            return $t.data(opts);
                        }
                        o[opts] = val;
                    }
                    else { o = opts; }
                    return tp_inst.control.create(tp_inst, obj, $t.data('unit'), $t.val(), o.min || $t.data('min'), o.max || $t.data('max'), o.step || $t.data('step'));
                },
                value: function (tp_inst, obj, unit, val) {
                    var $t = obj.children('select');
                    if (val !== undefined) {
                        return $t.val(val);
                    }
                    return $t.val();
                }
            }
        } // end _controls

    });

    $.fn.extend({
        /*
         * shorthand just to use timepicker.
         */
        timepicker: function (o) {
            o = o || {};
            var tmp_args = Array.prototype.slice.call(arguments);

            if (typeof o === 'object') {
                tmp_args[0] = $.extend(o, {
                    timeOnly: true
                });
            }

            return $(this).each(function () {
                $.fn.datetimepicker.apply($(this), tmp_args);
            });
        },

        /*
         * extend timepicker to datepicker
         */
        datetimepicker: function (o) {
            o = o || {};
            var tmp_args = arguments;

            if (typeof(o) === 'string') {
                if (o === 'getDate'  || (o === 'option' && tmp_args.length === 2 && typeof (tmp_args[1]) === 'string')) {
                    return $.fn.datepicker.apply($(this[0]), tmp_args);
                } else {
                    return this.each(function () {
                        var $t = $(this);
                        $t.datepicker.apply($t, tmp_args);
                    });
                }
            } else {
                return this.each(function () {
                    var $t = $(this);
                    $t.datepicker($.timepicker._newInst($t, o)._defaults);
                });
            }
        }
    });

    /*
     * Public Utility to parse date and time
     */
    $.datepicker.parseDateTime = function (dateFormat, timeFormat, dateTimeString, dateSettings, timeSettings) {
        var parseRes = parseDateTimeInternal(dateFormat, timeFormat, dateTimeString, dateSettings, timeSettings);
        if (parseRes.timeObj) {
            var t = parseRes.timeObj;
            parseRes.date.setHours(t.hour, t.minute, t.second, t.millisec);
            parseRes.date.setMicroseconds(t.microsec);
        }

        return parseRes.date;
    };

    /*
     * Public utility to parse time
     */
    $.datepicker.parseTime = function (timeFormat, timeString, options) {
        var o = extendRemove(extendRemove({}, $.timepicker._defaults), options || {}),
            iso8601 = (timeFormat.replace(/\'.*?\'/g, '').indexOf('Z') !== -1);

        // Strict parse requires the timeString to match the timeFormat exactly
        var strictParse = function (f, s, o) {

            // pattern for standard and localized AM/PM markers
            var getPatternAmpm = function (amNames, pmNames) {
                var markers = [];
                if (amNames) {
                    $.merge(markers, amNames);
                }
                if (pmNames) {
                    $.merge(markers, pmNames);
                }
                markers = $.map(markers, function (val) {
                    return val.replace(/[.*+?|()\[\]{}\\]/g, '\\$&');
                });
                return '(' + markers.join('|') + ')?';
            };

            // figure out position of time elements.. cause js cant do named captures
            var getFormatPositions = function (timeFormat) {
                var finds = timeFormat.toLowerCase().match(/(h{1,2}|m{1,2}|s{1,2}|l{1}|c{1}|t{1,2}|z|'.*?')/g),
                    orders = {
                        h: -1,
                        m: -1,
                        s: -1,
                        l: -1,
                        c: -1,
                        t: -1,
                        z: -1
                    };

                if (finds) {
                    for (var i = 0; i < finds.length; i++) {
                        if (orders[finds[i].toString().charAt(0)] === -1) {
                            orders[finds[i].toString().charAt(0)] = i + 1;
                        }
                    }
                }
                return orders;
            };

            var regstr = '^' + f.toString()
                    .replace(/([hH]{1,2}|mm?|ss?|[tT]{1,2}|[zZ]|[lc]|'.*?')/g, function (match) {
                        var ml = match.length;
                        switch (match.charAt(0).toLowerCase()) {
                            case 'h':
                                return ml === 1 ? '(\\d?\\d)' : '(\\d{' + ml + '})';
                            case 'm':
                                return ml === 1 ? '(\\d?\\d)' : '(\\d{' + ml + '})';
                            case 's':
                                return ml === 1 ? '(\\d?\\d)' : '(\\d{' + ml + '})';
                            case 'l':
                                return '(\\d?\\d?\\d)';
                            case 'c':
                                return '(\\d?\\d?\\d)';
                            case 'z':
                                return '(z|[-+]\\d\\d:?\\d\\d|\\S+)?';
                            case 't':
                                return getPatternAmpm(o.amNames, o.pmNames);
                            default:    // literal escaped in quotes
                                return '(' + match.replace(/\'/g, "").replace(/(\.|\$|\^|\\|\/|\(|\)|\[|\]|\?|\+|\*)/g, function (m) { return "\\" + m; }) + ')?';
                        }
                    })
                    .replace(/\s/g, '\\s?') +
                    o.timeSuffix + '$',
                order = getFormatPositions(f),
                ampm = '',
                treg;

            treg = s.match(new RegExp(regstr, 'i'));

            var resTime = {
                hour: 0,
                minute: 0,
                second: 0,
                millisec: 0,
                microsec: 0
            };

            if (treg) {
                if (order.t !== -1) {
                    if (treg[order.t] === undefined || treg[order.t].length === 0) {
                        ampm = '';
                        resTime.ampm = '';
                    } else {
                        ampm = $.inArray(treg[order.t].toUpperCase(), o.amNames) !== -1 ? 'AM' : 'PM';
                        resTime.ampm = o[ampm === 'AM' ? 'amNames' : 'pmNames'][0];
                    }
                }

                if (order.h !== -1) {
                    if (ampm === 'AM' && treg[order.h] === '12') {
                        resTime.hour = 0; // 12am = 0 hour
                    } else {
                        if (ampm === 'PM' && treg[order.h] !== '12') {
                            resTime.hour = parseInt(treg[order.h], 10) + 12; // 12pm = 12 hour, any other pm = hour + 12
                        } else {
                            resTime.hour = Number(treg[order.h]);
                        }
                    }
                }

                if (order.m !== -1) {
                    resTime.minute = Number(treg[order.m]);
                }
                if (order.s !== -1) {
                    resTime.second = Number(treg[order.s]);
                }
                if (order.l !== -1) {
                    resTime.millisec = Number(treg[order.l]);
                }
                if (order.c !== -1) {
                    resTime.microsec = Number(treg[order.c]);
                }
                if (order.z !== -1 && treg[order.z] !== undefined) {
                    resTime.timezone = $.timepicker.timezoneOffsetNumber(treg[order.z]);
                }


                return resTime;
            }
            return false;
        };// end strictParse

        // First try JS Date, if that fails, use strictParse
        var looseParse = function (f, s, o) {
            try {
                var d = new Date('2012-01-01 ' + s);
                if (isNaN(d.getTime())) {
                    d = new Date('2012-01-01T' + s);
                    if (isNaN(d.getTime())) {
                        d = new Date('01/01/2012 ' + s);
                        if (isNaN(d.getTime())) {
                            throw "Unable to parse time with native Date: " + s;
                        }
                    }
                }

                return {
                    hour: d.getHours(),
                    minute: d.getMinutes(),
                    second: d.getSeconds(),
                    millisec: d.getMilliseconds(),
                    microsec: d.getMicroseconds(),
                    timezone: d.getTimezoneOffset() * -1
                };
            }
            catch (err) {
                try {
                    return strictParse(f, s, o);
                }
                catch (err2) {
                    $.timepicker.log("Unable to parse \ntimeString: " + s + "\ntimeFormat: " + f);
                }
            }
            return false;
        }; // end looseParse

        if (typeof o.parse === "function") {
            return o.parse(timeFormat, timeString, o);
        }
        if (o.parse === 'loose') {
            return looseParse(timeFormat, timeString, o);
        }
        return strictParse(timeFormat, timeString, o);
    };

    /**
     * Public utility to format the time
     * @param {string} format format of the time
     * @param {Object} time Object not a Date for timezones
     * @param {Object} [options] essentially the regional[].. amNames, pmNames, ampm
     * @returns {string} the formatted time
     */
    $.datepicker.formatTime = function (format, time, options) {
        options = options || {};
        options = $.extend({}, $.timepicker._defaults, options);
        time = $.extend({
            hour: 0,
            minute: 0,
            second: 0,
            millisec: 0,
            microsec: 0,
            timezone: null
        }, time);

        var tmptime = format,
            ampmName = options.amNames[0],
            hour = parseInt(time.hour, 10);

        if (hour > 11) {
            ampmName = options.pmNames[0];
        }

        tmptime = tmptime.replace(/(?:HH?|hh?|mm?|ss?|[tT]{1,2}|[zZ]|[lc]|'.*?')/g, function (match) {
            switch (match) {
                case 'HH':
                    return ('0' + hour).slice(-2);
                case 'H':
                    return hour;
                case 'hh':
                    return ('0' + convert24to12(hour)).slice(-2);
                case 'h':
                    return convert24to12(hour);
                case 'mm':
                    return ('0' + time.minute).slice(-2);
                case 'm':
                    return time.minute;
                case 'ss':
                    return ('0' + time.second).slice(-2);
                case 's':
                    return time.second;
                case 'l':
                    return ('00' + time.millisec).slice(-3);
                case 'c':
                    return ('00' + time.microsec).slice(-3);
                case 'z':
                    return $.timepicker.timezoneOffsetString(time.timezone === null ? options.timezone : time.timezone, false);
                case 'Z':
                    return $.timepicker.timezoneOffsetString(time.timezone === null ? options.timezone : time.timezone, true);
                case 'T':
                    return ampmName.charAt(0).toUpperCase();
                case 'TT':
                    return ampmName.toUpperCase();
                case 't':
                    return ampmName.charAt(0).toLowerCase();
                case 'tt':
                    return ampmName.toLowerCase();
                default:
                    return match.replace(/'/g, "");
            }
        });

        return tmptime;
    };

    /*
     * the bad hack :/ override datepicker so it doesn't close on select
     // inspired: http://stackoverflow.com/questions/1252512/jquery-datepicker-prevent-closing-picker-when-clicking-a-date/1762378#1762378
     */
    $.datepicker._base_selectDate = $.datepicker._selectDate;
    $.datepicker._selectDate = function (id, dateStr) {
        var inst = this._getInst($(id)[0]),
            tp_inst = this._get(inst, 'timepicker'),
            was_inline;

        if (tp_inst && inst.settings.showTimepicker) {
            tp_inst._limitMinMaxDateTime(inst, true);
            was_inline = inst.inline;
            inst.inline = inst.stay_open = true;
            //This way the onSelect handler called from calendarpicker get the full dateTime
            this._base_selectDate(id, dateStr);
            inst.inline = was_inline;
            inst.stay_open = false;
            this._notifyChange(inst);
            this._updateDatepicker(inst);
        } else {
            this._base_selectDate(id, dateStr);
        }
    };

    /*
     * second bad hack :/ override datepicker so it triggers an event when changing the input field
     * and does not redraw the datepicker on every selectDate event
     */
    $.datepicker._base_updateDatepicker = $.datepicker._updateDatepicker;
    $.datepicker._updateDatepicker = function (inst) {

        // don't popup the datepicker if there is another instance already opened
        var input = inst.input[0];
        if ($.datepicker._curInst && $.datepicker._curInst !== inst && $.datepicker._datepickerShowing && $.datepicker._lastInput !== input) {
            return;
        }

        if (typeof(inst.stay_open) !== 'boolean' || inst.stay_open === false) {

            this._base_updateDatepicker(inst);

            // Reload the time control when changing something in the input text field.
            var tp_inst = this._get(inst, 'timepicker');
            if (tp_inst) {
                tp_inst._addTimePicker(inst);
            }
        }
    };

    /*
     * third bad hack :/ override datepicker so it allows spaces and colon in the input field
     */
    $.datepicker._base_doKeyPress = $.datepicker._doKeyPress;
    $.datepicker._doKeyPress = function (event) {
        var inst = $.datepicker._getInst(event.target),
            tp_inst = $.datepicker._get(inst, 'timepicker');

        if (tp_inst) {
            if ($.datepicker._get(inst, 'constrainInput')) {
                var ampm = tp_inst.support.ampm,
                    tz = tp_inst._defaults.showTimezone !== null ? tp_inst._defaults.showTimezone : tp_inst.support.timezone,
                    dateChars = $.datepicker._possibleChars($.datepicker._get(inst, 'dateFormat')),
                    datetimeChars = tp_inst._defaults.timeFormat.toString()
                        .replace(/[hms]/g, '')
                        .replace(/TT/g, ampm ? 'APM' : '')
                        .replace(/Tt/g, ampm ? 'AaPpMm' : '')
                        .replace(/tT/g, ampm ? 'AaPpMm' : '')
                        .replace(/T/g, ampm ? 'AP' : '')
                        .replace(/tt/g, ampm ? 'apm' : '')
                        .replace(/t/g, ampm ? 'ap' : '') +
                        " " + tp_inst._defaults.separator +
                        tp_inst._defaults.timeSuffix +
                        (tz ? tp_inst._defaults.timezoneList.join('') : '') +
                        (tp_inst._defaults.amNames.join('')) + (tp_inst._defaults.pmNames.join('')) +
                        dateChars,
                    chr = String.fromCharCode(event.charCode === undefined ? event.keyCode : event.charCode);
                return event.ctrlKey || (chr < ' ' || !dateChars || datetimeChars.indexOf(chr) > -1);
            }
        }

        return $.datepicker._base_doKeyPress(event);
    };

    /*
     * Fourth bad hack :/ override _updateAlternate function used in inline mode to init altField
     * Update any alternate field to synchronise with the main field.
     */
    $.datepicker._base_updateAlternate = $.datepicker._updateAlternate;
    $.datepicker._updateAlternate = function (inst) {
        var tp_inst = this._get(inst, 'timepicker');
        if (tp_inst) {
            var altField = tp_inst._defaults.altField;
            if (altField) { // update alternate field too
                var altFormat = tp_inst._defaults.altFormat || tp_inst._defaults.dateFormat,
                    date = this._getDate(inst),
                    formatCfg = $.datepicker._getFormatConfig(inst),
                    altFormattedDateTime = '',
                    altSeparator = tp_inst._defaults.altSeparator ? tp_inst._defaults.altSeparator : tp_inst._defaults.separator,
                    altTimeSuffix = tp_inst._defaults.altTimeSuffix ? tp_inst._defaults.altTimeSuffix : tp_inst._defaults.timeSuffix,
                    altTimeFormat = tp_inst._defaults.altTimeFormat !== null ? tp_inst._defaults.altTimeFormat : tp_inst._defaults.timeFormat;

                altFormattedDateTime += $.datepicker.formatTime(altTimeFormat, tp_inst, tp_inst._defaults) + altTimeSuffix;
                if (!tp_inst._defaults.timeOnly && !tp_inst._defaults.altFieldTimeOnly && date !== null) {
                    if (tp_inst._defaults.altFormat) {
                        altFormattedDateTime = $.datepicker.formatDate(tp_inst._defaults.altFormat, date, formatCfg) + altSeparator + altFormattedDateTime;
                    }
                    else {
                        altFormattedDateTime = tp_inst.formattedDate + altSeparator + altFormattedDateTime;
                    }
                }
                $(altField).val( inst.input.val() ? altFormattedDateTime : "");
            }
        }
        else {
            $.datepicker._base_updateAlternate(inst);
        }
    };

    /*
     * Override key up event to sync manual input changes.
     */
    $.datepicker._base_doKeyUp = $.datepicker._doKeyUp;
    $.datepicker._doKeyUp = function (event) {
        var inst = $.datepicker._getInst(event.target),
            tp_inst = $.datepicker._get(inst, 'timepicker');

        if (tp_inst) {
            if (tp_inst._defaults.timeOnly && (inst.input.val() !== inst.lastVal)) {
                try {
                    $.datepicker._updateDatepicker(inst);
                } catch (err) {
                    $.timepicker.log(err);
                }
            }
        }

        return $.datepicker._base_doKeyUp(event);
    };

    /*
     * override "Today" button to also grab the time.
     */
    $.datepicker._base_gotoToday = $.datepicker._gotoToday;
    $.datepicker._gotoToday = function (id) {
        var inst = this._getInst($(id)[0]),
            $dp = inst.dpDiv;
        this._base_gotoToday(id);
        var tp_inst = this._get(inst, 'timepicker');
        selectLocalTimezone(tp_inst);
        var now = new Date();
        this._setTime(inst, now);
        this._setDate(inst, now);
    };

    /*
     * Disable & enable the Time in the datetimepicker
     */
    $.datepicker._disableTimepickerDatepicker = function (target) {
        var inst = this._getInst(target);
        if (!inst) {
            return;
        }

        var tp_inst = this._get(inst, 'timepicker');
        $(target).datepicker('getDate'); // Init selected[Year|Month|Day]
        if (tp_inst) {
            inst.settings.showTimepicker = false;
            tp_inst._defaults.showTimepicker = false;
            tp_inst._updateDateTime(inst);
        }
    };

    $.datepicker._enableTimepickerDatepicker = function (target) {
        var inst = this._getInst(target);
        if (!inst) {
            return;
        }

        var tp_inst = this._get(inst, 'timepicker');
        $(target).datepicker('getDate'); // Init selected[Year|Month|Day]
        if (tp_inst) {
            inst.settings.showTimepicker = true;
            tp_inst._defaults.showTimepicker = true;
            tp_inst._addTimePicker(inst); // Could be disabled on page load
            tp_inst._updateDateTime(inst);
        }
    };

    /*
     * Create our own set time function
     */
    $.datepicker._setTime = function (inst, date) {
        var tp_inst = this._get(inst, 'timepicker');
        if (tp_inst) {
            var defaults = tp_inst._defaults;

            // calling _setTime with no date sets time to defaults
            tp_inst.hour = date ? date.getHours() : defaults.hour;
            tp_inst.minute = date ? date.getMinutes() : defaults.minute;
            tp_inst.second = date ? date.getSeconds() : defaults.second;
            tp_inst.millisec = date ? date.getMilliseconds() : defaults.millisec;
            tp_inst.microsec = date ? date.getMicroseconds() : defaults.microsec;

            //check if within min/max times..
            tp_inst._limitMinMaxDateTime(inst, true);

            tp_inst._onTimeChange();
            tp_inst._updateDateTime(inst);
        }
    };

    /*
     * Create new public method to set only time, callable as $().datepicker('setTime', date)
     */
    $.datepicker._setTimeDatepicker = function (target, date, withDate) {
        var inst = this._getInst(target);
        if (!inst) {
            return;
        }

        var tp_inst = this._get(inst, 'timepicker');

        if (tp_inst) {
            this._setDateFromField(inst);
            var tp_date;
            if (date) {
                if (typeof date === "string") {
                    tp_inst._parseTime(date, withDate);
                    tp_date = new Date();
                    tp_date.setHours(tp_inst.hour, tp_inst.minute, tp_inst.second, tp_inst.millisec);
                    tp_date.setMicroseconds(tp_inst.microsec);
                } else {
                    tp_date = new Date(date.getTime());
                    tp_date.setMicroseconds(date.getMicroseconds());
                }
                if (tp_date.toString() === 'Invalid Date') {
                    tp_date = undefined;
                }
                this._setTime(inst, tp_date);
            }
        }

    };

    /*
     * override setDate() to allow setting time too within Date object
     */
    $.datepicker._base_setDateDatepicker = $.datepicker._setDateDatepicker;
    $.datepicker._setDateDatepicker = function (target, _date) {
        var inst = this._getInst(target);
        var date = _date;
        if (!inst) {
            return;
        }

        if (typeof(_date) === 'string') {
            date = new Date(_date);
            if (!date.getTime()) {
                this._base_setDateDatepicker.apply(this, arguments);
                date = $(target).datepicker('getDate');
            }
        }

        var tp_inst = this._get(inst, 'timepicker');
        var tp_date;
        if (date instanceof Date) {
            tp_date = new Date(date.getTime());
            tp_date.setMicroseconds(date.getMicroseconds());
        } else {
            tp_date = date;
        }

        // This is important if you are using the timezone option, javascript's Date
        // object will only return the timezone offset for the current locale, so we
        // adjust it accordingly.  If not using timezone option this won't matter..
        // If a timezone is different in tp, keep the timezone as is
        if (tp_inst && tp_date) {
            // look out for DST if tz wasn't specified
            if (!tp_inst.support.timezone && tp_inst._defaults.timezone === null) {
                tp_inst.timezone = tp_date.getTimezoneOffset() * -1;
            }
            date = $.timepicker.timezoneAdjust(date, tp_inst.timezone);
            tp_date = $.timepicker.timezoneAdjust(tp_date, tp_inst.timezone);
        }

        this._updateDatepicker(inst);
        this._base_setDateDatepicker.apply(this, arguments);
        this._setTimeDatepicker(target, tp_date, true);
    };

    /*
     * override getDate() to allow getting time too within Date object
     */
    $.datepicker._base_getDateDatepicker = $.datepicker._getDateDatepicker;
    $.datepicker._getDateDatepicker = function (target, noDefault) {
        var inst = this._getInst(target);
        if (!inst) {
            return;
        }

        var tp_inst = this._get(inst, 'timepicker');

        if (tp_inst) {
            // if it hasn't yet been defined, grab from field
            if (inst.lastVal === undefined) {
                this._setDateFromField(inst, noDefault);
            }

            var date = this._getDate(inst);
            if (date && tp_inst._parseTime($(target).val(), tp_inst.timeOnly)) {
                date.setHours(tp_inst.hour, tp_inst.minute, tp_inst.second, tp_inst.millisec);
                date.setMicroseconds(tp_inst.microsec);

                // This is important if you are using the timezone option, javascript's Date
                // object will only return the timezone offset for the current locale, so we
                // adjust it accordingly.  If not using timezone option this won't matter..
                if (tp_inst.timezone != null) {
                    // look out for DST if tz wasn't specified
                    if (!tp_inst.support.timezone && tp_inst._defaults.timezone === null) {
                        tp_inst.timezone = date.getTimezoneOffset() * -1;
                    }
                    date = $.timepicker.timezoneAdjust(date, tp_inst.timezone);
                }
            }
            return date;
        }
        return this._base_getDateDatepicker(target, noDefault);
    };

    /*
     * override parseDate() because UI 1.8.14 throws an error about "Extra characters"
     * An option in datapicker to ignore extra format characters would be nicer.
     */
    $.datepicker._base_parseDate = $.datepicker.parseDate;
    $.datepicker.parseDate = function (format, value, settings) {
        var date;
        try {
            date = this._base_parseDate(format, value, settings);
        } catch (err) {
            // Hack!  The error message ends with a colon, a space, and
            // the "extra" characters.  We rely on that instead of
            // attempting to perfectly reproduce the parsing algorithm.
            if (err.indexOf(":") >= 0) {
                date = this._base_parseDate(format, value.substring(0, value.length - (err.length - err.indexOf(':') - 2)), settings);
                $.timepicker.log("Error parsing the date string: " + err + "\ndate string = " + value + "\ndate format = " + format);
            } else {
                throw err;
            }
        }
        return date;
    };

    /*
     * override formatDate to set date with time to the input
     */
    $.datepicker._base_formatDate = $.datepicker._formatDate;
    $.datepicker._formatDate = function (inst, day, month, year) {
        var tp_inst = this._get(inst, 'timepicker');
        if (tp_inst) {
            tp_inst._updateDateTime(inst);
            return tp_inst.$input.val();
        }
        return this._base_formatDate(inst);
    };

    /*
     * override options setter to add time to maxDate(Time) and minDate(Time). MaxDate
     */
    $.datepicker._base_optionDatepicker = $.datepicker._optionDatepicker;
    $.datepicker._optionDatepicker = function (target, name, value) {
        var inst = this._getInst(target),
            name_clone;
        if (!inst) {
            return null;
        }

        var tp_inst = this._get(inst, 'timepicker');
        if (tp_inst) {
            var min = null,
                max = null,
                onselect = null,
                overrides = tp_inst._defaults.evnts,
                fns = {},
                prop,
                ret,
                oldVal,
                $target;
            if (typeof name === 'string') { // if min/max was set with the string
                if (name === 'minDate' || name === 'minDateTime') {
                    min = value;
                } else if (name === 'maxDate' || name === 'maxDateTime') {
                    max = value;
                } else if (name === 'onSelect') {
                    onselect = value;
                } else if (overrides.hasOwnProperty(name)) {
                    if (typeof (value) === 'undefined') {
                        return overrides[name];
                    }
                    fns[name] = value;
                    name_clone = {}; //empty results in exiting function after overrides updated
                }
            } else if (typeof name === 'object') { //if min/max was set with the JSON
                if (name.minDate) {
                    min = name.minDate;
                } else if (name.minDateTime) {
                    min = name.minDateTime;
                } else if (name.maxDate) {
                    max = name.maxDate;
                } else if (name.maxDateTime) {
                    max = name.maxDateTime;
                }
                for (prop in overrides) {
                    if (overrides.hasOwnProperty(prop) && name[prop]) {
                        fns[prop] = name[prop];
                    }
                }
            }
            for (prop in fns) {
                if (fns.hasOwnProperty(prop)) {
                    overrides[prop] = fns[prop];
                    if (!name_clone) { name_clone = $.extend({}, name); }
                    delete name_clone[prop];
                }
            }
            if (name_clone && isEmptyObject(name_clone)) { return; }
            if (min) { //if min was set
                if (min === 0) {
                    min = new Date();
                } else {
                    min = new Date(min);
                }
                tp_inst._defaults.minDate = min;
                tp_inst._defaults.minDateTime = min;
            } else if (max) { //if max was set
                if (max === 0) {
                    max = new Date();
                } else {
                    max = new Date(max);
                }
                tp_inst._defaults.maxDate = max;
                tp_inst._defaults.maxDateTime = max;
            } else if (onselect) {
                tp_inst._defaults.onSelect = onselect;
            }

            // Datepicker will override our date when we call _base_optionDatepicker when
            // calling minDate/maxDate, so we will first grab the value, call
            // _base_optionDatepicker, then set our value back.
            if(min || max){
                $target = $(target);
                oldVal = $target.datetimepicker('getDate');
                ret = this._base_optionDatepicker.call($.datepicker, target, name_clone || name, value);
                $target.datetimepicker('setDate', oldVal);
                return ret;
            }
        }
        if (value === undefined) {
            return this._base_optionDatepicker.call($.datepicker, target, name);
        }
        return this._base_optionDatepicker.call($.datepicker, target, name_clone || name, value);
    };

    /*
     * jQuery isEmptyObject does not check hasOwnProperty - if someone has added to the object prototype,
     * it will return false for all objects
     */
    var isEmptyObject = function (obj) {
        var prop;
        for (prop in obj) {
            if (obj.hasOwnProperty(prop)) {
                return false;
            }
        }
        return true;
    };

    /*
     * jQuery extend now ignores nulls!
     */
    var extendRemove = function (target, props) {
        $.extend(target, props);
        for (var name in props) {
            if (props[name] === null || props[name] === undefined) {
                target[name] = props[name];
            }
        }
        return target;
    };

    /*
     * Determine by the time format which units are supported
     * Returns an object of booleans for each unit
     */
    var detectSupport = function (timeFormat) {
        var tf = timeFormat.replace(/'.*?'/g, '').toLowerCase(), // removes literals
            isIn = function (f, t) { // does the format contain the token?
                return f.indexOf(t) !== -1 ? true : false;
            };
        return {
            hour: isIn(tf, 'h'),
            minute: isIn(tf, 'm'),
            second: isIn(tf, 's'),
            millisec: isIn(tf, 'l'),
            microsec: isIn(tf, 'c'),
            timezone: isIn(tf, 'z'),
            ampm: isIn(tf, 't') && isIn(timeFormat, 'h'),
            iso8601: isIn(timeFormat, 'Z')
        };
    };

    /*
     * Converts 24 hour format into 12 hour
     * Returns 12 hour without leading 0
     */
    var convert24to12 = function (hour) {
        hour %= 12;

        if (hour === 0) {
            hour = 12;
        }

        return String(hour);
    };

    var computeEffectiveSetting = function (settings, property) {
        return settings && settings[property] ? settings[property] : $.timepicker._defaults[property];
    };

    /*
     * Splits datetime string into date and time substrings.
     * Throws exception when date can't be parsed
     * Returns {dateString: dateString, timeString: timeString}
     */
    var splitDateTime = function (dateTimeString, timeSettings) {
        // The idea is to get the number separator occurrences in datetime and the time format requested (since time has
        // fewer unknowns, mostly numbers and am/pm). We will use the time pattern to split.
        var separator = computeEffectiveSetting(timeSettings, 'separator'),
            format = computeEffectiveSetting(timeSettings, 'timeFormat'),
            timeParts = format.split(separator), // how many occurrences of separator may be in our format?
            timePartsLen = timeParts.length,
            allParts = dateTimeString.split(separator),
            allPartsLen = allParts.length;

        if (allPartsLen > 1) {
            return {
                dateString: allParts.splice(0, allPartsLen - timePartsLen).join(separator),
                timeString: allParts.splice(0, timePartsLen).join(separator)
            };
        }

        return {
            dateString: dateTimeString,
            timeString: ''
        };
    };

    /*
     * Internal function to parse datetime interval
     * Returns: {date: Date, timeObj: Object}, where
     *   date - parsed date without time (type Date)
     *   timeObj = {hour: , minute: , second: , millisec: , microsec: } - parsed time. Optional
     */
    var parseDateTimeInternal = function (dateFormat, timeFormat, dateTimeString, dateSettings, timeSettings) {
        var date,
            parts,
            parsedTime;

        parts = splitDateTime(dateTimeString, timeSettings);
        date = $.datepicker._base_parseDate(dateFormat, parts.dateString, dateSettings);

        if (parts.timeString === '') {
            return {
                date: date
            };
        }

        parsedTime = $.datepicker.parseTime(timeFormat, parts.timeString, timeSettings);

        if (!parsedTime) {
            throw 'Wrong time format';
        }

        return {
            date: date,
            timeObj: parsedTime
        };
    };

    /*
     * Internal function to set timezone_select to the local timezone
     */
    var selectLocalTimezone = function (tp_inst, date) {
        if (tp_inst && tp_inst.timezone_select) {
            var now = date || new Date();
            tp_inst.timezone_select.val(-now.getTimezoneOffset());
        }
    };

    /*
     * Create a Singleton Instance
     */
    $.timepicker = new Timepicker();

    /**
     * Get the timezone offset as string from a date object (eg '+0530' for UTC+5.5)
     * @param {number} tzMinutes if not a number, less than -720 (-1200), or greater than 840 (+1400) this value is returned
     * @param {boolean} iso8601 if true formats in accordance to iso8601 "+12:45"
     * @return {string}
     */
    $.timepicker.timezoneOffsetString = function (tzMinutes, iso8601) {
        if (isNaN(tzMinutes) || tzMinutes > 840 || tzMinutes < -720) {
            return tzMinutes;
        }

        var off = tzMinutes,
            minutes = off % 60,
            hours = (off - minutes) / 60,
            iso = iso8601 ? ':' : '',
            tz = (off >= 0 ? '+' : '-') + ('0' + Math.abs(hours)).slice(-2) + iso + ('0' + Math.abs(minutes)).slice(-2);

        if (tz === '+00:00') {
            return 'Z';
        }
        return tz;
    };

    /**
     * Get the number in minutes that represents a timezone string
     * @param  {string} tzString formatted like "+0500", "-1245", "Z"
     * @return {number} the offset minutes or the original string if it doesn't match expectations
     */
    $.timepicker.timezoneOffsetNumber = function (tzString) {
        var normalized = tzString.toString().replace(':', ''); // excuse any iso8601, end up with "+1245"

        if (normalized.toUpperCase() === 'Z') { // if iso8601 with Z, its 0 minute offset
            return 0;
        }

        if (!/^(\-|\+)\d{4}$/.test(normalized)) { // possibly a user defined tz, so just give it back
            return tzString;
        }

        return ((normalized.substr(0, 1) === '-' ? -1 : 1) * // plus or minus
            ((parseInt(normalized.substr(1, 2), 10) * 60) + // hours (converted to minutes)
                parseInt(normalized.substr(3, 2), 10))); // minutes
    };

    /**
     * No way to set timezone in js Date, so we must adjust the minutes to compensate. (think setDate, getDate)
     * @param  {Date} date
     * @param  {string} toTimezone formatted like "+0500", "-1245"
     * @return {Date}
     */
    $.timepicker.timezoneAdjust = function (date, toTimezone) {
        var toTz = $.timepicker.timezoneOffsetNumber(toTimezone);
        if (!isNaN(toTz)) {
            date.setMinutes(date.getMinutes() + -date.getTimezoneOffset() - toTz);
        }
        return date;
    };

    /**
     * Calls `timepicker()` on the `startTime` and `endTime` elements, and configures them to
     * enforce date range limits.
     * n.b. The input value must be correctly formatted (reformatting is not supported)
     * @param  {Element} startTime
     * @param  {Element} endTime
     * @param  {Object} options Options for the timepicker() call
     * @return {jQuery}
     */
    $.timepicker.timeRange = function (startTime, endTime, options) {
        return $.timepicker.handleRange('timepicker', startTime, endTime, options);
    };

    /**
     * Calls `datetimepicker` on the `startTime` and `endTime` elements, and configures them to
     * enforce date range limits.
     * @param  {Element} startTime
     * @param  {Element} endTime
     * @param  {Object} options Options for the `timepicker()` call. Also supports `reformat`,
     *   a boolean value that can be used to reformat the input values to the `dateFormat`.
     * @param  {string} method Can be used to specify the type of picker to be added
     * @return {jQuery}
     */
    $.timepicker.datetimeRange = function (startTime, endTime, options) {
        $.timepicker.handleRange('datetimepicker', startTime, endTime, options);
    };

    /**
     * Calls `datepicker` on the `startTime` and `endTime` elements, and configures them to
     * enforce date range limits.
     * @param  {Element} startTime
     * @param  {Element} endTime
     * @param  {Object} options Options for the `timepicker()` call. Also supports `reformat`,
     *   a boolean value that can be used to reformat the input values to the `dateFormat`.
     * @return {jQuery}
     */
    $.timepicker.dateRange = function (startTime, endTime, options) {
        $.timepicker.handleRange('datepicker', startTime, endTime, options);
    };

    /**
     * Calls `method` on the `startTime` and `endTime` elements, and configures them to
     * enforce date range limits.
     * @param  {string} method Can be used to specify the type of picker to be added
     * @param  {Element} startTime
     * @param  {Element} endTime
     * @param  {Object} options Options for the `timepicker()` call. Also supports `reformat`,
     *   a boolean value that can be used to reformat the input values to the `dateFormat`.
     * @return {jQuery}
     */
    $.timepicker.handleRange = function (method, startTime, endTime, options) {
        options = $.extend({}, {
            minInterval: 0, // min allowed interval in milliseconds
            maxInterval: 0, // max allowed interval in milliseconds
            start: {},      // options for start picker
            end: {}         // options for end picker
        }, options);

        // for the mean time this fixes an issue with calling getDate with timepicker()
        var timeOnly = false;
        if(method === 'timepicker'){
            timeOnly = true;
            method = 'datetimepicker';
        }

        function checkDates(changed, other) {
            var startdt = startTime[method]('getDate'),
                enddt = endTime[method]('getDate'),
                changeddt = changed[method]('getDate');

            if (startdt !== null) {
                var minDate = new Date(startdt.getTime()),
                    maxDate = new Date(startdt.getTime());

                minDate.setMilliseconds(minDate.getMilliseconds() + options.minInterval);
                maxDate.setMilliseconds(maxDate.getMilliseconds() + options.maxInterval);

                if (options.minInterval > 0 && minDate > enddt) { // minInterval check
                    endTime[method]('setDate', minDate);
                }
                else if (options.maxInterval > 0 && maxDate < enddt) { // max interval check
                    endTime[method]('setDate', maxDate);
                }
                else if (startdt > enddt) {
                    other[method]('setDate', changeddt);
                }
            }
        }

        function selected(changed, other, option) {
            if (!changed.val()) {
                return;
            }
            var date = changed[method].call(changed, 'getDate');
            if (date !== null && options.minInterval > 0) {
                if (option === 'minDate') {
                    date.setMilliseconds(date.getMilliseconds() + options.minInterval);
                }
                if (option === 'maxDate') {
                    date.setMilliseconds(date.getMilliseconds() - options.minInterval);
                }
            }

            if (date.getTime) {
                other[method].call(other, 'option', option, date);
            }
        }

        $.fn[method].call(startTime, $.extend({
            timeOnly: timeOnly,
            onClose: function (dateText, inst) {
                checkDates($(this), endTime);
            },
            onSelect: function (selectedDateTime) {
                selected($(this), endTime, 'minDate');
            }
        }, options, options.start));
        $.fn[method].call(endTime, $.extend({
            timeOnly: timeOnly,
            onClose: function (dateText, inst) {
                checkDates($(this), startTime);
            },
            onSelect: function (selectedDateTime) {
                selected($(this), startTime, 'maxDate');
            }
        }, options, options.end));

        checkDates(startTime, endTime);

        selected(startTime, endTime, 'minDate');
        selected(endTime, startTime, 'maxDate');

        return $([startTime.get(0), endTime.get(0)]);
    };

    /**
     * Log error or data to the console during error or debugging
     * @param  {Object} err pass any type object to log to the console during error or debugging
     * @return {void}
     */
    $.timepicker.log = function () {
        if (window.console) {
            window.console.log.apply(window.console, Array.prototype.slice.call(arguments));
        }
    };

    /*
     * Add util object to allow access to private methods for testability.
     */
    $.timepicker._util = {
        _extendRemove: extendRemove,
        _isEmptyObject: isEmptyObject,
        _convert24to12: convert24to12,
        _detectSupport: detectSupport,
        _selectLocalTimezone: selectLocalTimezone,
        _computeEffectiveSetting: computeEffectiveSetting,
        _splitDateTime: splitDateTime,
        _parseDateTimeInternal: parseDateTimeInternal
    };

    /*
     * Microsecond support
     */
    if (!Date.prototype.getMicroseconds) {
        Date.prototype.microseconds = 0;
        Date.prototype.getMicroseconds = function () { return this.microseconds; };
        Date.prototype.setMicroseconds = function (m) {
            this.setMilliseconds(this.getMilliseconds() + Math.floor(m / 1000));
            this.microseconds = m % 1000;
            return this;
        };
    }

    /*
     * Keep up with the version
     */
    $.timepicker.version = "1.5.0";

})(jQuery);
$.timepicker.textTimeControl = {
  create: function(tp_inst, obj, unit, val, min, max, step){

    if ((val+"").length === 1) {
      val = '0'+val;
    }

    var input = '<input value="'+val+'" style="width:50%"/>';

    $(input).appendTo(obj).change(function (e) {
      var $t = obj.children('input');

      if ($t.val().length === 0) {
        $t.val('00');
      } else if ($t.val().length === 1) {
        $t.val('0'+$t.val())
      }

      tp_inst._onTimeChange();
      tp_inst._onSelectHandler();
    }).keypress(function (e) {
      //http://stackoverflow.com/questions/891696/jquery-what-is-the-best-way-to-restrict-number-only-input-for-textboxes-all
      // Backspace, tab, enter, end, home, left, right
      // We don't support the del key in Opera because del == . == 46.
      var controlKeys = [8, 9, 13, 35, 36, 37, 39];
      // IE doesn't support indexOf
      var isControlKey = controlKeys.join(",").match(new RegExp(event.which));
      // Some browsers just don't raise events for control keys. Easy.
      // e.g. Safari backspace.
      if (!event.which || // Control keys in most browsers. e.g. Firefox tab is 0
        (49 <= event.which && event.which <= 57) || // Always 1 through 9
        (48 == event.which && $(this).attr("value")) || // No 0 first digit
        isControlKey) { // Opera assigns values for control keys.
        return;
      } else {
        event.preventDefault();
      }
    });

    return obj;
  },
  options: function(tp_inst, obj, unit, opts, val){
    return null;
  },
  value: function(tp_inst, obj, unit, val){
    var $t = obj.children('input');
    if (val !== undefined) {
      return $t.val(val);
    }
    return $t.val();
  }
};
/*! tooltipster v4.2.5 */!function(a,b){"function"==typeof define&&define.amd?define(["jquery"],function(a){return b(a)}):"object"==typeof exports?module.exports=b(require("jquery")):b(jQuery)}(this,function(a){function b(a){this.$container,this.constraints=null,this.__$tooltip,this.__init(a)}function c(b,c){var d=!0;return a.each(b,function(a,e){return void 0===c[a]||b[a]!==c[a]?(d=!1,!1):void 0}),d}function d(b){var c=b.attr("id"),d=c?h.window.document.getElementById(c):null;return d?d===b[0]:a.contains(h.window.document.body,b[0])}function e(){if(!g)return!1;var a=g.document.body||g.document.documentElement,b=a.style,c="transition",d=["Moz","Webkit","Khtml","O","ms"];if("string"==typeof b[c])return!0;c=c.charAt(0).toUpperCase()+c.substr(1);for(var e=0;e<d.length;e++)if("string"==typeof b[d[e]+c])return!0;return!1}var f={animation:"fade",animationDuration:350,content:null,contentAsHTML:!1,contentCloning:!1,debug:!0,delay:300,delayTouch:[300,500],functionInit:null,functionBefore:null,functionReady:null,functionAfter:null,functionFormat:null,IEmin:6,interactive:!1,multiple:!1,parent:null,plugins:["sideTip"],repositionOnScroll:!1,restoration:"none",selfDestruction:!0,theme:[],timer:0,trackerInterval:500,trackOrigin:!1,trackTooltip:!1,trigger:"hover",triggerClose:{click:!1,mouseleave:!1,originClick:!1,scroll:!1,tap:!1,touchleave:!1},triggerOpen:{click:!1,mouseenter:!1,tap:!1,touchstart:!1},updateAnimation:"rotate",zIndex:9999999},g="undefined"!=typeof window?window:null,h={hasTouchCapability:!(!g||!("ontouchstart"in g||g.DocumentTouch&&g.document instanceof g.DocumentTouch||g.navigator.maxTouchPoints)),hasTransitions:e(),IE:!1,semVer:"4.2.5",window:g},i=function(){this.__$emitterPrivate=a({}),this.__$emitterPublic=a({}),this.__instancesLatestArr=[],this.__plugins={},this._env=h};i.prototype={__bridge:function(b,c,d){if(!c[d]){var e=function(){};e.prototype=b;var g=new e;g.__init&&g.__init(c),a.each(b,function(a,b){0!=a.indexOf("__")&&(c[a]?f.debug&&console.log("The "+a+" method of the "+d+" plugin conflicts with another plugin or native methods"):(c[a]=function(){return g[a].apply(g,Array.prototype.slice.apply(arguments))},c[a].bridged=g))}),c[d]=g}return this},__setWindow:function(a){return h.window=a,this},_getRuler:function(a){return new b(a)},_off:function(){return this.__$emitterPrivate.off.apply(this.__$emitterPrivate,Array.prototype.slice.apply(arguments)),this},_on:function(){return this.__$emitterPrivate.on.apply(this.__$emitterPrivate,Array.prototype.slice.apply(arguments)),this},_one:function(){return this.__$emitterPrivate.one.apply(this.__$emitterPrivate,Array.prototype.slice.apply(arguments)),this},_plugin:function(b){var c=this;if("string"==typeof b){var d=b,e=null;return d.indexOf(".")>0?e=c.__plugins[d]:a.each(c.__plugins,function(a,b){return b.name.substring(b.name.length-d.length-1)=="."+d?(e=b,!1):void 0}),e}if(b.name.indexOf(".")<0)throw new Error("Plugins must be namespaced");return c.__plugins[b.name]=b,b.core&&c.__bridge(b.core,c,b.name),this},_trigger:function(){var a=Array.prototype.slice.apply(arguments);return"string"==typeof a[0]&&(a[0]={type:a[0]}),this.__$emitterPrivate.trigger.apply(this.__$emitterPrivate,a),this.__$emitterPublic.trigger.apply(this.__$emitterPublic,a),this},instances:function(b){var c=[],d=b||".tooltipstered";return a(d).each(function(){var b=a(this),d=b.data("tooltipster-ns");d&&a.each(d,function(a,d){c.push(b.data(d))})}),c},instancesLatest:function(){return this.__instancesLatestArr},off:function(){return this.__$emitterPublic.off.apply(this.__$emitterPublic,Array.prototype.slice.apply(arguments)),this},on:function(){return this.__$emitterPublic.on.apply(this.__$emitterPublic,Array.prototype.slice.apply(arguments)),this},one:function(){return this.__$emitterPublic.one.apply(this.__$emitterPublic,Array.prototype.slice.apply(arguments)),this},origins:function(b){var c=b?b+" ":"";return a(c+".tooltipstered").toArray()},setDefaults:function(b){return a.extend(f,b),this},triggerHandler:function(){return this.__$emitterPublic.triggerHandler.apply(this.__$emitterPublic,Array.prototype.slice.apply(arguments)),this}},a.tooltipster=new i,a.Tooltipster=function(b,c){this.__callbacks={close:[],open:[]},this.__closingTime,this.__Content,this.__contentBcr,this.__destroyed=!1,this.__$emitterPrivate=a({}),this.__$emitterPublic=a({}),this.__enabled=!0,this.__garbageCollector,this.__Geometry,this.__lastPosition,this.__namespace="tooltipster-"+Math.round(1e6*Math.random()),this.__options,this.__$originParents,this.__pointerIsOverOrigin=!1,this.__previousThemes=[],this.__state="closed",this.__timeouts={close:[],open:null},this.__touchEvents=[],this.__tracker=null,this._$origin,this._$tooltip,this.__init(b,c)},a.Tooltipster.prototype={__init:function(b,c){var d=this;if(d._$origin=a(b),d.__options=a.extend(!0,{},f,c),d.__optionsFormat(),!h.IE||h.IE>=d.__options.IEmin){var e=null;if(void 0===d._$origin.data("tooltipster-initialTitle")&&(e=d._$origin.attr("title"),void 0===e&&(e=null),d._$origin.data("tooltipster-initialTitle",e)),null!==d.__options.content)d.__contentSet(d.__options.content);else{var g,i=d._$origin.attr("data-tooltip-content");i&&(g=a(i)),g&&g[0]?d.__contentSet(g.first()):d.__contentSet(e)}d._$origin.removeAttr("title").addClass("tooltipstered"),d.__prepareOrigin(),d.__prepareGC(),a.each(d.__options.plugins,function(a,b){d._plug(b)}),h.hasTouchCapability&&a(h.window.document.body).on("touchmove."+d.__namespace+"-triggerOpen",function(a){d._touchRecordEvent(a)}),d._on("created",function(){d.__prepareTooltip()})._on("repositioned",function(a){d.__lastPosition=a.position})}else d.__options.disabled=!0},__contentInsert:function(){var a=this,b=a._$tooltip.find(".tooltipster-content"),c=a.__Content,d=function(a){c=a};return a._trigger({type:"format",content:a.__Content,format:d}),a.__options.functionFormat&&(c=a.__options.functionFormat.call(a,a,{origin:a._$origin[0]},a.__Content)),"string"!=typeof c||a.__options.contentAsHTML?b.empty().append(c):b.text(c),a},__contentSet:function(b){return b instanceof a&&this.__options.contentCloning&&(b=b.clone(!0)),this.__Content=b,this._trigger({type:"updated",content:b}),this},__destroyError:function(){throw new Error("This tooltip has been destroyed and cannot execute your method call.")},__geometry:function(){var b=this,c=b._$origin,d=b._$origin.is("area");if(d){var e=b._$origin.parent().attr("name");c=a('img[usemap="#'+e+'"]')}var f=c[0].getBoundingClientRect(),g=a(h.window.document),i=a(h.window),j=c,k={available:{document:null,window:null},document:{size:{height:g.height(),width:g.width()}},window:{scroll:{left:h.window.scrollX||h.window.document.documentElement.scrollLeft,top:h.window.scrollY||h.window.document.documentElement.scrollTop},size:{height:i.height(),width:i.width()}},origin:{fixedLineage:!1,offset:{},size:{height:f.bottom-f.top,width:f.right-f.left},usemapImage:d?c[0]:null,windowOffset:{bottom:f.bottom,left:f.left,right:f.right,top:f.top}}};if(d){var l=b._$origin.attr("shape"),m=b._$origin.attr("coords");if(m&&(m=m.split(","),a.map(m,function(a,b){m[b]=parseInt(a)})),"default"!=l)switch(l){case"circle":var n=m[0],o=m[1],p=m[2],q=o-p,r=n-p;k.origin.size.height=2*p,k.origin.size.width=k.origin.size.height,k.origin.windowOffset.left+=r,k.origin.windowOffset.top+=q;break;case"rect":var s=m[0],t=m[1],u=m[2],v=m[3];k.origin.size.height=v-t,k.origin.size.width=u-s,k.origin.windowOffset.left+=s,k.origin.windowOffset.top+=t;break;case"poly":for(var w=0,x=0,y=0,z=0,A="even",B=0;B<m.length;B++){var C=m[B];"even"==A?(C>y&&(y=C,0===B&&(w=y)),w>C&&(w=C),A="odd"):(C>z&&(z=C,1==B&&(x=z)),x>C&&(x=C),A="even")}k.origin.size.height=z-x,k.origin.size.width=y-w,k.origin.windowOffset.left+=w,k.origin.windowOffset.top+=x}}var D=function(a){k.origin.size.height=a.height,k.origin.windowOffset.left=a.left,k.origin.windowOffset.top=a.top,k.origin.size.width=a.width};for(b._trigger({type:"geometry",edit:D,geometry:{height:k.origin.size.height,left:k.origin.windowOffset.left,top:k.origin.windowOffset.top,width:k.origin.size.width}}),k.origin.windowOffset.right=k.origin.windowOffset.left+k.origin.size.width,k.origin.windowOffset.bottom=k.origin.windowOffset.top+k.origin.size.height,k.origin.offset.left=k.origin.windowOffset.left+k.window.scroll.left,k.origin.offset.top=k.origin.windowOffset.top+k.window.scroll.top,k.origin.offset.bottom=k.origin.offset.top+k.origin.size.height,k.origin.offset.right=k.origin.offset.left+k.origin.size.width,k.available.document={bottom:{height:k.document.size.height-k.origin.offset.bottom,width:k.document.size.width},left:{height:k.document.size.height,width:k.origin.offset.left},right:{height:k.document.size.height,width:k.document.size.width-k.origin.offset.right},top:{height:k.origin.offset.top,width:k.document.size.width}},k.available.window={bottom:{height:Math.max(k.window.size.height-Math.max(k.origin.windowOffset.bottom,0),0),width:k.window.size.width},left:{height:k.window.size.height,width:Math.max(k.origin.windowOffset.left,0)},right:{height:k.window.size.height,width:Math.max(k.window.size.width-Math.max(k.origin.windowOffset.right,0),0)},top:{height:Math.max(k.origin.windowOffset.top,0),width:k.window.size.width}};"html"!=j[0].tagName.toLowerCase();){if("fixed"==j.css("position")){k.origin.fixedLineage=!0;break}j=j.parent()}return k},__optionsFormat:function(){return"number"==typeof this.__options.animationDuration&&(this.__options.animationDuration=[this.__options.animationDuration,this.__options.animationDuration]),"number"==typeof this.__options.delay&&(this.__options.delay=[this.__options.delay,this.__options.delay]),"number"==typeof this.__options.delayTouch&&(this.__options.delayTouch=[this.__options.delayTouch,this.__options.delayTouch]),"string"==typeof this.__options.theme&&(this.__options.theme=[this.__options.theme]),null===this.__options.parent?this.__options.parent=a(h.window.document.body):"string"==typeof this.__options.parent&&(this.__options.parent=a(this.__options.parent)),"hover"==this.__options.trigger?(this.__options.triggerOpen={mouseenter:!0,touchstart:!0},this.__options.triggerClose={mouseleave:!0,originClick:!0,touchleave:!0}):"click"==this.__options.trigger&&(this.__options.triggerOpen={click:!0,tap:!0},this.__options.triggerClose={click:!0,tap:!0}),this._trigger("options"),this},__prepareGC:function(){var b=this;return b.__options.selfDestruction?b.__garbageCollector=setInterval(function(){var c=(new Date).getTime();b.__touchEvents=a.grep(b.__touchEvents,function(a,b){return c-a.time>6e4}),d(b._$origin)||b.close(function(){b.destroy()})},2e4):clearInterval(b.__garbageCollector),b},__prepareOrigin:function(){var a=this;if(a._$origin.off("."+a.__namespace+"-triggerOpen"),h.hasTouchCapability&&a._$origin.on("touchstart."+a.__namespace+"-triggerOpen touchend."+a.__namespace+"-triggerOpen touchcancel."+a.__namespace+"-triggerOpen",function(b){a._touchRecordEvent(b)}),a.__options.triggerOpen.click||a.__options.triggerOpen.tap&&h.hasTouchCapability){var b="";a.__options.triggerOpen.click&&(b+="click."+a.__namespace+"-triggerOpen "),a.__options.triggerOpen.tap&&h.hasTouchCapability&&(b+="touchend."+a.__namespace+"-triggerOpen"),a._$origin.on(b,function(b){a._touchIsMeaningfulEvent(b)&&a._open(b)})}if(a.__options.triggerOpen.mouseenter||a.__options.triggerOpen.touchstart&&h.hasTouchCapability){var b="";a.__options.triggerOpen.mouseenter&&(b+="mouseenter."+a.__namespace+"-triggerOpen "),a.__options.triggerOpen.touchstart&&h.hasTouchCapability&&(b+="touchstart."+a.__namespace+"-triggerOpen"),a._$origin.on(b,function(b){!a._touchIsTouchEvent(b)&&a._touchIsEmulatedEvent(b)||(a.__pointerIsOverOrigin=!0,a._openShortly(b))})}if(a.__options.triggerClose.mouseleave||a.__options.triggerClose.touchleave&&h.hasTouchCapability){var b="";a.__options.triggerClose.mouseleave&&(b+="mouseleave."+a.__namespace+"-triggerOpen "),a.__options.triggerClose.touchleave&&h.hasTouchCapability&&(b+="touchend."+a.__namespace+"-triggerOpen touchcancel."+a.__namespace+"-triggerOpen"),a._$origin.on(b,function(b){a._touchIsMeaningfulEvent(b)&&(a.__pointerIsOverOrigin=!1)})}return a},__prepareTooltip:function(){var b=this,c=b.__options.interactive?"auto":"";return b._$tooltip.attr("id",b.__namespace).css({"pointer-events":c,zIndex:b.__options.zIndex}),a.each(b.__previousThemes,function(a,c){b._$tooltip.removeClass(c)}),a.each(b.__options.theme,function(a,c){b._$tooltip.addClass(c)}),b.__previousThemes=a.merge([],b.__options.theme),b},__scrollHandler:function(b){var c=this;if(c.__options.triggerClose.scroll)c._close(b);else if(d(c._$origin)&&d(c._$tooltip)){var e=null;if(b.target===h.window.document)c.__Geometry.origin.fixedLineage||c.__options.repositionOnScroll&&c.reposition(b);else{e=c.__geometry();var f=!1;if("fixed"!=c._$origin.css("position")&&c.__$originParents.each(function(b,c){var d=a(c),g=d.css("overflow-x"),h=d.css("overflow-y");if("visible"!=g||"visible"!=h){var i=c.getBoundingClientRect();if("visible"!=g&&(e.origin.windowOffset.left<i.left||e.origin.windowOffset.right>i.right))return f=!0,!1;if("visible"!=h&&(e.origin.windowOffset.top<i.top||e.origin.windowOffset.bottom>i.bottom))return f=!0,!1}return"fixed"==d.css("position")?!1:void 0}),f)c._$tooltip.css("visibility","hidden");else if(c._$tooltip.css("visibility","visible"),c.__options.repositionOnScroll)c.reposition(b);else{var g=e.origin.offset.left-c.__Geometry.origin.offset.left,i=e.origin.offset.top-c.__Geometry.origin.offset.top;c._$tooltip.css({left:c.__lastPosition.coord.left+g,top:c.__lastPosition.coord.top+i})}}c._trigger({type:"scroll",event:b,geo:e})}return c},__stateSet:function(a){return this.__state=a,this._trigger({type:"state",state:a}),this},__timeoutsClear:function(){return clearTimeout(this.__timeouts.open),this.__timeouts.open=null,a.each(this.__timeouts.close,function(a,b){clearTimeout(b)}),this.__timeouts.close=[],this},__trackerStart:function(){var a=this,b=a._$tooltip.find(".tooltipster-content");return a.__options.trackTooltip&&(a.__contentBcr=b[0].getBoundingClientRect()),a.__tracker=setInterval(function(){if(d(a._$origin)&&d(a._$tooltip)){if(a.__options.trackOrigin){var e=a.__geometry(),f=!1;c(e.origin.size,a.__Geometry.origin.size)&&(a.__Geometry.origin.fixedLineage?c(e.origin.windowOffset,a.__Geometry.origin.windowOffset)&&(f=!0):c(e.origin.offset,a.__Geometry.origin.offset)&&(f=!0)),f||(a.__options.triggerClose.mouseleave?a._close():a.reposition())}if(a.__options.trackTooltip){var g=b[0].getBoundingClientRect();g.height===a.__contentBcr.height&&g.width===a.__contentBcr.width||(a.reposition(),a.__contentBcr=g)}}else a._close()},a.__options.trackerInterval),a},_close:function(b,c,d){var e=this,f=!0;if(e._trigger({type:"close",event:b,stop:function(){f=!1}}),f||d){c&&e.__callbacks.close.push(c),e.__callbacks.open=[],e.__timeoutsClear();var g=function(){a.each(e.__callbacks.close,function(a,c){c.call(e,e,{event:b,origin:e._$origin[0]})}),e.__callbacks.close=[]};if("closed"!=e.__state){var i=!0,j=new Date,k=j.getTime(),l=k+e.__options.animationDuration[1];if("disappearing"==e.__state&&l>e.__closingTime&&e.__options.animationDuration[1]>0&&(i=!1),i){e.__closingTime=l,"disappearing"!=e.__state&&e.__stateSet("disappearing");var m=function(){clearInterval(e.__tracker),e._trigger({type:"closing",event:b}),e._$tooltip.off("."+e.__namespace+"-triggerClose").removeClass("tooltipster-dying"),a(h.window).off("."+e.__namespace+"-triggerClose"),e.__$originParents.each(function(b,c){a(c).off("scroll."+e.__namespace+"-triggerClose")}),e.__$originParents=null,a(h.window.document.body).off("."+e.__namespace+"-triggerClose"),e._$origin.off("."+e.__namespace+"-triggerClose"),e._off("dismissable"),e.__stateSet("closed"),e._trigger({type:"after",event:b}),e.__options.functionAfter&&e.__options.functionAfter.call(e,e,{event:b,origin:e._$origin[0]}),g()};h.hasTransitions?(e._$tooltip.css({"-moz-animation-duration":e.__options.animationDuration[1]+"ms","-ms-animation-duration":e.__options.animationDuration[1]+"ms","-o-animation-duration":e.__options.animationDuration[1]+"ms","-webkit-animation-duration":e.__options.animationDuration[1]+"ms","animation-duration":e.__options.animationDuration[1]+"ms","transition-duration":e.__options.animationDuration[1]+"ms"}),e._$tooltip.clearQueue().removeClass("tooltipster-show").addClass("tooltipster-dying"),e.__options.animationDuration[1]>0&&e._$tooltip.delay(e.__options.animationDuration[1]),e._$tooltip.queue(m)):e._$tooltip.stop().fadeOut(e.__options.animationDuration[1],m)}}else g()}return e},_off:function(){return this.__$emitterPrivate.off.apply(this.__$emitterPrivate,Array.prototype.slice.apply(arguments)),this},_on:function(){return this.__$emitterPrivate.on.apply(this.__$emitterPrivate,Array.prototype.slice.apply(arguments)),this},_one:function(){return this.__$emitterPrivate.one.apply(this.__$emitterPrivate,Array.prototype.slice.apply(arguments)),this},_open:function(b,c){var e=this;if(!e.__destroying&&d(e._$origin)&&e.__enabled){var f=!0;if("closed"==e.__state&&(e._trigger({type:"before",event:b,stop:function(){f=!1}}),f&&e.__options.functionBefore&&(f=e.__options.functionBefore.call(e,e,{event:b,origin:e._$origin[0]}))),f!==!1&&null!==e.__Content){c&&e.__callbacks.open.push(c),e.__callbacks.close=[],e.__timeoutsClear();var g,i=function(){"stable"!=e.__state&&e.__stateSet("stable"),a.each(e.__callbacks.open,function(a,b){b.call(e,e,{origin:e._$origin[0],tooltip:e._$tooltip[0]})}),e.__callbacks.open=[]};if("closed"!==e.__state)g=0,"disappearing"===e.__state?(e.__stateSet("appearing"),h.hasTransitions?(e._$tooltip.clearQueue().removeClass("tooltipster-dying").addClass("tooltipster-show"),e.__options.animationDuration[0]>0&&e._$tooltip.delay(e.__options.animationDuration[0]),e._$tooltip.queue(i)):e._$tooltip.stop().fadeIn(i)):"stable"==e.__state&&i();else{if(e.__stateSet("appearing"),g=e.__options.animationDuration[0],e.__contentInsert(),e.reposition(b,!0),h.hasTransitions?(e._$tooltip.addClass("tooltipster-"+e.__options.animation).addClass("tooltipster-initial").css({"-moz-animation-duration":e.__options.animationDuration[0]+"ms","-ms-animation-duration":e.__options.animationDuration[0]+"ms","-o-animation-duration":e.__options.animationDuration[0]+"ms","-webkit-animation-duration":e.__options.animationDuration[0]+"ms","animation-duration":e.__options.animationDuration[0]+"ms","transition-duration":e.__options.animationDuration[0]+"ms"}),setTimeout(function(){"closed"!=e.__state&&(e._$tooltip.addClass("tooltipster-show").removeClass("tooltipster-initial"),e.__options.animationDuration[0]>0&&e._$tooltip.delay(e.__options.animationDuration[0]),e._$tooltip.queue(i))},0)):e._$tooltip.css("display","none").fadeIn(e.__options.animationDuration[0],i),e.__trackerStart(),a(h.window).on("resize."+e.__namespace+"-triggerClose",function(b){var c=a(document.activeElement);(c.is("input")||c.is("textarea"))&&a.contains(e._$tooltip[0],c[0])||e.reposition(b)}).on("scroll."+e.__namespace+"-triggerClose",function(a){e.__scrollHandler(a)}),e.__$originParents=e._$origin.parents(),e.__$originParents.each(function(b,c){a(c).on("scroll."+e.__namespace+"-triggerClose",function(a){e.__scrollHandler(a)})}),e.__options.triggerClose.mouseleave||e.__options.triggerClose.touchleave&&h.hasTouchCapability){e._on("dismissable",function(a){a.dismissable?a.delay?(m=setTimeout(function(){e._close(a.event)},a.delay),e.__timeouts.close.push(m)):e._close(a):clearTimeout(m)});var j=e._$origin,k="",l="",m=null;e.__options.interactive&&(j=j.add(e._$tooltip)),e.__options.triggerClose.mouseleave&&(k+="mouseenter."+e.__namespace+"-triggerClose ",l+="mouseleave."+e.__namespace+"-triggerClose "),e.__options.triggerClose.touchleave&&h.hasTouchCapability&&(k+="touchstart."+e.__namespace+"-triggerClose",l+="touchend."+e.__namespace+"-triggerClose touchcancel."+e.__namespace+"-triggerClose"),j.on(l,function(a){if(e._touchIsTouchEvent(a)||!e._touchIsEmulatedEvent(a)){var b="mouseleave"==a.type?e.__options.delay:e.__options.delayTouch;e._trigger({delay:b[1],dismissable:!0,event:a,type:"dismissable"})}}).on(k,function(a){!e._touchIsTouchEvent(a)&&e._touchIsEmulatedEvent(a)||e._trigger({dismissable:!1,event:a,type:"dismissable"})})}e.__options.triggerClose.originClick&&e._$origin.on("click."+e.__namespace+"-triggerClose",function(a){e._touchIsTouchEvent(a)||e._touchIsEmulatedEvent(a)||e._close(a)}),(e.__options.triggerClose.click||e.__options.triggerClose.tap&&h.hasTouchCapability)&&setTimeout(function(){if("closed"!=e.__state){var b="",c=a(h.window.document.body);e.__options.triggerClose.click&&(b+="click."+e.__namespace+"-triggerClose "),e.__options.triggerClose.tap&&h.hasTouchCapability&&(b+="touchend."+e.__namespace+"-triggerClose"),c.on(b,function(b){e._touchIsMeaningfulEvent(b)&&(e._touchRecordEvent(b),e.__options.interactive&&a.contains(e._$tooltip[0],b.target)||e._close(b))}),e.__options.triggerClose.tap&&h.hasTouchCapability&&c.on("touchstart."+e.__namespace+"-triggerClose",function(a){e._touchRecordEvent(a)})}},0),e._trigger("ready"),e.__options.functionReady&&e.__options.functionReady.call(e,e,{origin:e._$origin[0],tooltip:e._$tooltip[0]})}if(e.__options.timer>0){var m=setTimeout(function(){e._close()},e.__options.timer+g);e.__timeouts.close.push(m)}}}return e},_openShortly:function(a){var b=this,c=!0;if("stable"!=b.__state&&"appearing"!=b.__state&&!b.__timeouts.open&&(b._trigger({type:"start",event:a,stop:function(){c=!1}}),c)){var d=0==a.type.indexOf("touch")?b.__options.delayTouch:b.__options.delay;d[0]?b.__timeouts.open=setTimeout(function(){b.__timeouts.open=null,b.__pointerIsOverOrigin&&b._touchIsMeaningfulEvent(a)?(b._trigger("startend"),b._open(a)):b._trigger("startcancel")},d[0]):(b._trigger("startend"),b._open(a))}return b},_optionsExtract:function(b,c){var d=this,e=a.extend(!0,{},c),f=d.__options[b];return f||(f={},a.each(c,function(a,b){var c=d.__options[a];void 0!==c&&(f[a]=c)})),a.each(e,function(b,c){void 0!==f[b]&&("object"!=typeof c||c instanceof Array||null==c||"object"!=typeof f[b]||f[b]instanceof Array||null==f[b]?e[b]=f[b]:a.extend(e[b],f[b]))}),e},_plug:function(b){var c=a.tooltipster._plugin(b);if(!c)throw new Error('The "'+b+'" plugin is not defined');return c.instance&&a.tooltipster.__bridge(c.instance,this,c.name),this},_touchIsEmulatedEvent:function(a){for(var b=!1,c=(new Date).getTime(),d=this.__touchEvents.length-1;d>=0;d--){var e=this.__touchEvents[d];if(!(c-e.time<500))break;e.target===a.target&&(b=!0)}return b},_touchIsMeaningfulEvent:function(a){return this._touchIsTouchEvent(a)&&!this._touchSwiped(a.target)||!this._touchIsTouchEvent(a)&&!this._touchIsEmulatedEvent(a)},_touchIsTouchEvent:function(a){return 0==a.type.indexOf("touch")},_touchRecordEvent:function(a){return this._touchIsTouchEvent(a)&&(a.time=(new Date).getTime(),this.__touchEvents.push(a)),this},_touchSwiped:function(a){for(var b=!1,c=this.__touchEvents.length-1;c>=0;c--){var d=this.__touchEvents[c];if("touchmove"==d.type){b=!0;break}if("touchstart"==d.type&&a===d.target)break}return b},_trigger:function(){var b=Array.prototype.slice.apply(arguments);return"string"==typeof b[0]&&(b[0]={type:b[0]}),b[0].instance=this,b[0].origin=this._$origin?this._$origin[0]:null,b[0].tooltip=this._$tooltip?this._$tooltip[0]:null,this.__$emitterPrivate.trigger.apply(this.__$emitterPrivate,b),a.tooltipster._trigger.apply(a.tooltipster,b),this.__$emitterPublic.trigger.apply(this.__$emitterPublic,b),this},_unplug:function(b){var c=this;if(c[b]){var d=a.tooltipster._plugin(b);d.instance&&a.each(d.instance,function(a,d){c[a]&&c[a].bridged===c[b]&&delete c[a]}),c[b].__destroy&&c[b].__destroy(),delete c[b]}return c},close:function(a){return this.__destroyed?this.__destroyError():this._close(null,a),this},content:function(a){var b=this;if(void 0===a)return b.__Content;if(b.__destroyed)b.__destroyError();else if(b.__contentSet(a),null!==b.__Content){if("closed"!==b.__state&&(b.__contentInsert(),b.reposition(),b.__options.updateAnimation))if(h.hasTransitions){var c=b.__options.updateAnimation;b._$tooltip.addClass("tooltipster-update-"+c),setTimeout(function(){"closed"!=b.__state&&b._$tooltip.removeClass("tooltipster-update-"+c)},1e3)}else b._$tooltip.fadeTo(200,.5,function(){"closed"!=b.__state&&b._$tooltip.fadeTo(200,1)})}else b._close();return b},destroy:function(){var b=this;if(b.__destroyed)b.__destroyError();else{"closed"!=b.__state?b.option("animationDuration",0)._close(null,null,!0):b.__timeoutsClear(),b._trigger("destroy"),b.__destroyed=!0,b._$origin.removeData(b.__namespace).off("."+b.__namespace+"-triggerOpen"),a(h.window.document.body).off("."+b.__namespace+"-triggerOpen");var c=b._$origin.data("tooltipster-ns");if(c)if(1===c.length){var d=null;"previous"==b.__options.restoration?d=b._$origin.data("tooltipster-initialTitle"):"current"==b.__options.restoration&&(d="string"==typeof b.__Content?b.__Content:a("<div></div>").append(b.__Content).html()),d&&b._$origin.attr("title",d),b._$origin.removeClass("tooltipstered"),b._$origin.removeData("tooltipster-ns").removeData("tooltipster-initialTitle")}else c=a.grep(c,function(a,c){return a!==b.__namespace}),b._$origin.data("tooltipster-ns",c);b._trigger("destroyed"),b._off(),b.off(),b.__Content=null,b.__$emitterPrivate=null,b.__$emitterPublic=null,b.__options.parent=null,b._$origin=null,b._$tooltip=null,a.tooltipster.__instancesLatestArr=a.grep(a.tooltipster.__instancesLatestArr,function(a,c){return b!==a}),clearInterval(b.__garbageCollector)}return b},disable:function(){return this.__destroyed?(this.__destroyError(),this):(this._close(),this.__enabled=!1,this)},elementOrigin:function(){return this.__destroyed?void this.__destroyError():this._$origin[0]},elementTooltip:function(){return this._$tooltip?this._$tooltip[0]:null},enable:function(){return this.__enabled=!0,this},hide:function(a){return this.close(a)},instance:function(){return this},off:function(){return this.__destroyed||this.__$emitterPublic.off.apply(this.__$emitterPublic,Array.prototype.slice.apply(arguments)),this},on:function(){return this.__destroyed?this.__destroyError():this.__$emitterPublic.on.apply(this.__$emitterPublic,Array.prototype.slice.apply(arguments)),this},one:function(){return this.__destroyed?this.__destroyError():this.__$emitterPublic.one.apply(this.__$emitterPublic,Array.prototype.slice.apply(arguments)),this},open:function(a){return this.__destroyed?this.__destroyError():this._open(null,a),this},option:function(b,c){return void 0===c?this.__options[b]:(this.__destroyed?this.__destroyError():(this.__options[b]=c,this.__optionsFormat(),a.inArray(b,["trigger","triggerClose","triggerOpen"])>=0&&this.__prepareOrigin(),"selfDestruction"===b&&this.__prepareGC()),this)},reposition:function(a,b){var c=this;return c.__destroyed?c.__destroyError():"closed"!=c.__state&&d(c._$origin)&&(b||d(c._$tooltip))&&(b||c._$tooltip.detach(),c.__Geometry=c.__geometry(),c._trigger({type:"reposition",event:a,helper:{geo:c.__Geometry}})),c},show:function(a){return this.open(a)},status:function(){return{destroyed:this.__destroyed,enabled:this.__enabled,open:"closed"!==this.__state,state:this.__state}},triggerHandler:function(){return this.__destroyed?this.__destroyError():this.__$emitterPublic.triggerHandler.apply(this.__$emitterPublic,Array.prototype.slice.apply(arguments)),this}},a.fn.tooltipster=function(){var b=Array.prototype.slice.apply(arguments),c="You are using a single HTML element as content for several tooltips. You probably want to set the contentCloning option to TRUE.";if(0===this.length)return this;if("string"==typeof b[0]){var d="#*$~&";return this.each(function(){var e=a(this).data("tooltipster-ns"),f=e?a(this).data(e[0]):null;if(!f)throw new Error("You called Tooltipster's \""+b[0]+'" method on an uninitialized element');if("function"!=typeof f[b[0]])throw new Error('Unknown method "'+b[0]+'"');this.length>1&&"content"==b[0]&&(b[1]instanceof a||"object"==typeof b[1]&&null!=b[1]&&b[1].tagName)&&!f.__options.contentCloning&&f.__options.debug&&console.log(c);var g=f[b[0]](b[1],b[2]);return g!==f||"instance"===b[0]?(d=g,!1):void 0}),"#*$~&"!==d?d:this}a.tooltipster.__instancesLatestArr=[];var e=b[0]&&void 0!==b[0].multiple,g=e&&b[0].multiple||!e&&f.multiple,h=b[0]&&void 0!==b[0].content,i=h&&b[0].content||!h&&f.content,j=b[0]&&void 0!==b[0].contentCloning,k=j&&b[0].contentCloning||!j&&f.contentCloning,l=b[0]&&void 0!==b[0].debug,m=l&&b[0].debug||!l&&f.debug;return this.length>1&&(i instanceof a||"object"==typeof i&&null!=i&&i.tagName)&&!k&&m&&console.log(c),this.each(function(){var c=!1,d=a(this),e=d.data("tooltipster-ns"),f=null;e?g?c=!0:m&&(console.log("Tooltipster: one or more tooltips are already attached to the element below. Ignoring."),console.log(this)):c=!0,c&&(f=new a.Tooltipster(this,b[0]),e||(e=[]),e.push(f.__namespace),d.data("tooltipster-ns",e),d.data(f.__namespace,f),f.__options.functionInit&&f.__options.functionInit.call(f,f,{origin:this}),f._trigger("init")),a.tooltipster.__instancesLatestArr.push(f)}),this},b.prototype={__init:function(b){this.__$tooltip=b,this.__$tooltip.css({left:0,overflow:"hidden",position:"absolute",top:0}).find(".tooltipster-content").css("overflow","auto"),this.$container=a('<div class="tooltipster-ruler"></div>').append(this.__$tooltip).appendTo(h.window.document.body)},__forceRedraw:function(){var a=this.__$tooltip.parent();this.__$tooltip.detach(),this.__$tooltip.appendTo(a)},constrain:function(a,b){return this.constraints={width:a,height:b},this.__$tooltip.css({display:"block",height:"",overflow:"auto",width:a}),this},destroy:function(){this.__$tooltip.detach().find(".tooltipster-content").css({display:"",overflow:""}),this.$container.remove()},free:function(){return this.constraints=null,this.__$tooltip.css({display:"",height:"",overflow:"visible",width:""}),this},measure:function(){this.__forceRedraw();var a=this.__$tooltip[0].getBoundingClientRect(),b={size:{height:a.height||a.bottom-a.top,width:a.width||a.right-a.left}};if(this.constraints){var c=this.__$tooltip.find(".tooltipster-content"),d=this.__$tooltip.outerHeight(),e=c[0].getBoundingClientRect(),f={height:d<=this.constraints.height,width:a.width<=this.constraints.width&&e.width>=c[0].scrollWidth-1};b.fits=f.height&&f.width}return h.IE&&h.IE<=11&&b.size.width!==h.window.document.documentElement.clientWidth&&(b.size.width=Math.ceil(b.size.width)+1),b}};var j=navigator.userAgent.toLowerCase();-1!=j.indexOf("msie")?h.IE=parseInt(j.split("msie")[1]):-1!==j.toLowerCase().indexOf("trident")&&-1!==j.indexOf(" rv:11")?h.IE=11:-1!=j.toLowerCase().indexOf("edge/")&&(h.IE=parseInt(j.toLowerCase().split("edge/")[1]));var k="tooltipster.sideTip";return a.tooltipster._plugin({name:k,instance:{__defaults:function(){return{arrow:!0,distance:6,functionPosition:null,maxWidth:null,minIntersection:16,minWidth:0,position:null,side:"top",viewportAware:!0}},__init:function(a){var b=this;b.__instance=a,b.__namespace="tooltipster-sideTip-"+Math.round(1e6*Math.random()),b.__previousState="closed",b.__options,b.__optionsFormat(),b.__instance._on("state."+b.__namespace,function(a){"closed"==a.state?b.__close():"appearing"==a.state&&"closed"==b.__previousState&&b.__create(),b.__previousState=a.state}),b.__instance._on("options."+b.__namespace,function(){b.__optionsFormat()}),b.__instance._on("reposition."+b.__namespace,function(a){b.__reposition(a.event,a.helper)})},__close:function(){this.__instance.content()instanceof a&&this.__instance.content().detach(),this.__instance._$tooltip.remove(),this.__instance._$tooltip=null},__create:function(){var b=a('<div class="tooltipster-base tooltipster-sidetip"><div class="tooltipster-box"><div class="tooltipster-content"></div></div><div class="tooltipster-arrow"><div class="tooltipster-arrow-uncropped"><div class="tooltipster-arrow-border"></div><div class="tooltipster-arrow-background"></div></div></div></div>');this.__options.arrow||b.find(".tooltipster-box").css("margin",0).end().find(".tooltipster-arrow").hide(),this.__options.minWidth&&b.css("min-width",this.__options.minWidth+"px"),this.__options.maxWidth&&b.css("max-width",this.__options.maxWidth+"px"),
this.__instance._$tooltip=b,this.__instance._trigger("created")},__destroy:function(){this.__instance._off("."+self.__namespace)},__optionsFormat:function(){var b=this;if(b.__options=b.__instance._optionsExtract(k,b.__defaults()),b.__options.position&&(b.__options.side=b.__options.position),"object"!=typeof b.__options.distance&&(b.__options.distance=[b.__options.distance]),b.__options.distance.length<4&&(void 0===b.__options.distance[1]&&(b.__options.distance[1]=b.__options.distance[0]),void 0===b.__options.distance[2]&&(b.__options.distance[2]=b.__options.distance[0]),void 0===b.__options.distance[3]&&(b.__options.distance[3]=b.__options.distance[1]),b.__options.distance={top:b.__options.distance[0],right:b.__options.distance[1],bottom:b.__options.distance[2],left:b.__options.distance[3]}),"string"==typeof b.__options.side){var c={top:"bottom",right:"left",bottom:"top",left:"right"};b.__options.side=[b.__options.side,c[b.__options.side]],"left"==b.__options.side[0]||"right"==b.__options.side[0]?b.__options.side.push("top","bottom"):b.__options.side.push("right","left")}6===a.tooltipster._env.IE&&b.__options.arrow!==!0&&(b.__options.arrow=!1)},__reposition:function(b,c){var d,e=this,f=e.__targetFind(c),g=[];e.__instance._$tooltip.detach();var h=e.__instance._$tooltip.clone(),i=a.tooltipster._getRuler(h),j=!1,k=e.__instance.option("animation");switch(k&&h.removeClass("tooltipster-"+k),a.each(["window","document"],function(d,k){var l=null;if(e.__instance._trigger({container:k,helper:c,satisfied:j,takeTest:function(a){l=a},results:g,type:"positionTest"}),1==l||0!=l&&0==j&&("window"!=k||e.__options.viewportAware))for(var d=0;d<e.__options.side.length;d++){var m={horizontal:0,vertical:0},n=e.__options.side[d];"top"==n||"bottom"==n?m.vertical=e.__options.distance[n]:m.horizontal=e.__options.distance[n],e.__sideChange(h,n),a.each(["natural","constrained"],function(a,d){if(l=null,e.__instance._trigger({container:k,event:b,helper:c,mode:d,results:g,satisfied:j,side:n,takeTest:function(a){l=a},type:"positionTest"}),1==l||0!=l&&0==j){var h={container:k,distance:m,fits:null,mode:d,outerSize:null,side:n,size:null,target:f[n],whole:null},o="natural"==d?i.free():i.constrain(c.geo.available[k][n].width-m.horizontal,c.geo.available[k][n].height-m.vertical),p=o.measure();if(h.size=p.size,h.outerSize={height:p.size.height+m.vertical,width:p.size.width+m.horizontal},"natural"==d?c.geo.available[k][n].width>=h.outerSize.width&&c.geo.available[k][n].height>=h.outerSize.height?h.fits=!0:h.fits=!1:h.fits=p.fits,"window"==k&&(h.fits?"top"==n||"bottom"==n?h.whole=c.geo.origin.windowOffset.right>=e.__options.minIntersection&&c.geo.window.size.width-c.geo.origin.windowOffset.left>=e.__options.minIntersection:h.whole=c.geo.origin.windowOffset.bottom>=e.__options.minIntersection&&c.geo.window.size.height-c.geo.origin.windowOffset.top>=e.__options.minIntersection:h.whole=!1),g.push(h),h.whole)j=!0;else if("natural"==h.mode&&(h.fits||h.size.width<=c.geo.available[k][n].width))return!1}})}}),e.__instance._trigger({edit:function(a){g=a},event:b,helper:c,results:g,type:"positionTested"}),g.sort(function(a,b){if(a.whole&&!b.whole)return-1;if(!a.whole&&b.whole)return 1;if(a.whole&&b.whole){var c=e.__options.side.indexOf(a.side),d=e.__options.side.indexOf(b.side);return d>c?-1:c>d?1:"natural"==a.mode?-1:1}if(a.fits&&!b.fits)return-1;if(!a.fits&&b.fits)return 1;if(a.fits&&b.fits){var c=e.__options.side.indexOf(a.side),d=e.__options.side.indexOf(b.side);return d>c?-1:c>d?1:"natural"==a.mode?-1:1}return"document"==a.container&&"bottom"==a.side&&"natural"==a.mode?-1:1}),d=g[0],d.coord={},d.side){case"left":case"right":d.coord.top=Math.floor(d.target-d.size.height/2);break;case"bottom":case"top":d.coord.left=Math.floor(d.target-d.size.width/2)}switch(d.side){case"left":d.coord.left=c.geo.origin.windowOffset.left-d.outerSize.width;break;case"right":d.coord.left=c.geo.origin.windowOffset.right+d.distance.horizontal;break;case"top":d.coord.top=c.geo.origin.windowOffset.top-d.outerSize.height;break;case"bottom":d.coord.top=c.geo.origin.windowOffset.bottom+d.distance.vertical}"window"==d.container?"top"==d.side||"bottom"==d.side?d.coord.left<0?c.geo.origin.windowOffset.right-this.__options.minIntersection>=0?d.coord.left=0:d.coord.left=c.geo.origin.windowOffset.right-this.__options.minIntersection-1:d.coord.left>c.geo.window.size.width-d.size.width&&(c.geo.origin.windowOffset.left+this.__options.minIntersection<=c.geo.window.size.width?d.coord.left=c.geo.window.size.width-d.size.width:d.coord.left=c.geo.origin.windowOffset.left+this.__options.minIntersection+1-d.size.width):d.coord.top<0?c.geo.origin.windowOffset.bottom-this.__options.minIntersection>=0?d.coord.top=0:d.coord.top=c.geo.origin.windowOffset.bottom-this.__options.minIntersection-1:d.coord.top>c.geo.window.size.height-d.size.height&&(c.geo.origin.windowOffset.top+this.__options.minIntersection<=c.geo.window.size.height?d.coord.top=c.geo.window.size.height-d.size.height:d.coord.top=c.geo.origin.windowOffset.top+this.__options.minIntersection+1-d.size.height):(d.coord.left>c.geo.window.size.width-d.size.width&&(d.coord.left=c.geo.window.size.width-d.size.width),d.coord.left<0&&(d.coord.left=0)),e.__sideChange(h,d.side),c.tooltipClone=h[0],c.tooltipParent=e.__instance.option("parent").parent[0],c.mode=d.mode,c.whole=d.whole,c.origin=e.__instance._$origin[0],c.tooltip=e.__instance._$tooltip[0],delete d.container,delete d.fits,delete d.mode,delete d.outerSize,delete d.whole,d.distance=d.distance.horizontal||d.distance.vertical;var l=a.extend(!0,{},d);if(e.__instance._trigger({edit:function(a){d=a},event:b,helper:c,position:l,type:"position"}),e.__options.functionPosition){var m=e.__options.functionPosition.call(e,e.__instance,c,l);m&&(d=m)}i.destroy();var n,o;"top"==d.side||"bottom"==d.side?(n={prop:"left",val:d.target-d.coord.left},o=d.size.width-this.__options.minIntersection):(n={prop:"top",val:d.target-d.coord.top},o=d.size.height-this.__options.minIntersection),n.val<this.__options.minIntersection?n.val=this.__options.minIntersection:n.val>o&&(n.val=o);var p;p=c.geo.origin.fixedLineage?c.geo.origin.windowOffset:{left:c.geo.origin.windowOffset.left+c.geo.window.scroll.left,top:c.geo.origin.windowOffset.top+c.geo.window.scroll.top},d.coord={left:p.left+(d.coord.left-c.geo.origin.windowOffset.left),top:p.top+(d.coord.top-c.geo.origin.windowOffset.top)},e.__sideChange(e.__instance._$tooltip,d.side),c.geo.origin.fixedLineage?e.__instance._$tooltip.css("position","fixed"):e.__instance._$tooltip.css("position",""),e.__instance._$tooltip.css({left:d.coord.left,top:d.coord.top,height:d.size.height,width:d.size.width}).find(".tooltipster-arrow").css({left:"",top:""}).css(n.prop,n.val),e.__instance._$tooltip.appendTo(e.__instance.option("parent")),e.__instance._trigger({type:"repositioned",event:b,position:d})},__sideChange:function(a,b){a.removeClass("tooltipster-bottom").removeClass("tooltipster-left").removeClass("tooltipster-right").removeClass("tooltipster-top").addClass("tooltipster-"+b)},__targetFind:function(a){var b={},c=this.__instance._$origin[0].getClientRects();if(c.length>1){var d=this.__instance._$origin.css("opacity");1==d&&(this.__instance._$origin.css("opacity",.99),c=this.__instance._$origin[0].getClientRects(),this.__instance._$origin.css("opacity",1))}if(c.length<2)b.top=Math.floor(a.geo.origin.windowOffset.left+a.geo.origin.size.width/2),b.bottom=b.top,b.left=Math.floor(a.geo.origin.windowOffset.top+a.geo.origin.size.height/2),b.right=b.left;else{var e=c[0];b.top=Math.floor(e.left+(e.right-e.left)/2),e=c.length>2?c[Math.ceil(c.length/2)-1]:c[0],b.right=Math.floor(e.top+(e.bottom-e.top)/2),e=c[c.length-1],b.bottom=Math.floor(e.left+(e.right-e.left)/2),e=c.length>2?c[Math.ceil((c.length+1)/2)-1]:c[c.length-1],b.left=Math.floor(e.top+(e.bottom-e.top)/2)}return b}}}),a});/*!
	Autosize v1.18.4 - 2014-01-11
	Automatically adjust textarea height based on user input.
	(c) 2014 Jack Moore - http://www.jacklmoore.com/autosize
	license: http://www.opensource.org/licenses/mit-license.php
*/
!function(a){var b,c={className:"autosizejs",append:"",callback:!1,resizeDelay:10,placeholder:!0},d='<textarea tabindex="-1" style="position:absolute; top:-999px; left:0; right:auto; bottom:auto; border:0; padding: 0; -moz-box-sizing:content-box; -webkit-box-sizing:content-box; box-sizing:content-box; word-wrap:break-word; height:0 !important; min-height:0 !important; overflow:hidden; transition:none; -webkit-transition:none; -moz-transition:none;"/>',e=["fontFamily","fontSize","fontWeight","fontStyle","letterSpacing","textTransform","wordSpacing","textIndent"],f=a(d).data("autosize",!0)[0];f.style.lineHeight="99px","99px"===a(f).css("lineHeight")&&e.push("lineHeight"),f.style.lineHeight="",a.fn.autosize=function(d){return this.length?(d=a.extend({},c,d||{}),f.parentNode!==document.body&&a(document.body).append(f),this.each(function(){function c(){var b,c=window.getComputedStyle?window.getComputedStyle(m,null):!1;c?(b=m.getBoundingClientRect().width,0===b&&(b=parseInt(c.width,10)),a.each(["paddingLeft","paddingRight","borderLeftWidth","borderRightWidth"],function(a,d){b-=parseInt(c[d],10)})):b=Math.max(n.width(),0),f.style.width=b+"px"}function g(){var g={};if(b=m,f.className=d.className,j=parseInt(n.css("maxHeight"),10),a.each(e,function(a,b){g[b]=n.css(b)}),a(f).css(g),c(),window.chrome){var h=m.style.width;m.style.width="0px";{m.offsetWidth}m.style.width=h}}function h(){var e,h;b!==m?g():c(),f.value=!m.value&&d.placeholder?(a(m).attr("placeholder")||"")+d.append:m.value+d.append,f.style.overflowY=m.style.overflowY,h=parseInt(m.style.height,10),f.scrollTop=0,f.scrollTop=9e4,e=f.scrollTop,j&&e>j?(m.style.overflowY="scroll",e=j):(m.style.overflowY="hidden",k>e&&(e=k)),e+=o,h!==e&&(m.style.height=e+"px",p&&d.callback.call(m,m))}function i(){clearTimeout(l),l=setTimeout(function(){var a=n.width();a!==r&&(r=a,h())},parseInt(d.resizeDelay,10))}var j,k,l,m=this,n=a(m),o=0,p=a.isFunction(d.callback),q={height:m.style.height,overflow:m.style.overflow,overflowY:m.style.overflowY,wordWrap:m.style.wordWrap,resize:m.style.resize},r=n.width();n.data("autosize")||(n.data("autosize",!0),("border-box"===n.css("box-sizing")||"border-box"===n.css("-moz-box-sizing")||"border-box"===n.css("-webkit-box-sizing"))&&(o=n.outerHeight()-n.height()),k=Math.max(parseInt(n.css("minHeight"),10)-o||0,n.height()),n.css({overflow:"hidden",overflowY:"hidden",wordWrap:"break-word",resize:"none"===n.css("resize")||"vertical"===n.css("resize")?"none":"horizontal"}),"onpropertychange"in m?"oninput"in m?n.on("input.autosize keyup.autosize",h):n.on("propertychange.autosize",function(){"value"===event.propertyName&&h()}):n.on("input.autosize",h),d.resizeDelay!==!1&&a(window).on("resize.autosize",i),n.on("autosize.resize",h),n.on("autosize.resizeIncludeStyle",function(){b=null,h()}),n.on("autosize.destroy",function(){b=null,clearTimeout(l),a(window).off("resize",i),n.off("autosize").off(".autosize").css(q).removeData("autosize")}),h())})):this}}(window.jQuery||window.$);function FOXexpander(id, minHeight, openClass, openPrompt, closeClass, closePrompt, accessibleOpenPrompt, accessibleClosePrompt, animationDuration) {
  var $expanderElement = $('#' + id);
  var $button = $('#' + id + "-button");
  if($expanderElement.height() > parseInt(minHeight)) {
    $expanderElement.animate({height:minHeight}, animationDuration);
    $button.removeClass(closeClass);
    $button.addClass(openClass)
    $expanderElement.addClass('show-expander-gradient-background');
    $button.text(openPrompt);
    $expanderElement.attr('aria-expanded',  'false');
    $button.attr('aria-label', accessibleOpenPrompt);
  } else {
    $expanderElement.animate({height:$expanderElement.get(0).scrollHeight}, animationDuration);
    $button.text(closePrompt);
    $expanderElement.removeClass('show-expander-gradient-background');
    $button.removeClass(openClass);
    $button.addClass(closeClass);
    $expanderElement.attr('aria-expanded',  'true');
    $button.attr('aria-label', accessibleClosePrompt);
  }

  //Avoid the page jumping
  return false;
}
