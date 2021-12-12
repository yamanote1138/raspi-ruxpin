'use strict';

const socket = io(window.location.href);



let txtVolume = document.getElementById('txtVolume');
let btnVolume = document.getElementById('btnVolume');

let txtPhrase = document.getElementById('txtPhrase');
let btnSpeak = document.getElementById('btnSpeak');
let selFilename = document.getElementById('selFilename');
let btnPlay = document.getElementById('btnPlay');
let spnSpeakIcon = document.getElementById('spnSpeakIcon');
let spnPlayIcon = document.getElementById('spnPlayIcon');

let updateUI = function(){
  imgBear.src = '/public/img/teddy_e'+bear.eyes.charAt(0)+'m'+bear.mouth.charAt(0)+'.png';

  chkEyes.checked = bear.eyes == 'open';
  chkMouth.checked = bear.mouth == 'open';
  chkBoth.checked = (bear.eyes == 'open' && bear.mouth == 'open');
}

document.addEventListener('DOMContentLoaded', function() {
  socket.emit('update_bear', bear);
  socket.emit('fetch_phrases');
}, false);


btnVolume.addEventListener('click', function(e){
  e.preventDefault();
  socket.emit('set_volume', parseInt(txtVolume.value));
});

let disableInputs = function(isEnabled){
  txtPhrase.disabled = isEnabled;
  btnSpeak.disabled = isEnabled;
  selFilename.disabled = isEnabled;
  btnPlay.disabled = isEnabled;
}

let sendSpeak = function(){
  disableInputs(true);
  spnSpeakIcon.className="spinner-border spinner-border-sm";
  socket.emit('speak', txtPhrase.value);
}

txtPhrase.addEventListener('keyup', function(e) {
  e.preventDefault();
  if(e.key === 'Enter') sendSpeak();
}, false);

btnSpeak.addEventListener('click', function(e){
  e.preventDefault();
  sendSpeak();
}, false);

btnPlay.addEventListener('click', function(e){
  e.preventDefault();
  disableInputs(true);
  spnPlayIcon.className="spinner-border spinner-border-sm";
  socket.emit('play', selFilename.value);
}, false);



// when phrases are loaded, populate dropdown
socket.on('phrases_fetched', function (data){
  for (const property in data) {
    selFilename.options[selFilename.options.length] = new Option(data[property], property);
  }
});


// when bear has finished speaking text
socket.on('speaking_done', function (data){
  console.log('speaking done');
  spnSpeakIcon.className="fa fa-bullhorn";
  disableInputs(false);
});

// when bear has finished playing audio file
socket.on('playing_done', function (data){
  console.log('playing done');
  spnPlayIcon.className="fa fa-play-circle";
  disableInputs(false);
});

socket.on('volume_set', function (data){
  console.log('volume set');
});
