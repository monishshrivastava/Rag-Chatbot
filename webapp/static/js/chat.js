const messagesEl = document.getElementById('messages');
const inputEl = document.getElementById('input');
const formEl = document.getElementById('composer');

function appendMessage(text, who='bot'){
  const wrap = document.createElement('div');
  wrap.className = 'message ' + (who==='user' ? 'user' : 'bot');
  const bubble = document.createElement('div');
  bubble.className = 'bubble ' + (who==='user' ? 'user' : 'bot');
  bubble.innerText = text;
  wrap.appendChild(bubble);
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

async function sendMessage(message){
  appendMessage(message, 'user');
  appendMessage('…', 'bot');
  const botBubble = messagesEl.querySelector('.message.bot:last-child .bubble');
  try{
    const resp = await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message})});
    const data = await resp.json();
    botBubble.innerText = data.answer || 'No answer';
    if(data.sources && data.sources.length){
      const s = document.createElement('small');
      s.className = 'sources';
      s.innerText = 'Sources: ' + data.sources.join(', ');
      botBubble.appendChild(s);
    }
  }catch(e){
    botBubble.innerText = 'Error: ' + e.message;
  }
}

formEl.addEventListener('submit', (e)=>{
  e.preventDefault();
  const v = inputEl.value.trim();
  if(!v) return;
  inputEl.value='';
  sendMessage(v);
});

// Small demo welcome
appendMessage('Hello — ask me about the documents in the repo.');
