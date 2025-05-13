const BASE_API = "https://l4wefjcn1i.execute-api.us-east-1.amazonaws.com/dev";
const SUBSCRIPTION_API_URL = `${BASE_API}/subscription`;

function validateEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email.toLowerCase());
}

document.getElementById("remove-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("email").value.trim();
  const route = document.getElementById("route").value.trim();
  const messageEl = document.getElementById("remove-message");

  messageEl.textContent = "";
  messageEl.className = "message";

  if (!validateEmail(email) || !route) {
    messageEl.textContent = "Please provide a valid email and route.";
    messageEl.classList.add("error");
    return;
  }

  try {
    const url = `${SUBSCRIPTION_API_URL}?route=${encodeURIComponent(route)}`;

    const response = await fetch(url, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ email })
    });

    const result = await response.json();

    if (!response.ok) {
      messageEl.textContent = result.error || "Failed to remove subscription.";
      messageEl.classList.add("error");
    } else {
      messageEl.textContent = result.message || "Subscription removed successfully.";
      messageEl.classList.add("success");
    }
  } catch (err) {
    messageEl.textContent = "Network error. Please try again.";
    messageEl.classList.add("error");
  }
});
