// Thanks to author of this cool javascript :)

function getCursor(input){
	var result = {start: 0, end: 0};
	if (input.setSelectionRange){
		result.start= input.selectionStart;
		result.end = input.selectionEnd;
	} else if (!document.selection) {
		return false;
	} else if (document.selection && document.selection.createRange) {
		var range = document.selection.createRange();
		var stored_range = range.duplicate();
		stored_range.moveToElementText(input);
		stored_range.setEndPoint('EndToEnd', range);
		result.start = stored_range.text.length - range.text.length;
		result.end = result.start + range.text.length;
	}
	return result;
}

function setCursor(txtarea, start, end){
	if(txtarea.createTextRange) {
		var range = txtarea.createTextRange();
		range.move("character", start);
		range.select();
	} else if(txtarea.selectionStart) {
		txtarea.setSelectionRange(start, end);
	}
}

function insert_tag(startTag, endTag){
	var txtarea = document.getElementById("id_info") || document.getElementById("id_msg_input");
	txtarea.focus();

	var scrtop = txtarea.scrollTop;

	var cursorPos = getCursor(txtarea);
	var txt_pre = txtarea.value.substring(0, cursorPos.start);
	var txt_sel = txtarea.value.substring(cursorPos.start, cursorPos.end);
	var txt_aft = txtarea.value.substring(cursorPos.end);

	if (cursorPos.start == cursorPos.end){
		var nuCursorPos = cursorPos.start + startTag.length;
	}else{
		var nuCursorPos=String(txt_pre + startTag + txt_sel + endTag).length;
	}
	txtarea.value = txt_pre + startTag + txt_sel + endTag + txt_aft;
	setCursor(txtarea,nuCursorPos,nuCursorPos);

	if (scrtop) txtarea.scrollTop=scrtop;
}

function insert_text(tagName){
	if (tagName == 'moderator') {
		var startTag = '<span class="moderator">';
		var endTag = '</span>';
	} else {
		var startTag = '<' + tagName + '>';
		var endTag = '</' + tagName + '>';
	}
	insert_tag(startTag, endTag);	
	return false;
}

function insert_image(){
	var src = prompt('enter image src', 'http://');
	if(src){
		insert_tag('<img src="' + src + '" alt="image">', '');
	}
}

function insert_link(){
	var href = prompt('Введите ссылку', 'http://');
	if(href){
		insert_tag('<a href="' + href + '">', '</a>');
	}
}