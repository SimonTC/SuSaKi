wgPageName === "Special:Search" && $(document).ready(function($){
  var redlink = true;
  var $a = $(".mw-search-createlink .new");
  if ( $a.length === 0 ){
  	$a = $(".mw-search-createlink a");
  	redlink = false;
  }
  if ( $a.length === 0 ){return;}
  var htitle = $a.text(), href = $a.attr("href"), $s = $(".searchresults");
  $.get("/w/api.php", { format: "json", action: 'query', generator: 'backlinks', gbltitle: htitle, gblnamespace: 0, prop: 'revisions', rvprop: 'content' }, function(b){
    if ( !b || !b.query ){return;}
    b = b.query.pages;
    for ( var i in b ){
      var c = b[i].revisions[0]['*'], title = b[i].title, 
        r = new RegExp("\\n\\*+:?\\s+\\[?\\[?([^\\]:\\n]+)\\]?\\]?:[^\\n]*\\{\\{t[-+ø]?\\|([^|]+)\\|" + htitle + "(\\|[^\\}\\|]+)*\\}\\}","g"), m, 
        rr = /\{\{trans-top(\|?[^\}]*)\}\}/g, transtops = [];
      for( ; m = rr.exec( c ); ){
        transtops.push( m );
      }
      for( ; m = r.exec( c ); ){
        for( ; transtops[1] && m.index > transtops[1].index; ){
          transtops.shift();
        }
        var mo = {
          gloss: transtops[0][1] && transtops[0][1].substr(1),
          langname: m[1],
          langcode: m[2]
        };
        if( mo.langname.substr(0, 6) === "\{\{ttbc" ){
          continue;
        }
        for( ; m.length > 3; ){
          var p = m.pop();
          if( p && ( p = p.split("=") ).length === 2 ){
            mo[ p[ 0 ].substr(1) ] = p[1];
          }
        }
        $s.prepend( newNode("p", newNode("a", {'class': (mo.sc || "Latn") + " mention-" + (mo.sc || "Latn") + (redlink?" new":""), lang: mo.langcode, href: href + (redlink?"":"#"+mo.langname), style: "font-weight: 700;"}, mo.alt || htitle), " is a" + ( "AEIOU".indexOf( mo.langname.charAt( 0 ) )=== -1 ? " " : "n " ) + mo.langname + " translation of the word ", newNode("a", {style: "font-weight: 700;", class: "mention-Latn", href: "/wiki/" + title}, title), (mo.gloss ? " (\"" + mo.gloss + "\")" : "") + ".") );
      }
    }
  });
});