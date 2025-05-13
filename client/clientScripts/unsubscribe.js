const BASE_API = "https://l4wefjcn1i.execute-api.us-east-1.amazonaws.com/dev";
const UNSUBSCRIBE_API_URL = `${BASE_API}/unsubscribe`;

// Helper: email validator
function validateEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email.toLowerCase());
}

document.getElementById("unsubscribe-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const email = document.getElementById("email").value.trim();
  const messageEl = document.getElementById("unsubscribe-message");

  messageEl.textContent = "";
  messageEl.className = "message";

  if (!validateEmail(email)) {
    messageEl.textContent = "Please enter a valid email address.";
    messageEl.classList.add("error");
    return;
  }

  try {
    const response = await fetch(UNSUBSCRIBE_API_URL, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ email })
    });

    const result = await response.json();

    if (!response.ok) {
      messageEl.textContent = result.error || "Failed to unsubscribe.";
      messageEl.classList.add("error");
    } else {
      messageEl.textContent = result.message || "You have been unsubscribed.";
      messageEl.classList.add("success");
    }
  } catch (err) {
    messageEl.textContent = "Network error. Please try again later.";
    messageEl.classList.add("error");
  }
});
