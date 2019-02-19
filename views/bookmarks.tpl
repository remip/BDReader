% include('header.tpl')

<div class="container">

<h2>Bookmarks</h2>

% for bookmark in bookmarks:
 <div class="cellcontainer">
  <div class="cell">
   <div class="thumbnail">
    <a href="/read/{{bookmark.album.serie.urlname}}/{{bookmark.album.urlname}}">
     <img src="/thumbnail/{{bookmark.album.id}}"/>
    </a>
   </div>
   <div class="title">
     {{bookmark.serie.name}}
% if bookmark.album.volume:
     - T{{bookmark.album.volume}}
% end
     - {{bookmark.album.name}}
     - page {{bookmark.page}}
   </div>
  </div>
 </div>
%end


</div>

% include('footer.tpl')
