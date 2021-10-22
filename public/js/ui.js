'use strict';

const socket = io(window.location.href);

let bear = {
  eyes: 'open',
  mouth: 'closed'
};

let btnPuppet = document.getElementById('btnPuppet');
let btnParrot = document.getElementById('btnParrot');
let divPuppet = document.getElementById('divPuppet');
let divParrot = document.getElementById('divParrot');

let imgBear = document.getElementById('imgBear');
let areaEyeState = document.getElementById('areaEyeState');
let areaMouthState = document.getElementById('areaMouthState');
let selEyeState = document.getElementById('selEyeState');
let selMouthState = document.getElementById('selMouthState');
let btnUpdateBear = document.getElementById('btnUpdateBear');
let txtPhrase = document.getElementById('txtPhrase');
let btnSpeak = document.getElementById('btnSpeak');
let selFilename = document.getElementById('selFilename');
let btnPlay = document.getElementById('btnPlay');

let updateUI = function(){
  imgBear.src = '/public/img/teddy_e'+bear.eyes.charAt(0)+'m'+bear.mouth.charAt(0)+'.png';
  selEyeState.value = bear.eyes;
  selMouthState.value = bear.mouth;
}

document.addEventListener('DOMContentLoaded', function() {
  socket.emit('update_bear', bear);
  socket.emit('fetch_phrases');
}, false);

btnPuppet.addEventListener('click', function(e){
  e.preventDefault();
  divPuppet.style.display = 'block';
  divParrot.style.display = 'none';
  btnPuppet.className='btn btn-info active';
  btnParrot.className='btn btn-default';
}, false);

btnParrot.addEventListener('click', function(e){
  e.preventDefault();
  divPuppet.style.display = 'none';
  divParrot.style.display = 'block';
  btnPuppet.className='btn btn-default';
  btnParrot.className='btn btn-info active';
}, false);

areaEyeState.addEventListener('click', function(e){
  e.preventDefault();
  let data = { eyes: (bear.eyes=='open') ? 'closed' : 'open' };
  socket.emit('update_bear', data);
}, false);

areaMouthState.addEventListener('click', function(e){
  e.preventDefault();
  let data = { mouth: (bear.mouth=='open') ? 'closed' : 'open' };
  socket.emit('update_bear', data);
}, false);

btnUpdateBear.addEventListener('click', function(e){
  e.preventDefault();
  let data = {
    eyes: selEyeState.value,
    mouth: selMouthState.value
  };
  socket.emit('update_bear', data);
}, false);

let disableInputs = function(isEnabled){
  txtPhrase.disabled = isEnabled;
  btnSpeak.disabled = isEnabled;
  selFilename.disabled = isEnabled;
  btnPlay.disabled = isEnabled;
}

txtPhrase.addEventListener('keyup', function(e) {
  e.preventDefault();
  if(e.key === 'Enter'){
    disableInputs(true);
    socket.emit('speak', txtPhrase.value);
  }
}, false);

btnSpeak.addEventListener('click', function(e){
  e.preventDefault();
  disableInputs(true);
  socket.emit('speak', txtPhrase.value);
}, false);

btnPlay.addEventListener('click', function(e){
  e.preventDefault();
  disableInputs(true);
  socket.emit('play', selFilename.value);
}, false);

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

// when either of the audio methods has finished
socket.on('speaking_done', function (data){
  // graft update data onto bear object
  disableInputs(false);
});
