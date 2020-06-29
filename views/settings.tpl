% include('header.tpl')


<div class="container">

<div class="icontitle">
  <img src="/static/icons/refresh.svg" class="icon"> <a href="/scan">Scan the library</a>
</div>

<h2>Status</h2>

<table>
  <tr>
    <th>&nbsp;</th>
    <th>Series</th>
    <th>Albums</th>
  </tr>
  <tr>
    <td>Added</td>
    <td>{{newSeries}}</td>
    <td>{{newAlbums}}</td>
  </tr>
  <tr>
    <td>Deleted</td>
    <td>{{delSeries}}</td>
    <td>{{delAlbums}}</td>
  </tr>
  <tr>
    <td>Total</td>
    <td>{{totalSeries}}</td>
    <td>{{totalAlbums}}</td>
  </tr>  
</table>

<p>
<table>
 <tr><th>Stats</th><th>Count</th></tr>
 <tr><td>Library</td><td>{{totalSize}}</td></tr>
 <tr><td>cbz</td><td>{{totalCBZ}}</td></tr>
 <tr><td>cbr</td><td>{{totalCBR}}</td></tr>
 <tr><td>pdf</td><td>{{totalPDF}}</td></tr>
 <tr><td>ComicInfo</td><td>{{totalValidated}}</td></tr>
 <tr><td>Authors</td><td>{{totalAuthors}}</td></tr>
</table>

</div>

% include('footer.tpl')
