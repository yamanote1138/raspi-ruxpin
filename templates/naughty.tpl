<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Naughty Ruxpin</title>
    
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
      <form action="/naughty" method="post" class="form-inline">
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
              <option value="ants">Archer: You want ants...</option>
              <option value="believeitornot">doggo: believe it or not...</option>
              <option value="dogofwisdom">doggo: ba daba da ba</option>
              <option value="merryxmas">clark: boss rant</option>
              <option value="grownman">airplane: grown man naked</option>
              <option value="gymnasium">airplane: hang around the gymnasium</option>
              <option value="gladiators">airplane: movies about gladiators</option>
              <option value="turkish">airplane: turkish prison</option>
              <option value="surely">airplane: don't call me surely</option>
              <option value="88miles">doc: if my calculations are correct...</option>
              <option value="dumber">harry: just when I think...</option>
              <option value="nerfherder">leia: why you stuck up...</option>
              <option value="breath">vader: breathing</option>
              <option value="failed">vader: you have failed me for the last time</option>
              <option value="father">vader: No, I am your father</option>
              <option value="forceiswithyou">vader: The force is with you...</option>
              <option value="chewie">chewie: grawgrhghghg...</option>
              <option value="trynot">yoda: Try not...</option>
              <option value="everyone">billy madison: everyone is now dumber</option>
              <option value="hiney">billy madison: so hot, want to touch the hiney</option>
              <option value="bleep">happy gilmore: *bleep*</option>
              <option value="gohome">happy gilmore: are you too good for your home?</option>
              <option value="jackass">happy gilmore: you suck, ya jackass</option>
              <option value="kickmyownass">happy gilmore: .. I'd have to kick my own ass</option>
              <option value="piecesofshit">happy gilmore: I eat pieces of shit like you...</option>
              <option value="priceiswrong">happy gilmore: the price is wrong</option>
              <option value="shutthehellup">happy gilmore: nice glass of shut the hell up</option>
              <option value="taparoo">happy gilmore: give it a tappy</option>
              <option value="purpose">rick and morty: what is my purpose? oh my god.</option>
              <option value="assholomio">ace ventura: assholomio, oh sodomia</option>
              <option value="donotgointhere">ace ventura: do NOT go in there... whew!</option>
              <option value="fart">monty python: I fart in your general direction</option>
              <option value="ni">monty python: we are the nights who say... ni!</option>
              <option value="taunt">monty python: Now go away or I shall taunt you a second time.</option>
              <option value="hamster">monty python: Your mother was a hamster...</option>
              <option value="takedrugs">caddyshack: Do you take drugs Danny?</option>
              <option value="getnothing">caddyshack: you'll get nothing and like it</option>
              <option value="billybaroo">caddyshack: billy baroo</option>
              <option value="cinderella">caddyshack: cinderalla scene</option>
              <option value="bowlofsoup">caddyshack: free bowl of soup</option>
              <option value="whatthecrap">strong bad: what the crap were you doing</option>
              <option value="heystupid">homestar: hey stupid</option>
              <option value="canubelieveit">homestar: can you believe it?</option>
              <option value="baleeted">homestar: baleeted</option>
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