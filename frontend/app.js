const API_BASE = window.location.origin;
let token="", username="", ws, roomId="", isAdmin=false;
const canvas=document.getElementById("canvas"), ctx=canvas.getContext("2d");
let drawing=false;

// ---------------- AUTH ----------------
async function login(){
  username=document.getElementById("username").value;
  const password=document.getElementById("password").value;
  const res=await fetch(`${API_BASE}/login`,{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body:JSON.stringify({username,password})
  });
  const data=await res.json();
  if(data.status=="ok"){
    token=data.token;
    isAdmin=data.is_admin;
    document.getElementById("auth").style.display="none";
    if(isAdmin) document.getElementById("admin_panel").style.display="block";
    else document.getElementById("game").style.display="block";
  } else alert(data.message);
}

// ---------------- ADMIN ----------------
async function createRoom(){
  const rounds=parseInt(document.getElementById("rounds").value);
  const time_limit=parseInt(document.getElementById("time_limit").value);
  const res=await fetch(`${API_BASE}/create_room?token=${token}&rounds=${rounds}&time_limit=${time_limit}`, {method:"POST"});
  const data=await res.json();
  if(data.status=="ok"){
    document.getElementById("admin_status").innerText="Room Created: "+data.room_id;
    roomId=data.room_id;
    joinRoom(roomId);
  }
}

// ---------------- ROOM ----------------
async function joinRoom(rid){
  roomId=rid;
  await fetch(`${API_BASE}/join_room?token=${token}&room_id=${roomId}`,{method:"POST"});
  connectWS();
  document.getElementById("game").style.display="block";
  document.getElementById("room_id").innerText=roomId;
}

// ---------------- WEBSOCKET ----------------
function connectWS(){
  ws=new WebSocket((location.protocol==="https:"?"wss://":"ws://")+location.host+`/ws/${roomId}/${token}`);
  ws.onmessage=(e)=>{ const data=JSON.parse(e.data);
    if(data.type=="draw") draw(data.x,data.y);
    if(data.type=="new_round"){ document.getElementById("drawer").innerText=data.drawer; ctx.clearRect(0,0,canvas.width,canvas.height);}
    if(data.type=="timer") document.getElementById("timer").innerText=data.time;
    if(data.type=="guess_correct"){ appendChat(data.user+" guessed correctly!"); }
    if(data.type=="game_over"){ appendChat("Game over! Scores: "+JSON.stringify(data.scores)); }
  }
}

// ---------------- DRAW ----------------
canvas.addEventListener("mousedown",()=>drawing=true);
canvas.addEventListener("mouseup",()=>drawing=false);
canvas.addEventListener("mousemove",(e)=>{ if(!drawing||!ws)return; sendDraw(e); });
canvas.addEventListener("touchmove",(e)=>{ if(!ws)return; sendDraw(e.touches[0]); });

function sendDraw(e){
  const rect=canvas.getBoundingClientRect();
  const x=e.clientX-rect.left, y=e.clientY-rect.top;
  draw(x,y);
  ws.send(JSON.stringify({type:"draw",x,y}));
}
function draw(x,y){ ctx.fillRect(x,y,4,4); }

// ---------------- GUESS ----------------
function sendGuess(){
  const g=document.getElementById("guess").value;
  ws.send(JSON.stringify({type:"guess",guess:g}));
  document.getElementById("guess").value="";
}

function appendChat(msg){
  const div=document.getElementById("chat");
  div.innerHTML+=msg+"<br>";
  div.scrollTop=div.scrollHeight;
}