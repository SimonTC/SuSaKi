/*jshint undef:true, strict:true */
/*global mw, jQuery, newNode */
/** 

  Adds a feedback to to the bottom of the page on the left. This has only been tested with Monobook as it is intended for IPs only.

**/

var fb_comment_url = mw.config.get('wgScript') +
  "?title=Wiktionary:Feedback"+
  "&action=edit&section=new"+
  "&preload=Wiktionary:Feedback%2Fpreload"+
  "&editintro=Wiktionary:Feedback%2Fintro"+
  "&preloadtitle="+
   encodeURIComponent("[[:"+mw.config.get('wgPageName').replace(/_/g, ' ')+"]]");

var fb_thanks = "Thank you for giving us some of your time.";
var fb_comment = "If you have time, leave us a note.";

var fb_questions = [];

fb_questions[0] = 
["Submit anonymous feedback about Wiktionary:",
  ['Good', 
   'Bad', 
   'Messy', 
   'Mistake in definition',
   'Confusing',
   'Could not find the word I want', 
   'Incomplete', 
   'Entry has inaccurate information',
   'Definition is too complicated']
];

var fb_options;
var fb_text;
var fb_sent = false;
var fb_sent2= false;

function fb_buildBox(){
  var sidebar = document.getElementById('mw-panel');
  if(!sidebar) return false;

/*  
  var list = newNode('ul',{'id':'fb_list'});
  
  for(var i=0;i<fb_options.length;i++){
    list.appendChild( 
      newNode('li',
        newNode('a',{'click':fb_click,'id':"FB"+i},fb_options[i]) 
      )
    );
  }
 */

  sidebar.appendChild(    
    newNode('div',{'class':"portal expanded",'id':"p-feedback"},
      newNode('a',{'name':"feedback"}),
      newNode('h3',"Feedback"),
      newNode('div',{'class':"body", 'style':"display: block;"},
//      newNode('p',{'style':'font-size: 90%'},fb_text),
//      list,
        newNode('p',{'style':'font-size: 80%'},
          newNode('a',{'href':fb_comment_url},fb_comment)
        )
      )
    )
  );
}

function fb_click(e){
  var fb = false;
  var fbi = false;
  
  try{
    fb = e.target.childNodes[0].nodeValue;
    fbi = e.target.getAttribute('id').replace("FB",'');
  }catch(e){ try{
    fb = window.event.srcElement.childNodes[0].nodeValue;
    fbi = window.event.srcElement.getAttribute('id').replace("FB",'');
  } catch(e){ }}
  
  if(fb){
    fb_send(fb);
  }
  
  var list = document.getElementById('fb_list');
  
  list.parentNode.insertBefore(
    newNode('p',fb_thanks),list
  );
  list.parentNode.removeChild(list);
  
  return false;  
}

function fb_send(string) {
  if (fb_sent) return false;
  fb_sent = true;
  
  var wiki = mw.config.get('wgServer').replace(/(https?:)?\/\/([^\.]*\.[^\.]*)\.org/, "$2");
  
  var page = mw.config.get('wgPageName');
  if (mw.config.get('wgCanonicalSpecialPageName') === 'Search'){
    var sb = document.getElementById('lsearchbox');
    if (sb) page += ('/' + sb.value);
  }
  var url = '//toolserver.org/~enwikt/feedback/?action=feedback' +
    '&wiki=' + encodeURIComponent(wiki) +
    '&title=' + encodeURIComponent(page) +
    '&feedback=' + encodeURIComponent(string);

  document.body.appendChild(
    newNode('iframe',{'src':url,'style':'display:none'})
 ); 
}

jQuery(function () {
  var index = Math.floor(Math.random()*(fb_questions.length)); 
  fb_text = fb_questions[index][0];
  fb_options = fb_questions[index][1]; 
  fb_buildBox();
});