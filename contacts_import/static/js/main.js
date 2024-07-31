!(function ($) {
  "use strict";

  // Smooth scroll for the navigation menu and links with .scrollto classes
  $(document).on('click', '.nav-menu a, .mobile-nav a, .scrollto', function (e) {
    if (location.pathname.replace(/^\//, '') == this.pathname.replace(/^\//, '') && location.hostname == this.hostname) {
      var target = $(this.hash);
      if (target.length) {
        e.preventDefault();

        var scrollto = target.offset().top;
        var scrolled = 0;

        if ($('#header').length) {
          scrollto -= $('#header').outerHeight()

          if (!$('#header').hasClass('header-scrolled')) {
            scrollto += scrolled;
          }
        }

        if ($(this).attr("href") == '#header') {
          scrollto = 0;
        }

        $('html, body').animate({
          scrollTop: scrollto
        }, 1500, 'easeInOutExpo');

        if ($(this).parents('.nav-menu, .mobile-nav').length) {
          $('.nav-menu .active, .mobile-nav .active').removeClass('active');
          $(this).closest('li').addClass('active');
        }

        if ($('body').hasClass('mobile-nav-active')) {
          $('body').removeClass('mobile-nav-active');
          $('.mobile-nav-toggle i').toggleClass('icofont-navigation-menu icofont-close');
          $('.mobile-nav-overly').fadeOut();
        }
        return false;
      }
    }
  });

  // Advanced Filters under search bar
  $('#search_filters').on('click', function () {
    $('.filter-form').toggleClass('filter-hide');
  });

  $(document).on("click", function (e) {
    var elemExclude = $(".filter-form, input#search_filters");
    if ($('.filter-form').not('.filter-hide')) {
      if (!elemExclude.is(e.target) && elemExclude.has(e.target).length === 0) {
        $('.filter-form').addClass('filter-hide');
      }
    }

  });

  // Mobile Navigation
  if ($('.nav-menu').length) {
    var $mobile_nav = $('.nav-menu').clone().prop({
      class: 'mobile-nav d-lg-none'
    });
    $('body').append($mobile_nav);
    $('body').prepend('<button type="button" class="mobile-nav-toggle d-lg-none"><i class="icofont-navigation-menu"></i></button>');
    $('body').append('<div class="mobile-nav-overly"></div>');

    $(document).on('click', '.mobile-nav-toggle', function (e) {
      $('body').toggleClass('mobile-nav-active');
      $('.mobile-nav-toggle i').toggleClass('icofont-navigation-menu icofont-close');
      $('.mobile-nav-overly').toggle();
    });

    $(document).on('click', '.mobile-nav .drop-down > a', function (e) {
      e.preventDefault();
      $(this).next().slideToggle(300);
      $(this).parent().toggleClass('active');
    });

    $(document).click(function (e) {
      var container = $(".mobile-nav, .mobile-nav-toggle");
      if (!container.is(e.target) && container.has(e.target).length === 0) {
        if ($('body').hasClass('mobile-nav-active')) {
          $('body').removeClass('mobile-nav-active');
          $('.mobile-nav-toggle i').toggleClass('icofont-navigation-menu icofont-close');
          $('.mobile-nav-overly').fadeOut();
        }
      }
    });
  } else if ($(".mobile-nav, .mobile-nav-toggle").length) {
    $(".mobile-nav, .mobile-nav-toggle").hide();
  }
  // Back to top button
  $(window).scroll(function () {
    if ($(this).scrollTop() > 100) {
      $('.back-to-top').fadeIn('slow');
    } else {
      $('.back-to-top').fadeOut('slow');
    }

    if ($(this).scrollTop() > 140) {
      $('.search-container').addClass('sticky');
    } else {
      $('.search-container').removeClass('sticky');
    }
  });

  $('.back-to-top').click(function () {
    $('html, body').animate({
      scrollTop: 0
    }, 1500, 'easeInOutExpo');
    return false;
  });

  // Clients carousel (uses the Owl Carousel library)
  $(".result-carousel").owlCarousel({
    nav: true,
    autoplay: false,
    dots: false,
    loop: true,
    items: 3
  });

  // Initi AOS
  function aos_init() {
    AOS.init({
      duration: 1000,
      easing: "ease-in-out-back",
      once: true
    });
  }
  aos_init();


  populateCountries("countrys_list", "state_list");

  function reSet() {
    document.getElementById("adv_filtr_frm").reset();
  }
  $('#reset_filter_frm').on('click', reSet);

  // progress bars in Advanced Filter
  $('.progress-container').each(function () {
    var contn = $(this);
    var nxtBtn = $(this).children('button.nexts');
    var prevBtn = $(this).children('button.previouss');
    var prgsBar = contn.children('.bar-progress');
    var prgrs = prgsBar.children();
    var firstPrgrs = prgrs.first();
    var lastPrgrs = prgrs.last();

    if (firstPrgrs.hasClass('active')) {
      prevBtn.addClass('disabled');
    } else {
      prevBtn.removeClass('disabled');
    }

    if (lastPrgrs.hasClass('active')) {
      nxtBtn.addClass('disabled');
    } else {
      nxtBtn.removeClass('disabled');
    }

    contn.on('click', 'button', function (e) {
      var prgrsActive = $(this).siblings().children('.active');
      if ($(e.target).is('.nexts')) {
        prgrsActive.removeClass('active');
        prgrsActive.next().addClass('active');
      }
      if ($(e.target).is('.previouss')) {
        prgrsActive.removeClass('active');
        prgrsActive.prev().addClass('active');
      }
      if (firstPrgrs.hasClass('active')) {
        prevBtn.addClass('disabled');
      } else {
        prevBtn.removeClass('disabled');
      }

      if (lastPrgrs.hasClass('active')) {
        nxtBtn.addClass('disabled');
      } else {
        nxtBtn.removeClass('disabled');
      }
    })

    prgsBar.on('click', '.prgrs', function (e) {
      $(this).siblings().removeClass('active');
      $(this).addClass('active');
      if (firstPrgrs.hasClass('active')) {
        prevBtn.addClass('disabled');
      } else {
        prevBtn.removeClass('disabled');
      }

      if (lastPrgrs.hasClass('active')) {
        nxtBtn.addClass('disabled');
      } else {
        nxtBtn.removeClass('disabled');
      }
    });
  });

})(jQuery);