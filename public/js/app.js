'use strict';

import Vue from 'https://cdn.jsdelivr.net/npm/vue@2.6.14/dist/vue.esm.browser.min.js';
import { io } from 'https://cdn.jsdelivr.net/npm/socket.io-client@4.4.0/dist/socket.io.esm.min.js';
import VueSocketIOExt from 'https://cdn.jsdelivr.net/npm/vue-socket.io-extended@4.2.0/dist/vue-socket.io-ext.esm.js';

const socket = io(window.location.href);
Vue.use(VueSocketIOExt, socket);

var app = new Vue({
  el: '#app',
  data: {
    mode: 'puppet',
    speaking: false,
    bear: {
      eyes: false,
      mouth: false
    },
    volume: 70,
    speaking: false,
    phrases: {},
    filename: ''
  },
  computed: {
    bearimg: {
      get: function () {
        let e = this.bear.eyes ? 'o' : 'c';
        let m = this.bear.mouth ? 'o' : 'c';
        return `/public/img/teddy_e${e}m${m}.png`;
      }
    },
    both: {
      get: function () {
        return this.bear.eyes && this.bear.mouth;
      },
      set: function (isOpen) {
        this.bear.eyes = isOpen;
        this.bear.mouth = isOpen;
      }
    }
  },
  sockets:{
    connect: function(){
      this.$socket.client.emit('fetch_phrases');
    },
    bear_updated: function(val){
      console.log('bear updated');
    },
    phrases_fetched: function(data){
      this.phrases = data;
    }
  },
  methods: {
    setMode: function(mode){
      this.mode = mode;
    },
    toggleEyes: function(){
      this.bear.eyes = !this.bear.eyes;
      this.updateBear();
    },
    toggleMouth: function(){
      this.bear.mouth = !this.bear.mouth;
      this.updateBear();
    },
    updateBear: function(){
      this.$socket.client.emit('update_bear', this.bear);
    },
    play: function(){
      if(this.filename!==''){
        this.$socket.client.emit('play', this.filename);
      }
    }
  }
});