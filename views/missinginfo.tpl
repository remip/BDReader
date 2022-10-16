<h4>Library</h4>

<p>
{{serie.name}} - {{serie.count}} volumes
</p>
<table class="table">
 <tr><th>#</th><th>Title</th>
% for album in albums:
 <tr><td>{{album.volume}}</td><td>{{album.name}}</td></tr>
%end
</table>

<h4>Online</h4>

<p>
{{online_nb}} volumes, complete: {{online_complete}}<br>
<a href="{{url}}" target=_blank>Bedetheque</a>
</p>

<h4>Missing</h4>
<table class="table">
 <tr><th>#</th><th>Title</th>
% for album in missing:
 <tr><td>{{album["volume"]}}</td><td>{{album["title"]}}</td></tr>
%end
</table>

<p>
<span id="complete">
    <a href="" onclick="setComplete('{{serie.urlname}}'); return false;">Set serie as complete</a>
</span>

<script type="text/javascript">

function setComplete(urlname) {
  console.log("setComplete(" + urlname + ")");

  $.get("/complete/" + urlname, function(data) {    
      $("#complete").html("Serie is complete");
      console.log("done");
  });  
}
</script>