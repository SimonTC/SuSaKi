// This script adds an "Add definition" button to the toolbox section of the sidebar.

var bodyContent;

if(mw.config.get("wgNamespaceNumber") == 0 && mw.config.get("wgCurRevisionId") && mw.config.get("wgAction") == "view" && !/&printable=yes|&diff=|&oldid=/.test(window.location.search))
{
  jQuery(document).ready(function()
  {
    bodyContent = document.getElementById('bodyContent');
    mw.util.addPortletLink('p-tb', 'javascript:addDefinition()', 'Add definition');
  });
}

var currentBoxToBeAdded, definitionHover, tempDefinitionText

function setUpBoxToBeAdded()
{
  bodyContent.appendChild(currentBoxToBeAdded);
  document.onmousemove =
    function (e)
    {
      e = e || event;
      currentBoxToBeAdded.style.left = e.clientX + 2 + 'px';
      currentBoxToBeAdded.style.top = e.clientY + 2 + 'px';
    };
  document.body.style.cursor = 'move';
}

function addDefinition()
{
  var instructions = "Type in your definition, drag it to where it should be placed, and click there to place it.",
    temp;
  currentBoxToBeAdded =
  (
    newNode
    (
      'div',
      {
        style:
          'border: 1px solid #000000;' +
          'position:fixed; left:200px; top:500px; z-index:5;' +
          'padding:10px; background-color:#FFFFFF;'
      },
      newNode
      (
        'nobr',
        'Definition: ',
        newNode
        (
          'input',
          {
            size: 100,
            blur: function(){
              if(definitionHover)
                {addDefinition2(definitionHover, currentBoxToBeAdded.lastChild.lastChild.value.replace(instructions,''))}
              else
                {tempDefinitionText=currentBoxToBeAdded.lastChild.lastChild.value.replace(instructions,'');}
              bodyContent.removeChild(currentBoxToBeAdded);
              document.onmousemove = null;
              document.body.style.cursor = '';
              for(var ols = document.getElementsByTagName('ol'), i = 0; i < ols.length; i++)
              {
                for(var lis = ols[i].getElementsByTagName('li'), ii = 0; ii < lis.length; ii++)
                {
                  if(lis[ii].parentNode == ols[i])
                  {
                    lis[ii].onmouseover = lis[ii].onmouseout = null
                  }
                }
              }
            },
            value: tempDefinitionText || ""
          }
        )
      )
    )
  );
  setUpBoxToBeAdded();
  temp=currentBoxToBeAdded.lastChild.lastChild
  temp.focus();
  if(!temp.value){
    temp.value = instructions
    temp.style.color="#AAA"
    temp.onkeydown=function(){
      this.style.color = "#000";
      this.value=''
      this.onkeydown=null
      }
    }

  for(var ols = document.getElementsByTagName('ol'), i = 0; i < ols.length; i++)
  {
    for(var lis = ols[i].getElementsByTagName('li'), ii = 0; ii < lis.length; ii++)
    {
      if(lis[ii].parentNode == ols[i])
      {
        lis[ii].onmouseover =
          function () { this.style.borderBottom = '1px solid #000000'; definitionHover=this; };
        lis[ii].onmouseout =
          function () { this.style.borderBottom = this.style.borderTopStyle=="dashed"?"2px #00FF00 dashed":""; definitionHover=null };
      }
    }
  }
}

function addDefinition2(q, newdef)
{
  q.style.borderBottom = q.style.borderTopStyle=="dashed"?"2px #00FF00 dashed":"";
  definitionHover = tempDefinitionText = null;

  var qq = newNode('li', newNode('span'));
  JsMwApi().page(mw.config.get("wgPageName")).parseFragment(newdef, function (res) { qq.lastChild.innerHTML = res; });

  function addDefinition3(wikitext)
  {
    var prevheader = q, prevols=0, prevlis=1;
    while(prevheader.previousSibling)
      { 
        prevheader = prevheader.previousSibling; 
        if(prevheader.nodeName.toLowerCase() == "li")
          {prevlis++}
      }
    prevheader=prevheader.parentNode;
    while(! /^h\d$/i.test(prevheader.nodeName))
      { 
        prevheader = prevheader.previousSibling; 
        if(prevheader.nodeName.toLowerCase() == "ol")
          {prevols++}
      }

    var findNumberOfHeaders =
      Number(prevheader.lastChild.getElementsByTagName('a')[0].href.match(/\d*$/));
    wikitext =
    (
      wikitext.replace
      (
        RegExp("((?:(^|\n)=[\\s\\S]*?){" + findNumberOfHeaders + "}([\\s\\S]*?\n#[\\s\\S]*?\n(?!#)){" + prevols+ "}([\\s\\S]*?\n#(?![#:\\*])){" + prevlis + "}[\\s\\S]*?)(\n(?!#[#:\\*])|$)"),
        '$1\n# ' + newdef + '\n'
      )
    );
    return ccc = wikitext;
  }

  var updatecatscallback,
    editor=new Editor()
  editor.addEdit({
              edit: addDefinition3,
              redo: function ()
                    {
                      q.parentNode.insertBefore(qq, q.nextSibling);
                      if(window.makedefsidebox && qq.childNodes.length == 1 && window.defsidebuttons && defsidebuttons.length)
                        { makedefsidebox(qq); } // User:Yair_rand/editor.js stuff
                      if(window.updateCategories && window.tabbedLanguages)
                        { updatecatscallback = updateCategories((q.parentNode.parentNode.nodeName.toLowerCase()=="li"?q.parentNode.parentNode:q).parentNode.parentNode, newdef); } 
                    },
            undo: function () { q.parentNode.removeChild(qq); updatecatscallback && updatecatscallback() },
            summary: "+def: " +newdef
        }, qq);
}