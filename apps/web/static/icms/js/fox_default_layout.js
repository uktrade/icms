function compressTopMenu() {
  //Reset any compression performed before
  $(".overflow-menu").remove();
  $("#top-menu>li").not('#user-info').removeAttr('style');
  

  //If the media query has collapsed the menu down anyway, don't continue
  if($('#top-nav-toggle-label').css('display') == 'block') {
    return true;
  }

  //Find the width of all the elements in the menu bar
  //Add 20px at the start so we start collapsing a bit before stuff starts touching
  var totalWidth = 25;
  totalWidth += $('#menu-bar>h1').outerWidth();

  $('#top-menu>li').each(function(){
    totalWidth += $(this).outerWidth();
  });

  //If the menu is going to overflow, compress it
  if(totalWidth > $(window).width()){

    //Put in the 'More' dropdown and make sure we take its width into account
    $('#top-menu>li').not('.top-menu-button').not('#user-info').last().after('<li class="top-menu-dropdown overflow-menu"><a class="dropdown-label" href="#">More</a><ul></ul></li>');
    var compressedWidth = totalWidth + $('.overflow-menu').outerWidth();

    $($("#top-menu>li").not('.top-menu-button').not('#user-info').not('.overflow-menu').get().reverse()).each(function() { 
      compressedWidth -= $(this).outerWidth();
      $(this).clone().prependTo('.overflow-menu>ul')
      $(this).hide(0);  
      if(compressedWidth <= $(window).width()) {
        return false; //break out of .each()
      }    
    });

    //If we're still overflowing, start collapsing the buttons too
    if(compressedWidth > $(window).width()) {
      $($("#top-menu>li.top-menu-button").get().reverse()).each(function() {
        compressedWidth -= $(this).outerWidth();
        $(this).clone().prependTo('.overflow-menu>ul')
        $(this).hide(0);  
        if(compressedWidth <= $(window).width()) {
          return false; //break out of .each()
        }  
      });
    }
  }
}

$(window).resize(compressTopMenu);
$(window).load(compressTopMenu);


var StickySidebar = {
  gSidebarExists: null,
  gOriginalTop: null,
  gSidebarHeight: null,
  gIsFixed: null,
  gPrevScrollPosition: 0,
  gIsMobile: null,

  processScroll: function() {
    //No sticky sidebar if we're on mobile, or there's no sidebar, or the sidebar is taller than the content
    if(this.gIsMobile || !this.gSidebarExists || $('#sidebar').height() > $('#content').height()) {
      return true;
    }

    //Handle simple case where sidebar is shorter than viewport.
    //We can just switch between position:fixed and position:relative
    if(this.gSidebarHeight <= $(window).height()) {
      if($(document).scrollTop() > this.gOriginalTop) {
        if(!this.gIsFixed) {
          $('#sidebar').css('position','fixed');
          $('#sidebar-substitute').show(0);
          this.gIsFixed = true;
        }
      }
      else {
        if(this.gIsFixed) {
          $('#sidebar').css('position','relative');
          $('#sidebar-substitute').hide(0);
          this.gIsFixed = false;
        }    
      }
    }
    //We're scrolling down but the sidebar is already position: fixed, so recalculate its top
    else if(this.gPrevScrollPosition < $(window).scrollTop() && this.gIsFixed && $(window).height() + $(window).scrollTop() <= this.gSidebarHeight + this.gOriginalTop) {
      var newTop = parseFloat($('#sidebar').css('top')) + (this.gPrevScrollPosition - $(window).scrollTop());
      newTop = (newTop > 0) ? 0 : newTop;
      $('#sidebar').css('top',newTop);
    }    
    //We're scrolling down and the bottom of the sidebar is now visible
    //Switch to position:fixed so bottom of sidebar remains at bottom of viewport
    else if(this.gPrevScrollPosition < $(window).scrollTop() && $(window).height() + $(window).scrollTop() > this.gSidebarHeight + this.gOriginalTop) {
      $('#sidebar').css('position','fixed');
      $('#sidebar').css('top',$(window).height() - this.gSidebarHeight);
      $('#sidebar-substitute').show(0);
      this.gIsFixed = true;
    }
    //We're scrolling up so scroll the sidebar up, unless the top of the sidebar is already at the top of the viewport
    else if(this.gIsFixed && this.gPrevScrollPosition > $(window).scrollTop() && $(window).scrollTop() > this.gOriginalTop) {
      var newTop = parseFloat($('#sidebar').css('top')) + (this.gPrevScrollPosition - $(window).scrollTop());
      newTop = (newTop > 0) ? 0 : newTop;
      $('#sidebar').css('top',newTop);
    }
    else if(this.gIsFixed && this.gPrevScrollPosition > $(window).scrollTop() && $(window).scrollTop() <= this.gOriginalTop){
      $('#sidebar').css('position','relative');
      $('#sidebar-substitute').hide(0);
      this.gIsFixed = false;     
    }

    this.gPrevScrollPosition = $(window).scrollTop();
  },

  checkIfMobile: function() {
    if(!this.gSidebarExists) {
      return true;
    }

    if($(window).width() < 800) {
      $('#sidebar').css('position','relative');
      $('#sidebar-substitute').hide(0);
      this.gIsFixed = false;  
      this.gIsMobile = true;        
    } 
    else {
      this.gIsMobile = false;
    }
  },

  init: function() {

    if($('#sidebar').length > 0) {
      this.gSidebarExists = true;
    } 
    else {
      this.gSidebarExists = false;
      return;
    }

    this.gOriginalTop = $('#sidebar').offset().top - parseInt($('#sidebar').css('padding-top'));
    this.gSidebarHeight = parseFloat($('#sidebar').css('height')) + parseFloat($('#sidebar').css('padding-top')) + parseFloat($('#sidebar').css('padding-bottom'));
    this.gPrevScrollPosition = $(window).scrollTop();
    this.gIsFixed = false;
    this.gIsMobile = false;
  }
};

$(window).load(StickySidebar.init);
$(window).load(StickySidebar.checkIfMobile);
$(window).scroll(StickySidebar.processScroll);
$(window).resize(StickySidebar.checkIfMobile);


//Expand nav bar dropdown when tabbing
//Use delegated events for .top-menu-dropdown so it works for the 'More' menu, which is created dynamically
$('body').on('focusin','#top-menu>li',function() { 
  $(this).children("ul").css("display", "block"); 
  $(this).addClass("focussed");
});

$('body').on('focusout','#top-menu>li',function() { 
  $(this).children("ul").css("display", ""); 
  $(this).removeClass("focussed");
});

$('body').on('focusin','.top-menu-subcategory-action',function() { 
  $(this).addClass("focussed");
});

$('body').on('focusout','.top-menu-subcategory-action',function() { 
  $(this).removeClass("focussed");
});

$('body').on('click','.dropdown-label',function(e) { 
  return false; 
});