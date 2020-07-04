% include('header.tpl')


<div class="container">

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
% if serie.complete:
   <div class="complete"><img src="/static/icons/tick.svg" alt="Complete"/></div>
% end
  </div>
 </div>
%end

</div>

% include('footer.tpl')
