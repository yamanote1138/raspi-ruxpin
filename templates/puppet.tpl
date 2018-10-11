<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>RasPi Ruxpin - Puppet Mode</title>
    
    <meta name="description" content="Make the bear talk">
    <meta name="author" content="Chad Francis">
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
    
    <!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">
    <!-- Optional theme -->
    <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap-theme.min.css" integrity="sha384-rHyoN1iRsVXV4nD0JutlnGaslCJuC7uwjduW9SVrLvRYooPp2bWYgmgJQIXwl/Sp" crossorigin="anonymous">

    <script src="https://use.fontawesome.com/12a0b300c5.js"></script>
  </head>
  <body style="background-image: url(public/bg_naughty.png)">
    <div class="container">
      <a href="/"><img src="public/naughty_ruxpin.png" class="img-responsive"></a>
      <form action="/" method="post" class="form-inline">
        <div class="well form-group">
          <div class="input-group">
            <select name="part" class="form-control" id="part">
              <option value="">Select part</option>
              <option value="mouth"{{'selected="selected"' if part=='mouth'}}>mouth</option>
              <option value="eyes">eyes</option>
            </select>
            <select name="direction" class="form-control" id="part">
              <option value="">Select direction</option>
              <option value="open">open</option>
              <option value="close">close</option>
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