% include('header.tpl')
% current_year = 1900

<div class="container">



<div>
% for album in albums:

% if album.year != current_year:
    </div>
    <h2>{{album.year}}</h2>
    <div>
% current_year = album.year
%end
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
