% include('header.tpl')


<div class="container">

<div>
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

</div>

% include('footer.tpl')
