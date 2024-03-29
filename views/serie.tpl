% include('header.tpl')


<div class="container">

  <h2>{{serie.name}}</h2>

% if serie.complete:
  <div class="icontitle"><img src="/static/icons/tick.svg" class="icon" alt="Complete"/>Complete</div>
%end

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
% if album.volume is not None:
{{album.volume}}.
% end
     {{album.name}}
    </div>
% if album.read:
     <div class="read"><img src="/static/icons/ok.svg" alt="read"/></div>
% end
% if album.validated:
     <div class="validated"><img src="/static/icons/checklist.svg" alt="info validated"/></div>
% end
    </div>
  </div>
%end
  </div>

  <div class="icontitle">
    <img src="/static/icons/edit_image.svg" title="rename" class="icon" />
    <a href="#" onclick="showModal('serieName');">Rename serie</a>
  </div>

   <div class="icontitle">
    <img src="/static/icons/checklist.svg" title="complete" class="icon" />
    <a href="/complete/{{serie.urlname}}">Set/unset as complete</a>
  </div>

  <div class="icontitle">
    <img src="/static/icons/internet.png" title="rename" class="icon" />
    <a href="#" onclick="checkMissing('{{serie.urlname}}');">Check online</a>
  </div>

</div>


<div id="serieName" class="modal">
  <div class="modal-content">
    <span class="close" onclick="hideModal('serieName');">&times;</span>
    <div class="icontitle">
      <img src="/static/icons/questions.svg" title="Rename" class="icon">
      <h2>Rename serie</h2>
    </div>
    <div class="content">
      <form method="POST" action="/rename/serie">
        <input type="hidden" name="urlname" value="{{serie.urlname}}">
        <label for="name">Name: </label>
        <input type="text" id="name" name="name" value="{{serie.name}}">
        <br>
        <input type="submit" name="go" value="Rename">
        <br>
        <!--<input type="button" onclick="scrapSerie();" value="Scrapper">-->
      </form>
    </div>
  </div>
</div>


<div id="scrap" class="modal">
  <div class="modal-content">
    <span class="close" onclick="hideModal('scrap');">&times;</span>
    <div class="icontitle">
      <img src="/static/icons/idea.svg" title="Search" class="icon">
      <h2>Scrapper</h2>
    </div>
    <div class="content" id="serieContent">

    </div>
  </div>
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

function scrapSerie() {
  serie = $("#name").val();

  $.getJSON("/scrap/serie/" + serie, function(json) {
    $.each(json, function(index, guess){
      $("#serieContent").append(guess['label'])
    });
  });

  return showModal('scrap')
}

</script>

% include('footer.tpl')
