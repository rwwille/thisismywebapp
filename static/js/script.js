document.getElementById('newActivityForm').addEventListener('submit', function (event) {
    event.preventDefault();
    var newActivityName = document.getElementById('newActivityName').value;
    // TODO: Send a request to the server to create a new activity
});

document.getElementById('newActivityForm').addEventListener('submit', function (event) {
    event.preventDefault();

    var newActivityName = document.getElementById('newActivityName').value;

    fetch('/add_activity', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name: newActivityName })
    })
        .then(response => response.json())
        .then(data => {
            var select = document.getElementById('activitySelect');
            var option = document.createElement('option');
            option.value = data.id;
            option.text = data.name;
            select.add(option);
        });
});
