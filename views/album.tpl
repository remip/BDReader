% include('header.tpl')


<div class="container2">
  <div class="cover">
    <img src="/thumbnail/{{album.id}}"/>
  </div>
  <div class="details">
    <h3>{{album.name}}</h3>
    <p>
% if album.volume is not None:
      Volume {{album.volume}} -
% end
      {{album.pages}} pages - {{album.filetype}}</p>
  </div>


<table>
  <tr>
    <td>Serie:</td>
    <td>{{album.serie.name}}</td>
  </tr>

  <tr>
    <td>Writer:</td>
    <td>{{writers}}</td>
  </tr>
  <tr>
    <td>Penciller:</td>
    <td>{{pencillers}}</td>
  </tr><tr>
    <td>Colorist:</td>
    <td>{{colorists}}</td>
  </tr><tr>
    <td>Publisher:</td>
    <td>{{album.publisher}}</td>
  </tr><tr>
    <td>Year:</td>
    <td>{{album.year}}</td>
  </tr><tr>
    <td>Link:</td>
    <td><a href="{{album.link}}">{{album.link}}</a></td>
  </tr><tr>
    <td>Summary</td>
    <td>{{album.summary}}</td>
  </tr>
</table>

<div class="clear"></div>

<a class="btn btn-action btn-read" href="/read/{{serie.urlname}}/{{album.urlname}}">Read</a>

<hr>
<div class="icontitle" style="float: left;">
  <img src="/static/icons/download.svg" title="Download" class="icon">
  <a href="/download/{{serie.urlname}}/{{album.urlname}}">Download</a>
</div>
<div class="icontitle">
  <img src="/static/icons/reading.svg" title="Read" class="icon">
  <a href="/read/{{serie.urlname}}/{{album.urlname}}">Read</a>
</div>
<div class="icontitle">
  <img src="/static/icons/edit_image.svg" title="rename" class="icon" />
  <a href="#" onclick="showModal('albumName');">Rename album</a>
</div>
% if album.read:
<div class="icontitle">
  <img src="/static/icons/cancel.svg" title="unread" class="icon" />
  <a href="/mark/unread/{{serie.urlname}}/{{album.urlname}}">Mark as unread</a>
</div>
% else :
<div class="icontitle">
  <img src="/static/icons/ok.svg" title="read" class="icon" />
  <a href="/mark/read/{{serie.urlname}}/{{album.urlname}}">Mark as read</a>
</div>
% end

<div class="icontitle">
  <img src="/static/icons/left.svg" title="back" class="icon" />
  <a href="/serie/{{serie.urlname}}">Go back to the serie</a>
</div>

</div>

<div id="albumName" class="modal">
  <div class="modal-content">
    <span class="close" onclick="hideModal('albumName');">&times;</span>
    <div class="icontitle">
      <img src="/static/icons/questions.svg" title="Search" class="icon">
      <h2>Edit album</h2>
    </div>
    <div class="content">
      <form method="POST" action="/edit/album">
        <input type="hidden" name="serie" value="{{serie.urlname}}">
        <input type="hidden" name="album" value="{{album.urlname}}">

        <label for="name">Name: </label>
        <input type="text" id="name" name="name" value="{{album.name}}">
        <br/>
        <label for="volume">Volume: </label>
        <input type="text" id="volume" name="volume" value="{{album.volume}}">
        <br/>
        <input type="submit" name="go" value="Edit">
        <br/>
        <!--<input type="button" onclick="scrapSerie();" value="Scrapper">-->
      </form>
    </div>
  </div>
</div>


% include('footer.tpl')
