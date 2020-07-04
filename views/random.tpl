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
   <div class="title">
    {{album.serie.name}}
% if album.volume is not None:
- {{album.volume}} -
%end
    {{album.name}}
   </div>
% if album.read:
     <div class="read"><img src="/static/icons/ok.svg" alt="read"/></div>
% end
  </div>
</div>
%end
</div>

</div>

% include('footer.tpl')
