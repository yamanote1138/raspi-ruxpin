'use strict';

const socket = io(window.location.href);

let bear = {
  eyes: 'open',
  mouth: 'closed'
};

let btnPuppetMode = document.getElementById('btnPuppetMode');
let btnSpeakMode = document.getElementById('btnSpeakMode');
let divPuppetMode = document.getElementById('divPuppetMode');
let divSpeakMode = document.getElementById('divSpeakMode');

let btnConnected = document.getElementById('btnConnected');
let btnDisconnected = document.getElementById('btnDisconnected');

let imgBear = document.getElementById('imgBear');
let areaEyeState = document.getElementById('areaEyeState');
let areaMouthState = document.getElementById('areaMouthState');
let chkEyes = document.getElementById('chkEyes');
let chkMouth = document.getElementById('chkMouth');
let chkBoth = document.getElementById('chkBoth');
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

btnPuppetMode.addEventListener('click', function(e){
  e.preventDefault();
  divPuppetMode.style.display = 'block';
  divSpeakMode.style.display = 'none';
  btnPuppetMode.className='btn btn-primary';
  btnSpeakMode.className='btn btn-outline-secondary';
}, false);

btnSpeakMode.addEventListener('click', function(e){
  e.preventDefault();
  divPuppetMode.style.display = 'none';
  divSpeakMode.style.display = 'block';
  btnPuppetMode.className='btn btn-outline-secondary';
  btnSpeakMode.className='btn btn-primary';
}, false);

areaEyeState.addEventListener('click', function(e){
  e.preventDefault();
  let data = { eyes: (bear.eyes=='open') ? 'closed' : 'open' };
  socket.emit('update_bear', data);
}, false);

areaMouthState.addEventListener('click', function(e){
  let data = { mouth: (bear.mouth=='open') ? 'closed' : 'open' };
  socket.emit('update_bear', data);
}, false);

let updateBear = function(e, data){
  socket.emit('update_bear', data);
}

chkEyes.addEventListener('click', function(e){
  updateBear(e, {
    eyes: chkEyes.checked ? 'open' : 'closed'
  });
}, false);

chkMouth.addEventListener('click', function(e){
  updateBear(e, {
    mouth: chkMouth.checked ? 'open' : 'closed'
  });
}, false);

chkBoth.addEventListener('click', function(e){
  updateBear(e, {
    eyes: chkBoth.checked ? 'open' : 'closed',
    mouth: chkBoth.checked ? 'open' : 'closed'
  });
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


// respond to changes in connection
socket.on('connect', () => {
  btnConnectionStatus.className='btn btn-success';
  btnConnectionStatus.innerHTML = 'CONNECTED!';
  console.log(`${socket.id} connected`);
});

socket.on('disconnect', () => {
  btnConnectionStatus.className='btn btn-danger';
  btnConnectionStatus.innerHTML = 'DISCONNECTED :(';
  console.log('socket disconnected');
});

// when phrases are loaded, populate dropdown
socket.on('phrases_fetched', function (data){
  for (const property in data) {
    selFilename.options[selFilename.options.length] = new Option(data[property], property);
  }
});

// if bear status is updated on server, change image accordingly
socket.on('bear_updated', function (data){
  // graft update data onto bear object
  Object.assign(bear, data);
  updateUI();
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
