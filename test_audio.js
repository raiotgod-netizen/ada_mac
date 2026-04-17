const io = require('socket.io-client');
const sio = io('http://localhost:8000', { transports: ['websocket'] });

sio.on('connect', () => {
  console.log('Connected!');
  sio.emit('start_audio', { vision_mode: 'screen' });
  console.log('Sent start_audio');
  setTimeout(() => sio.disconnect(), 5000);
});

sio.on('disconnect', () => console.log('Disconnected'));
sio.on('error', e => console.error('Error:', e));
