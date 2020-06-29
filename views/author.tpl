% include('header.tpl')


<div class="container">

<table>
 <tr>
  <th>Name</th>
  <th>Job</th>
  <th>Albums</th>
</tr>
% for author in authors:
 <tr>
  <td><a href="/link/author/{{author.name}}">{{author.name}}</a></td>
  <td>
% for job in author.jobs.split(","):
    {{joblist[job]}}
% end
  </td>
  <td>{{author.albumcount}}</td>
</tr>
%end

</div>

% include('footer.tpl')
