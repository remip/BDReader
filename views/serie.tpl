% include('header.tpl')


<div class="container">

  <h2>{{serie.name}}</h2>

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
    </div>
  </div>
%end
  </div>

  <div class="icontitle">
    <img src="/static/icons/edit_image.svg" title="rename" class="icon" />
    <a href="#" onclick="showModal('serieName');">Rename serie</a>
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

<script type="text/javascript">

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
