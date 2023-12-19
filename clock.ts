let hrs = document.getElementById("hrs") as HTMLDivElement;
let min = document.getElementById("min") as HTMLDivElement;
let sec = document.getElementById("sec") as HTMLDivElement;

setInterval(()=>{
  let currentTime = new Date();

  hrs.innerHTML = (currentTime.getHours()<10?"0":"") + currentTime.getHours();
  min.innerHTML = (currentTime.getMinutes()<10?"0":"") + currentTime.getMinutes();
  sec.innerHTML = (currentTime.getSeconds()<10?"0":"") + currentTime.getSeconds();
}, 1000)
