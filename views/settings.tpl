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

</div>

% include('footer.tpl')
