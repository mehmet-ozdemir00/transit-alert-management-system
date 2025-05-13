const BASE_API = "https://l4wefjcn1i.execute-api.us-east-1.amazonaws.com/dev";
const STATUS_API_URL = `${BASE_API}/status`;

document.getElementById("load-status-btn").addEventListener("click", async () => {
  const messageEl = document.getElementById("status-message");
  const resultsEl = document.getElementById("status-results");

  messageEl.textContent = "";
  resultsEl.innerHTML = "";
  resultsEl.style.display = "none";

  try {
    const response = await fetch(STATUS_API_URL);
    const result = await response.json();

    if (!response.ok) {
      messageEl.textContent = result.error || "Failed to fetch statuses.";
      messageEl.className = "message error";
      return;
    }

    const subscriptions = result.subscriptions.filter(sub => sub.email_status === "confirmed");

    if (subscriptions.length === 0) {
      messageEl.textContent = "No confirmed subscriptions available.";
      messageEl.className = "message";
      return;
    }

    resultsEl.innerHTML = `<h4>Confirmed Subscriptions</h4>`;
    subscriptions.forEach(sub => {
      resultsEl.innerHTML += `
        <div class="subscription-alert">
          <p><strong>Email:</strong> ${sub.email}</p>
          <p><strong>Route:</strong> ${sub.bus_route}</p>
          <p>⚠️ <strong>Delay Alert:</strong> Anticipated 15-minute delay.</p>
        </div>
      `;
    });

    resultsEl.style.display = "block";
    messageEl.textContent = "";
  } catch (error) {
    messageEl.textContent = "Network error while fetching statuses.";
    messageEl.className = "message error";
  }
});
