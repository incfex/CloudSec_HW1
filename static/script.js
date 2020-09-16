'use strict';

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

document.addEventListener('DOMContentLoaded', function () {
  reqJSON('GET', '/events')
    .then(({ status, data }) => {
      console.log(data)
      var tblBody = document.getElementById('event-table');
      for (let r of data) {
        let row = document.createElement("tr");
        
        let time_cell = document.createElement("td")
        let time_cellText = document.createTextNode(r.time)
        time_cell.appendChild(time_cellText)
        row.appendChild(time_cell)

        let name_cell = document.createElement("td")
        let name_cellText = document.createTextNode(r.name)
        name_cell.appendChild(name_cellText)
        row.appendChild(name_cell)

        let event_date = new Date(r.time)
        let date_diff = event_date - Date.now()
        console.log(date_diff)

        let left_cell = document.createElement("td")
        var left_cellText
        if (date_diff < 0) {
          left_cellText = document.createTextNode('Passed')
        }
        else {
          let seconds = Math.round(date_diff/1000)
          left_cellText = document.createTextNode(seconds + 's')
        }
        left_cell.appendChild(left_cellText)
        row.appendChild(left_cell)


        tblBody.appendChild(row)

        console.log(r)
      }
    })
});