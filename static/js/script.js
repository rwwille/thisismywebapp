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

// let startTime;
// let endTime;

// // Assume this function is called when the user starts an activity
// function startActivity() {
//     startTime = Date.now();
// }

// // Assume this function is called when the user ends an activity
// function endActivity() {
//     endTime = Date.now();

//     // Now send the start and end times to the server
//     fetch('/your-flask-route', {
//         method: 'POST',
//         headers: {
//             'Content-Type': 'application/json',
//         },
//         body: JSON.stringify({
//             startTime: startTime,
//             endTime: endTime,
//             // Include any other data about the activity here
//         }),
//     })
//         .then(response => response.json())
//         .then(data => console.log('Success:', data))
//         .catch((error) => console.error('Error:', error));
// }
