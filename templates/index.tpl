<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>RasPi Ruxpin</title>
    
    <meta name="description" content="Make the bear talk">
    <meta name="author" content="Chad Francis">
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
    
    <!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">
    <!-- Optional theme -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap-theme.min.css" integrity="sha384-rHyoN1iRsVXV4nD0JutlnGaslCJuC7uwjduW9SVrLvRYooPp2bWYgmgJQIXwl/Sp" crossorigin="anonymous">

    <script src="https://use.fontawesome.com/12a0b300c5.js"></script>

    <style type="text/css">
      area:focus{
        border: none;
        outline-style: none; 
        -moz-outline-style:none;  
      }
    </style>
  </head>
  <body style="background-image: url(public/bg_naughty.png)">
    <div class="container">
      <a href="/"><img src="public/naughty_ruxpin.png" class="img-responsive"></a>
<%
  ex = 'c' if e == 'o' else 'o'
  mx = 'c' if m == 'o' else 'o'
%>
      <map name="teddymap">
        <area shape="rect" coords="0,0,200,100" href="?e={{ex}}&m={{m}}" alt="Sun" />
        <area shape="rect" coords="0,100,200,200" href="?e={{e}}&m={{mx}}" alt="Sun" />
      </map>
      <img src="/public/teddy_e{{e}}m{{m}}.png" class="img-responsive" usemap="#teddymap">
      <form action="/" method="get" class="form-inline">
        <div class="well form-group">
          <label for="e" class="col-sm-2 control-label">Eyes</label>
          <div class="col-sm-10">
            <select name="e" class="form-control" id="e">
              <option value="o"{{'selected="selected"' if e == 'o' else ''}}>open</option>
              <option value="c"{{'selected="selected"' if e == 'c' else ''}}>close</option>
            </select>
          </div>
          <label for="m" class="col-sm-2 control-label">Mouth</label>
          <div class="col-sm-10">
            <select name="m" class="form-control" id="m">
              <option value="o"{{'selected="selected"' if m == 'o' else ''}}>open</option>
              <option value="c"{{'selected="selected"' if m == 'c' else ''}}>close</option>
            </select>
          </div>
          <button type="submit" class="btn btn-info"><i class="fa fa-play-circle" aria-hidden="true"></i></button>
        </div>
      </form>
      <form action="/" method="post" class="form-inline">
        <div class="well form-group">
          <div class="input-group">
            <input type="text" name="speech" class="form-control" id="speech" placeholder="Type anything here and Mappy will say it... I mean anything!">
            <span class="input-group-btn">
              <button type="submit" class="btn btn-info"><i class="fa fa-bullhorn" aria-hidden="true"></i></button>
            </span>
          </div>
        </div>
        <div class="well form-group">
          <div class="input-group">
            <select name="phrase" class="form-control" id="phrase">
              <option value="">Select a pre-recorded sound file</option>
              % for key in phrases:
              <option value="{{key}}">{{phrases[key]}}</option>
              % end
            </select>
            <span class="input-group-btn">
              <button type="submit" class="btn btn-info"><i class="fa fa-play-circle" aria-hidden="true"></i></button>
            </span>
          </div>
        </div>
      </form>
    </div>
  </body>
</html>