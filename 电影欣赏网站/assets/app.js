
document.addEventListener('click', function(e){
  if(e.target.matches('.read-more')){
    e.preventDefault();
    var href = e.target.getAttribute('href');
    window.location = href;
  }
});
