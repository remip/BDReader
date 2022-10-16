% include('header.tpl')


<div class="container">

  <h2>Missing albums</h2>


% for serie in series:
 <div class="cellcontainer">
  <div class="cell">
   <div class="thumbnail">
    <a href="/serie/{{serie.urlname}}">
     <img src="/thumbnail/{{serie.image}}"/>
    </a>
   </div>
   <div class="title">
    {{serie.name}}<br>
    <a href="" onclick="checkMissing('{{serie.urlname}}'); return false;">Check online</a><br>
   </div>
   <div class="count">{{serie.count}}</div>
  </div>
 </div>
%end

</div>

<div id="checkMissing" class="modal">
  <div class="modal-content-big">
    <span class="close" onclick="hideModal('checkMissing');">&times;</span>
    <div class="icontitle">
      <img src="/static/icons/idea.svg" title="Search" class="icon">
      <h2>Check online</h2>
    </div>
    <div class="content" id="missingContent">

    </div>
  </div>
</div>

<script type="text/javascript">

function checkMissing(urlname) {

  $("#missingContent").html("");

  $.get("/missinginfo/" + urlname, function(data) {
      $("#missingContent").html(data)    
  });

  return showModal('checkMissing');
}

</script>

% include('footer.tpl')
