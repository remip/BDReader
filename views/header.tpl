% setdefault('prevpage', 0)
% setdefault('nextpage', 0)
<!doctype html>
<html>
 <head>
  <meta charset="utf-8">
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
  <link rel="stylesheet" type="text/css" href="/static/css/main.css">
  <script type="text/javascript" src="/static/js/jquery-3.3.1.min.js"></script>
 </head>
 <body>
  <div class="header">
    <div class="headerleft">
% if prevpage != 0:
      <a href="/page/{{prevpage}}">
        <img src="/static/icons/previous.svg" title="Previous page" class="icon">
      </a>
% end
  </div>

  <div class="headerright">
% if nextpage != 0:
    <a href="/page/{{nextpage}}">
      <img src="/static/icons/next.svg" title="next.svg" class="icon">
    </a>
% end
  </div>

  <div class="headercenter">
    <a href="/"><img src="/static/icons/home.svg" title="Homepage" class="icon"></a>
    <a href="/settings"><img src="/static/icons/settings.svg" title="Settings" class="icon"></a>
    <a href="#" onclick="showSearch();"><img src="/static/icons/search.svg" title="Search" class="icon"></a>
    <a href="/random"><img src="/static/icons/random.svg" title="Random" class="icon"></a>
    <a href="/last"><img src="/static/icons/clock.svg" title="Last" class="icon"></a>
    <a href="/bookmarks"><img src="/static/icons/bookmark.svg" title="Bookmarks" class="icon"></a>
  </div>

</div>


<div id="search" class="modal">
  <div class="modal-content">
    <span class="close" onclick="hideModal('search');">&times;</span>
    <div class="icontitle">
      <img src="/static/icons/search.svg" title="Search" class="icon">
      <h2>Search</h2>
    </div>
    <div class="content">
      <form method="POST" action="/result">
        <input id="searchinput" type="text" name="term">
        <input type="submit" name="go" value="Search">
      </form>
    </div>
  </div>
</div>


<script type="text/javascript">

function showSearch() {
  showModal('search');

  $('#searchinput').focus();

  return false;
}

function showModal(id) {
  var modal = document.getElementById(id);

  modal.style.display = "block";

  return false;
}

function hideModal(id) {
  var modal = document.getElementById(id);

  modal.style.display = "none";

  return false;
}

</script>
