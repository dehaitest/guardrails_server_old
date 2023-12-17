var socket = io.connect('http://localhost:5000');

$(document).ready(function() {
    $('#userInput').keypress(function(event) {
        // Check if the pressed key is the Enter key (keycode 13)
        if (event.which == 13) {
            event.preventDefault(); // Prevent default action (like form submission)
            sendMessage();  // Call the sendMessage function
        }
    });
});

// Handle the "Add guardrails" button click
function addGuardrails() {
    let checkboxes = $('#checkboxList input:checkbox:checked, #anotherCheckboxList input:checkbox:checked').map(function() {
        return this.value;
    }).get();
    socket.emit('add_guardrails', {selected_options: checkboxes});
}

socket.on('receive_message', function(data) {
    $('#messages').append('<div class="server-message message">' + data.msg + '</div>');
    // Auto-scroll to the latest message
    $('#messages').scrollTop($('#messages')[0].scrollHeight);
});

socket.on('chain_message', function(data) {
    var messageElement;
    if (data.type === "end") {
        messageElement = '<div class="hr-line"></div>';
    } else {
        messageElement = '<div class="chain-message ' + data.type + '" style="text-align: center;"><strong>' + data.type.toUpperCase() + ':</strong> ' + data.content + '</div><div class="down-arrow"></div>';
    }
    $('#chainProgress').append(messageElement);
    $('#chainProgress').scrollTop($('#chainProgress')[0].scrollHeight);
});


socket.on('background_message', function(data) {
    var currentContent = $('#backendResponse').val();
    $('#backendResponse').val(currentContent + '\n' + data.content);
    $('#backendResponse').scrollTop($('#backendResponse')[0].scrollHeight);
});

function sendMessage() {
    let message = $('#userInput').val().trim();
    let instruction = $('#textEditField').val();
    if (message) { // Check if the message is not empty
        $('#messages').append('<div class="user-message message">' + message + '</div>');
        $('#messages').scrollTop($('#messages')[0].scrollHeight);
        socket.emit('send_message', {msg: message, ins: instruction});
        $('#userInput').val('');
    }
}

function sendSplContent() {
    let message = $('#textEditField').val();
    
    // Emit the message and wait for an acknowledgement from the server
    socket.emit('send_Spl', {msg: message}, function(acknowledgement) {
        if (acknowledgement.success) {
            loadCheckboxLists();
        } else {
            console.error("Error sending message:", acknowledgement.error);
        }
    });
}

function loadCheckboxLists() {
    $.getJSON('/get-checkbox-lists', function(data) {
        // Clear previous checkboxes, if any
        $('#checkboxListContainer').empty();
        $('#anotherCheckboxListContainer').empty();

        // Populate the checkboxes for the first list
        data.list1.forEach(function(item) {
            $('#checkboxListContainer').append('<div class="form-check"><input type="checkbox" class="form-check-input" value="' + item + '"><label class="form-check-label">' + item + '</label></div>');
        });

        // Populate the checkboxes for the second list
        data.list2.forEach(function(item) {
            $('#anotherCheckboxListContainer').append('<div class="form-check"><input type="checkbox" class="form-check-input" value="' + item + '"><label class="form-check-label">' + item + '</label></div>');
        });
    });
} 