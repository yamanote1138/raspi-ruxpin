<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Mappy Ruxpin</title>
    
    <meta name="description" content="Make the bear talk">
    <meta name="author" content="Chad Francis">
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
    
    <!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">
    <!-- Optional theme -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap-theme.min.css" integrity="sha384-rHyoN1iRsVXV4nD0JutlnGaslCJuC7uwjduW9SVrLvRYooPp2bWYgmgJQIXwl/Sp" crossorigin="anonymous">

    <script src="https://use.fontawesome.com/12a0b300c5.js"></script>
  </head>
  <body style="background-image: url(public/bg.png)">
    <div class="container">
      <a href="/naughty"><img src="public/mappy_ruxpin.png" class="img-responsive"></a>
      <form action="/" method="post" class="form-inline">
        <div class="well">
          <button type="submit" name="demo" value="1" class="btn btn-info btn-block"><i class="fa fa-map-marker"></i> Directions Demo</button>
          <span class="help-block">Have Mappy read a canned set of turn-by-turn directions from our guidance API</span>
        </div>
        <div class="well">
          <button type="submit" name="tweet" value="1" class="btn btn-info btn-block"><i class="fa fa-twitter"></i> MapQuest Tweets</button>
          <span class="help-block">Mappy will read a random tweet that mentions <code>@MapQuest</code></span>
        </div>
      </form>
    </div>
  </body>
</html>