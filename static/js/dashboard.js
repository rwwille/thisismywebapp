document
    .getElementById("newActivityForm")
    .addEventListener("submit", function (event) {
        event.preventDefault();

        const newActivityName =
            document.getElementById("newActivityName").value;
        console.log(newActivityName);

        fetch("/add_activity", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ name: newActivityName }),
        })
            .then((response) => response.json())
            .then((data) => {
                var select = document.getElementById("activitySelect");
                var option = document.createElement("option");
                option.value = data.id;
                option.text = data.name;
                select.add(option);
            });
    });

var startButton = document.getElementById("startButton");
var stopButton = document.getElementById("stopButton");
var timer = document.getElementById("timer");
var resetButton = document.getElementById("saveButton");
var startTime;
var endTime;
var elapsedTime;

var hours = 0,
    minutes = 0,
    seconds = 0,
    t;

function add() {
    seconds++;
    if (seconds >= 60) {
        seconds = 0;
        minutes++;
        if (minutes >= 60) {
            minutes = 0;
            hours++;
        }
    }

    timer.textContent =
        (hours ? (hours > 9 ? hours : "0" + hours) : "00") +
        ":" +
        (minutes ? (minutes > 9 ? minutes : "0" + minutes) : "00") +
        ":" +
        (seconds > 9 ? seconds : "0" + seconds);

    timerCycle();
}

function timerCycle() {
    t = setTimeout(add, 1000);
}

startButton.onclick = timerCycle;

stopButton.onclick = function () {
    clearTimeout(t);
};

resetButton.onclick = function () {
    timer.textContent = "0:00:00";
    seconds = 0;
    minutes = 0;
    hours = 0;
};
startButton.addEventListener("click", function () {
    startTime = Date.now();
    console.log(startTime);
    startButton.disabled = true;
    stopButton.disabled = false;
    document.getElementById("saveButton").disabled = true;
});

stopButton.addEventListener("click", function () {
    endTime = Date.now();
    console.log(endTime);
    elapsedTime = endTime - startTime;
    console.log(elapsedTime);
    document.getElementById("saveButton").disabled = false;
    startButton.disabled = false;
    stopButton.disabled = true;
});

document
    .getElementById("recordActivityForm")
    .addEventListener("submit", function (event) {
        event.preventDefault();

        var activityId = document.getElementById("activitySelect").value;
        console.log(activityId);
        var notes = document.getElementById("notes").value;

        fetch("/save_record", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                activityId: activityId,
                startTime: startTime,
                endTime: endTime,
                notes: notes,
                elapsedTime: elapsedTime,
            }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.id) {
                    console.log("Record added successfully with ID: " + data.id);
                    // Clear the form fields after successful submission
                    document.getElementById("activitySelect").value = "";
                    document.getElementById("notes").value = "";
                    document.getElementById("timer").textContent = "0:00:00";
                    // Make the element with id="activityData" not visible
                    document.getElementById("activityData").style.display = "none";
                } else {
                    console.log("An error occurred while adding the record.");
                }
            })
            .catch((error) => console.error("Error:", error));
    });


document.getElementById("activitySelect").addEventListener("change", function () {
    var sel = document.getElementById("activitySelect");
    var selectedActivity = sel.options[sel.selectedIndex].text;
    console.log(selectedActivity);
    fetch('/get_activity_data/' + selectedActivity).then(response => response.json())
        .then(data => {
            // update the HTML content of the page with the fetched data
            document.getElementById("activityData").innerHTML =
                '<p>Activity: ' + data.name + '</p>' +
                '<p>Total Time: ' + data.total_time + '</p>' +
                '<p>10,000 Hours: ' + data.percent + '</p>' +
                '<p>Previous: ' + data.last_pt + " --- " + data.last_prac + '</p>';
            document.getElementById("activityData").style.display = "block";

        });
});


document.addEventListener("DOMContentLoaded", function () {
    const habitsList = document.getElementById("habitsList");
    // Get the completed habits from the session (if any)
    const sessionCompletedHabits = JSON.parse(habitsList.getAttribute("data-completed-habits"));
    console.log(sessionCompletedHabits)
    const checkboxes = document.querySelectorAll('input[type="checkbox"][name="habit"]');
    // Function to check if a habit is completed for today
    function isHabitCompleted(habitId) {
        return sessionCompletedHabits && sessionCompletedHabits.includes(habitId);
    }

    // Function to update the appearance of the habit checkbox
    function updateHabitAppearance(habitId) {
        const habitElement = document.querySelector(`input[type="checkbox"][name="habit"][value="${habitId}"]`);
        if (isHabitCompleted(habitId)) {
            habitElement.checked = true;
            habitElement.nextElementSibling.classList.add("done");
        } else {
            habitElement.checked = false;
            habitElement.nextElementSibling.classList.remove("done");
        }
    }

    // Call this function for each habit to update their appearance
    const habitCheckboxes = document.querySelectorAll('input[type="checkbox"][name="habit"]');
    habitCheckboxes.forEach((checkbox) => {
        const habitName = checkbox.value;
        updateHabitAppearance(habitName);
    });

    // Add event listener to update habit appearance on checkbox change
    habitCheckboxes.forEach((checkbox) => {
        checkbox.addEventListener("change", function () {
            const habitName = this.value;
            const completed = this.checked;
            if (completed) {
                markHabitCompleted(habitName);
            } else {
                unmarkHabitCompleted(habitName);
            }
        });
    });
});

// Function to handle marking a habit as completed
function markHabitCompleted(habitId) {
    fetch(`/mark_habit_completed/${habitId}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
    })
        .then((response) => response.json())
        .then((data) => {
            // If the request is successful, update the appearance of the habit to indicate it's completed.
            if (data.message === "Habit marked as completed") {
                updateHabitAppearance(habitId);
            }
        })
        .catch((error) => {
            console.error("Error completing habit:", error);
        });
}

// Function to handle unmarking a habit as completed
function unmarkHabitCompleted(habitId) {
    fetch(`/unmark_habit_completed/${habitId}`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
    })
        .then((response) => response.json())
        .then((data) => {
            // If the request is successful, update the appearance of the habit to indicate it's not completed.
            if (data.message === "Habit unmarked as completed") {
                updateHabitAppearance(habitId);
            }
        })
        .catch((error) => {
            console.error("Error unmarking habit:", error);
        });
}

document.addEventListener("DOMContentLoaded", function () {
    const addHabitForm = document.getElementById("habitsForm");

    // Add event listener for the form submission
    addHabitForm.addEventListener("submit", function (event) {
        event.preventDefault();

        // Get the new habit name from the form input
        const newHabitName = document.getElementById("habitName").value;

        // Send a POST request to the server to add the new habit
        fetch("/add_habit", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ name: newHabitName }),
        })
            .then((response) => response.json())
            .then((data) => {
                // After successfully adding the habit, you can update the UI or perform any other actions as needed.
                console.log("New habit added:", data);

                // For example, you can clear the form input field after adding the habit.
                document.getElementById("habitName").value = "";

            })
            .catch((error) => {
                console.error("Error adding habit:", error);
            });
        setTimeout(function () {
            window.location.reload();
        }, 500);
    });
});

function markCompletedHabitsAsDone(completedHabits) {
    const checkboxes = document.querySelectorAll('input[type="checkbox"][name="habit"]');
    checkboxes.forEach((checkbox) => {
        const habitName = checkbox.value;
        if (completedHabits.includes(habitName)) {
            checkbox.checked = true;
            checkbox.nextElementSibling.classList.add("done");
        }
    });
}

document.addEventListener("DOMContentLoaded", function () {
    // Fetch the completed habits from the server
    fetch("/get_completed_habits")
        .then((response) => response.json())
        .then((data) => {
            const completedHabits = data;
            markCompletedHabitsAsDone(completedHabits);
        })
        .catch((error) => {
            console.error("Error fetching completed habits:", error);
        });

    // Rest of the code...
});
