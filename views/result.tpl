% include('header.tpl')


<div class="container">

<h2>Series</h2>

% for serie in series:
 <div class="cellcontainer">
  <div class="cell">
   <div class="thumbnail">
    <a href="/serie/{{serie.urlname}}">
     <img src="/thumbnail/{{serie.image}}"/>
    </a>
   </div>
   <div class="title">{{serie.name}}</div>
   <div class="count">{{serie.count}}</div>
  </div>
 </div>
%end

<h2>Albums</h2>

% for album in albums:
 <div class="cellcontainer">
  <div class="cell">
   <div class="thumbnail">
    <a href="/album/{{album.serie.urlname}}/{{album.urlname}}">
     <img src="/thumbnail/{{album.id}}"/>
    </a>
   </div>
   <div class="title">{{album.name}}</div>
  </div>
 </div>
%end


</div>

% include('footer.tpl')
