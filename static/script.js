'use strict';

// Wrapper function from lab requirement
function reqJSON(method, url, data) {
  return new Promise((resolve, reject) => {
    let xhr = new XMLHttpRequest();
    xhr.open(method, url);
    xhr.responseType = 'json';

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve({ status: xhr.status, data: xhr.response });
      }
      else {
        reject({ status: xhr.status, data: xhr.response });
      }
    };
    xhr.onerror = () => {
      reject({ status: xhr.status, data: xhr.response });
    };

    xhr.send(data)
  });
}

// Handler for adding event
async function addEvent() {
  // get info from html
  var name = document.getElementById("event-name").value;
  var time = document.getElementById("event-time").value;
  // create payload
  var payload = {
    "name": name,
    "time": time
  };
  // send out request
  await reqJSON('POST', '/event', JSON.stringify(payload));
  // refresh events
  getEvent();
}

// Handler for deleting event
function delEvent(eventID) {
  // after send out delete request, refresh event
  reqJSON('DELETE','/event/'+eventID).then(getEvent());
}

// Make the clock tick tock
function countDown() {
  // find the table
  var table = document.getElementById("event-table")

  // make sure there are events
  if (table.hasChildNodes()) {
    // loop for each row
    table.childNodes.forEach((currentValue, currentIndex, listObj) => {
      // get the time string
      let t_text = currentValue.childNodes[2].innerText;
      // convert to int
      let t_int = parseInt(t_text.slice(0, -1));
      // if the timer reaches 0, trigger the delete function through getEvent()
      if (t_int <= 0) {getEvent()}
      // minus the current time by 1 second
      currentValue.childNodes[2].innerText = (t_int - 1) + 's';
    })
  }
}

// Handler for event table
function getEvent() {
  // get event info
  reqJSON('GET', '/events')
    .then(({ status, data }) => {
      // find the table element
      var tblBody = document.getElementById('event-table');
      // clear table
      tblBody.innerHTML = ""
      // loop through events
      for (let r of data) {
        // create a new row
        let row = document.createElement("tr");
        
        // create cell for event time
        let time_cell = document.createElement("td")
        let time_cellText = document.createTextNode(r.time)
        time_cell.appendChild(time_cellText)
        row.appendChild(time_cell)

        // create cell for event name
        let name_cell = document.createElement("td")
        let name_cellText = document.createTextNode(r.name)
        name_cell.appendChild(name_cellText)
        row.appendChild(name_cell)

        // calculate the time difference between now and the event
        let event_date = new Date(r.time)
        let date_diff = event_date - Date.now()

        // create cell for time left
        let left_cell = document.createElement("td")
        var left_cellText
        // logic for passed event
        if (date_diff < 0) {
          left_cellText = document.createTextNode('Passed')
          // delete passed event
          delEvent(r.id)
        }
        // logic for future event
        else {
          let seconds = Math.round(date_diff/1000)
          left_cellText = document.createTextNode(seconds + 's')
        }
        left_cell.appendChild(left_cellText)
        row.appendChild(left_cell)

        // make a delete button for corresponding event
        let del_button = document.createElement("button")
        del_button.innerHTML = "DELETE"
        del_button.addEventListener("click", () => {delEvent(r.id)})
        row.appendChild(del_button)

        // add row to table
        tblBody.appendChild(row)
      }
    })
}

// add listeners
document.getElementById("post").addEventListener("click", addEvent);
document.addEventListener('DOMContentLoaded', getEvent);
// start countdown function
setInterval(countDown, 1000)