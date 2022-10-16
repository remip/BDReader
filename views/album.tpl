% include('header.tpl')


<div class="container2">
  <div class="cover">
    <img src="/thumbnail/{{album.id}}"/>
  </div>
  <div class="details">
    <h3>{{album.name}}</h3>
    <table>     
% if album.volume is not None:
     <tr><td>Volume</td><td>{{album.volume}}</td></tr>
% end
     <tr><td>Pages</td><td>{{album.pages}}</td></tr>
     <tr><td>Format</td><td>{{album.filetype}}</td></tr>
     <tr><td>Size</td><td>{{sizemb}} MB</td></tr>
    </table>
    <br/>
  </div>


<table>
  <tr>
    <td>Serie:</td>
    <td>{{album.serie.name}}</td>
  </tr>

% if writers:
  <tr>
    <td>Writer:</td>
    <td>
% for writer in writers:
    <a href="/link/author/{{writer}}">{{writer}}</a>
%end
    </td>
  </tr>
% end
% if pencillers:
  <tr>
    <td>Penciller:</td>
    <td>
% for penciller in pencillers:
    <a href="/link/author/{{penciller}}">{{penciller}}</a>
%end
    </td>
  </tr>
% end
% if colorists:
  <tr>
    <td>Colorist:</td>
    <td>
% for colorist in colorists:
    <a href="/link/author/{{colorist}}">{{colorist}}</a>
%end
    </td>
  </tr>
%end
% if album.publisher:
  <tr>
    <td>Publisher:</td>
    <td><a href="/link/publisher/{{album.publisher.name}}">{{album.publisher.name}}</a></td>
  </tr>
%end
% if album.imprint:
  <tr>
    <td>Imprint:</td>
    <td><a href="/link/imprint/{{album.imprint.name}}">{{album.imprint.name}}</a></td>
  </tr>
%end
% if album.year:
  <tr>
    <td>Year:</td>
    <td>{{album.year}}</td>
  </tr>
% end
% if album.link:
  <tr>
    <td>Link:</td>
    <td><a href="{{album.link}}">{{album.link}}</a></td>
  </tr>
% end
% if album.summary:
  <tr>
    <td>Summary:</td>
    <td>{{album.summary}}</td>
  </tr>
% end
</table>

<div class="clear"></div>
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
% if album.filetype == 'pdf':
<div class="icontitle">
  <img src="/static/icons/settings.svg" title="convert" class="icon" />
  <a href="/convert/{{serie.urlname}}/{{album.urlname}}">Convert to cbz</a>
</div>
% end

<div class="icontitle">
  <img src="/static/icons/settings.svg" title="refresh" class="icon" />
  <a href="/refresh/{{serie.urlname}}/{{album.urlname}}">Refresh from comicinfo.xml</a>
</div>

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
