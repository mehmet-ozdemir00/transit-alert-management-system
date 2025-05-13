const BASE_API = "https://l4wefjcn1i.execute-api.us-east-1.amazonaws.com/dev";
const SUBSCRIBE_API_URL = `${BASE_API}/subscribe`;

document.getElementById("subscribe-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const route = document.getElementById("route").value.trim();
  const stop_id = document.getElementById("stop_id").value.trim();
  const email = document.getElementById("email").value.trim();
  const messageEl = document.getElementById("message");

  messageEl.textContent = "";
  messageEl.className = "message";

  if (!route || !stop_id || !email) {
    showMessage("All fields are required.", "error");
    return;
  }

  if (!validateEmail(email)) {
    showMessage("Invalid email format.", "error");
    return;
  }

  try {
    const response = await fetch(SUBSCRIBE_API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ route, stop_id, email })
    });

    const result = await response.json();

    if (!response.ok) {
      showMessage(result.error || "An error occurred.", "error");
      hideBusInfo();
    } else {
      showMessage(result.message || "Subscription successful!", "success");
      showBusInfo(route, stop_id);
    }
  } catch (error) {
    showMessage("Network error. Please try again.", "error");
    hideBusInfo();
  }
});

function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function showMessage(msg, type) {
  const messageEl = document.getElementById("message");
  messageEl.textContent = msg;
  messageEl.className = `message ${type}`;
}

function showBusInfo(route, stopId) {
  let infoBox = document.getElementById("bus-info");

  if (!infoBox) {
    infoBox = document.createElement("div");
    infoBox.id = "bus-info";
    document.querySelector(".form-container").appendChild(infoBox);
  }

  infoBox.innerHTML = `
    <h4>Subscribed Route Info</h4>
    <p><strong>Route:</strong> ${route}</p>
    <p><strong>Stop ID:</strong> ${stopId}</p>
  `;
  infoBox.style.display = "block";
}

function hideBusInfo() {
  const infoBox = document.getElementById("bus-info");
  if (infoBox) {
    infoBox.style.display = "none";
  }
}
