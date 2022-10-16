<html>
 <head>
  <meta charset="utf-8">
  <link rel="stylesheet" type="text/css" href="/static/css/nav.css">
  <script type="text/javascript" src="/static/js/jquery-3.3.1.min.js"></script>
  <script type="text/javascript" src="/static/js/NoSleep.js"></script>
  <script type="text/javascript">

  /* prevent android sleep */
  $(document).ready(function(){
    var isAndroid = navigator.userAgent.toLowerCase().indexOf("android");
    var isiPad = navigator.userAgent.toLowerCase().indexOf("ipad");
    if(isAndroid > -1 || isiPad > -1) 
    {
      var noSleep = new NoSleep();
      document.addEventListener('click', function enableNoSleep() {
        document.removeEventListener('click', enableNoSleep, false);
        noSleep.enable();
      }, false);
    }     
});


  var page = {{page}};

  function preload(url) {
    var img = new Image();
    img.src = url;
  }

  function showPage(n) {
    page = n;
    $('#spinner').show();
    $('#page').html(page); //update page number
    $('#image').one("load", function() { $('#spinner').hide(); }).attr('src', "/getpage/{{serie.urlname}}/{{album.urlname}}/" + page);

    return false;
  }

  function prevPage() {
    if(page > 1) {
      page -= 1;
      $('#spinner').show();
      $('#image').one("load", function() { $('#spinner').hide(); }).attr('src', "/getpage/{{serie.urlname}}/{{album.urlname}}/" + page);
      $('#page').html(page); //update page number
      saveBookmark(page);
    }
    return false;
  }

  function nextPage() {
      if(page < {{album.pages}}) {
        page += 1;
        $('#spinner').show();
        $('#image').one("load", function() {
          $('#spinner').hide();
          if(page + 1 < {{album.pages}} ) {
            preload("/getpage/{{serie.urlname}}/{{album.urlname}}/" + (page + 1))
          }
        }).attr('src', "/getpage/{{serie.urlname}}/{{album.urlname}}/" + page);
        $('#page').html(page)
        saveBookmark(page);
    }
    return false;
  }

  function fitToHeight() {
    $('#image').css('height', '100%');
    $('#image').css('width', 'auto');

    return false;
  }

  function fitToWidth() {
    $('#image').css('width', '100%');
    $('#image').css('height', 'auto');

    return false;
  }

  function toggleNav() {
    if($('#nav').css('display') == 'none') {
      $('#nav').css('display', 'block');
    } else {
      $('#nav').css('display', 'none');
    }
    return false;
  }

  function saveBookmark(page) {
    $.post("/bookmark/{{serie.urlname}}/{{album.urlname}}", { page: page});
  }

  $( document ).ready(function(){
    showPage(page);
  });

  </script>
 </head>
 <body>




<img id="image" class="image" src="" />-

<div class="touchleft" onclick="prevPage();"></div>
<div class="touchoption" onclick="toggleNav();"></div>
<div class="touchright"  onclick="nextPage();"></div>

<div id="nav" class="nav">
  <div class="left">
    <img src="/static/icons/previous.svg" title="Previous page" class="bigicon">
  </div>
  <div class="optiontop"></div>
  <div class="optionlist">
    <div class="optionlist2">
      <p>Page <span id="page">{{page}}</span> of {{album.pages}}</p>
      <button id="width"  class="button" onclick="fitToWidth();">Fit to width</button>
      <button id="height" class="button" onclick="fitToHeight();">Fit to Heigth</button>
      <p>&nbsp;</p>
      <button id="pageStart" class="button" onclick="showPage(1);">Go to the first page</button>
      <button id="pageEnd"  class="button" onclick="showPage({{album.pages}});">Go to last page</button>
      <p>&nbsp;</p>
      <a id="close"  class="button" href="/serie/{{serie.urlname}}">Close the book</a>
    </div>
  </div>
  <div class="optionbottom"></div>
  <div class="right">
    <img src="/static/icons/next.svg" title="next.svg" class="bigicon">
  </div>
</div>

<div id="spinner" class="spinner">
    <img src="/static/icons/Eclipse-1s-200px.gif"/>
</div>

</body>
</html>

